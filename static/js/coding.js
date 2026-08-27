(function () {
  const meta = App.readJsonScript('problemMeta');
  const editorHost = document.getElementById('monacoEditor');
  const runBtn = document.getElementById('runBtn');
  const submitBtn = document.getElementById('submitBtn');
  const outputBox = document.getElementById('outputBox');
  const languageSelect = document.getElementById('languageSelect');
  const sampleCases = document.getElementById('sampleCases');
  const constraintsBox = document.getElementById('constraintsBox');
  const editorialCode = document.getElementById('editorialCode');
  const editorialExplanation = document.getElementById('editorialExplanation');

  if (!meta || !editorHost || !runBtn || !submitBtn || !outputBox || !languageSelect) return;

  // Render Editorial content
  if (meta.solution) {
    if (editorialCode) editorialCode.textContent = meta.solution.code || '';
    if (editorialExplanation) editorialExplanation.innerHTML = meta.solution.explanation || '';
  }

  // Problem Tab switching (Description, Editorial, Solutions, Submissions)
  document.querySelectorAll('#leftTabs .lc-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('#leftTabs .lc-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      
      // Hide all panels
      document.querySelectorAll('.lc-left-panel').forEach(p => p.style.display = 'none');
      // Show selected panel
      const targetId = 'tabContent-' + tab.getAttribute('data-tab');
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) targetPanel.style.display = 'block';
    });
  });

  // Console Tab switching (Testcase / Test Result)
  const testcasePanel = document.getElementById('testcasePanel');
  const resultPanel = document.getElementById('resultPanel');
  const customInputBox = document.getElementById('customInputBox');
  
  document.querySelectorAll('.lc-console-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.lc-console-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      
      const tabName = tab.getAttribute('data-tab');
      if (tabName === 'testcase') {
        testcasePanel.style.display = 'block';
        resultPanel.style.display = 'none';
      } else {
        testcasePanel.style.display = 'none';
        resultPanel.style.display = 'block';
      }
    });
  });

  // Show result tab when running code
  function showResultTab() {
    document.querySelectorAll('.lc-console-tab').forEach(t => t.classList.remove('active'));
    document.querySelector('.lc-console-tab[data-tab="result"]').classList.add('active');
    testcasePanel.style.display = 'none';
    resultPanel.style.display = 'block';
  }

  // Show testcase tab
  function showTestcaseTab() {
    document.querySelectorAll('.lc-console-tab').forEach(t => t.classList.remove('active'));
    const testcaseTab = document.querySelector('.lc-console-tab[data-tab="testcase"]');
    if (testcaseTab) testcaseTab.classList.add('active');
    if (testcasePanel) testcasePanel.style.display = 'block';
    if (resultPanel) resultPanel.style.display = 'none';
  }

  // Initialize - show testcase tab by default
  showTestcaseTab();

  const templates = meta.templates || {};
  const languageMap = {
    python: 'python',
    javascript: 'javascript',
    java: 'java',
    cpp: 'cpp'
  };

  let editor = null;
  let fallbackEditor = null;
  let currentLanguage = 'python';
  let codeByLanguage = {
    python: templates.python || '',
    javascript: templates.javascript || '',
    java: templates.java || '',
    cpp: templates.cpp || ''
  };

  function renderConstraints() {
    constraintsBox.innerHTML = '';
    (meta.constraints || []).forEach((item) => {
      const row = document.createElement('div');
      row.className = 'lc-constraint-item';
      row.textContent = String(item);
      constraintsBox.appendChild(row);
    });
  }

  function renderSamples() {
    sampleCases.innerHTML = '';
    const testcaseTabList = document.getElementById('testcaseTabList');
    
    if (testcaseTabList) testcaseTabList.innerHTML = '';

    const formatVal = val => typeof val === 'object' ? JSON.stringify(val, null, 2) : String(val || '');

    (meta.sample_tests || []).forEach((t, i) => {
      const inputStr = t.input_formatted || formatVal(t.input);
      const outputStr = t.output_formatted || formatVal(t.output);

      // Add to problem description
      const card = document.createElement('div');
      card.className = 'lc-sample';
      card.innerHTML = `
        <div class="lc-sample-header">Example ${i + 1}</div>
        <div class="lc-sample-body">
          <div class="lc-sample-row">
            <span class="lc-sample-label">Input</span>
            <pre class="lc-sample-value">${inputStr}</pre>
          </div>
          <div class="lc-sample-row">
            <span class="lc-sample-label">Output</span>
            <pre class="lc-sample-value">${outputStr}</pre>
          </div>
        </div>`;
      sampleCases.appendChild(card);
      
      // Add to Testcase panel
      if (testcaseTabList && customInputBox) {
        // Tab Button
        const btn = document.createElement('div');
        btn.textContent = `Case ${i + 1}`;
        btn.style.cssText = `padding:8px 16px; border-radius:8px; font-size:13px; font-weight:500; cursor:pointer; transition:all 0.2s; background:rgba(255,255,255,0.05); color:rgba(255,255,255,0.7);`;
        
        const rawInputJson = formatVal(t.input);

        if (i === 0) {
          btn.style.background = 'rgba(255,255,255,0.1)';
          btn.style.color = 'white';
          customInputBox.value = rawInputJson;
        }

        btn.onclick = () => {
          Array.from(testcaseTabList.children).forEach(c => {
            c.style.background = 'rgba(255,255,255,0.05)';
            c.style.color = 'rgba(255,255,255,0.7)';
          });
          btn.style.background = 'rgba(255,255,255,0.1)';
          btn.style.color = 'white';
          customInputBox.value = rawInputJson;
        };

        testcaseTabList.appendChild(btn);
      }
    });
  }

  function initSolution() {
    const solution = meta.solution || {};
    solutionCode.textContent = solution.code || '';
    solutionExplanation.textContent = solution.explanation || '';
    solutionBtn.addEventListener('click', () => {
      const arrow = document.getElementById('solutionArrow');
      const isOpen = solutionPanel.classList.contains('open');
      if (!isOpen) {
        solutionPanel.classList.add('open');
        if (arrow) arrow.classList.add('open');
      } else {
        solutionPanel.classList.remove('open');
        if (arrow) arrow.classList.remove('open');
      }
    });
  }

  function initMonaco() {
    function enableFallbackEditor() {
      editorHost.innerHTML = '';
      fallbackEditor = document.createElement('textarea');
      fallbackEditor.className = 'code-area-fallback';
      fallbackEditor.value = codeByLanguage[currentLanguage] || '';
      editorHost.appendChild(fallbackEditor);
      if (basicEditorBtn) {
        basicEditorBtn.textContent = 'Basic Editor Active';
        basicEditorBtn.disabled = true;
      }
      fallbackEditor.focus();
    }

    function getCurrentCode() {
      if (editor) return editor.getValue();
      if (fallbackEditor) return fallbackEditor.value;
      return '';
    }

    function setCurrentCode(nextCode) {
      if (editor) {
        editor.setValue(nextCode || '');
        editor.focus();
        return;
      }
      if (fallbackEditor) {
        fallbackEditor.value = nextCode || '';
        fallbackEditor.focus();
      }
    }

    function applyLanguage(nextLanguage) {
      codeByLanguage[currentLanguage] = getCurrentCode();
      currentLanguage = nextLanguage;
      setCurrentCode(codeByLanguage[currentLanguage] || '');
      if (editor && editor.getModel()) {
        monaco.editor.setModelLanguage(editor.getModel(), languageMap[currentLanguage] || 'python');
      }
    }

    languageSelect.addEventListener('change', () => applyLanguage(languageSelect.value));

    if (!window.require) {
      enableFallbackEditor();
      return;
    }

    window.require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs' } });
    window.require(['vs/editor/editor.main'], function () {
      try {
        editor = monaco.editor.create(editorHost, {
          value: codeByLanguage.python,
          language: 'python',
          theme: 'vs-dark',
          automaticLayout: true,
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          roundedSelection: true,
          readOnly: false,
          domReadOnly: false,
          contextmenu: true
        });
        editorHost.addEventListener('click', () => editor && editor.focus());
        editor.onDidAttemptReadOnlyEdit(() => {
          editor.updateOptions({ readOnly: false, domReadOnly: false });
        });
        editor.focus();
      } catch (e) {
        editor = null;
        enableFallbackEditor();
      }
    });

    // If Monaco script hangs or never initializes, keep editor usable.
    setTimeout(() => {
      if (!editor && !fallbackEditor) enableFallbackEditor();
    }, 2000);

    // expose helpers for request handlers
    initMonaco.getCode = getCurrentCode;
    initMonaco.enableFallbackEditor = enableFallbackEditor;
  }

  function setConsoleState(state) {
    outputBox.classList.remove('status-success', 'status-fail', 'status-error',
      'lc-console-body-status-success', 'lc-console-body-status-fail', 'lc-console-body-status-error');
    if (state === 'success') {
      outputBox.classList.add('status-success', 'lc-console-body-status-success');
    }
    if (state === 'fail') {
      outputBox.classList.add('status-fail', 'lc-console-body-status-fail');
    }
    if (state === 'error') {
      outputBox.classList.add('status-error', 'lc-console-body-status-error');
    }
  }

  function renderInteractiveResult(data, isSubmit) {
    if (!data || typeof data !== 'object') {
      return `<div style="color:#f85149;padding:16px;">❌ Runtime Error<br><br>Unexpected response from server.</div>`;
    }

    if (!data.ok && data.status !== 'failed') {
      return `<div style="color:#f85149;padding:16px;">
        <div style="font-size:20px;font-weight:600;margin-bottom:12px;">Runtime Error</div>
        <div style="background:rgba(248,81,73,0.1);border:1px solid rgba(248,81,73,0.3);padding:12px;border-radius:8px;font-family:monospace;white-space:pre-wrap;">${String(data.error || 'Execution failed')}</div>
      </div>`;
    }

    let isAccepted = data.ok || data.status === 'accepted';
    let results = Array.isArray(data.results) ? data.results : [];
    
    // Add custom input to results if mode is custom_input
    if (data.mode === 'custom_input') {
        isAccepted = true;
        results = [{
            case: 1,
            passed: true,
            input: 'Custom Input',
            expected: 'N/A',
            actual: data.output || '',
            runtime_ms: data.runtime_ms || 0
        }];
    }

    const titleColor = isAccepted ? '#2ea043' : '#f85149';
    const titleText = isAccepted ? 'Accepted' : 'Wrong Answer';
    
    let html = `
      <div style="padding:16px 0;">
        <div style="color:${titleColor}; font-size:22px; font-weight:600; margin-bottom:16px;">${titleText}</div>
        <div style="display:flex; gap:8px; margin-bottom:16px; overflow-x:auto;" id="resultTabList"></div>
        <div id="resultBodyList"></div>
      </div>
    `;
    
    // We must return HTML and then wire up the tabs after it's injected.
    // Instead of doing it inline, we attach it to window to call immediately after injection.
    window._wireResultTabs = () => {
      const tabList = document.getElementById('resultTabList');
      const bodyList = document.getElementById('resultBodyList');
      if (!tabList || !bodyList) return;
      
      let failedIndex = results.findIndex(r => !r.passed);
      if (failedIndex === -1) failedIndex = 0;

      results.forEach((r, i) => {
        const btn = document.createElement('div');
        btn.innerHTML = `<span style="color:${r.passed ? '#2ea043' : '#f85149'}; margin-right:4px;">•</span> Case ${r.case}`;
        btn.style.cssText = `padding:8px 16px; border-radius:8px; font-size:13px; font-weight:500; cursor:pointer; transition:all 0.2s; background:rgba(255,255,255,0.05); color:rgba(255,255,255,0.7); display:flex; align-items:center;`;
        
        const body = document.createElement('div');
        body.style.display = 'none';
        body.innerHTML = `
          <div style="margin-bottom:16px;">
            <div style="font-size:12px;color:rgba(255,255,255,0.5);margin-bottom:6px;">Input:</div>
            <div style="background:rgba(255,255,255,0.05);border-radius:8px;padding:12px;font-family:monospace;font-size:13px;color:#e6edf3;white-space:pre-wrap;">${r.input || ''}</div>
          </div>
          <div style="margin-bottom:16px;">
            <div style="font-size:12px;color:rgba(255,255,255,0.5);margin-bottom:6px;">Output:</div>
            <div style="background:${r.passed ? 'rgba(255,255,255,0.05)' : 'rgba(248,81,73,0.1)'};border:${r.passed ? 'none' : '1px solid rgba(248,81,73,0.3)'};border-radius:8px;padding:12px;font-family:monospace;font-size:13px;color:${r.passed ? '#e6edf3' : '#f85149'};white-space:pre-wrap;">${r.actual || ''}</div>
          </div>
          <div style="margin-bottom:16px;">
            <div style="font-size:12px;color:rgba(255,255,255,0.5);margin-bottom:6px;">Expected:</div>
            <div style="background:rgba(255,255,255,0.05);border-radius:8px;padding:12px;font-family:monospace;font-size:13px;color:#e6edf3;white-space:pre-wrap;">${r.expected || ''}</div>
          </div>
        `;

        if (i === failedIndex) {
          btn.style.background = 'rgba(255,255,255,0.1)';
          btn.style.color = 'white';
          body.style.display = 'block';
        }

        btn.onclick = () => {
          Array.from(tabList.children).forEach(c => {
            c.style.background = 'rgba(255,255,255,0.05)';
            c.style.color = 'rgba(255,255,255,0.7)';
          });
          Array.from(bodyList.children).forEach(c => c.style.display = 'none');
          btn.style.background = 'rgba(255,255,255,0.1)';
          btn.style.color = 'white';
          body.style.display = 'block';
        };

        tabList.appendChild(btn);
        bodyList.appendChild(body);
      });
    };

    return html;
  }

  function formatRunResult(data) {
    return renderInteractiveResult(data, false);
  }

  function formatSubmitResult(data) {
    return renderInteractiveResult(data, true);
  }

  async function call(endpoint) {
    const getCode = initMonaco.getCode || (() => '');
    const code = getCode();
    if (!code.trim()) {
      outputBox.innerHTML = '<div style="color:#f85149;">Error: Please write code before running.</div>';
      setConsoleState('error');
      return;
    }
    
    // Show result tab
    showResultTab();
    
    setConsoleState('');
    outputBox.innerHTML = '<div style="color:rgba(255,255,255,0.6);display:flex;align-items:center;gap:8px;"><div class="lc-spinner"></div>Running...</div>';
    
    const payload = {
      problem_id: meta.id,
      code,
      language: currentLanguage,
    };
    
    // If custom input box exists and has value, use it; otherwise run samples
    if (endpoint.includes('/run') && customInputBox && customInputBox.value.trim()) {
      payload.custom_input = customInputBox.value;
    }
    
    const resp = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await resp.json();
    if (!resp.ok) {
      setConsoleState('error');
      outputBox.innerHTML = `<div style="color:#f85149;">❌ Runtime Error<br><br>${String(data.error || 'Execution failed')}</div>`;
      return;
    }

    if (endpoint.includes('/submit')) {
      outputBox.innerHTML = formatSubmitResult(data);
    } else {
      outputBox.innerHTML = formatRunResult(data);
    }
    
    if (window._wireResultTabs) {
      window._wireResultTabs();
      delete window._wireResultTabs;
    }

    if (data.ok) {
      setConsoleState('success');
    } else if (data.status === 'failed') {
      setConsoleState('fail');
    } else {
      setConsoleState('error');
    }
  }

  runBtn.addEventListener('click', () => call('/api/code/run'));
  submitBtn.addEventListener('click', () => call('/api/code/submit'));

  renderConstraints();
  renderSamples();
  initMonaco();
})();
