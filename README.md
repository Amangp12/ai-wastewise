# AI WasteWise

**AI-Powered Waste Classification, Disposal and Sustainability Decision-Support System**

Upload a photo of a waste item → the system identifies it, classifies it into a
waste category, and generates a disposal recommendation grounded in real
Indian government waste-management documents (via RAG) — with honest
uncertainty handling when the image is unclear or the knowledge base doesn't
cover the item.

## How it works

```
Frontend (React) → Backend API (FastAPI) → Multimodal AI (Gemini)
    → Classification logic → RAG retrieval (Chroma) → Grounded generation (Gemini)
    → Anonymized analytics (SQLite + Streamlit)
```

See [`docs/AI_WasteWise_Documentation.docx`](docs/AI_WasteWise_Documentation.docx)
for the full write-up (architecture, methodology, testing, Responsible AI
evaluation, limitations, future scope).

## Project structure

```
backend/          FastAPI backend: image analysis, classification, RAG, analytics
  main.py            API endpoint wiring everything together
  analyze_image.py   Phase 5 — multimodal image analysis
  classify_waste.py  Phase 6 — rule-based waste classification
  rag_query.py        Phase 7 — RAG retrieval + grounded generation
  ingest_knowledge_base.py   One-time script to build the vector store
  analytics_db.py    Phase 10 — anonymized SQLite logging
  dashboard.py        Phase 10 — Streamlit analytics dashboard
  knowledge_base/     Real source documents (CPCB / SWM Rules 2026)

frontend/          React + Vite web interface

docs/               Full documentation and Responsible AI evaluation

testing/            Test log tracking real test results across waste categories
```

## Running it locally

You'll need Python 3.10+, Node.js, and a free Google Gemini API key
([aistudio.google.com](https://aistudio.google.com)).

**1. Backend:**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env      # then paste your Gemini API key into .env
python ingest_knowledge_base.py   # one-time: build the vector store
python -m uvicorn main:app --reload
```

**2. Frontend** (in a separate terminal):
```bash
cd frontend
npm install
npm run dev
```
Open the printed local URL (usually `http://localhost:5173`).

**3. Analytics dashboard** (optional, in a third terminal):
```bash
cd backend
python -m streamlit run dashboard.py
```

## Status

Core pipeline (image analysis → classification → grounded recommendation →
frontend → analytics) is implemented and tested end-to-end. Testing across
all waste categories is ongoing — see `testing/test_log_template.md` for the
current, honest state of what has and hasn't been verified, and
`docs/phase12_responsible_ai.md` for the Responsible AI evaluation.

## License

Add a license of your choice (e.g. MIT) if you intend this repository to be
reused by others.
