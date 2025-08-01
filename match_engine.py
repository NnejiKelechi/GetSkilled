# match_engine.py (updated with habit tracker integration)

import pandas as pd
from sentence_transformers import SentenceTransformer, util
import os
import numpy as np
from datetime import datetime

DATA_DIR = "data"
MATCHES_FILE = os.path.join(DATA_DIR, "matches.csv")
USER_FILE = os.path.join(DATA_DIR, "users.csv")
TARGETS_FILE = os.path.join(DATA_DIR, "targets.csv")
# match_engine.py (updated with habit tracker integration)

import pandas as pd
from sentence_transformers import SentenceTransformer, util
import os
import numpy as np
from datetime import datetime

DATA_DIR = "data"
MATCHES_FILE = os.path.join(DATA_DIR, "matches.csv")
USER_FILE = os.path.join(DATA_DIR, "users.csv")
TARGETS_FILE = os.path.join(DATA_DIR, "targets.csv")

model = SentenceTransformer("all-MiniLM-L6-v2")

# --- Match Learners to Teachers ---
def find_matches(df, threshold=0.6):
    if not all(col in df.columns for col in ["Name", "WantsToLearn", "CanTeach"]):
        return pd.DataFrame(), []

    # Basic mock matching logic
    learners = df[df["Role"] == "Learner"]
    teachers = df[df["Role"] == "Teacher"]

    matches = []
    unmatched = []

    for _, learner in learners.iterrows():
        match_found = False
        for _, teacher in teachers.iterrows():
            if learner["WantsToLearn"].strip().lower() == teacher["CanTeach"].strip().lower():
                matches.append({
                    "Learner": learner["Name"],
                    "Teacher": teacher["Name"],
                    "Skill": learner["WantsToLearn"],
                    "Confidence": 1.0  # Simulated
                })
                match_found = True
                break
        if not match_found:
            unmatched.append(learner["Name"])

    matches_df = pd.DataFrame(matches)
    return matches_df, unmatched


# --- Save matches to CSV ---
def save_matches(matches_df):
    matches_df.to_csv(MATCHES_FILE, index=False)


# --- AI-Inferred Study Target Suggestions (from habit_tracker.py) ---
def generate_study_targets(users_df):
    targets = []
    for _, row in users_df.iterrows():
        base = 30
        boost = 10 if row.get("SkillLevel", "").lower() == "beginner" else 5

        wants = str(row.get("WantsToLearn", ""))
        teach = str(row.get("CanTeach", ""))

        sim_score = util.cos_sim(
            model.encode(wants, convert_to_tensor=True),
            model.encode(teach, convert_to_tensor=True)
        ).item() * 10

        target = base + boost + sim_score
        targets.append({"Name": row["name"], "TargetMinutes": round(target, 2)})

    df = pd.DataFrame(targets)
    df.to_csv(TARGETS_FILE, index=False)
    return df


# --- Display Learner Match ---
def display_learner_match(name, matches_df):
    return matches_df[matches_df["Learner"].str.lower() == name.lower()]


# --- Get Unmatched Learners ---
def get_unmatched_learners(unmatched_names):
    return pd.DataFrame({"Unmatched Learner": unmatched_names})

model = SentenceTransformer("all-MiniLM-L6-v2")

# --- Match Learners to Teachers ---
def find_matches(users_df, threshold=0.6):
    learners = users_df[users_df["WantsToLearn"].notnull()].copy()
    teachers = users_df[users_df["CanTeach"].notnull()].copy()

    matches = []
    matched_learners = set()

    for _, learner_row in learners.iterrows():
        if learner_row["name"] in matched_learners:
            continue

        learner_embedding = model.encode(str(learner_row["WantsToLearn"]))
        best_match = None
        best_score = 0
        best_teacher = None

        for _, teacher_row in teachers.iterrows():
            score = util.cos_sim(
                learner_embedding, model.encode(str(teacher_row["CanTeach"]))
            ).item()

            if score > best_score and score >= threshold:
                best_score = score
                best_teacher = teacher_row

        if best_teacher is not None:
            explanation = f"Paired based on {learner_row['WantsToLearn']} and {best_teacher['CanTeach']}"
            matches.append({
                "Learner": learner_row["name"],
                "Teacher": best_teacher["name"],
                "Skill": learner_row["WantsToLearn"],
                "AI_Confidence (%)": round(best_score * 100, 2),
                "Explanation": explanation,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            matched_learners.add(learner_row["name"])

    return pd.DataFrame(matches)


# --- Save matches to CSV ---
def save_matches(matches_df):
    matches_df.to_csv(MATCHES_FILE, index=False)


# --- AI-Inferred Study Target Suggestions (from habit_tracker.py) ---
def generate_study_targets(users_df):
    targets = []
    for _, row in users_df.iterrows():
        base = 30
        boost = 10 if row.get("SkillLevel", "").lower() == "beginner" else 5

        wants = str(row.get("WantsToLearn", ""))
        teach = str(row.get("CanTeach", ""))

        sim_score = util.cos_sim(
            model.encode(wants, convert_to_tensor=True),
            model.encode(teach, convert_to_tensor=True)
        ).item() * 10

        target = base + boost + sim_score
        targets.append({"Name": row["name"], "TargetMinutes": round(target, 2)})

    df = pd.DataFrame(targets)
    df.to_csv(TARGETS_FILE, index=False)
    return df
