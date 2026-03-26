import json
import os
from datetime import datetime, date, timedelta
from pathlib import Path

import anthropic
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DATA_FILE = "youtube_sessions.json"
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# --- Data layer ---

def load_sessions():
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []


def save_sessions(sessions):
    with open(DATA_FILE, "w") as f:
        json.dump(sessions, f, indent=2)


def record_session(start_dt: datetime, end_dt: datetime):
    sessions = load_sessions()
    duration = (end_dt - start_dt).total_seconds() / 60
    sessions.append({
        "date": start_dt.strftime("%Y-%m-%d"),
        "start_time": start_dt.isoformat(),
        "end_time": end_dt.isoformat(),
        "duration_minutes": round(duration, 1),
    })
    save_sessions(sessions)


def record_manual_session(date_str: str, total_minutes: float):
    sessions = load_sessions()
    sessions.append({
        "date": date_str,
        "start_time": None,
        "end_time": None,
        "duration_minutes": round(total_minutes, 1),
        "manual": True,
    })
    save_sessions(sessions)


def daily_total(date_str: str) -> float:
    return sum(s["duration_minutes"] for s in load_sessions() if s["date"] == date_str)


def week_totals() -> dict[str, float]:
    today = date.today()
    totals = {(today - timedelta(days=i)).strftime("%Y-%m-%d"): 0.0 for i in range(6, -1, -1)}
    for s in load_sessions():
        if s["date"] in totals:
            totals[s["date"]] += s["duration_minutes"]
    return totals


# --- AI agent tools ---

TOOLS = [
    {
        "name": "get_today_stats",
        "description": "Get total YouTube minutes watched today.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_weekly_stats",
        "description": "Get YouTube minutes watched each day for the past 7 days.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_all_sessions",
        "description": "Get every recorded session with its date and duration.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_date_stats",
        "description": "Get total YouTube minutes for a specific date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"}
            },
            "required": ["date"],
        },
    },
]


def run_tool(name: str, inputs: dict) -> str:
    if name == "get_today_stats":
        today = date.today().strftime("%Y-%m-%d")
        mins = daily_total(today)
        return f"Today ({today}): {mins:.1f} min  ({mins / 60:.2f} h)"

    if name == "get_weekly_stats":
        data = week_totals()
        lines = [f"  {d}: {m:.1f} min ({m / 60:.2f} h)" for d, m in data.items()]
        total = sum(data.values())
        lines.append(f"\nWeek total: {total:.1f} min ({total / 60:.2f} h)")
        return "\n".join(lines)

    if name == "get_all_sessions":
        sessions = load_sessions()
        if not sessions:
            return "No sessions recorded yet."
        return "\n".join(f"{s['date']}: {s['duration_minutes']:.1f} min" for s in sessions)

    if name == "get_date_stats":
        d = inputs["date"]
        mins = daily_total(d)
        return f"{d}: {mins:.1f} min ({mins / 60:.2f} h)"

    return f"Unknown tool: {name}"


SYSTEM_PROMPT = (
    "You are a supportive YouTube time-tracking coach. "
    "Use the available tools to look up the user's actual data before answering. "
    "Be concise, honest, and give actionable advice. "
    "If the user hasn't logged much data yet, encourage them to start tracking."
)


def ask_agent(user_question: str) -> str:
    messages = [{"role": "user", "content": user_question}]

    for _ in range(10):  # cap iterations
        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            tools=TOOLS,
            messages=messages,
        ) as stream:
            response = stream.get_final_message()

        if response.stop_reason == "end_turn":
            return next((b.text for b in response.content if b.type == "text"), "")

        if response.stop_reason == "tool_use":
            # Preserve full content (including thinking blocks) for the next turn
            messages.append({"role": "assistant", "content": response.content})
            tool_results = [
                {
                    "type": "tool_result",
                    "tool_use_id": b.id,
                    "content": run_tool(b.name, b.input),
                }
                for b in response.content
                if b.type == "tool_use"
            ]
            messages.append({"role": "user", "content": tool_results})
            continue

        break

    return "Sorry, I could not complete the analysis."


