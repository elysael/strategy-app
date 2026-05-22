import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# -----------------------------
# Load data
# -----------------------------
df = pd.read_csv("strategy_only_participants.csv")

# convert to plain Python list (avoids Arrow indexing issues)
participants = df["participant_id"].unique().tolist()

ROTATION_START = 113

df["rel_trial"] = df["cutrial_no"] - ROTATION_START

# -----------------------------
# Labeler login
# -----------------------------
labeler_id = st.text_input("Enter your name / ID")

if labeler_id:
    seed = abs(hash(labeler_id)) % (2**32)

    # deterministic shuffle per labeler
    participants = (
        pd.Series(participants)
        .sample(frac=1, random_state=seed)
        .tolist()
    )
else:
    st.warning("Please enter your name to begin labeling.")
    st.stop()

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

if "finished" not in st.session_state:
    st.session_state.finished = False

# -----------------------------
# Finished screen
# -----------------------------
if st.session_state.finished:

    st.title("Labeling Complete!")

    df_out = pd.DataFrame(st.session_state.results)

    st.download_button(
        "Download Final CSV",
        data=df_out.to_csv(index=False),
        file_name=f"learning_labels_{labeler_id}.csv",
        mime="text/csv"
    )

    st.stop()

# -----------------------------
# Helpers
# -----------------------------
def current_pid():

    if st.session_state.idx >= len(participants):
        st.session_state.finished = True
        st.rerun()

    return participants[st.session_state.idx]


def reset_clicks():
    st.session_state.clicks = []


def save_current():

    start, end = st.session_state.clicks

    st.session_state.results.append({
        "participant_id": current_pid(),
        "learning_start": start,
        "learning_end": end,
        "phenotype": st.session_state.phenotype,
        "Clear": clear_checked,
        "labeler_id": labeler_id
    })

# -----------------------------
# UI
# -----------------------------
st.title("Strategy Label Tool (Click on Graph)")

pid = current_pid()

st.subheader(f"Participant: {pid}")

pdat = df[
    (df["participant_id"] == pid) &
    (df["trial_type"] == "rotated")
]

# -----------------------------
# Phenotype selection
# -----------------------------
st.session_state.phenotype = st.radio(
    "Phenotype",
    ["gradual", "stepwise", "exploratory"]
)

clear_checked = st.checkbox("Clear?")

# -----------------------------
# Plot
# -----------------------------
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=pdat["rel_trial"],
        y=pdat["aimdeviation_deg"],
        mode="lines+markers",
        name="trajectory"
    )
)

# selected clicks
for c in st.session_state.clicks:
    fig.add_vline(x=c, line_color="red")

# dynamic y-axis scaling
y_min = pdat["aimdeviation_deg"].min()
y_max = pdat["aimdeviation_deg"].max()

y_pad = 10

fig.update_layout(
    xaxis_title="Trial",
    yaxis_title="Aim Deviation (deg)",
    yaxis_range=[y_min - y_pad, y_max + y_pad],
    dragmode=False,
    clickmode="event"
)

# -----------------------------
# Capture clicks
# -----------------------------
event = st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun",
    config={
        "doubleClick": False,
        "scrollZoom": False,
        "displayModeBar": False
    }
)

if event and event.selection and event.selection.get("points"):

    x = event.selection["points"][0]["x"]

    if len(st.session_state.clicks) < 2:
        st.session_state.clicks.append(int(x))

# -----------------------------
# Controls
# -----------------------------
st.write("Clicks:", st.session_state.clicks)

col1, col2, col3 = st.columns(3)

# reset
with col1:

    if st.button("Reset"):
        reset_clicks()

# next participant
with col2:

    # allow advancing even without clicks
    if st.button("Next participant"):

        # only save if 2 clicks exist
        if len(st.session_state.clicks) == 2:
            save_current()

        reset_clicks()

        # final participant
        if st.session_state.idx >= len(participants) - 1:

            st.session_state.finished = True

        else:
            st.session_state.idx += 1

        st.rerun()

# manual download anytime
with col3:

    if len(st.session_state.results) > 0:

        df_out = pd.DataFrame(st.session_state.results)

        st.download_button(
            "Download CSV",
            data=df_out.to_csv(index=False),
            file_name=f"learning_labels_{labeler_id}.csv",
            mime="text/csv"
        )