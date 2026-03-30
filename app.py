from random import random

import streamlit as st
import pandas as pd
from modules.analyzer import analyze_topics, get_weak_topics
from modules.recommender import recommend_topics
import os
from modules.scorer import calculate_score, get_level
from modules.pattern_analyzer import analyze_patterns
from modules.interview import get_question
import time

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "interview_score" not in st.session_state:
    st.session_state.interview_score = 0

if "questions_attempted" not in st.session_state:
    st.session_state.questions_attempted = 0


st.set_page_config(page_title="AI Interview Assistant", layout="wide")

st.title("AI Interview Preparation Assistant 🚀")

# -----------------------------
# Load Data
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "questions.csv")
EXPECTED_COLUMNS = ["question", "topic", "difficulty", "status"]


def normalize_columns(df):
    """Normalize CSV columns to expected schema when possible."""
    normalized = {col.strip().lower(): col for col in df.columns}

    if set(EXPECTED_COLUMNS).issubset(normalized.keys()):
        rename_map = {normalized[col]: col for col in EXPECTED_COLUMNS}
        df = df.rename(columns=rename_map)
        return df[EXPECTED_COLUMNS]

    return None


def load_data():
    if os.path.exists(DATA_FILE):
        # First try standard CSV parsing with header.
        try:
            raw_df = pd.read_csv(DATA_FILE)
        except Exception:
            raw_df = pd.DataFrame()

        df = normalize_columns(raw_df) if not raw_df.empty else None

        # Fallback for headerless CSV files.
        if df is None:
            raw_df = pd.read_csv(
                DATA_FILE,
                header=None,
                names=EXPECTED_COLUMNS,
                on_bad_lines="skip"
            )

            if not raw_df.empty:
                first_row = [str(value).strip().lower() for value in raw_df.iloc[0].tolist()]
                if first_row == EXPECTED_COLUMNS:
                    raw_df = raw_df.iloc[1:]

            df = raw_df[EXPECTED_COLUMNS]
    else:
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)

    # Normalize string values for clean display and analysis.
    for col in EXPECTED_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    return df


def save_data(df):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    df.to_csv(DATA_FILE, index=False)


def load_uploaded_csv(uploaded_file):
    """Load uploaded CSV with the same schema tolerance as disk loader."""
    try:
        raw_df = pd.read_csv(uploaded_file)
    except Exception:
        raw_df = pd.DataFrame()

    df = normalize_columns(raw_df) if not raw_df.empty else None

    if df is None:
        uploaded_file.seek(0)
        raw_df = pd.read_csv(
            uploaded_file,
            header=None,
            names=EXPECTED_COLUMNS,
            on_bad_lines="skip"
        )

        if not raw_df.empty:
            first_row = [str(value).strip().lower() for value in raw_df.iloc[0].tolist()]
            if first_row == EXPECTED_COLUMNS:
                raw_df = raw_df.iloc[1:]

        df = raw_df[EXPECTED_COLUMNS]

    for col in EXPECTED_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    return df


df = load_data()

# -----------------------------
# Layout
# -----------------------------
col1, col2 = st.columns(2)

# -----------------------------
# Add Question Section
# -----------------------------
with col1:
    st.subheader("Add New Question")

    question = st.text_input("Question Name")
    topic = st.selectbox("Topic", ["Array", "Linked List", "Tree", "Graph", "DP"])
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
    status = st.selectbox("Status", ["Solved", "Unsolved"])

    if st.button("Add Question"):
        if question:
            new_row = pd.DataFrame(
                [[question, topic, difficulty, status]],
                columns=df.columns
            )

            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)

            st.success("Question added successfully!")
        else:
            st.warning("Please enter a question name.")

# -----------------------------
# Display Data
# -----------------------------
with col2:
    st.subheader("Your Questions")
    st.caption(f"Loaded from: {DATA_FILE}")

    if st.button("Reload CSV"):
        st.rerun()

    with st.expander("Import Questions CSV"):
        st.caption("CSV should contain columns: question, topic, difficulty, status")
        uploaded = st.file_uploader("Upload CSV", type=["csv"], key="questions_uploader")

        import_col1, import_col2 = st.columns(2)

        if import_col1.button("Replace with uploaded CSV", disabled=uploaded is None):
            imported_df = load_uploaded_csv(uploaded)
            save_data(imported_df)
            st.success(f"Imported {len(imported_df)} rows (replace mode).")
            st.rerun()

        if import_col2.button("Append uploaded CSV", disabled=uploaded is None):
            imported_df = load_uploaded_csv(uploaded)
            merged_df = pd.concat([df, imported_df], ignore_index=True)
            merged_df = merged_df.drop_duplicates().reset_index(drop=True)
            save_data(merged_df)
            st.success(f"Imported {len(imported_df)} rows (append mode).")
            st.rerun()

    if not df.empty:
        st.dataframe(df, width="stretch")

        if len(df) == 1:
            st.warning(
                "Only 1 row is currently saved in questions.csv. "
                "Use Import Questions CSV to load your full dataset."
            )
    else:
        st.info("No questions added yet.")

st.divider()

# -----------------------------
# Basic Stats
# -----------------------------
st.subheader("Progress Overview")

if not df.empty:

    total = len(df)
    solved = len(df[df["status"].str.lower().str.strip().isin(["solved", "accepted"])])
    unsolved = total - solved

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Questions", total)
    col2.metric("Solved", solved)
    col3.metric("Unsolved", unsolved)

else:
    st.info("Add some questions to see progress.")

st.divider()

# -----------------------------
# Weak Topic Detection
# -----------------------------
st.subheader("Weak Topics")

