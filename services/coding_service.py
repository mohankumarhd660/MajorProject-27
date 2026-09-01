import json
import re
import subprocess
import sys
import tempfile
import time
from shutil import which

from models.coding import CodingProblem, Submission
from utils.db import get_db_session

import re

_FORBIDDEN = [
    r"\bimport\s+os\b",
    r"\bimport\s+subprocess\b",
    r"\bimport\s+socket\b",
    r"\bopen\s*\(",
    r"__import__",
    r"eval\s*\(",
    r"exec\s*\(",
]

def _validate_code(code: str) -> str | None:
    for pat in _FORBIDDEN:
        if re.search(pat, code):
            return "Unsafe code detected"
    return None



LANGUAGE_TEMPLATES = {
    "python": """import sys

def solve(data: str) -> str:
    # Write your logic here
    return data.strip()

if __name__ == "__main__":
    raw = sys.stdin.read()
    print(solve(raw))
""",
    "javascript": """function solve(data) {
  // Write your logic here
  return data.trim();
}

const fs = require("fs");
const raw = fs.readFileSync(0, "utf8");
process.stdout.write(String(solve(raw)));
""",
    "cpp": """#include <bits/stdc++.h>
using namespace std;

string solve(const string& data) {
    // Write your logic here
    return data;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string input((istreambuf_iterator<char>(cin)), istreambuf_iterator<char>());
    cout << solve(input);
    return 0;
}
""",
    "java": """import java.io.*;

public class Main {
    static String solve(String data) {
        // Write your logic here
        return data.trim();
    }

    public static void main(String[] args) throws Exception {
        String input = new String(System.in.readAllBytes());
        System.out.print(solve(input));
    }
}
""",
}

SUPPORTED_LANGUAGES = set(LANGUAGE_TEMPLATES.keys())


def list_coding_problems(user_id: int = None):
    db = get_db_session()
    problems = db.query(CodingProblem).order_by(CodingProblem.id.asc()).all()
    
    if user_id is None:
        return problems
    
    # Get user's submissions grouped by problem
    from sqlalchemy import func
    
    user_status = (
        db.query(
            Submission.problem_id,
            func.max(Submission.status == "accepted").label("solved"),
            func.count(Submission.id).label("attempts")
        )
        .filter(Submission.user_id == user_id)
        .group_by(Submission.problem_id)
        .all()
    )
    
    status_map = {row.problem_id: row for row in user_status}
    
    results = []
    for p in problems:
        s = status_map.get(p.id)
        results.append({
            "problem": p,
            "solved": bool(s.solved) if s else False,
            "attempts": s.attempts if s else 0,
        })
    return results


def get_problem(problem_id: int):
    db = get_db_session()
    return db.query(CodingProblem).filter(CodingProblem.id == problem_id).first()


def _parse_tests(problem: CodingProblem) -> dict:
    try:
        raw = json.loads(problem.tests_json or "{}")
    except Exception:
        raw = {}

    if raw.get("type") == "leetcode_function":
        return raw

    constraints = raw.get("constraints") or [
        "Execution time limit: 2 seconds",
        "Avoid using system/network/file access",
        "Return exact output format",
    ]

    samples = raw.get("sample_tests") or []
    hidden = raw.get("hidden_tests") or []

    # Backward compatibility for old schema
    cases = raw.get("cases") or []
    if not samples and cases:
        samples = cases[:2]
    if not hidden and len(cases) > 2:
        hidden = cases[2:]

    if len(samples) < 2:
        samples.extend(
            [
                {"input": "hello world", "output": "hello world"},
                {"input": "  cursor ai  ", "output": "cursor ai"},
            ][: 2 - len(samples)]
        )
    if len(hidden) < 5:
        filler = [
            {"input": "A", "output": "A"},
            {"input": "123", "output": "123"},
            {"input": "test case", "output": "test case"},
            {"input": "line1\nline2", "output": "line1\nline2"},
            {"input": " edge ", "output": "edge"},
        ]
        hidden.extend(filler[: 5 - len(hidden)])

    solution = raw.get("solution") or {
        "code": LANGUAGE_TEMPLATES["python"],
        "explanation": "Read input, process it in solve(), and return the exact expected output.",
    }

    return {
        "constraints": constraints,
        "sample_tests": samples[:2],
        "hidden_tests": hidden[:5],
        "solution": solution,
    }


