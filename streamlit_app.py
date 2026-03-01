import streamlit as st
import pandas as pd
import time
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Streamlit Page Config
st.set_page_config(page_title="Autonomous Cyber Defense", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    .critical-alert {
        background-color: #450a0a;
        color: #f87171;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #ef4444;
        text-align: center;
        margin-bottom: 20px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
        70% { box-shadow: 0 0 0 20px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Autonomous Cyber Defense System")

# Init Supabase Client
supabase_url = os.environ.get("SUPABASE_URL", "https://your-project.supabase.co")
supabase_key = os.environ.get("SUPABASE_KEY", "your-anon-key")
try:
    supabase: Client = create_client(supabase_url, supabase_key)
except Exception as e:
    st.error(f"Error initializing Supabase. Check Environment Variables: {e}")
    st.stop()

# Helper to load data
def load_data():
    try:
        logs_res = supabase.table("raw_logs").select("*").order("timestamp", desc=True).limit(20).execute()
        logs = logs_res.data
        
        alerts_res = supabase.table("alerts").select("*, raw_logs(*)").order("id", desc=True).limit(20).execute()
        alerts = alerts_res.data
        
        proofs_res = supabase.table("blockchain_proofs").select("*, alerts(*)").order("id", desc=True).limit(10).execute()
        proofs = proofs_res.data
        
        return logs, alerts, proofs
    except Exception as e:
        st.error(f"Database fetch failed: {e}")
        return [], [], []

logs, alerts, proofs = load_data()

# Find Critical Alert
critical_alert = None
for a in alerts:
    if a.get('severity') == 'CRITICAL':
        critical_alert = a
        break

if critical_alert:
    st.markdown(f"""
    <div class="critical-alert">
        <h2>🚨 CRITICAL THREAT ISOLATED 🚨</h2>
        <p><strong>Target User:</strong> {critical_alert.get('raw_logs', {}).get('user_id', 'UNKNOWN')}</p>
        <p><strong>Action:</strong> {critical_alert.get('raw_logs', {}).get('action', 'UNKNOWN')}</p>
        <p><strong>Anomaly Score:</strong> {critical_alert.get('anomaly_score', 0):.2f}</p>
        <h3>STATUS: CONNECTION SEVERED 🔒</h3>
    </div>
    """, unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📡 Live Ingest Stream")
    if logs:
        for log in logs:
            st.info(f"**{log['user_id']}** | Vol: {log['volume']}\n\n*Action: {log['action']}*")
    else:
        st.write("No logs waiting...")

with col2:
    st.subheader("📈 Threat Visualizer")
    if alerts:
        # Convert alerts to pandas df for charting
        df = pd.DataFrame(alerts)
        df = df[::-1] # Reverse to chronological
        if not df.empty and 'anomaly_score' in df.columns:
            st.line_chart(df['anomaly_score'])
        else:
            st.write("No score data available.")
    else:
        st.write("No anomaly data yet.")

with col3:
    st.subheader("⛓️ The Blockchain Vault")
    if proofs:
        for proof in proofs:
            st.success(f"**SHA256 Hash:**\n`{proof['sha256_hash']}`\n\n**Local Tx ID:** `{proof['transaction_id']}`")
    else:
        st.write("Vault is empty...")

# Auto-refresh workaround for Streamlit
time.sleep(3)
st.rerun()
