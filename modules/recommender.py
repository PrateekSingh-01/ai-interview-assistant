def recommend_topics(weak_topics):

    recommendations = []

    for topic, stats in weak_topics.items():

        solved = stats["solved"]
        total = stats["total"]

        recommendations.append(
            f"Focus on {topic} ({solved}/{total} solved)"
        )

    return recommendations