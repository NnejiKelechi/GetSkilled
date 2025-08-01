import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from match_engine import find_matches, display_learner_match, get_unmatched_learners
from habit_tracker import load_users, get_study_targets, simulate_checkins, log_study_activity

# --- Constants ---
DATA_DIR = "data"
USER_FILE = os.path.join(DATA_DIR, "users.csv")
MATCH_FILE = os.path.join(DATA_DIR, "matches.csv")
UNMATCHED_FILE = os.path.join(DATA_DIR, "unmatched.csv")
RATINGS_FILE = os.path.join(DATA_DIR, "ratings.csv")

st.set_page_config(page_title="GetSkilled Admin", layout="centered")
st.title("💡 GetSkilled Platform")
st.markdown(
    "<div style='text-align:center; font-style:italic; font-weight:bold; font-size:20px;'>Connect. Learn. Grow. 🚀</div>",
    unsafe_allow_html=True
)

@st.cache_data(show_spinner=False)
def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame()

@st.cache_data(show_spinner=False)
def load_ratings():
    if os.path.exists(RATINGS_FILE):
        return pd.read_csv(RATINGS_FILE)
    return pd.DataFrame(columns=["user", "partner", "skill", "rating"])

def get_users_hash(users_df):
    return hash(pd.util.hash_pandas_object(users_df, index=True).sum())

# Ensure data dir and unmatched file
os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(UNMATCHED_FILE):
    pd.DataFrame(columns=["Name", "WantsToLearn", "Reason"]).to_csv(UNMATCHED_FILE, index=False)

# Load data
users_df = load_users()
ratings_df = load_data(RATINGS_FILE)

if os.path.exists(MATCH_FILE):
    previous_hash = get_users_hash(pd.read_csv(USER_FILE))
else:
    previous_hash = None

current_hash = get_users_hash(users_df)

if previous_hash != current_hash:
    matched_df, unmatched_names = find_matches(users_df, threshold=0.6)
    unmatched_df = get_unmatched_learners(unmatched_names)
    matched_df.to_csv(MATCH_FILE, index=False)
    unmatched_df.to_csv(UNMATCHED_FILE, index=False)
else:
    matched_df = load_data(MATCH_FILE)
    unmatched_df = load_data(UNMATCHED_FILE)

# --- Sidebar Navigation ---
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

if menu == "Admin":
    st.markdown("---")
    st.subheader("🔐 Admin Dashboard")

    admin_username = st.text_input("Admin Username")
    admin_password = st.text_input("Admin Password", type="password")
    login_button = st.button("Login")

    if login_button:
        if admin_username == "admin" and admin_password == "admin123":
            st.success("✅ Login successful! Welcome, Admin.")

            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📋 User Data", "⭐ Ratings", "🔗 Matches",
                "🧠 AI Match Engine", "📈 Match Summary"
            ])

            with tab1:
                st.subheader("👥 Registered Users")
                st.dataframe(users_df)

            with tab2:
                st.subheader("⭐ User Ratings")
                st.dataframe(ratings_df)

            with tab3:
                st.subheader("🔗 Matches")
                st.dataframe(matched_df)

                st.markdown("### ❌ Unmatched Learners")
                st.dataframe(unmatched_df)

            with tab4:
                st.subheader("🧠 AI Match Engine (Learner View)")
                name_input = st.text_input("🔍 Enter your name to see your match", "").strip().lower()
                if name_input:
                    learner_match = display_learner_match(name_input, matched_df)
                    if not learner_match.empty:
                        st.success("Match found!")
                        st.dataframe(learner_match)
                    else:
                        st.warning("No match found for this name.")

            with tab5:
                st.subheader("📊 Match Summary by Skill")
                if not matched_df.empty:
                    skill_counts = matched_df["Skill"].value_counts().reset_index()
                    skill_counts.columns = ["Skill", "Matches"]
                    st.bar_chart(skill_counts.set_index("Skill"))
                    st.metric("Learners", len(matched_df))
                    st.metric("Unmatched", len(unmatched_df))
                else:
                    st.info("ℹ️ No match data available.")

elif menu == "Home":
    st.markdown("---")
    st.subheader("👋 Welcome to SkillSpark!")
    st.markdown("### 📝 Register or Log In")

    auth_option = st.radio("Choose an option", ["Login", "Register"])

    if auth_option == "Login":
        with st.form("user_login_form"):
            name_input = st.text_input("Enter your Full Name").strip().lower()
            submit_login = st.form_submit_button("Login")

        if submit_login and name_input:
            user_row = users_df[users_df["Name"].str.strip().str.lower() == name_input]

            if not user_row.empty:
                user_actual_name = user_row.iloc[0]['Name']
                st.success(f"✅ Login successful! Welcome back, {user_actual_name.title()}!")

                st.balloons()
                st.markdown("### 🎉 You're In!")
                st.success("Enjoy personalized study insights and your matched partner below.")

                if not matched_df.empty:
                    learner_match = display_learner_match(name_input, matched_df)
                    if not learner_match.empty:
                        st.markdown("### 🤝 Your Match")
                        st.dataframe(learner_match)
                    else:
                        st.warning("⏳ You are not matched yet. Please check back soon!")

                st.markdown("### 📈 Your Study Progress")
                weekly_summary = get_study_targets(users_df)
                if weekly_summary:
                    st.write(weekly_summary)
                else:
                    st.info("No study activity recorded yet.")
            else:
                st.warning("User not found. Please register below.")

    elif auth_option == "Register":
        st.markdown("### 🧾 Register New User")
        role = st.selectbox("Registering as:", ["Learner", "Teacher"])

        with st.form("user_register_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name")
                email = st.text_input("Email")
            with col2:
                skill = st.text_input("Skill")
                reason = st.text_area("Why do you want to join?")

            submit_register = st.form_submit_button("Register")

        if submit_register:
            if email.lower() in users_df["Email"].str.lower().values:
                st.warning("⚠️ This email is already registered. Please log in instead.")
            else:
                new_user = pd.DataFrame([{
                    "Name": name,
                    "Email": email,
                    "Role": role,
                    "CanTeach": skill if role == "Teacher" else "",
                    "WantsToLearn": skill if role == "Learner" else "",
                    "Reason": reason,
                    "Date": datetime.now()
                }])

                users_df = pd.concat([users_df, new_user], ignore_index=True)
                users_df.to_csv(USER_FILE, index=False)

                matched_df, unmatched_names = find_matches(users_df, threshold=0.6)
                unmatched_df = get_unmatched_learners(unmatched_names)
                matched_df.to_csv(MATCH_FILE, index=False)
                unmatched_df.to_csv(UNMATCHED_FILE, index=False)

                st.success("✅ Registration complete! You've been matched (or queued).")
                st.rerun()
