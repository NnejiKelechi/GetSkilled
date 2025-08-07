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
    required_columns = ["name", "WantsToLearn", "CanTeach", "IsMatched"]
    if not all(col in users_df.columns for col in required_columns):
        print("Missing columns in users_df.")
        return pd.DataFrame(columns=["Learner", "Teacher", "Skill", "AI_Confidence (%)", "Explanation", "Timestamp"]), []

    learners = users_df[(users_df["WantsToLearn"].notnull()) & (users_df["IsMatched"] != True)].copy()
    teachers = users_df[(users_df["CanTeach"].notnull())].copy()

    matches = []
    matched_learners = set()
    matched_teachers = set()
    unmatched_learners = []

    for _, learner_row in learners.iterrows():
        learner_name = learner_row["name"]
        learner_skill = str(learner_row["WantsToLearn"])

        learner_embedding = model.encode(learner_skill)

        best_score = 0
        best_teacher = None

        for _, teacher_row in teachers.iterrows():
            teacher_name = teacher_row["name"]
            teacher_skill = str(teacher_row["CanTeach"])

            teacher_embedding = model.encode(teacher_skill)
            score = util.cos_sim(learner_embedding, teacher_embedding).item()

            if score > best_score and score >= threshold:
                best_score = score
                best_teacher = teacher_row

        if best_teacher is not None:
            teacher_name = best_teacher["name"]
            teacher_skill = best_teacher["CanTeach"]

            matches.append({
                "Learner": learner_name,
                "Teacher": teacher_name,
                "Skill": learner_skill,
                "AI_Confidence (%)": round(best_score * 100, 2),
                "Explanation": f"Paired based on similarity between '{learner_skill}' and '{teacher_skill}'",
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            matched_learners.add(learner_name)
            matched_teachers.add(teacher_name)

            # Update matched status
            users_df.loc[users_df["name"] == learner_name, "IsMatched"] = True
            users_df.loc[users_df["name"] == teacher_name, "IsMatched"] = True
        else:
            unmatched_learners.append(learner_name)

    # Save updated user status
    users_df.to_csv(USER_FILE, index=False)

    matches_df = pd.DataFrame(matches, columns=["Learner", "Teacher", "Skill", "AI_Confidence (%)", "Explanation", "Timestamp"])
    save_matches(matches_df)

    return matches_df, unmatched_learners


# --- Save matches to CSV ---
def save_matches(matches_df):
    if not matches_df.empty:
        matches_df.to_csv(MATCHES_FILE, index=False)


# --- Display a Learner's Match ---
def display_learner_match(name, matches_df):
    if "Learner" not in matches_df.columns:
        return pd.DataFrame()
    return matches_df[matches_df["Learner"].str.lower() == name.lower()]


# --- Get Unmatched Learners as DataFrame ---
def get_unmatched_learners(unmatched_names):
    return pd.DataFrame({"Unmatched Learner": unmatched_names})


# --- Generate AI-Inferred Study Targets ---
def generate_study_targets(users_df):
    targets = []
    for _, row in users_df.iterrows():
        base = 30
        boost = 10 if str(row.get("SkillLevel", "")).lower() == "beginner" else 5

        wants = str(row.get("WantsToLearn", ""))
        teach = str(row.get("CanTeach", ""))

        try:
            sim_score = util.cos_sim(
                model.encode(wants, convert_to_tensor=True),
                model.encode(teach, convert_to_tensor=True)
            ).item() * 10
        except:
            sim_score = 0

        targets.append({
            "Name": row["name"],
            "TargetMinutes": round(base + boost + sim_score, 2)
        })

    df = pd.DataFrame(targets)
    df.to_csv(TARGETS_FILE, index=False)
    return df
