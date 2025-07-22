# main.py 
import streamlit as st
import pandas as pd
import os
import time
from admin_users import admin_dashboard
from match_engine import find_matches
from sentence_transformers import SentenceTransformer

from habit_tracker import (
    load_users, 
    get_study_targets, 
    log_study_activity, 
    simulate_checkins, 
    get_weekly_summary, 
    get_defaulters
)

# --- Constants ---
USER_FILE = "data/users.csv"
RATINGS_FILE = "data/ratings.csv"
MATCH_FILE = "data/matches.csv"
PAIRED_FILE = "data/paired_users.csv"
UNPAIRED_FILE = "data/unpaired_users.csv"

# --- Streamlit Setup ---
st.set_page_config(page_title="GetSkilled Admin", layout="centered")
st.title("💡 GetSkilled Platform")
st.markdown(
    "<div style='text-align:center; font-style:italic; font-weight:bold; font-size:20px;'>Connect. Learn. Grow. 🚀</div>",
    unsafe_allow_html=True
)


# --- Cached Resources ---
@st.cache_resource(show_spinner=False)
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

@st.cache_data(show_spinner=False)
def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame()

# --- Load Model & Data ---
model = load_model()
users = load_data(USER_FILE)
ratings = load_data(RATINGS_FILE)
matches = load_data(MATCH_FILE)
paired_df = load_data(PAIRED_FILE)
unpaired_df = load_data(UNPAIRED_FILE)

# --- Generate AI Study Targets ---
if not users.empty:
    get_study_targets(users)

# --- Menu ---
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
        if admin_username == "admin" and admin_password == "admin123":  # Replace with real validation
            st.success("✅ Login successful! Welcome, Admin.")

            # ✅ TABBED DASHBOARD START
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📋 User Data", "⭐ Ratings", "🔗 Matches",
                "🧠 AI Match Engine", "📈 Match Summary"
            ])

            with tab1:
                st.subheader("👥 Registered Users")
                st.dataframe(users)

            with tab2:
                st.subheader("⭐ User Ratings")
                st.dataframe(ratings)

            with tab3:
                st.subheader("🔗 Matches")
                st.dataframe(matches)

            with tab4:
                st.subheader("🧠 AI Match Engine")
                threshold = st.slider("Match Threshold", 0.5, 0.9, 0.6)
                run_match = st.button("Run Matching")

                if run_match:
                    with st.spinner("Running AI matching engine..."):
                        matched_df, unmatched_df = find_matches(users, threshold=threshold, show_progress=True)
                        matched_df.to_csv(MATCH_FILE, index=False)
                        st.success("✅ Matching complete!")
                        st.dataframe(matched_df)

                        with tab5:
                            st.subheader("📈 Match Summary")
                
                # Skill match summary
                if not matches.empty:
                    st.markdown("#### 🧠 Skill-wise Match Count")
                    summary = matches.groupby("Skill").size().reset_index(name="Match Count")
                    st.dataframe(summary)
                else:
                    st.info("ℹ️ No match data available yet.")

                # Show all users
                st.markdown("#### 👥 All Registered Users")
                if not users.empty:
                    st.dataframe(users)
                else:
                    st.warning("No user data available.")

                # Show paired users
                st.markdown("#### ✅ Paired Users")
                if not paired_df.empty:
                    st.dataframe(paired_df)
                else:
                    st.info("No paired users found.")

                # Show unpaired users
                st.markdown("#### ❌ Unpaired Users")
                if not unpaired_df.empty:
                    st.dataframe(unpaired_df)
                else:
                    st.info("No unpaired users found.")

