import streamlit as st
import pandas as pd
from modules.analyzer import analyze_topics, get_weak_topics
from modules.recommender import recommend_topics

st.set_page_config(page_title="AI Interview Assistant", layout="wide")

st.title("AI Interview Preparation Assistant 🚀")

# -----------------------------
# Load Data
# -----------------------------
def load_data():
    try:
        df = pd.read_csv("data/questions.csv")
    except:
        df = pd.DataFrame(columns=["question", "topic", "difficulty", "status"])
    return df


def save_data(df):
    df.to_csv("data/questions.csv", index=False)


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

    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No questions added yet.")

st.divider()

# -----------------------------
# Basic Stats
# -----------------------------
st.subheader("Progress Overview")

if not df.empty:

    total = len(df)
    solved = len(df[df["status"] == "Solved"])
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