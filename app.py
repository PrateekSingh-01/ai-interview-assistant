import streamlit as st
import pandas as pd
from modules.analyzer import analyze_topics, get_weak_topics
from modules.recommender import recommend_topics
import os
from modules.scorer import calculate_score, get_level

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