def get_problem_payload(problem_id: int):
    problem = get_problem(problem_id)
    if not problem:
        return None
    parsed = _parse_tests(problem)
    templates = LANGUAGE_TEMPLATES.copy()
    if parsed.get("type") == "leetcode_function":
        templates["python"] = problem.starter_code

    return {
        "id": problem.id,
        "title": problem.title,
        "difficulty": problem.difficulty,
        "description": problem.description,
        "templates": templates,
        "constraints": parsed.get("constraints", []),
        "sample_tests": parsed.get("sample_tests", []),
        "solution": parsed.get("solution", {}),
    }





def _run_subprocess(cmd: list[str], input_text: str, cwd: str):
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            input=input_text,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Execution timed out"}
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    output = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if proc.returncode != 0:
        return {"ok": False, "error": err or "Runtime error", "runtime_ms": elapsed_ms}
    return {"ok": True, "output": output, "runtime_ms": elapsed_ms}


def _execute_case(language: str, code: str, case_input: str, td: str, parsed: dict = None):
    if language == "python":
        if _validate_code(code):
            return {"ok": False, "error": "Unsafe code detected"}
        if parsed and parsed.get("type") == "leetcode_function":
            func_name = parsed.get("function_name", "solve")
            wrapper = f"""
import sys
import json
import numpy as np

# --- USER CODE START ---
{code}
# --- USER CODE END ---

if __name__ == "__main__":
    try:
        raw = sys.stdin.read()
        test_case = json.loads(raw) if raw.strip() else dict()
        solution = Solution()
        result = getattr(solution, '{func_name}')(**test_case)
        print(json.dumps(result))
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
"""
            return _run_subprocess([sys.executable, "-I", "-c", wrapper], case_input, td)
        
        return _run_subprocess([sys.executable, "-I", "-c", code], case_input, td)

    if language == "javascript":
        if not which("node"):
            return {"ok": False, "error": "Node.js runtime is not available on server"}
        return _run_subprocess(["node", "-e", code], case_input, td)

    if language == "cpp":
        if not which("g++"):
            return {"ok": False, "error": "g++ compiler is not available on server"}
        cpp_file = f"{td}/main.cpp"
        with open(cpp_file, "w", encoding="utf-8") as f:
            f.write(code)
        built = _run_subprocess(["g++", cpp_file, "-O2", "-std=c++17", "-o", f"{td}/main.exe"], "", td)
        if not built["ok"]:
            return {"ok": False, "error": f"Compile error: {built.get('error', '')}"}
        return _run_subprocess([f"{td}/main.exe"], case_input, td)

    if language == "java":
        if not which("javac") or not which("java"):
            return {"ok": False, "error": "Java runtime/compiler is not available on server"}
        java_file = f"{td}/Main.java"
        with open(java_file, "w", encoding="utf-8") as f:
            f.write(code)
        built = _run_subprocess(["javac", java_file], "", td)
        if not built["ok"]:
            return {"ok": False, "error": f"Compile error: {built.get('error', '')}"}
        return _run_subprocess(["java", "-cp", td, "Main"], case_input, td)

    return {"ok": False, "error": "Unsupported language"}


