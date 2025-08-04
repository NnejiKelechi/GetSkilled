# match_engine.py

import pandas as pd
from sentence_transformers import SentenceTransformer, util
import os
from datetime import datetime

# --- Paths ---
DATA_DIR = "data"
USER_FILE = os.path.join(DATA_DIR, "users.csv")
MATCHES_FILE = os.path.join(DATA_DIR, "matches.csv")
UNMATCHED_FILE = os.path.join(DATA_DIR, "unmatched.csv")
TARGETS_FILE = os.path.join(DATA_DIR, "targets.csv")

# --- Load model once ---
model = SentenceTransformer("all-MiniLM-L6-v2")

# --- AI-Powered Match Learners to Teachers ---
def find_matches(users_df, threshold=0.6):
    learners = users_df[(users_df["Role"] == "Learner") & (users_df["WantsToLearn"].notnull())].copy()
    teachers = users_df[(users_df["Role"] == "Teacher") & (users_df["CanTeach"].notnull())].copy()

    matches = []
    matched_learners = set()
    unmatched_learners = []

    if learners.empty or teachers.empty:
        return pd.DataFrame(), learners["Name"].tolist()

    for _, learner in learners.iterrows():
        if learner["Name"] in matched_learners:
            continue

        learner_embedding = model.encode(learner["WantsToLearn"], convert_to_tensor=True)
        best_match = None
        best_score = 0.0

        for _, teacher in teachers.iterrows():
            teacher_embedding = model.encode(teacher["CanTeach"], convert_to_tensor=True)
            similarity = util.cos_sim(learner_embedding, teacher_embedding).item()

            if similarity > best_score:
                best_score = similarity
                best_match = teacher

        if best_score >= threshold and best_match is not None:
            explanation = (
                f"Matched based on your interest in learning '{learner['WantsToLearn']}' "
                f"and {best_match['Name']}'s ability to teach it."
            )
            matches.append({
                "Learner": learner["Name"],
                "Teacher": best_match["Name"],
                "Skill": learner["WantsToLearn"],
                "AI_Confidence (%)": round(best_score * 100, 2),
                "Explanation": explanation,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            matched_learners.add(learner["Name"])
        else:
            unmatched_learners.append(learner["Name"])

    matches_df = pd.DataFrame(matches)
    matches_df.to_csv(MATCHES_FILE, index=False)

    unmatched_df = pd.DataFrame({"Unmatched": unmatched_learners})
    unmatched_df.to_csv(UNMATCHED_FILE, index=False)

    # Update users_df IsMatched field
    users_df["IsMatched"] = users_df["Name"].apply(
        lambda x: True if x in matched_learners else (
            False if x in unmatched_learners else users_df[users_df["Name"] == x]["IsMatched"].iloc[0]
            if "IsMatched" in users_df.columns else False
        )
    )
    users_df.to_csv(USER_FILE, index=False)

    return matches_df, unmatched_learners

# --- Get Unmatched Learners as DataFrame ---
def get_unmatched_learners(unmatched_names):
    return pd.DataFrame({"Name": unmatched_names, "WantsToLearn": "", "Reason": "No matching teacher found."})

# --- Display Match Info for a Learner ---
def display_learner_match(name, matches_df):
    return matches_df[matches_df["Learner"].str.lower() == name.lower()]

# --- Load Matches and Unmatched ---
def load_matches():
    if os.path.exists(MATCHES_FILE):
        matches_df = pd.read_csv(MATCHES_FILE)
    else:
        matches_df = pd.DataFrame(columns=["Learner", "Teacher", "Skill", "AI_Confidence (%)", "Explanation", "Timestamp"])

    if os.path.exists(UNMATCHED_FILE):
        unmatched_df = pd.read_csv(UNMATCHED_FILE)
        unmatched_list = unmatched_df["Unmatched"].tolist()
    else:
        unmatched_list = []

    return matches_df, unmatched_list

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

        target = base + boost + sim_score
        targets.append({"Name": row["Name"], "TargetMinutes": round(target, 2)})

    df = pd.DataFrame(targets)
    df.to_csv(TARGETS_FILE, index=False)
    return df
