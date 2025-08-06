# app.py

import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from match_engine import find_matches, display_learner_match, get_unmatched_learners
from habit_tracker import load_users, get_study_targets, simulate_checkins, log_study_activity
try:
    from rating import load_ratings, save_rating, add_rating, get_average_ratings, generate_study_targets
except Exception as e:
    import traceback
    print("Import Error in rating.py:", traceback.format_exc())

# --- Constants ---
DATA_DIR = "data"
USER_FILE = os.path.join(DATA_DIR, "users.csv")
MATCH_FILE = os.path.join(DATA_DIR, "matches.csv")
UNMATCHED_FILE = os.path.join(DATA_DIR, "unmatched.csv")
RATINGS_FILE = os.path.join(DATA_DIR, "ratings.csv")

st.set_page_config(page_title="GetSkilled", layout="centered")
st.title("💡 GetSkilled Platform")
st.markdown(
    "<div style='text-align:center; font-style:italic; font-weight:bold; font-size:20px;'>Connect. Learn. Grow. 🚀</div>",
    unsafe_allow_html=True
)

@st.cache_data(show_spinner=True)
def load_data(file_path):
    return pd.read_csv(file_path) if os.path.exists(file_path) else pd.DataFrame()

def get_users_hash(users_df):
    return hash(pd.util.hash_pandas_object(users_df, index=True).sum())

os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(UNMATCHED_FILE):
    pd.DataFrame(columns=["Name", "WantsToLearn", "Reason"]).to_csv(UNMATCHED_FILE, index=False)

# Load initial data
users_df = load_users()
targets = get_study_targets(users_df)
ratings_df = load_ratings()
study_targets = generate_study_targets(users_df)

# Match Logic
unmatched_users = users_df[users_df["IsMatched"] == False] if "IsMatched" in users_df.columns else users_df

if not unmatched_users.empty:
    matched_df, unmatched_names = find_matches(users_df, threshold=0.6)
    users_df.loc[users_df["Name"].isin(matched_df["Learner"]), "IsMatched"] = True
    users_df.to_csv(USER_FILE, index=False)

    unmatched_df = get_unmatched_learners(unmatched_names)
    matched_df.to_csv(MATCH_FILE, index=False)
    unmatched_df.to_csv(UNMATCHED_FILE, index=False)
else:
    matched_df = load_data(MATCH_FILE)
    unmatched_df = load_data(UNMATCHED_FILE)

# --- Sidebar ---
menu = st.sidebar.selectbox("Menu", ["Home", "Admin"])
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style='margin-top:30px; font-weight:bold;'>
        <i>GetSkilled is an AI-powered platform that connects learners with expert teachers in data analysis. 
        Track progress, get matched smartly, and grow your skills with ease.</i>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Admin Section ---
if menu == "Admin":
    st.subheader("🔐 Admin Dashboard")
    admin_username = st.text_input("Admin Username")
    admin_password = st.text_input("Admin Password", type="password")
    login_button = st.button("Login")

    if login_button:
        if admin_username == "admin" and admin_password == "admin123":
            st.success("✅ Login successful! Welcome, Admin.")
            tab1, tab2, tab3, tab4 = st.tabs([
                "📋 User Data", "⭐ Ratings", "🔗 Matches", "📈 Match Summary"
            ])

            with tab1:
                st.subheader("👥 Registered Users")
                st.dataframe(users_df)

            with tab2:
                st.subheader("⭐ User Ratings")
                st.dataframe(ratings_df)
                st.subheader("📊 Average Ratings")
                st.dataframe(get_average_ratings())

            with tab3:
                st.subheader("🔗 Matches")
                st.dataframe(matched_df)
                st.subheader("❌ Unmatched Learners")
                st.dataframe(unmatched_df)

            with tab4:
                st.subheader("📈 Match Summary by Skill")
                if not matched_df.empty and "Skill" in matched_df.columns:
                    skill_counts = matched_df["Skill"].value_counts().reset_index()
                    skill_counts.columns = ["Skill", "Matches"]
                    st.bar_chart(skill_counts.set_index("Skill"))
                    st.metric("Learners", len(matched_df))
                    st.metric("Unmatched", len(unmatched_df))
                else:
                    st.info("ℹ️ No match data available.")
        else:
            st.error("❌ Invalid admin credentials.")

