# 🛡️ Autonomous Cyber Defense System

An agentic, edge-compute cybersecurity platform that monitors logs, detects threats using local mathematical optimization, evaluates context via an LLM, executes autonomous lockdown, and mints a tamper-proof SHA-256 hash of the event to the Polygon blockchain.

## Features

- **Agent 1 (Monitor/Ingestion):** Ingests raw logs via FastAPI.
- **Agent 2 (Math Engine):** Calculates mathematical volume deviation penalties ($\Delta$) to detect anomalies without ML models.
- **Agent 3 (Decision Engine):** Invokes OpenAI `gpt-4o-mini` to classify the severity of the flagged log.
- **Agent 4 (Autonomous Responder):** Automatically severs connections for `CRITICAL` threats by updating the database.
- **Agent 5 (Blockchain Vault):** Creates an immutable, tamper-proof SHA-256 hash of critical alerts and mints a 0-value transaction to the Polygon Amoy Testnet.

## Project Structure

- `backend/`: FastAPI application handling the 5 microservice agents.
- `frontend/`: Next.js & Tailwind CSS dynamic dashboard.
- `streamlit_app.py`: Alternative lightweight Python dashboard for Streamlit Community Cloud deployment.
- `schema.sql`: Supabase PostgreSQL database schema.

## Getting Started

### Database Setup
Execute the contents of `schema.sql` in your Supabase SQL editor.

### Backend (FastAPI)
1. Navigate to the `backend/` directory.
2. Create a `.env` file based on `.env.example`.
3. Install dependencies: `pip install -r requirements.txt`
4. Run the server: `uvicorn main:app --reload`

### Frontend (Next.js)
1. Navigate to the `frontend/` directory.
2. Install dependencies: `npm install`
3. Set your Supabase keys in `.env.local`.
4. Run the development server: `npm run dev`

### Frontend (Streamlit)
For a rapid deployment to Streamlit Community Cloud:
1. Ensure `streamlit_app.py` is in your repository root.
2. Link your GitHub repo to Streamlit and add Supabase environment variables.

## Testing the System
Force a critical alert by sending a massive volume payload to the ingestion endpoint:
```bash
curl -X POST "http://localhost:8000/ingest" \
-H "Content-Type: application/json" \
-d '{"user_id": "attacker@corp.com", "action": "MASS_DOWNLOAD", "volume": 5000}'
```
Wait a few seconds, watch the Next.js or Streamlit dashboard spike, and verify the transaction hash on polygonscan!