elif menu == "Home":
    st.markdown("---")
    st.subheader("👋 Welcome to GetSkilled!")
    st.markdown("### 📝 Register or Log In")

    auth_option = st.radio("Choose an option", ["Login", "Register"])

    if auth_option == "Login":
        with st.form("user_login_form"):
            name_input = st.text_input("Enter your Full Name").strip().lower()
            submit_login = st.form_submit_button("Login")

        if submit_login and name_input:
            user_row = users[users["Name"].str.strip().str.lower() == name_input]

            if not user_row.empty:
                user_actual_name = user_row.iloc[0]['Name']
                st.success(f"✅ Login successful! Welcome back, {user_actual_name.title()}!")

                with st.spinner("Loading your dashboard..."):
                    time.sleep(2)

                st.balloons()
                st.markdown("### 🎉 You're In!")
                st.success("Enjoy personalized study insights and your matched partner below.")
                role = user_row.iloc[0]["Role"]

                if not matches.empty:
                    name_matches = matches[
                        (matches["Learner"].str.strip().str.lower() == name_input) |
                        (matches["Teacher"].str.strip().str.lower() == name_input)
                    ]

                    if not name_matches.empty:
                        st.markdown("### 🤝 Your Match")
                        row = name_matches.iloc[0]
                        partner = row["Teacher"] if row["Learner"].strip().lower() == name_input else row["Learner"]
                        skill = row.get("Skill", "Not Specified")
                        st.success(f"You have been paired with {partner.title()} to learn {skill}.")
                    else:
                        st.warning("⏳ You are not matched yet. Please check back soon!")
                else:
                    st.info("Matches not available yet.")

                st.markdown("### 📈 Your Study Progress")
                weekly_summary = get_weekly_summary(name_input)
                if weekly_summary:
                    for day, status in weekly_summary.items():
                        st.write(f"{day}: {status}")
                else:
                    st.info("No study activity recorded yet.")

                st.markdown("### ⭐ Rate Your Partner")
                matched = matches[
                    (matches["Learner"].str.lower() == name_input) |
                    (matches["Teacher"].str.lower() == name_input)
                ]

                if not matched.empty:
                    for _, row in matched.iterrows():
                        partner = row["Teacher"] if row["Learner"].lower() == name_input else row["Learner"]
                        st.write(f"Rate your partner: {partner.title()}")

                        with st.form(f"rating_form_{partner}"):
                            score = st.slider("How would you rate them (1-5)?", 1, 5)
                            comment = st.text_area("Comments")
                            rate_submit = st.form_submit_button("Submit Rating")

                            if rate_submit:
                                new_rating = pd.DataFrame([{
                                    "Rater": name_input,
                                    "Rated": partner.lower(),
                                    "Score": score,
                                    "Comment": comment,
                                    "Timestamp": pd.Timestamp.now()
                                }])
                                updated_ratings = pd.concat([ratings, new_rating], ignore_index=True)
                                updated_ratings.to_csv(RATINGS_FILE, index=False)
                                st.success("✅ Rating submitted!")
                else:
                    st.info("You have no partner to rate yet.")
            else:
                st.warning("User not found. Please register below.")

elif auth_option == "Register":
    st.markdown("### 🧾 Register New User")
    role = st.selectbox("Registering as:", ["Learner", "Teacher"])

    # Load users file safely
    try:
        users = pd.read_csv(USER_FILE)
    except FileNotFoundError:
        users = pd.DataFrame(columns=[
            "name", "email", "gender", "agerange", "skilllevel",
            "role", "timestamp", "canteach", "wantstolearn", "studydays"
        ])

    # Normalize column names
    users.columns = users.columns.astype(str).str.strip().str.lower()

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

        if role == "Teacher":
            can_teach = st.selectbox("What can you teach?", [
                "Python for Data Analysis", "SQL", "Excel", "Communication", "Data analysis"
            ])
            wants_to_learn = ""
        else:
            wants_to_learn = st.selectbox("What do you want to learn?", [
                "Python for Data Analysis", "SQL", "Excel", "Communication", "Data analysis"
            ])
            can_teach = ""

        submit_register = st.form_submit_button("Register")

    # Form logic after submission
    if submit_register:
        if "email" in users.columns and email.lower() in users["email"].str.lower().values:
            st.warning("⚠️ This email is already registered. Please log in instead.")
        else:
            new_user = pd.DataFrame([{
                "name": name,
                "email": email,
                "gender": gender,
                "agerange": age_range,
                "skilllevel": skill_level,
                "role": role,
                "timestamp": timestamp,
                "canteach": can_teach,
                "wantstolearn": wants_to_learn,
                "studydays": study_days
            }])

            updated_users = pd.concat([users, new_user], ignore_index=True)
            updated_users.to_csv(USER_FILE, index=False)

            with st.spinner("🔄 Matching you with the best partner using AI engine..."):
                matched_df, unmatched_df = find_matches(updated_users, threshold=0.6, show_progress=True)
                time.sleep(3)

            if not matched_df.empty:
                st.success("✅ Matching Complete! Your best match has been found.")
            else:
                st.warning("⚠️ No match found. Please check back later.")

            st.info("Registration complete! Please go to the Login tab to access your dashboard.")
            st.stop()

