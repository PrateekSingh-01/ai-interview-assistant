def analyze_patterns(topic_stats):

    strong = []
    weak = []
    overfocus = []

    # Average total for comparison
    totals = [stats["total"] for stats in topic_stats.values()]
    avg_total = sum(totals) / len(totals) if totals else 0

    for topic, stats in topic_stats.items():

        accuracy = stats["accuracy"]
        total = stats["total"]

        if accuracy >= 0.75:
            strong.append(topic)

        if accuracy < 0.5:
            weak.append(topic)

        if total > avg_total * 1.5:
            overfocus.append(topic)

    return strong, weak, overfocus