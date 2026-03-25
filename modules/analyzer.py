def analyze_topics(df):

    topic_stats = {}

    for topic in df["topic"].unique():

        topic_df = df[df["topic"] == topic]

        total = len(topic_df)

        # ✅ FIX: define solved properly
        solved = len(
            topic_df[
                topic_df["status"].str.lower().str.strip().isin(["solved", "accepted"])
            ]
        )

        topic_stats[topic] = {
            "total": total,
            "solved": solved,
            "accuracy": solved / total if total > 0 else 0
        }

    return topic_stats


def get_weak_topics(topic_stats):

    # Sort topics by accuracy (ascending)
    sorted_topics = sorted(
        topic_stats.items(),
        key=lambda x: x[1]["accuracy"]
    )

    # Pick top 2 weakest topics
    weak_topics = dict(sorted_topics[:2])

    return weak_topics