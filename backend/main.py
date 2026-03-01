import os
import json
import hashlib
import asyncio
from datetime import datetime
import numpy as np
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from openai import AsyncOpenAI
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Environment Variables Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "your-anon-key")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "sk-...")
POLYGON_RPC_URL = os.environ.get("POLYGON_RPC_URL", "https://rpc-amoy.polygon.technology")
WALLET_PRIVATE_KEY = os.environ.get("WALLET_PRIVATE_KEY", "0x0000000000000000000000000000000000000000000000000000000000000000")
WALLET_ADDRESS = os.environ.get("WALLET_ADDRESS", "0x0000000000000000000000000000000000000000")

# Initialize Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
w3 = Web3(Web3.HTTPProvider(POLYGON_RPC_URL))

app = FastAPI(title="Autonomous Cyber Defense PoC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LogEvent(BaseModel):
    user_id: str
    action: str
    volume: int

# Global State for Math Engine Baseline
volume_history = {}
EXPECTED_VOLUME_THRESHOLD_EPSILON = 50.0
LAMBDA_PENALTY_WEIGHT = 0.5


# ==========================================
# AGENT 5: The Blockchain Vault
# ==========================================
async def vault_agent(log_data: dict, alert_id: str):
    print(f"[Agent 5] Minting block for Critical Alert {alert_id}")
    try:
        log_str = json.dumps(log_data, sort_keys=True)
        sha256_hash = hashlib.sha256(log_str.encode('utf-8')).hexdigest()
        
        if not w3.is_connected():
            print("[Agent 5] Web3 not connected. Skipping blockchain tx.")
            tx_id = f"NO_RPC_{int(datetime.now().timestamp())}"
        else:
            nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)
            tx = {
                'nonce': nonce,
                'to': WALLET_ADDRESS,
                'value': w3.to_wei(0, 'ether'),
                'gas': 2000000,
                'gasPrice': w3.eth.gas_price,
                'data': w3.to_hex(text=sha256_hash),
                'chainId': 80002 # Polygon Amoy Testnet chain ID
            }
            signed_tx = w3.eth.account.sign_transaction(tx, WALLET_PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_id = tx_hash.hex()
            print(f"[Agent 5] Successfully minted Hash to Polygon. Tx: {tx_id}")
            
    except Exception as e:
        print(f"[Agent 5] Blockchain transaction failed: {e}")
        tx_id = f"FAILED_{int(datetime.now().timestamp())}"
        sha256_hash = "FAILED_HASH"

    try:
        supabase.table("blockchain_proofs").insert({
            "alert_id": alert_id,
            "sha256_hash": sha256_hash,
            "transaction_id": tx_id
        }).execute()
        print(f"[Agent 5] Vault record saved in Supabase.")
    except Exception as e:
        print(f"[Agent 5] Supabase save failed: {e}")


# ==========================================
# AGENT 4: Autonomous Responder
# ==========================================
async def responder_agent(alert_id: str, severity: str, log_data: dict, bg_tasks: BackgroundTasks):
    print(f"[Agent 4] Evaluating Severity: {severity}")
    if severity.upper() == "CRITICAL":
        try:
            supabase.table("alerts").update({"status": "BLOCKED"}).eq("id", alert_id).execute()
            print(f"[Agent 4] Alert {alert_id} upgraded to BLOCKED. Connection Severed.")
            bg_tasks.add_task(vault_agent, log_data, alert_id)
        except Exception as e:
            print(f"[Agent 4] Failed to respond: {e}")
    else:
        print(f"[Agent 4] Severity {severity} is not CRITICAL. No autonomous blocking.")


# ==========================================
# AGENT 3: Decision Engine
# ==========================================
async def decision_engine_agent(log_id: str, log_data: dict, penalty_score: float, bg_tasks: BackgroundTasks):
    print(f"[Agent 3] Evaluating threat for log {log_id} with penalty {penalty_score}")
    
    prompt = f"""
    You are an autonomous SOC analyst. Review this anomalous user action and mathematical penalty score.
    Classify severity as LOW, MEDIUM, or CRITICAL.
    Return a strict JSON with 'severity' and a 1-sentence 'reason'.
    
    Penalty Score: {penalty_score}
    User Action Log:
    {json.dumps(log_data)}
    """
    
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a cybersecurity AI. Reply only in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        severity = result.get("severity", "MEDIUM").upper()
        reason = result.get("reason", "Unknown reason.")
        print(f"[Agent 3] Assessment: {severity} - {reason}")
        
        alert_res = supabase.table("alerts").insert({
            "log_id": log_id,
            "anomaly_score": penalty_score,
            "severity": severity,
            "status": "PENDING"
        }).execute()
        
        if alert_res.data:
            alert_id = alert_res.data[0]['id']
            await responder_agent(alert_id, severity, log_data, bg_tasks)
            
    except Exception as e:
        print(f"[Agent 3] Decision Engine failed: {e}")


# ==========================================
# AGENT 2: The Math Engine
# ==========================================
def math_engine_agent(log_id: str, log_data: dict, bg_tasks: BackgroundTasks):
    user_id = log_data["user_id"]
    current_volume = log_data["volume"]
    
    if user_id not in volume_history:
        volume_history[user_id] = []
        
    history = volume_history[user_id]
    
    if len(history) < 3:
        history.append(current_volume)
        print(f"[Agent 2] Gathering baseline for {user_id}. Volume: {current_volume}")
        return
        
    baseline_volume = np.mean(history)
    delta = abs(current_volume - baseline_volume)
    
    deviation_above_threshold = max(0, delta - EXPECTED_VOLUME_THRESHOLD_EPSILON)
    penalty_score = LAMBDA_PENALTY_WEIGHT * (deviation_above_threshold ** 2)
    
    print(f"[Agent 2] User: {user_id} | Delta: {delta:.2f} | Penalty: {penalty_score:.2f}")
    
    if penalty_score > 0:
        print(f"[Agent 2] Anomaly Detected! Escalating to Agent 3.")
        bg_tasks.add_task(decision_engine_agent, log_id, log_data, penalty_score, bg_tasks)
        
    history.append(current_volume)
    if len(history) > 100:
        history.pop(0)


# ==========================================
# AGENT 1: Monitor / Ingestion
# ==========================================
@app.post("/ingest")
async def ingest_log(event: LogEvent, background_tasks: BackgroundTasks):
    print(f"[Agent 1] Received Log: {event.action} from {event.user_id} vol {event.volume}")
    try:
        res = supabase.table("raw_logs").insert({
            "user_id": event.user_id,
            "action": event.action,
            "volume": event.volume
        }).execute()
        
        if not res.data:
            raise HTTPException(status_code=500, detail="Failed to insert log")
            
        log_id = res.data[0]['id']
        log_data = res.data[0]
        
        math_engine_agent(log_id, log_data, background_tasks)
        
        return {"status": "Ingested", "log_id": log_id}
        
    except Exception as e:
        print(f"[Agent 1] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Autonomous Cyber Defense PoC"}
