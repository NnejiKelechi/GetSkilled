import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from match_engine import find_matches, display_learner_match, get_unmatched_learners
from habit_tracker import load_users, get_study_targets, simulate_checkins, log_study_activity
from rating import load_ratings, save_rating, generate_study_targets

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

def get_users_hash(users_df):
    return hash(pd.util.hash_pandas_object(users_df, index=True).sum())

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(UNMATCHED_FILE):
    pd.DataFrame(columns=["Name", "WantsToLearn", "Reason"]).to_csv(UNMATCHED_FILE, index=False)

# Load Data
users_df = load_users(USER_FILE)
ratings_df = load_data(RATINGS_FILE)

# Match Data Loading Logic
if not users_df.empty:
    current_hash = get_users_hash(users_df)
    previous_hash = get_users_hash(pd.read_csv(USER_FILE)) if os.path.exists(MATCH_FILE) else None

    if previous_hash != current_hash:
        if "Role" in users_df.columns and (
            (users_df["Role"] == "Learner").any() and (users_df["Role"] == "Teacher").any()
        ):
            matched_df, unmatched_names = find_matches(users_df, threshold=0.6)
            unmatched_df = get_unmatched_learners(unmatched_names)
            matched_df.to_csv(MATCH_FILE, index=False)
            unmatched_df.to_csv(UNMATCHED_FILE, index=False)
        else:
            matched_df = pd.DataFrame()
            unmatched_df = users_df[users_df["Role"] == "Learner"]
    else:
        matched_df = load_data(MATCH_FILE)
        unmatched_df = load_data(UNMATCHED_FILE)
else:
    matched_df = pd.DataFrame()
    unmatched_df = pd.DataFrame()

# Load targets
study_targets = generate_study_targets(users_df)

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

# --- Admin Panel ---
if menu == "Admin":
    st.markdown("---")
    st.subheader("🔐 Admin Dashboard")

    admin_username = st.text_input("Admin Username")
    admin_password = st.text_input("Admin Password", type="password")
    login_button = st.button("Login")

    if login_button:
        if admin_username == "admin" and admin_password == "admin123":
            st.success("✅ Login successful! Welcome, Admin.")
            tab1, tab2, tab3, tab4 = st.tabs([
                "📋 User Data", "⭐ Ratings", "🔗 Matches",
                "📈 Match Summary"
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
                st.subheader("📈 Match Summary by Skill")
                if not matched_df.empty and "Skill" in matched_df.columns:
                    skill_counts = matched_df["Skill"].value_counts().reset_index()
                    skill_counts.columns = ["Skill", "Matches"]
                    st.bar_chart(skill_counts.set_index("Skill"))
                    st.metric("Learners", len(matched_df))
                    st.metric("Unmatched", len(unmatched_df))
                else:
                    st.info("ℹ️ No match data available.")

# --- Home / User Interaction ---
elif menu == "Home":
    st.markdown("---")
    st.markdown("#### 📝 Register or Log In")

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

                tab1, tab2, tab3 = st.tabs(["AI Match Engine", "📈 Study Progress", "⭐ Rate Your Match"])

                with tab1:
                    st.subheader("🤖 AI Match Result")
                    if matched_df is not None and isinstance(matched_df, pd.DataFrame) and not matched_df.empty:
                        if "Learner" in matched_df.columns:
                            matched_row = matched_df[matched_df["Learner"].str.lower() == name_input]
                            if not matched_row.empty:
                                match = matched_row.iloc[0]
                                st.success(f"🎉 You’ve been matched with **{match['Teacher']}** to learn **{match['Skill']}**")
                                st.markdown(f"🧠 *{match['Explanation']}*")
                                st.info(f"Confidence Score: **{match['AI_Confidence (%)']}%**")
                            else:
                                st.info(f"👋 Welcome, {user_actual_name.title()}. You haven’t been matched yet. Please check back later as new teachers or learners join!")
                        else:
                            st.warning("⚠️ Match data is missing the required 'Learner' column.")
                    else:
                        st.warning("⚠️ Match data is not available yet. Please try again later.")

                with tab2:
                    st.subheader("📊 Your Study Progress")
                    targets = study_targets[study_targets["Name"].str.lower() == name_input]
                    if not targets.empty:
                        st.write("🎯 Your weekly target (minutes):", targets.iloc[0]["TargetMinutes"])
                        st.write("📅 Simulating check-ins...")
                        checkins = simulate_checkins(targets.iloc[0]["TargetMinutes"])
                        st.line_chart(checkins)
                    else:
                        st.info("No study target found.")

                with tab3:
                    st.subheader("⭐ Rate Your Match")
                    rating = st.slider("How would you rate your current match?", 1, 5)
                    if st.button("Submit Rating"):
                        new_rating = pd.DataFrame([{"Name": user_actual_name, "Rating": rating}])
                        ratings_df = pd.concat([ratings_df, new_rating], ignore_index=True)
                        save_rating(ratings_df)
                        st.success("✅ Rating submitted successfully!")
            else:
                st.sidebar.error("User not found. Please check your name or register.")

    elif auth_option == "Register":
        st.markdown("### 📒 Register New User")
        role = st.selectbox("Registering as:", ["Learner", "Teacher"])

        with st.form("user_register_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                age_range = st.selectbox("Age Range", ["18 - 24", "25 - 34", "35 - 44", "55+"])
            with col2:
                skill_level = st.selectbox("Skill Level", ["Beginner", "Intermediate", "Advanced"])
                study_days = st.slider("How many days per week can you study?", 1, 7, 3)
                timestamp = pd.Timestamp.now()

            st.markdown("---")
            skill_label = "What can you teach?" if role == "Teacher" else "What do you want to learn?"
            skill = st.selectbox(skill_label, ["Excel", "SQL", "Python", "Data analysis", "Data Science"])

            submit_register = st.form_submit_button("Register")

        if submit_register:
            if email.lower() in users_df["Email"].str.lower().values:
                st.warning("⚠️ This email is already registered. Please log in instead.")
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
                    "Date": datetime.now()
                }])

                users_df = pd.concat([users_df, new_user], ignore_index=True)
                users_df.to_csv(USER_FILE, index=False)
                users_df = pd.read_csv(USER_FILE)

                if (users_df["Role"] == "Learner").any() and (users_df["Role"] == "Teacher").any():
                    matched_df, unmatched_names = find_matches(users_df, threshold=0.6)
                    unmatched_df = get_unmatched_learners(unmatched_names)
                    matched_df.to_csv(MATCH_FILE, index=False)
                    unmatched_df.to_csv(UNMATCHED_FILE, index=False)

                st.success("✅ Registration complete! You've been matched (or queued). Please login to see details.")
                st.balloons()
                time.sleep(3.5)
                st.rerun()
