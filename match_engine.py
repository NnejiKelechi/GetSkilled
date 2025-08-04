
# match_engine.py

import pandas as pd
from sentence_transformers import SentenceTransformer, util
import os
from datetime import datetime

# --- Paths ---
DATA_DIR = "data"
MATCHES_FILE = os.path.join(DATA_DIR, "matches.csv")
USER_FILE = os.path.join(DATA_DIR, "users.csv")
TARGETS_FILE = os.path.join(DATA_DIR, "targets.csv")

# --- Load model once ---
model = SentenceTransformer("all-MiniLM-L6-v2")

# --- AI-Powered Match Learners to Teachers ---
def find_matches(users_df, threshold=0.6):
    if not all(col in users_df.columns for col in ["name", "WantsToLearn", "CanTeach"]):
        return pd.DataFrame(), []

    learners = users_df[users_df["WantsToLearn"].notnull()].copy()
    teachers = users_df[users_df["CanTeach"].notnull()].copy()

    matches = []
    matched_learners = set()
    unmatched_learners = []

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
            explanation = f"Paired based on similarity between '{learner_row['WantsToLearn']}' and '{best_teacher['CanTeach']}'"
            matches.append({
                "Learner": learner_row["name"],
                "Teacher": best_teacher["name"],
                "Skill": learner_row["WantsToLearn"],
                "AI_Confidence (%)": round(best_score * 100, 2),
                "Explanation": explanation,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            matched_learners.add(learner_row["name"])
        else:
            unmatched_learners.append(learner_row["name"])

    matches_df = pd.DataFrame(matches)
    return matches_df, unmatched_learners


# --- Save matches to CSV ---
def save_matches(matches_df):
    if not matches_df.empty:
        matches_df.to_csv(MATCHES_FILE, index=False)


# --- Generate AI-Inferred Study Targets ---
def generate_study_targets(users_df):
    targets = []
    for _, row in users_df.iterrows():
        base = 30
        boost = 10 if row.get("SkillLevel", "").lower() == "beginner" else 5

        wants = str(row.get("WantsToLearn", ""))
        teach = str(row.get("CanTeach", ""))

        try:
            sim_score = util.cos_sim(
                model.encode(wants, convert_to_tensor=True),
                model.encode(teach, convert_to_tensor=True)
            ).item() * 10
        except:
            sim_score = 0

        target = base + boost + sim_score
        targets.append({"Name": row["name"], "TargetMinutes": round(target, 2)})

    df = pd.DataFrame(targets)
    df.to_csv(TARGETS_FILE, index=False)
    return df


# --- Display a Learner's Match ---
def display_learner_match(name, matches_df):
    return matches_df[matches_df["Learner"].str.lower() == name.lower()]


# --- Get Unmatched Learners as DataFrame ---
def get_unmatched_learners(unmatched_names):
    return pd.DataFrame({"Unmatched Learner": unmatched_names})
