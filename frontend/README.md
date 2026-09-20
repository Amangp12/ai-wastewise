# Phase 9 — Frontend

## What this is

A React interface for AI WasteWise: upload an image, click Analyze, and
see the full result from your backend (Phase 8) — detected item, waste
category, recommended action, explanation, sustainability impact, and
sources — rendered as an actual UI instead of raw JSON.

It talks to your backend at `http://127.0.0.1:8000/analyze`. The backend
must be running (see Phase 8's README) before you use this.

## Setup

You'll need **Node.js** installed (if you don't have it: download from
nodejs.org, the LTS version). Then:

```bash
cd frontend
npm install
```

## Run it

**First, make sure your backend is running** in a separate terminal
(Phase 8):
```bash
cd backend
python -m uvicorn main:app --reload
```

**Then, in a new terminal, start the frontend:**
```bash
cd frontend
npm run dev
```

You'll see output like:
```
  VITE ready
  ➜  Local:   http://localhost:5173/
```

Open `http://localhost:5173` in your browser. You now have two servers
running at once — backend on port 8000, frontend on port 5173 — talking
to each other. This is normal for a full-stack app during development.

## What to test

- Upload your plastic bottle photo → should show a classified result
  card with category, action, explanation, and sources.
- Upload your blurry test photo → should show the "not confident enough"
  panel instead of a result card.
- Upload a real multi-item photo → should show multiple item cards, one
  per detected object.
- Try analyzing without selecting a file first — the Analyze button
  should stay disabled.
- Stop the backend server, then try analyzing — you should see a clear
  error message, not a silent failure.

## If something doesn't connect

If you get a "Can't reach the backend" error even though uvicorn is
running, double check:
1. The backend is actually running on port 8000 (check the terminal
   for errors).
2. You're not blocking `localhost` connections with a firewall/antivirus.
3. Both servers are running at the same time, in separate terminals.
