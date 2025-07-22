# match_engine.py (Enhanced AI-Powered Version with unmatched notice)

from sentence_transformers import SentenceTransformer, util
import pandas as pd
import streamlit as st

# --- Load AI Model ---
model = SentenceTransformer('all-MiniLM-L6-v2')

# --- AI-Powered Matching Function ---
def find_matches(df, threshold=0.5, show_progress=False):
    matches = []
    matched_learners = set()
    unmatched_learners = []

    # Filter learners and teachers
    learners = df[df["Role"].str.lower() == "learner"]
    teachers = df[df["Role"].str.lower() == "teacher"]

    # Pre-encode teacher skills for efficiency
    teacher_embeddings = []
    for _, teacher in teachers.iterrows():
        skills = str(teacher.get("CanTeach", "")).strip()
        if skills:
            embedding = model.encode(skills, convert_to_tensor=True)
            teacher_embeddings.append((teacher, embedding))

    # Progress setup
    progress_bar = st.progress(0) if show_progress else None
    total_learners = len(learners)
    progress_count = 0

    # Match each learner to best teacher
    for _, learner in learners.iterrows():
        learner_name = learner.get("Name", "").strip()
        if learner_name.lower() in matched_learners:
            continue

        wants = str(learner.get("WantsToLearn", "")).strip()
        if not wants:
            continue

        learner_embedding = model.encode(wants, convert_to_tensor=True)

        best_score = 0
        best_match = None

        for teacher, teacher_embedding in teacher_embeddings:
            score = util.pytorch_cos_sim(learner_embedding, teacher_embedding).item()
            if score > best_score:
                best_score = score
                best_match = teacher

        if best_match is not None and best_score >= threshold:
            matches.append({
                "Learner": learner_name,
                "Teacher": best_match["Name"],
                "Skill": wants,
                "Score": round(best_score, 4),
                "AI_Confidence (%)": round(best_score * 100, 2),
                "Message_Learner": f"🎯 AI matched you with {best_match['Name']} to learn '{wants}'.",
                "Message_Teacher": f"🎓 AI matched you with {learner_name} to teach '{best_match['CanTeach']}'."
            })
            matched_learners.add(learner_name.lower())
        else:
            # Record unmatched learner for separate display
            unmatched_learners.append({
                "Learner": learner_name,
                "Skill": wants,
                "Status": "❗ No match found yet. Please check back later – we’re still learning!"
            })

        if show_progress and progress_bar:
            progress_count += 1
            progress_bar.progress(progress_count / total_learners)

    if show_progress and progress_bar:
        progress_bar.empty()

    matched_df = pd.DataFrame(matches)
    unmatched_df = pd.DataFrame(unmatched_learners)

    return matched_df, unmatched_df