# --- User Interface ---
elif menu == "Home":
    st.markdown("### 📝 Register or Log In")
    auth_option = st.radio("Choose an option", ["Login", "Register"])

    if auth_option == "Login":
        with st.form("user_login_form"):
            name_input = st.text_input("Enter your Full Name").strip().lower()
            submit_login = st.form_submit_button("Login")

        if submit_login:
            user_row = users_df[users_df["Name"].str.strip().str.lower() == name_input]
            if not user_row.empty:
                user_actual_name = user_row.iloc[0]["Name"]
                st.success(f"✅ Welcome back, {user_actual_name.title()}!")
                st.balloons()

                tab1, tab2, tab3 = st.tabs(["🤖 AI Match Engine", "📈 Study Progress", "⭐ Rate Your Match"])

                with tab1:
                    st.subheader("Your AI Match Result")
                    matched_df = load_data(MATCH_FILE)
                    unmatched_df = load_data(UNMATCHED_FILE)
                    if not matched_df.empty and "Learner" in matched_df.columns:
                        matched_row = matched_df[matched_df["Learner"].str.lower() == name_input]
                        if not matched_row.empty:
                            match = matched_row.iloc[0]
                            st.success(f"🎉 You’ve been matched with **{match['Teacher']}** to learn **{match['Skill']}**")
                            st.markdown(f"🧠 *{match['Explanation']}*")
                            st.info(f"Confidence Score: **{match['AI_Confidence (%)']}%**")
                        else:
                            st.info("😕 You are currently unmatched. Please check back later.")
                    else:
                        st.warning("👋 You haven’t been matched yet. Please check back later as new teachers or learners join!")

                with tab2:
                    st.subheader("📊 Your Study Progress")
                    targets = study_targets[study_targets["Name"].str.lower() == name_input]
                    if not targets.empty:
                        st.write("🎯 Weekly target (minutes):", targets.iloc[0]["TargetMinutes"])
                        st.write("📅 Simulated check-ins")
                        checkins = simulate_checkins(targets.iloc[0]["TargetMinutes"], users_df)
                        st.line_chart(checkins)
                    else:
                        st.info("No study target found.")

                with tab3:
                    st.subheader("⭐ Rate Your Match")
                    rating = st.slider("Rate your match", 1, 5)
                    if st.button("Submit Rating"):
                        teacher_name = matched_row.iloc[0]["Teacher"] if not matched_row.empty else "N/A"
                        add_rating(user_actual_name, teacher_name, rating)
                        st.success("✅ Rating submitted successfully!")
            else:
                st.error("❌ User not found. Please register.")

    elif auth_option == "Register":
        st.subheader("📒 Register New User")
        role = st.selectbox("Registering as:", ["Learner", "Teacher"])

        with st.form("user_register_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                age_range = st.selectbox("Age Range", ["18 - 24", "25 - 34", "35 - 44", "55+"])
            with col2:
                skill_label = "What can you teach?" if role == "Teacher" else "What do you want to learn?"
                skill = st.selectbox(skill_label, ["Excel", "SQL", "Python", "Power BI", "R", "Tableau", "Data Science"])
                skill_level = st.selectbox("Skill Level", ["Beginner", "Intermediate", "Advanced"])
                study_days = st.slider("Study Days per Week", 1, 7, 3)
                timestamp = pd.Timestamp.now()

            submit_register = st.form_submit_button("Register")

        if submit_register:
            if email.lower() in users_df["Email"].str.lower().values:
                st.warning("⚠️ This email is already registered. Try logging in.")
            else:
                new_user = pd.DataFrame([{
                    "Name": name,
                    "Email": email,
                    "Role": role,
                    "Gender": gender,
                    "AgeRange": age_range,
                    "SkillLevel": skill_level,
                    "StudyDays": study_days,
                    "Timestamp": timestamp,
                    "CanTeach": skill if role == "Teacher" else "",
                    "WantsToLearn": skill if role == "Learner" else "",
                    "Reason": "",
                    "Date": datetime.now(),
                    "IsMatched": False
                }])

                users_df = pd.concat([users_df, new_user], ignore_index=True)
                users_df.to_csv(USER_FILE, index=False)

                unmatched_users = users_df[users_df["IsMatched"] == False] if "IsMatched" in users_df.columns else users_df

                if not unmatched_users.empty:
                    matched_df, unmatched_names = find_matches(users_df, threshold=0.6)

                    # Mark matched learners as IsMatched = True
                    users_df.loc[users_df["Name"].isin(matched_df["Learner"]), "IsMatched"] = True
                    users_df.to_csv(USER_FILE, index=False)

                    unmatched_df = get_unmatched_learners(unmatched_names)
                    matched_df.to_csv(MATCH_FILE, index=False)
                    unmatched_df.to_csv(UNMATCHED_FILE, index=False)


                st.success("✅ Registration complete! You've been matched (or queued). Please login to see details.")
                st.balloons()
                time.sleep(5.5)
                st.rerun()






