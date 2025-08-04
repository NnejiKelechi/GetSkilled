import pandas as pd
from sentence_transformers import SentenceTransformer, util
import os

model = SentenceTransformer("all-MiniLM-L6-v2")
MATCHES_FILE = os.path.join("data", "matches.csv")

def find_matches(users_df, threshold=0.6):
    learners = users_df[users_df["role"] == "Learner"]
    teachers = users_df[users_df["role"] == "Teacher"]

    matches = []
    unmatched_learners = []

    for _, learner in learners.iterrows():
        learner_query = learner["WantsToLearn"]
        learner_embedding = model.encode(learner_query, convert_to_tensor=True)

        best_score = 0
        best_match = None

        for _, teacher in teachers.iterrows():
            teacher_query = teacher["CanTeach"]
            teacher_embedding = model.encode(teacher_query, convert_to_tensor=True)
            similarity = util.pytorch_cos_sim(learner_embedding, teacher_embedding).item()

            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = teacher

        if best_match is not None:
            matches.append({
                "Learner": learner["name"],
                "Teacher": best_match["name"],
                "Skill": learner_query,
                "AI_Confidence (%)": round(best_score * 100, 2),
                "Explanation": f"The learner wants to learn '{learner_query}', which closely matches the teacher’s skill '{best_match['CanTeach']}'."
            })
        else:
            unmatched_learners.append(learner)

    matches_df = pd.DataFrame(matches)
    return matches_df, unmatched_learners

def save_matches(matches_df):
    if not matches_df.empty:
        matches_df.to_csv(MATCHES_FILE, index=False)

def load_matches():
    if os.path.exists(MATCHES_FILE):
        return pd.read_csv(MATCHES_FILE)
    return pd.DataFrame(columns=["Learner", "Teacher", "Skill", "AI_Confidence (%)", "Explanation"])

def display_learner_match(learner_name, matches_df):
    return matches_df[matches_df["Learner"].str.lower() == learner_name.lower()]

def get_unmatched_learners(unmatched_list):
    return pd.DataFrame(unmatched_list) if unmatched_list else pd.DataFrame(columns=["name", "email", "WantsToLearn", "SkillLevel"])

def generate_study_targets(users_df, default_minutes=90):
    targets = []
    for _, user in users_df.iterrows():
        if user["role"] == "Learner":
            targets.append({
                "Name": user["name"],
                "TargetMinutes": default_minutes
            })
    return pd.DataFrame(targets)

