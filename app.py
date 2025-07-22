# main.py 
import streamlit as st
import pandas as pd
import os
from admin_users import admin_dashboard
from match_engine import find_matches
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import pytorch_cos_sim

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

# --- Streamlit Setup ---
st.set_page_config(page_title="GetSkilled Admin", layout="centered")
st.title("💡 GetSkilled Platform")

# --- Cached Resources ---
@st.cache_resource(show_spinner=False)
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

@st.cache_data(show_spinner=False)
def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame()

@st.cache_data(show_spinner=False)
def embed_texts(texts):
    model = load_model()
    return model.encode(texts, convert_to_tensor=True)

# --- Load Model & Data ---
model = load_model()
users = load_data(USER_FILE)
ratings = load_data(RATINGS_FILE)
matches = load_data(MATCH_FILE)

# --- Generate AI Study Targets ---
if not users.empty:
    get_study_targets(users)

# --- Menu ---
menu = st.sidebar.selectbox("Menu", ["Home", "Admin"])

if menu == "Admin":
    admin_dashboard()

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
            user_row = users[users["Name"].str.lower() == name_input]

            if not user_row.empty:
                st.success(f"Welcome back, {user_row.iloc[0]['Name'].title()}!")
                role = user_row.iloc[0]["Role"]
            else:
                st.warning("User not found. Please register below.")

            # --- MATCH DISPLAY ---
            if not matches.empty:
                name_matches = matches[
                    (matches["Learner"].str.lower() == name_input) | 
                    (matches["Teacher"].str.lower() == name_input)
                ]

                if not name_matches.empty:
                    st.markdown("### 🤝 Your Match")
                    displayed = set()
                    for _, row in name_matches.iterrows():
                        if row.to_json() in displayed: continue
                        role = "Learner" if row["Learner"].lower() == name_input else "Teacher"
                        partner = row["Teacher"] if role == "Learner" else row["Learner"]
                        skill = row.get("Skill", "Not Specified")
                        score = row.get("Score", "-")
                        st.info(f"**You are a {role} matched with {partner.title()} for skill: {skill} (Match Score: {score})**")
                        displayed.add(row.to_json())
                else:
                    st.warning("You are not yet matched. Please check back later.")
            else:
                st.info("Matches not available yet.")

            # --- STUDY PROGRESS ---
            st.markdown("### 📈 Your Study Progress")
            weekly_summary = get_weekly_summary(name_input)
            if weekly_summary:
                for day, status in weekly_summary.items():
                    st.write(f"{day}: {status}")
            else:
                st.info("No study activity recorded yet.")

            # --- RATINGS ---
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

    elif auth_option == "Register":
        with st.form("user_register_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                age_range = st.selectbox("Age Range", ["18 - 24", "25 - 34", "35 - 44", "55+"])
            with col2:
                skill_level = st.selectbox("Skill Level", ["Beginner", "Intermediate", "Advanced"])
                number_of_days = st.number_input("Days per week", min_value=1, max_value=7, value=5)
                role = st.selectbox("Role", ["Learner", "Teacher"])
                timestamp = pd.Timestamp.now()

            if role == "Teacher":
                can_teach = st.multiselect("What can you teach?", ["Python for Data Analysis", "SQL", "Excel", "Communication", "Data analysis"])
                wants_to_learn = []
            else:
                wants_to_learn = st.multiselect("What do you want to learn?", ["Python for Data Analysis", "SQL", "Excel", "Communication", "Data analysis"])
                can_teach = []

            submit_register = st.form_submit_button("Register")

            if submit_register:
                new_user = pd.DataFrame([{
                    "Name": name, "Email": email, "Gender": gender, "AgeRange": age_range,
                    "SkillLevel": skill_level, "Role": role, "Timestamp": timestamp,
                    "CanTeach": ", ".join(can_teach), "WantsToLearn": ", ".join(wants_to_learn)
                }])
                updated_users = pd.concat([users, new_user], ignore_index=True)
                os.makedirs(os.path.dirname(USER_FILE), exist_ok=True)
                if os.path.exists(USER_FILE):
                    updated_users = pd.concat([pd.read_csv(USER_FILE), updated_users], ignore_index=True)
                updated_users.to_csv(USER_FILE, index=False)
                st.success("✅ Registration successful. Please reload the page to continue.")
                st.stop()
