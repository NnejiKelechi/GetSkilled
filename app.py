import streamlit as st
import pandas as pd
import os
from datetime import datetime
from match_engine import find_matches, display_learner_match, get_unmatched_learners, save_matches, generate_study_targets
from habit_tracker import load_users, save_users, log_study_activity, load_matches

# --- Constants and Setup ---
st.set_page_config(page_title="GetSkilled", layout="wide")
DATA_DIR = "data"
USER_FILE = os.path.join(DATA_DIR, "users.csv")

# --- Load or initialize users ---
def load_user_data():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    return pd.DataFrame(columns=["name", "email", "role", "WantsToLearn", "CanTeach", "SkillLevel", "IsMatched"])

def update_is_matched_flag(user_name):
    df = load_user_data()
    if "IsMatched" not in df.columns:
        df["IsMatched"] = False
    df.loc[df["name"].str.lower() == user_name.lower(), "IsMatched"] = True
    df.to_csv(USER_FILE, index=False)

def main():
    st.title("🎓 GetSkilled: Connect Learners to Teachers")

    menu = ["Register", "Login", "Admin"]
    choice = st.sidebar.selectbox("Navigation", menu)

    users = load_user_data()

    if choice == "Register":
        st.subheader("🔐 Register")
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        role = st.selectbox("Role", ["Learner", "Teacher"])
        skill = st.text_input("Wants to Learn" if role == "Learner" else "Can Teach")
        skill_level = st.selectbox("Skill Level", ["Beginner", "Intermediate", "Advanced"])

        if st.button("Submit"):
            if name and email and skill:
                new_user = {
                    "name": name,
                    "email": email,
                    "role": role,
                    "WantsToLearn": skill if role == "Learner" else "",
                    "CanTeach": skill if role == "Teacher" else "",
                    "SkillLevel": skill_level,
                    "IsMatched": False
                }
                users = users.append(new_user, ignore_index=True)
                users.to_csv(USER_FILE, index=False)

                # Automatically run matching
                matches_df, unmatched_learners = find_matches(users)
                save_matches(matches_df)
                generate_study_targets(users)

                for matched_name in matches_df["Learner"].unique():
                    update_is_matched_flag(matched_name)

                st.success("✅ You have been registered and matched (or queued). Please login to see your match.")
            else:
                st.warning("Please fill all required fields.")

    elif choice == "Login":
        st.subheader("🔓 Login")
        name_input = st.text_input("Enter your full name")
        role = st.selectbox("Role", ["Learner", "Teacher"])
        if st.button("Login"):
            user_row = users[users["name"].str.lower() == name_input.lower()]
            if not user_row.empty:
                user_row = user_row.iloc[0]
                is_matched = user_row.get("IsMatched", False)

                if role == "Learner":
                    if not is_matched:
                        st.warning("⏳ Matching in progress... Please check back shortly.")
                        return
                    else:
                        matches_df = load_matches()
                        learner_matches = display_learner_match(name_input, matches_df)
                        st.subheader(f"Welcome, {name_input} 👋")
                        if learner_matches.empty:
                            st.info("No match found yet. Please check again later.")
                        else:
                            st.success("🎯 You have been successfully matched!")
                            for _, row in learner_matches.iterrows():
                                st.write(f"**Skill:** {row['Skill']}")
                                st.write(f"**Teacher:** {row['Teacher']}")
                                st.write(f"**AI Confidence:** {row['AI_Confidence (%)']}%")
                                st.caption(f"🧠 _{row['Explanation']}_")
                            st.divider()
                else:
                    st.subheader(f"Welcome, {name_input} 👋")
                    st.success("You are logged in as a teacher.")
            else:
                st.error("User not found. Please register.")

    elif choice == "Admin":
        st.subheader("📊 Admin Dashboard")
        st.write("### Registered Users")
        st.dataframe(users)

        matches_df = load_matches()
        st.write("### Matches")
        st.dataframe(matches_df)

        _, unmatched_learners = find_matches(users)
        unmatched_df = get_unmatched_learners(unmatched_learners)
        st.write("### Unmatched Learners")
        st.dataframe(unmatched_df)

if __name__ == "__main__":
    main()
