# SmartLearn ( AI-Powered Smart Learning Assistant )

## Setup

1. Create a virtualenv and install dependencies:

```bash
pip install -r requirements.txt
```

2. Create `.env`:

```bash
copy .env.example .env
```

Set:

- `SECRET_KEY`
- `GROQ_API_KEY`

3. Run:

```bash
python app.py
```

Open:

- http://127.0.0.1:5000/

## Dataset

The app loads datasets strictly from:

- `./Dataset/`

It supports:

- JSON (intents-style)
- CSV (Problem/Solution or Problem/Python Code)
- TXT

On first start, it imports dataset entries into SQLite and builds a FAISS index.
