def calculate_score(df, topic_stats):

    total = len(df)

    if total == 0:
        return 0

    # 1. Accuracy score (50%)
    solved = len(df[df["status"].str.lower().isin(["solved", "accepted"])])
    accuracy = solved / total

    accuracy_score = accuracy * 50

    # 2. Topic balance (30%)
    weak_topics = [t for t in topic_stats if topic_stats[t]["accuracy"] < 0.6]

    balance_score = max(0, 30 - (len(weak_topics) * 5))

    # 3. Difficulty coverage (20%)
    difficulties = df["difficulty"].str.lower().unique()

    difficulty_score = 0

    if "easy" in difficulties:
        difficulty_score += 5
    if "medium" in difficulties:
        difficulty_score += 10
    if "hard" in difficulties:
        difficulty_score += 5

    total_score = accuracy_score + balance_score + difficulty_score

    return round(min(total_score, 100), 2)


def get_level(score):

    if score >= 80:
        return "Ready for Advanced Interviews 🚀"
    elif score >= 60:
        return "Ready for Medium Interviews 👍"
    else:
        return "Need More Practice ⚠️"