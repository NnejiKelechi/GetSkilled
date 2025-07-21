import streamlit as st
import pandas as pd
import os
from sentence_transformers import SentenceTransformer, util
from match_engine import find_matches
from utils import safe_load_users
from constants import USER_FILE, RATINGS_FILE, MATCH_FILE

# Load model globally
model = SentenceTransformer('all-MiniLM-L6-v2')

def admin_dashboard():
    st.subheader("🔐 Admin Panel")
    password = st.text_input("Enter admin password", type="password")

    if st.button("Login"):
        if password == "admin123":
            st.success("✅ Access granted!")

            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "👤 User Data", "📊 Ratings", "🤝 Matches", "🧠 AI Match Engine", "📋 Match Summary"
            ])

            # --- USER DATA ---
            with tab1:
                st.markdown("### 👥 Manage User Data")
                if st.button("🧹 Clean & Format User Data"):
                    users = safe_load_users()
                    users.to_csv(USER_FILE, index=False)
                    st.success("✅ Data cleaned and saved successfully.")

                if os.path.exists(USER_FILE):
                    st.dataframe(pd.read_csv(USER_FILE))

            # --- RATINGS ---
            with tab2:
                st.markdown("### 🌟 Submitted Ratings")
                if os.path.exists(RATINGS_FILE):
                    ratings_df = pd.read_csv(RATINGS_FILE)
                    st.dataframe(ratings_df)
                else:
                    st.info("No ratings file found yet.")

            # --- MATCHES ---
            with tab3:
                st.markdown("### 🤝 AI-Matched Pairs")
                if os.path.exists(MATCH_FILE):
                    matches = pd.read_csv(MATCH_FILE)
                    paired_users = []

                    for _, row in matches.iterrows():
                        try:
                            learner = row["Learner"]
                            teacher = row["Teacher"]
                            skill = row.get("Skill", "")

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
                        except KeyError:
                            st.warning("⚠️ Missing 'Skill' field in some match records.")

                    paired_df = pd.DataFrame(paired_users)
                    st.dataframe(paired_df)
                else:
                    st.info("No match data available yet.")

            # --- AI MATCH ENGINE ---
            with tab4:
                st.markdown("### ⚙️ Run AI Matching Engine")
                if os.path.exists(USER_FILE):
                    if st.button("🔄 Re-run AI Matching"):
                        user_df = pd.read_csv(USER_FILE)
                        matches = find_matches(user_df, threshold=0.6, show_progress=True)
                        pd.DataFrame(matches).to_csv(MATCH_FILE, index=False)
                        st.success("✅ Matches re-generated and saved.")
                        st.dataframe(pd.DataFrame(matches))
                else:
                    st.warning("User file not found.")

            # --- MATCH SUMMARY ---
            with tab5:
                st.markdown("### 📋 User Match Summary")

                if os.path.exists(USER_FILE):
                    all_users = pd.read_csv(USER_FILE)
                    all_users["Name"] = all_users["Name"].astype(str).str.strip().str.lower()

                    matched_names = set()
                    if os.path.exists(MATCH_FILE):
                        matches = pd.read_csv(MATCH_FILE)
                        matches["Learner"] = matches["Learner"].astype(str).str.lower()
                        matches["Teacher"] = matches["Teacher"].astype(str).str.lower()
                        matched_names = set(matches["Learner"]) | set(matches["Teacher"])

                    all_users["Match Status"] = all_users["Name"].apply(
                        lambda n: "Paired" if n in matched_names else "Unpaired"
                    )

                    # 🔍 All Users
                    st.markdown("#### ✅ All Users")
                    st.dataframe(all_users[[
                        "Name", "Email", "Gender", "SkillLevel", "Role", 
                        "CanTeach", "WantsToLearn", "Timestamp", "Match Status"
                    ]])

                    # 🔗 Paired Users
                    paired_users = all_users[all_users["Match Status"] == "Paired"]
                    st.markdown("#### 🔗 Paired Users")
                    st.dataframe(paired_users[[
                        "Name", "Email", "Gender", "SkillLevel", "Role", 
                        "CanTeach", "WantsToLearn", "Timestamp"
                    ]])

                    # ❌ Unpaired Users
                    unpaired_users = all_users[all_users["Match Status"] == "Unpaired"]
                    st.markdown("#### ❌ Unpaired Users")
                    st.dataframe(unpaired_users[[
                        "Name", "Email", "Gender", "SkillLevel", "Role", 
                        "CanTeach", "WantsToLearn", "Timestamp"
                    ]])
                else:
                    st.warning("User file not found.")