if not df.empty:

    topic_stats = analyze_topics(df)
    weak_topics = get_weak_topics(topic_stats)

    if weak_topics:
        for topic, stats in weak_topics.items():
            st.write(f"⚠️ {topic} → {stats['solved']} / {stats['total']} solved")
    else:
        st.success("No weak topics! Great job 🔥")

else:
    st.info("Add questions to analyze topics.")

st.divider()

# -----------------------------
# Recommendation System
# -----------------------------
st.subheader("Recommended Next")

if not df.empty:

    topic_stats = analyze_topics(df)
    weak_topics = get_weak_topics(topic_stats)

    recommendations = recommend_topics(weak_topics)

    if recommendations:
        for rec in recommendations:
            st.write(f"👉 {rec}")
    else:
        st.success("You're doing great! Keep practicing 🚀")

else:
    st.info("Add questions to get recommendations.")


st.divider()

# -----------------------------
# Topic-wise Progress Dashboard
# -----------------------------
st.subheader("Topic-wise Progress")

if not df.empty:

    topic_stats = analyze_topics(df)

    topic_data = []

    for topic, stats in topic_stats.items():

        percent = round(stats["accuracy"] * 100, 2)

        topic_data.append({
            "Topic": topic,
            "Solved": stats["solved"],
            "Total": stats["total"],
            "Progress (%)": percent
        })

    topic_df = pd.DataFrame(topic_data)

    # Sort by performance (low → high)
    topic_df = topic_df.sort_values(by="Progress (%)")

    st.dataframe(topic_df, width="stretch")

else:
    st.info("Add questions to see topic performance.")

st.subheader("Topic Performance Chart")

if not topic_df.empty:

    chart_df = topic_df.set_index("Topic")["Progress (%)"]

    st.bar_chart(chart_df)

st.divider()

# -----------------------------
# Interview Readiness Score
# -----------------------------
st.subheader("Interview Readiness Score")

if not df.empty:

    topic_stats = analyze_topics(df)

    score = calculate_score(df, topic_stats)

    level = get_level(score)

    st.metric("Score", f"{score} / 100")

    st.write(level)

else:
    st.info("Add questions to calculate readiness.")

st.divider()

# -----------------------------
# Pattern Intelligence
# -----------------------------
st.subheader("Pattern Insights")

if not df.empty:

    topic_stats = analyze_topics(df)

    strong, weak, overfocus = analyze_patterns(topic_stats)

    if strong:
        st.success(f"Strong in: {', '.join(strong)}")

    if weak:
        st.warning(f"Weak in: {', '.join(weak)}")

    if overfocus:
        st.info(f"Over-focused on: {', '.join(overfocus)}")

else:
    st.info("Add data to analyze patterns.")

# -----------------------------
# Adaptive Interview Mode + Timer (FIXED)
# -----------------------------
st.divider()
st.subheader("🧠 Adaptive Interview Mode")

import time
import random

# Initialize session state
if "current_question" not in st.session_state:
    st.session_state.current_question = None

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "interview_score" not in st.session_state:
    st.session_state.interview_score = 0

if "questions_attempted" not in st.session_state:
    st.session_state.questions_attempted = 0


# -----------------------------
# Get weakest topic
# -----------------------------
if not df.empty:

    topic_stats = analyze_topics(df)
    weak_topics = get_weak_topics(topic_stats)

    if weak_topics:
        weakest_topic = list(weak_topics.keys())[0]
    else:
        weakest_topic = random.choice(list(df["topic"].unique()))

    st.write(f"🎯 Recommended Focus: **{weakest_topic}**")

else:
    weakest_topic = None


# -----------------------------
# Start Interview
# -----------------------------
if st.button("🚀 Start Interview"):

    if weakest_topic:
        q = get_question(weakest_topic, None)
    else:
        q = get_question()

    if q:
        st.session_state.current_question = q
        st.session_state.start_time = time.time()


# -----------------------------
# Display Question + Timer
# -----------------------------
if st.session_state.current_question:

    q = st.session_state.current_question

    st.markdown(f"### 📌 {q['question']}")
    st.write(f"**Topic:** {q['topic']} | **Difficulty:** {q['difficulty']}")

    # 🔥 TIMER FIX
    if st.session_state.start_time:
        elapsed = int(time.time() - st.session_state.start_time)
        remaining = max(0, 120 - elapsed)

        st.metric("⏱️ Time Remaining", f"{remaining} sec")

        # Auto refresh every second
        time.sleep(1)
        st.rerun()

        if remaining == 0:
            st.warning("⏰ Time's up!")


    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💡 Hint"):
            st.info("Break into smaller parts. Think of patterns.")

    with col2:
        if st.button("🧠 Approach"):
            st.success("Identify pattern (DFS / DP / Sliding Window).")

    with col3:
        if st.button("🔄 New Question"):
            st.session_state.current_question = get_question(weakest_topic, None)
            st.session_state.start_time = time.time()
            st.rerun()


    st.divider()
    st.subheader("Your Answer")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Solved"):
            st.session_state.interview_score += 10
            st.session_state.questions_attempted += 1
            st.success("Great job!")

            st.session_state.current_question = None
            st.session_state.start_time = None

    with col2:
        if st.button("❌ Not Solved"):
            st.session_state.questions_attempted += 1
            st.error("Keep practicing!")

            st.session_state.current_question = None
            st.session_state.start_time = None


# -----------------------------
# Scoreboard
# -----------------------------
st.divider()
st.subheader("📊 Interview Performance")

attempted = st.session_state.questions_attempted
score = st.session_state.interview_score

accuracy = round((score / (attempted * 10)) * 100, 2) if attempted > 0 else 0

st.write(f"Questions Attempted: {attempted}")
st.write(f"Score: {score}")
st.write(f"Accuracy: {accuracy}%")