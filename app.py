import streamlit as st
import pandas as pd
import os
import time
import random

from modules.analyzer import analyze_topics, get_weak_topics
from modules.recommender import recommend_topics
from modules.scorer import calculate_score, get_level
from modules.pattern_analyzer import analyze_patterns
from modules.interview import get_question


# -----------------------------
# Load Data
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "questions.csv")

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=["question", "topic", "difficulty", "status"])

    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

# -----------------------------
# Add Question Section
# -----------------------------
st.divider()
st.markdown("## ➕ Add New Question")

col1, col2 = st.columns(2)

with col1:
    question = st.text_input("Question Name")

    topic = st.selectbox(
        "Topic",
        ["Array", "Linked List", "Tree", "Graph", "DP", "Stack", "Heap", "Sliding Window"]
    )

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
            st.rerun()
        else:
            st.warning("Please enter question name")

with col2:
    st.markdown("### 📋 Your Questions")

    if not df.empty:
        st.dataframe(df, width="stretch")
    else:
        st.info("No questions yet")

# -----------------------------
# Session State
# -----------------------------
if "current_question" not in st.session_state:
    st.session_state.current_question = None

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "interview_score" not in st.session_state:
    st.session_state.interview_score = 0

if "questions_attempted" not in st.session_state:
    st.session_state.questions_attempted = 0

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="AI Interview Assistant", layout="wide")

st.markdown("""
<h1 style='text-align: center;'>🚀 AI Interview Assistant</h1>
<p style='text-align: center; color: gray;'>Track • Analyze • Improve • Practice</p>
""", unsafe_allow_html=True)

# -----------------------------
# Load Data
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "questions.csv")

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=["question", "topic", "difficulty", "status"])

    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

# -----------------------------
# Dashboard
# -----------------------------
st.divider()
st.markdown("## 📊 Dashboard Overview")

if not df.empty:
    total = len(df)
    solved = len(df[df["status"].str.lower().isin(["solved", "accepted"])])
    unsolved = total - solved

    col1, col2, col3 = st.columns(3)
    col1.metric("📘 Total", total)
    col2.metric("✅ Solved", solved)
    col3.metric("❌ Unsolved", unsolved)

    progress = solved / total if total > 0 else 0
    st.progress(progress)
    st.write(f"Overall Progress: {round(progress*100,2)}%")
else:
    st.info("No data available")

# -----------------------------
# Weak Topics
# -----------------------------
st.divider()
st.markdown("## 🧠 Weak Topics")

if not df.empty:
    topic_stats = analyze_topics(df)
    weak_topics = get_weak_topics(topic_stats)

    if weak_topics:
        for topic, stats in weak_topics.items():
            percent = round((stats["solved"]/stats["total"])*100,2)
            st.error(f"{topic} → {percent}% ({stats['solved']}/{stats['total']})")
    else:
        st.success("No weak topics 🔥")

# -----------------------------
# Recommendations
# -----------------------------
st.divider()
st.markdown("## 🎯 Recommendations")

if not df.empty:
    recommendations = recommend_topics(weak_topics)

    if recommendations:
        for rec in recommendations:
            st.info(rec)
    else:
        st.success("You're doing great 🚀")

# -----------------------------
# Topic Dashboard
# -----------------------------
st.divider()
st.markdown("## 📊 Topic Performance")

if not df.empty:
    topic_data = []

    for topic, stats in topic_stats.items():
        percent = round(stats["accuracy"]*100,2)
        topic_data.append({
            "Topic": topic,
            "Solved": stats["solved"],
            "Total": stats["total"],
            "Progress (%)": percent
        })

    topic_df = pd.DataFrame(topic_data).sort_values(by="Progress (%)")

    st.dataframe(topic_df, width="stretch")
    st.bar_chart(topic_df.set_index("Topic")["Progress (%)"])

# -----------------------------
# Interview Score
# -----------------------------
st.divider()
st.markdown("## 🧠 Interview Readiness")

if not df.empty:
    score = calculate_score(df, topic_stats)
    level = get_level(score)

    st.metric("Score", f"{score}/100")
    st.write(level)

# -----------------------------
# Pattern Insights
# -----------------------------
st.divider()
st.markdown("## 🔍 Pattern Insights")

if not df.empty:
    strong, weak, overfocus = analyze_patterns(topic_stats)

    if strong:
        st.success("💪 Strong: " + ", ".join(strong))
    if weak:
        st.warning("⚠️ Weak: " + ", ".join(weak))
    if overfocus:
        st.info("📌 Over-focused: " + ", ".join(overfocus))

# -----------------------------
# Adaptive Interview Mode
# -----------------------------
st.divider()
st.markdown("## 🧠 Adaptive Interview Mode")

if not df.empty:
    if weak_topics:
        weakest_topic = list(weak_topics.keys())[0]
    else:
        weakest_topic = random.choice(list(df["topic"].unique()))

    st.write(f"🎯 Focus: **{weakest_topic}**")
else:
    weakest_topic = None

# Start Interview
if st.button("🚀 Start Interview"):
    q = get_question(weakest_topic, None)
    if q:
        st.session_state.current_question = q
        st.session_state.start_time = time.time()

# Show Question
if st.session_state.current_question:
    q = st.session_state.current_question

    st.markdown(f"""
    ### 📌 {q['question']}
    **Topic:** {q['topic']}  
    **Difficulty:** {q['difficulty']}
    """)

    # Timer
    if st.session_state.start_time:
        elapsed = int(time.time() - st.session_state.start_time)
        remaining = max(0, 120 - elapsed)

        st.metric("⏱️ Time Remaining", f"{remaining}s")

        time.sleep(1)
        st.rerun()

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Solved"):
            st.session_state.interview_score += 10
            st.session_state.questions_attempted += 1
            st.session_state.current_question = None
            st.session_state.start_time = None

    with col2:
        if st.button("❌ Not Solved"):
            st.session_state.questions_attempted += 1
            st.session_state.current_question = None
            st.session_state.start_time = None

# -----------------------------
# Scoreboard
# -----------------------------
st.divider()
st.markdown("## 📊 Interview Performance")

attempted = st.session_state.questions_attempted
score_val = st.session_state.interview_score

accuracy = round((score_val/(attempted*10))*100,2) if attempted else 0

col1, col2, col3 = st.columns(3)
col1.metric("Questions", attempted)
col2.metric("Score", score_val)
col3.metric("Accuracy", f"{accuracy}%")