# match_engine.py (AI-powered version)

from sentence_transformers import SentenceTransformer, util
import pandas as pd
from tqdm import tqdm
import streamlit as st

# --- Load AI Model ---
model = SentenceTransformer('all-MiniLM-L6-v2')

# --- AI-Powered Matching Function ---
def find_matches(df, threshold=0.5, show_progress=False):
    matches = []
    matched_learners = set()

    learners = df[df["Role"].str.lower() == "learner"]
    teachers = df[df["Role"].str.lower() == "teacher"]

    learner_iterator = tqdm(learners.iterrows(), total=len(learners)) if not show_progress else learners.iterrows()
    progress_bar = st.progress(0) if show_progress else None
    progress_step = 1 / len(learners) if show_progress else None
    progress_count = 0

    for _, learner in learner_iterator:
        if learner["Name"] in matched_learners:
            continue

        learner_skill = str(learner.get("WantsToLearn", "")).strip()
        if not learner_skill:
            continue

        learner_embed = model.encode(learner_skill, convert_to_tensor=True)

        best_score = 0
        best_match = None

        for _, teacher in teachers.iterrows():
            teacher_skill = str(teacher.get("CanTeach", "")).strip()
            if not teacher_skill:
                continue

            teacher_embed = model.encode(teacher_skill, convert_to_tensor=True)
            score = util.pytorch_cos_sim(learner_embed, teacher_embed).item()

            if score > best_score:
                best_score = score
                best_match = teacher

        if best_match and best_score >= threshold:
            matches.append({
                "Learner": learner["Name"],
                "Teacher": best_match["Name"],
                "Skill": learner_skill,
                "SimilarityScore": round(best_score, 4),
                "AI_Confidence (%)": round(best_score * 100, 2),
                "Message_Learner": f"🎯 AI matched you with {best_match['Name']} to learn '{learner_skill}'.",
                "Message_Teacher": f"🎓 AI matched you with {learner['Name']} to teach '{best_match['CanTeach']}'."
            })
            matched_learners.add(learner["Name"])

        if show_progress and progress_bar:
            progress_count += 1
            progress_bar.progress(min(progress_count * progress_step, 1.0))

    if show_progress and progress_bar:
        progress_bar.empty()

    return pd.DataFrame(matches)
