# match_engine.py (Enhanced AI-Powered Version with Explanations and Ratings)

from sentence_transformers import SentenceTransformer, util
import pandas as pd
import streamlit as st
import os

# --- Load AI Model ---
model = SentenceTransformer('all-MiniLM-L6-v2')

# --- AI-Powered Matching Function ---
def find_matches(df, threshold=0.5, show_progress=False):
    # Normalize column names
    df.columns = df.columns.str.lower()

    # Validate required column
    if 'role' not in df.columns:
        st.error("❌ The uploaded data is missing the required 'Role' column.")
        return pd.DataFrame(), pd.DataFrame()

    matches = []
    matched_learners = set()
    unmatched_learners = []

    # Filter learners and teachers
    learners = df[df["role"].str.lower() == "learner"]
    teachers = df[df["role"].str.lower() == "teacher"]

    # Pre-encode teacher skills for efficiency
    teacher_embeddings = []
    for _, teacher in teachers.iterrows():
        skills = str(teacher.get("canteach", "")).strip()
        if skills:
            embedding = model.encode(skills, convert_to_tensor=True)
            teacher_embeddings.append((teacher, embedding))

    # Progress setup
    progress_bar = st.progress(0) if show_progress else None
    total_learners = len(learners)
    progress_count = 0

    # Match each learner to best teacher
    for _, learner in learners.iterrows():
        learner_name = learner.get("name", "").strip()
        if learner_name.lower() in matched_learners:
            continue

        wants = str(learner.get("wantstolearn", "")).strip()
        if not wants:
            continue

        learner_embedding = model.encode(wants, convert_to_tensor=True)

        best_score = 0
        best_match = None
        match_explanation = ""

        for teacher, teacher_embedding in teacher_embeddings:
            score = util.pytorch_cos_sim(learner_embedding, teacher_embedding).item()
            if score > best_score:
                best_score = score
                best_match = teacher
                match_explanation = (
                    f"Your interest in learning '{wants}' closely matches with {teacher['name']}'s ability to teach '{teacher['canteach']}'. "
                    f"The AI model found a semantic similarity score of {round(score * 100, 2)}%."
                )

        if best_match is not None and best_score >= threshold:
            matches.append({
                "Learner": learner_name,
                "Teacher": best_match["name"],
                "Skill": wants,
                "Score": round(best_score, 4),
                "AI_Confidence (%)": round(best_score * 100, 2),
                "Message_Learner": f"🎯 AI matched you with {best_match['name']} to learn '{wants}'.",
                "Message_Teacher": f"🎓 AI matched you with {learner_name} to teach '{best_match['canteach']}'.",
                "Explanation": match_explanation,
                "Rating": None  # Learner can update this later via UI
            })
            matched_learners.add(learner_name.lower())
        else:
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


# --- Display Learner Match and Rating ---
def display_learner_match(matches, name_input, RATINGS_FILE):
    st.markdown("### 🎉 Your Match")

    # Ensure name_input is lowercase
    name_input = name_input.lower()

    # Filter match where user is either a learner or teacher
    if "Learner" in matches.columns and "Teacher" in matches.columns:
        name_matches = matches[
            (matches["Learner"].str.lower() == name_input) |
            (matches["Teacher"].str.lower() == name_input)
        ]
    else:
        st.warning("⚠️ Match data is missing expected columns.")
        return

    if not name_matches.empty:
        row = name_matches.iloc[0]
        learner = row["Learner"]
        teacher = row["Teacher"]
        skill = row["Skill"]
        explanation = row.get("Explanation", "")
        score = row.get("AI_Confidence (%)", "")

        st.success(f"🎯 You've been paired with **{teacher.title()}** to learn **{skill}**.")
        st.info(f"🧠 _AI Match Explanation_: {explanation}")
        st.caption(f"🤖 Confidence Score: **{score}**")

        # --- Rating Section ---
        st.markdown("### ⭐ Rate Your Match")
        rating = st.slider("How well does this match meet your expectations?", 1, 5, 3)
        if st.button("Submit Rating"):
            new_rating = {
                "user": learner,
                "partner": teacher,
                "skill": skill,
                "rating": rating
            }

            # Append to ratings file
            if os.path.exists(RATINGS_FILE):
                ratings_df = pd.read_csv(RATINGS_FILE)
                ratings_df = pd.concat([ratings_df, pd.DataFrame([new_rating])], ignore_index=True)
            else:
                ratings_df = pd.DataFrame([new_rating])

            ratings_df.to_csv(RATINGS_FILE, index=False)
            st.success("✅ Thank you for rating your match!")
    else:
        st.warning("😕 No match found for your name. Please ensure it’s correctly spelled.")