# --- Streamlit UI ---

st.set_page_config(page_title="YouTube Time Tracker", page_icon="▶️", layout="wide")
st.title("▶️ YouTube Time Tracker")
st.caption("Log your YouTube sessions and get AI-powered insights into your habits.")

if "tracking" not in st.session_state:
    st.session_state.tracking = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None

left, right = st.columns(2)

# ---- Left column: logging ----
with left:
    st.subheader("⏱ Live Timer")

    if not st.session_state.tracking:
        if st.button("▶  Start watching YouTube", use_container_width=True, type="primary"):
            st.session_state.tracking = True
            st.session_state.start_time = datetime.now()
            st.rerun()
    else:
        elapsed = datetime.now() - st.session_state.start_time
        m, s = divmod(int(elapsed.total_seconds()), 60)
        st.info(f"Recording session… {m}m {s}s elapsed")
        if st.button("⏹  Stop watching", use_container_width=True):
            record_session(st.session_state.start_time, datetime.now())
            st.session_state.tracking = False
            st.session_state.start_time = None
            st.success("Session saved!")
            st.rerun()

    st.divider()
    st.subheader("✏️ Log a Past Session")

    log_date = st.date_input("Date", value=date.today(), key="log_date")
    c1, c2 = st.columns(2)
    with c1:
        log_h = st.number_input("Hours", min_value=0, max_value=23, value=0, key="log_h")
    with c2:
        log_m = st.number_input("Minutes", min_value=0, max_value=59, value=30, key="log_m")

    if st.button("Save session", use_container_width=True):
        total = log_h * 60 + log_m
        if total > 0:
            record_manual_session(log_date.strftime("%Y-%m-%d"), float(total))
            st.success(f"Logged {log_h}h {log_m}m on {log_date}.")
            st.rerun()
        else:
            st.warning("Duration must be greater than zero.")

# ---- Right column: dashboard ----
with right:
    st.subheader("📊 This Week")

    week = week_totals()
    today_str = date.today().strftime("%Y-%m-%d")
    today_mins = daily_total(today_str)
    h, m = divmod(int(today_mins), 60)
    st.metric("Today's total", f"{h}h {m}m")

    if any(v > 0 for v in week.values()):
        chart_data = {
            datetime.strptime(d, "%Y-%m-%d").strftime("%a %-m/%-d"): round(mins / 60, 2)
            for d, mins in week.items()
        }
        st.bar_chart(chart_data, y_label="Hours", color="#FF0000")
    else:
        st.info("No sessions logged this week yet — start tracking above!")

    # Recent sessions table
    sessions = load_sessions()
    if sessions:
        st.caption("Recent sessions")
        recent = sorted(sessions, key=lambda s: s["date"], reverse=True)[:10]
        rows = [
            {
                "Date": s["date"],
                "Duration": f"{int(s['duration_minutes'])}m",
                "Type": "Manual" if s.get("manual") else "Timer",
            }
            for s in recent
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)

st.divider()

# ---- AI coach ----
st.subheader("🤖 AI Time Coach")
st.caption("Ask Claude anything about your YouTube habits.")

question = st.text_input(
    "Your question",
    placeholder="How much time did I watch this week? Am I overdoing it?",
)

if st.button("Ask coach", type="primary", disabled=not question):
    with st.spinner("Analyzing your data…"):
        answer = ask_agent(question)
    st.info(answer)

st.caption("Quick questions:")
q1, q2, q3 = st.columns(3)

with q1:
    if st.button("📈 Weekly summary", use_container_width=True):
        with st.spinner("Checking…"):
            st.info(ask_agent("Summarize my YouTube usage this week. How does it look overall?"))

with q2:
    if st.button("💡 Tips to cut back", use_container_width=True):
        with st.spinner("Thinking…"):
            st.info(ask_agent(
                "Based on my YouTube data, give me 3 concrete tips to reduce screen time "
                "or make my watching more intentional."
            ))

with q3:
    if st.button("📅 Today's report", use_container_width=True):
        with st.spinner("Checking…"):
            st.info(ask_agent("How much YouTube have I watched today? Is that healthy?"))