def _evaluate(problem: CodingProblem, language: str, code: str, include_hidden: bool):
    parsed = _parse_tests(problem)
    tests = list(parsed.get("sample_tests", []))
    if include_hidden:
        tests.extend(parsed.get("hidden_tests", []))

    results = []
    is_leetcode = parsed.get("type") == "leetcode_function"
    
    with tempfile.TemporaryDirectory() as td:
        for idx, case in enumerate(tests, start=1):
            if is_leetcode:
                input_str = json.dumps(case.get("input", {}))
                expected_obj = case.get("output")
            else:
                input_str = str(case.get("input", ""))
                expected_obj = str(case.get("output", "")).strip()

            res = _execute_case(language, code, input_str, td, parsed=parsed)
            if not res["ok"]:
                return {
                    "ok": False,
                    "status": "error",
                    "error": res["error"],
                    "failed_case": idx,
                    "results": results,
                }
                
            actual_raw = str(res.get("output", "")).strip()
            
            if is_leetcode:
                try:
                    passed = json.loads(actual_raw) == expected_obj
                except Exception:
                    passed = False
                expected_display = case.get("output_formatted") or json.dumps(expected_obj)
                actual_display = actual_raw
                input_display = case.get("input_formatted") or json.dumps(case.get("input", {}))
            else:
                passed = expected_obj == actual_raw
                expected_display = expected_obj
                actual_display = actual_raw
                input_display = str(case.get("input", ""))

            item = {
                "case": idx,
                "input": input_display,
                "expected": expected_display,
                "actual": actual_display,
                "passed": passed,
                "runtime_ms": res.get("runtime_ms", 0),
            }
            results.append(item)
            if not passed:
                return {
                    "ok": False,
                    "status": "failed",
                    "failed_case": idx,
                    "failed": item,
                    "results": results,
                }

    return {"ok": True, "status": "accepted", "results": results}


def run_code(
    user_id: int,
    problem_id: int,
    code: str,
    language: str = "python",
    custom_input: str | None = None,
) -> dict:
    language = (language or "python").lower()
    if language not in SUPPORTED_LANGUAGES:
        return {"ok": False, "error": "Unsupported language"}

    err = _validate_code(code)
    if err and language == "python":
        return {"ok": False, "error": err}

    db = get_db_session()
    problem = get_problem(problem_id)
    if not problem:
        return {"ok": False, "error": "Problem not found"}

    if custom_input is not None:
        with tempfile.TemporaryDirectory() as td:
            parsed = _parse_tests(problem)
            res = _execute_case(language, code, str(custom_input), td, parsed=parsed)
        if res.get("ok"):
            result = {
                "ok": True,
                "status": "ran",
                "mode": "custom_input",
                "output": res.get("output", ""),
                "runtime_ms": res.get("runtime_ms", 0),
            }
        else:
            result = {
                "ok": False,
                "status": "error",
                "mode": "custom_input",
                "error": res.get("error", "Execution failed"),
                "runtime_ms": res.get("runtime_ms", 0),
            }
    else:
        result = _evaluate(problem, language, code, include_hidden=False)

    status = "ran" if result.get("ok") else result.get("status", "error")
    output = json.dumps(result, ensure_ascii=False, indent=2)[:8000]

    db.add(
        Submission(
            user_id=user_id,
            problem_id=problem_id,
            code=code,
            language=language,
            status=status,
            output=output,
        )
    )
    db.commit()

    return result


def submit_code(user_id: int, problem_id: int, code: str, language: str = "python") -> dict:
    language = (language or "python").lower()
    if language not in SUPPORTED_LANGUAGES:
        return {"ok": False, "error": "Unsupported language"}

    db = get_db_session()
    problem = get_problem(problem_id)
    if not problem:
        return {"ok": False, "error": "Problem not found"}

    result = _evaluate(problem, language, code, include_hidden=True)
    status = "accepted" if result.get("ok") else result.get("status", "failed")

    db.add(
        Submission(
            user_id=user_id,
            problem_id=problem_id,
            code=code,
            language=language,
            status=status,
            output=json.dumps(result, ensure_ascii=False, indent=2)[:8000],
        )
    )
    db.commit()

    return result
