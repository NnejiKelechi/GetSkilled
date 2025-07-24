# match_engine.py (Optimized AI-Powered Matching Engine)

import pandas as pd
import streamlit as st
from sentence_transformers import SentenceTransformer, util
import torch

# --- Load & Cache the AI Model ---
@st.cache_resource(show_spinner=False)
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

# --- Optimized AI-Powered Matching Function ---
def find_matches(df, threshold=0.5, show_progress=False):
    matches = []
    unmatched_learners = []

    # Filter and reset index
    learners = df[df["Role"].str.lower() == "learner"].reset_index(drop=True)
    teachers = df[df["Role"].str.lower() == "teacher"].reset_index(drop=True)

    # Extract teacher data and encode
    teacher_names = teachers["Name"].astype(str).tolist()
    teacher_skills = teachers["CanTeach"].fillna("").astype(str).tolist()
    teacher_embeddings = model.encode(teacher_skills, convert_to_tensor=True)

    # Progress setup
    progress_bar = st.progress(0) if show_progress else None
    total = len(learners)

    # Pre-encode learners in batch
    learner_names = learners["Name"].astype(str).tolist()
    learner_skills = learners["WantsToLearn"].fillna("").astype(str).tolist()
    learner_embeddings = model.encode(learner_skills, convert_to_tensor=True)

    # Compute cosine similarity matrix
    similarity_matrix = util.cos_sim(learner_embeddings, teacher_embeddings)

    for idx, learner_name in enumerate(learner_names):
        best_match_idx = torch.argmax(similarity_matrix[idx]).item()
        best_score = similarity_matrix[idx][best_match_idx].item()

        if best_score >= threshold:
            teacher_name = teacher_names[best_match_idx]
            skill = learner_skills[idx]
            matches.append({
                "Learner": learner_name,
                "Teacher": teacher_name,
                "Skill": skill,
                "Score": round(best_score, 4),
                "AI_Confidence (%)": round(best_score * 100, 2),
                "Message_Learner": f"🎯 AI matched you with {teacher_name} to learn '{skill}'.",
                "Message_Teacher": f"🎓 AI matched you with {learner_name} to teach '{teachers.loc[best_match_idx, 'CanTeach']}'."
            })
        else:
            unmatched_learners.append({
                "Learner": learner_name,
                "Skill": learner_skills[idx],
                "Status": "❗ No match found yet. Please check back later – we’re still learning!"
            })

        if show_progress:
            progress_bar.progress((idx + 1) / total)

    if show_progress:
        progress_bar.empty()

    return pd.DataFrame(matches), pd.DataFrame(unmatched_learners)
