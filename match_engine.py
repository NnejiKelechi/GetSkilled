import pandas as pd

def find_matches(df):
    matches = []
    matched_learners = set()
    matched_teachers = set()
    level_order = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}

    if "SkillLevel" not in df.columns:
        df["SkillLevel"] = "Intermediate"

    for _, learner in df.sample(frac=1).iterrows():
        learner_name = learner["Name"]
        learner_skill = learner["WantsToLearn"]
        learner_level = level_order.get(learner["SkillLevel"], 1)

        if learner["Role"] != "Learner" or learner_name in matched_learners:
            continue

        potential_teachers = df[
            (df["Role"] == "Teacher") &
            (df["CanTeach"] == learner_skill) &
            (~df["Name"].isin(matched_teachers))
        ]

        for _, teacher in potential_teachers.iterrows():
            teacher_level = level_order.get(teacher["SkillLevel"], 3)
            if teacher_level > learner_level:
                teacher_name = teacher["Name"]
                matches.append({
                    "Learner": learner_name,
                    "Teacher": teacher_name,
                    "Skill": learner_skill,
                    "Message_Learner": f"You are being matched with {teacher_name} to learn {learner_skill}.",
                    "Message_Teacher": f"You are being matched with {learner_name} to teach {learner_skill}."
                })
                matched_learners.add(learner_name)
                matched_teachers.add(teacher_name)
                break

    return matches
