import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# -----------------------------
# Load data
# -----------------------------
df = pd.read_csv("strategy_only_participants.csv")
participants = df["participant_id"].unique()
ROTATION_START = 113

df["rel_trial"] = df["cutrial_no"] - ROTATION_START

# -----------------------------
# Session state setup
# -----------------------------
if "idx" not in st.session_state:
    st.session_state.idx = 0

if "clicks" not in st.session_state:
    st.session_state.clicks = []

if "results" not in st.session_state:
    st.session_state.results = []

if "phenotype" not in st.session_state:
    st.session_state.phenotype = "gradual"

# -----------------------------
# Helpers
# -----------------------------
def current_pid():
    return participants[st.session_state.idx]

def reset_clicks():
    st.session_state.clicks = []

def save_current():
    start, end = st.session_state.clicks

    st.session_state.results.append({
        "participant_id": current_pid(),
        "learning_start": start,
        "learning_end": end,
        "phenotype": st.session_state.phenotype
    })

def save_to_csv():
    out = pd.DataFrame(st.session_state.results)
    file = "learning_labels.csv"

    if os.path.exists(file):
        old = pd.read_csv(file)
        out = pd.concat([old, out], ignore_index=True)

    out.to_csv(file, index=False)

# -----------------------------
# UI
# -----------------------------
st.title("Strategy Label Tool (Click on Graph)")

pid = current_pid()
st.subheader(f"Participant: {pid}")

pdat = df[(df["participant_id"] == pid) & (df["trial_type"] == "rotated")]

# -----------------------------
# Phenotype selection
# -----------------------------
st.session_state.phenotype = st.radio(
    "Phenotype",
    ["gradual", "stepwise", "exploratory"]
)

# -----------------------------
# Plotly figure
# -----------------------------
fig = go.Figure()

fig.add_trace(go.Scatter(
    x = pdat["rel_trial"],
    y=pdat["aimdeviation_deg"],
    mode="lines+markers",
    name="trajectory"
))

# draw selected clicks
for c in st.session_state.clicks:
    fig.add_vline(x=c, line_color="red")

fig.update_layout(
    xaxis_title="Trial",
    yaxis_title="Aim Deviation (deg)",
    yaxis_range=[-20, 65],
    clickmode="event+select"
)

# -----------------------------
# Capture clicks
# -----------------------------
event = st.plotly_chart(fig, use_container_width=True, on_select="rerun")

if event and event.selection and event.selection.get("points"):
    x = event.selection["points"][0]["x"]

    if len(st.session_state.clicks) < 2:
        st.session_state.clicks.append(int(x))

# -----------------------------
# Controls
# -----------------------------
st.write("Clicks:", st.session_state.clicks)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Reset"):
        reset_clicks()

with col2:
    if len(st.session_state.clicks) == 2:
        if st.button("Save participant"):
            save_current()
            reset_clicks()
            st.session_state.idx += 1
            st.rerun()

with col3:
    if st.button("Export CSV"):
        save_to_csv()
        st.success("Saved learning_labels.csv") 