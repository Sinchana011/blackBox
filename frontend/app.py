import os
import streamlit as st
import requests
import time
from datetime import datetime

try:
    BACKEND = st.secrets["BACKEND_URL"]
except Exception:
    BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="BlackBox Guardian", layout="wide")

# Color scheme (modify to match your dashboard image)
PRIMARY = "#0b5f75"

def severity_score(sev):
    if not sev: return 0
    s = sev.lower()
    if "high" in s or "critical" in s:
        return 10
    if "medium" in s:
        return 5
    if "low" in s:
        return 2
    return 1


st.title("BlackBox Guardian")

# Input panel
with st.container():
    col1, col2 = st.columns([3,1])
    with col1:
        target_url = st.text_input("Target URL", value="http://example.com")
    with col2:
        if st.button("Start Scan"):
            try:
                r = requests.post(f"{BACKEND}/scan/start", json={"url": target_url}, timeout=10)
                r.raise_for_status()
                scan = r.json()
                scan_id = scan.get("id")
                st.session_state["scan_id"] = scan_id
                st.success(f"Scan started: {scan_id}")
            except Exception as e:
                st.error(f"Failed to start scan: {e}")

# If there's an active scan id, poll for status
scan_id = st.session_state.get("scan_id")
if scan_id:
    st.subheader("Scan Monitor")
    status_col, score_col = st.columns([3,1])
    with status_col:
        st.markdown("**Status**")
        status_text = st.empty()
        processes = st.container()
    with score_col:
        st.markdown("**Risk Score**")
        score_box = st.empty()

    # Polling loop (non-blocking UI: we use manual refresh button)
    if st.button("Refresh Status"):
        pass

    # Fetch current scan
    try:
        r = requests.get(f"{BACKEND}/scan/{scan_id}", timeout=5)
        r.raise_for_status()
        scan = r.json()
        status = scan.get("status")
        created = scan.get("created_at")
        updated = scan.get("updated_at")
        status_text.markdown(f"**{status}**")

        # Fetch findings
        fr = requests.get(f"{BACKEND}/scan/{scan_id}/findings", timeout=5)
        fr.raise_for_status()
        findings = fr.json()

        # Determine tool completion by presence of findings per tool
        tools = {"ZAP": False, "Nmap": False, "SQLMap": False}
        for f in findings:
            tool = f.get("tool_source", "Unknown")
            if tool and tool.lower().startswith("zap"):
                tools["ZAP"] = True
            if tool and tool.lower().startswith("nmap"):
                tools["Nmap"] = True
            if tool and tool.lower().startswith("sql"):
                tools["SQLMap"] = True

        with processes:
            tcols = st.columns(3)
            tool_names = list(tools.keys())
            for i, name in enumerate(tool_names):
                done = tools[name]
                color = "green" if done else "orange" if status=="RUNNING" else "gray"
                tcols[i].markdown(f"**{name}**\n\n: { '✅' if done else '⏳' } ")

        # Compute simple risk score
        score = 0
        for f in findings:
            score += severity_score(f.get("severity"))
        score_box.markdown(f"### {score}")

        # Findings list
        st.subheader("Findings")
        if findings:
            for f in findings:
                with st.expander(f"{f.get('name')} — {f.get('severity')}"):
                    st.markdown(f"**Source:** {f.get('tool_source')}")
                    st.markdown(f"**URL:** {f.get('url')}")
                    st.markdown("**Description:**")
                    st.write(f.get('evidence'))
        else:
            st.info("No findings yet. Refresh to poll again.")

        # Timeline
        st.subheader("Timeline")
        if created:
            created_dt = datetime.fromisoformat(created.replace('Z','+00:00')) if created.endswith('Z') else datetime.fromisoformat(created)
            st.write(f"Created: {created_dt}")
        if updated:
            updated_dt = datetime.fromisoformat(updated.replace('Z','+00:00')) if updated.endswith('Z') else datetime.fromisoformat(updated)
            st.write(f"Last updated: {updated_dt}")

        # Logs — we don't have a logs endpoint; provide instructions
        st.subheader("Logs")
        try:
            lr = requests.get(f"{BACKEND}/scan/{scan_id}/logs", timeout=5)
            lr.raise_for_status()
            logs = lr.json()
            for l in logs:
                created = l.get('created_at')
                st.write(f"{created} — {l.get('message')}")
        except Exception:
            st.info("Logs are not available from the server. You can stream logs locally with:\n`docker compose logs -f backend celery_worker`")

    except Exception as e:
        st.error(f"Error fetching scan info: {e}")

# Recent scans panel
st.sidebar.header("Recent Scans")
try:
    rs = requests.get(f"{BACKEND}/scans?limit=10", timeout=5)
    rs.raise_for_status()
    recent = rs.json()
    for s in recent:
        st.sidebar.write(f"{s.get('id')[:8]} — {s.get('target_url')} — {s.get('status')}")
except Exception:
    st.sidebar.info("Could not load recent scans")
