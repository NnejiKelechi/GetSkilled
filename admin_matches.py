import streamlit as st
import pandas as pd
import os
from sentence_transformers import SentenceTransformer, util

MATCH_FILE = "data/matches.csv"

# Load model once
model = SentenceTransformer("all-MiniLM-L6-v2")

def show_matches_tab():
    st.markdown("### 🤝 AI-Matched Pairs")

    if not os.path.exists(MATCH_FILE):
        st.info("No match data available yet.")
        return

    matches = pd.read_csv(MATCH_FILE)

    if not {"Learner", "Teacher", "Skill"}.issubset(matches.columns):
        st.error("❌ Missing required columns in matches.csv (Learner, Teacher, Skill)")
        return

    matches["Learner"] = matches["Learner"].astype(str).str.strip().str.lower()
    matches["Teacher"] = matches["Teacher"].astype(str).str.strip().str.lower()

    paired_users = []

    for _, row in matches.iterrows():
        learner = row["Learner"]
        teacher = row["Teacher"]
        skill = row["Skill"]

        learner_embed = model.encode(learner, convert_to_tensor=True)
        teacher_embed = model.encode(teacher, convert_to_tensor=True)
        skill_embed = model.encode(skill, convert_to_tensor=True)

        match_score = (
            util.pytorch_cos_sim(learner_embed, skill_embed).item() +
            util.pytorch_cos_sim(teacher_embed, skill_embed).item()
        ) / 2
        confidence = round(match_score * 100, 2)

        paired_users.append({
            "User": learner.title(), "Paired With": teacher.title(),
            "Role": "Learner", "Skill": skill, "AI Confidence": confidence
        })
        paired_users.append({
            "User": teacher.title(), "Paired With": learner.title(),
            "Role": "Teacher", "Skill": skill, "AI Confidence": confidence
        })

    paired_df = pd.DataFrame(paired_users)
    st.dataframe(paired_df)
