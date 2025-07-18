import streamlit as st
import pandas as pd
import os
from PIL import Image
import altair as alt
from datetime import datetime
from match_engine import find_matches
from habit_tracker import load_users, get_study_targets, simulate_checkins, log_study_activity
import random
from faker import Faker
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Constants and Setup ---
st.set_page_config(page_title="GetSkilled", layout="centered")
DATA_DIR = "data"
USER_FILE = os.path.join(DATA_DIR, "users.csv")
MATCH_FILE = os.path.join(DATA_DIR, "matches.csv")
LOG_FILE = os.path.join(DATA_DIR, "study_log.csv")
RATINGS_FILE = os.path.join(DATA_DIR, "ratings.csv")

# --- Helper Functions ---
def send_email(recipient_email, subject, body):
    sender_email = "youremail@example.com"
    sender_password = "yourpassword"
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        return False

# --- Load Users Safely with Schema Upgrade ---
def safe_load_users():
    base_columns = ["Name", "Email", "Gender", "SkillLevel", "Role", "CanTeach", "WantsToLearn", "Timestamp"]
    if os.path.exists(USER_FILE):
        users = load_users(USER_FILE)
        for col in base_columns:
            if col not in users.columns:
                users[col] = ""
        users = users[base_columns]  # Ensure column order and presence
        users['Name'] = users['Name'].astype(str)
        users['Email'] = users['Email'].astype(str)
        return users
    else:
        return pd.DataFrame(columns=base_columns)

# --- Skill Filter ---
def get_available_skills(users_df):
    return sorted(set(users_df['CanTeach'].dropna().unique()).union(users_df['WantsToLearn'].dropna().unique()))

# --- Save Rating ---
def save_rating(rater, rated, role, rating):
    new_rating = pd.DataFrame({"Rater": [rater], "Rated": [rated], "Role": [role], "Rating": [rating]})
    if os.path.exists(RATINGS_FILE):
        existing = pd.read_csv(RATINGS_FILE)
        ratings_df = pd.concat([existing, new_rating], ignore_index=True)
    else:
        ratings_df = new_rating
    ratings_df.to_csv(RATINGS_FILE, index=False)

# --- Auto Match Generation ---
def auto_generate_matches():
    users = safe_load_users()
    matches = find_matches(users)
    match_df = pd.DataFrame(matches)

    if not match_df.empty:
        match_df.to_csv(MATCH_FILE, index=False)
        matched_names = set(match_df["Learner"]).union(set(match_df["Teacher"]))
        users["Match Status"] = users["Name"].apply(lambda x: "Paired" if x in matched_names else "Unpaired")
        users.to_csv(USER_FILE, index=False)

        #st.success("✅ Matches generated successfully!")


# --- Streamlit UI ---
menu = st.sidebar.selectbox("Choose an option:", ["Submit Info", "View Match", "Log Study", "Insights", "Admin"])
st.title("🔗 GetSkilled - Connect Learners & Teachers")
st.sidebar.markdown("""
---
#### 👋 Welcome to **GetSkilled**  
Connect with learners and teachers.  
Submit your info, match up, and start learning!
""")

# --- Sidebar ---
#with st.sidebar:
  #  st.image("data/logo.png", width=150)
  #  st.markdown("""
  #  Welcome to **GetSkilled**! This app connects learners and teachers based on skills they want to learn and teach. 
  #  Submit your details, match with a partner, and track your learning progress.
  #  """)

#  --- Submit Info Section ---
if menu == "Submit Info":
    st.subheader("📋 Register as a Teacher or Learner")
    st.markdown("""
    Fill out the form below to register as a teacher or learner.
    - **Learners**: Select a skill you want to learn.
    - **Teachers**: Select a skill you can teach.
    """)

    name = st.text_input("Your Full Name")
    email = st.text_input("Email Address")
    gender = st.selectbox("Gender", ["Male", "Female", "Prefer not to tell"])
    skill_level = st.selectbox("Skill Level", ["Beginner", "Intermediate", "Advanced"])
    role = st.selectbox("Registering as:", ["Learner", "Teacher"])

    skills = ["Python", "Excel", "SQL", "Power BI", "Communication", "Data Analysis"]

    if role == "Teacher":
        can_teach = st.selectbox("Which skill can you teach?", skills)
        wants_to_learn = ""
    else:
        wants_to_learn = st.selectbox("Which skill do you want to learn?", skills)
        can_teach = ""

    if st.button("Submit"):
        if not name or not email:
            st.error("Please enter your name and email.")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_user = pd.DataFrame([{
                "Name": name.strip(),
                "Email": email.strip(),
                "Gender": gender,
                "SkillLevel": skill_level,
                "Role": role,
                "CanTeach": can_teach,
                "WantsToLearn": wants_to_learn,
                "Timestamp": timestamp
            }])

            if os.path.exists(USER_FILE):
                existing = pd.read_csv(USER_FILE)
                updated = pd.concat([existing, new_user], ignore_index=True)
            else:
                updated = new_user

            updated.to_csv(USER_FILE, index=False)
            st.success(f"🎉 Successfully registered as a {role.lower()}!")

        # Auto generate matches after submission
            auto_generate_matches()

elif menu == "View Match":
    st.subheader("👥 Your Match Details")
    name = st.text_input("Enter your name to check match")
    if st.button("Check Match"):
        if os.path.exists(MATCH_FILE):
            matches = pd.read_csv(MATCH_FILE)
            matches = matches.astype(str)
            name_lower = name.strip().lower()
            found = False
            for _, row in matches.iterrows():
                if row['Learner'].strip().lower() == name_lower:
                    st.success(f"You are being matched with {row['Teacher']} to learn {row['Skill']}")
                    found = True
                elif row['Teacher'].strip().lower() == name_lower:
                    st.success(f"You are being matched with {row['Learner']} to teach {row['Skill']}")
                    found = True
            if not found:
                st.warning("No match found. You may still be in the queue.")
        else:
            st.warning("No match data found yet.")

# ---- Log Study Section -----
elif menu == "Log Study":
    st.subheader("📚 Log Your Study Activity")
    st.markdown("""
    Use this section to log your study hours and skills.
    - Select your name and the skill you are studying.
    - Log the number of hours you studied today.
    """)
    users = safe_load_users()
    user_names = users["Name"].tolist()
    selected_user = st.selectbox("Who is studying now?", user_names)
    selected_skill = st.selectbox("What are you studying?", get_available_skills(users))
    hours = st.slider("How many hours did you study today?", 0.5, 10.0, 1.0)
    log_button = st.button("Log Study")

    if log_button:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = pd.DataFrame({"Name": [selected_user], "Skill": [selected_skill], "Hours": [hours], "Timestamp": [timestamp]})
        if os.path.exists(LOG_FILE):
            existing_log = pd.read_csv(LOG_FILE)
            log_df = pd.concat([existing_log, log_entry], ignore_index=True)
        else:
            log_df = log_entry
        log_df.to_csv(LOG_FILE, index=False)
        st.success("✅ Study log recorded successfully!")

# ----  View Insights -----
elif menu == "Insights":
    st.subheader("📊 Insights and Analytics")
    st.markdown("""
    View insights on study hours and user activity.
    - Total study hours by each learner.
    - Visualize study patterns and trends.
    """)
    if os.path.exists(LOG_FILE):
        log_df = pd.read_csv(LOG_FILE)
        total_hours = log_df.groupby("Name")["Hours"].sum().reset_index().sort_values(by="Hours", ascending=False)
        chart = alt.Chart(total_hours).mark_bar().encode(
            x=alt.X("Hours", title="Total Hours Studied"),
            y=alt.Y("Name", sort='-x', title="Learner"),
            tooltip=["Name", "Hours"]
        ).properties(title="Total Study Hours by Learner", width=700)
        st.altair_chart(chart)
    else:
        st.info("No study log data available.")

#  --- Admin Section ---
elif menu == "Admin":
    st.subheader("🔐 Admin Panel")
    password = st.text_input("Enter admin password", type="password")
    if st.button("Login"):
        if password == "admin123":
            st.success("Access granted!")

            if st.button("Clean & Format User Data"):
                users = safe_load_users()
                users.to_csv(USER_FILE, index=False)
                st.success("✅ Data cleaned and formatted successfully.")

            if st.button("Generate 100 Dummy Users"):
                faker = Faker()
                skills = ["Python", "Excel", "SQL", "Power BI", "Communication", "Data Analysis"]
                dummy_users = []
                for _ in range(100):
                    name = faker.name()
                    email = faker.email()
                    gender = random.choice(["Male", "Female", "Prefer not to tell"])
                    skill_level = random.choice(["Beginner", "Intermediate", "Advanced"])
                    role = random.choice(["Teacher", "Learner"])
                    if role == "Teacher":
                        can_teach = random.choice(skills)
                        wants_to_learn = ""
                    else:
                        can_teach = ""
                        wants_to_learn = random.choice(skills)
                    dummy_users.append({
                        "Name": name,
                        "Email": email,
                        "Gender": gender,
                        "SkillLevel": skill_level,
                        "Role": role,
                        "CanTeach": can_teach,
                        "WantsToLearn": wants_to_learn,
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                dummy_df = pd.DataFrame(dummy_users)
                dummy_df.to_csv(USER_FILE, index=False)
                st.success("✅ 100 dummy users generated!")

            # Ratings View
            if os.path.exists(RATINGS_FILE):
                st.markdown("### 📊 Submitted Ratings")
                ratings_df = pd.read_csv(RATINGS_FILE)
                st.dataframe(ratings_df)

            # Match Overview
            st.markdown("### 👥 Match Overview")
            if os.path.exists(USER_FILE):
                all_users = pd.read_csv(USER_FILE)
                all_users["Name"] = all_users["Name"].astype(str).str.strip().str.lower()
                matched_names = set()
                if os.path.exists(MATCH_FILE):
                    matches = pd.read_csv(MATCH_FILE)
                    matches["Learner"] = matches["Learner"].astype(str).str.strip().str.lower()
                    matches["Teacher"] = matches["Teacher"].astype(str).str.strip().str.lower()
                    matched_names = set(matches["Learner"]).union(set(matches["Teacher"]))

                    st.markdown("#### ✅ Paired Users")
                    paired_users = []
                    for _, row in matches.iterrows():
                        paired_users.append({"User": row["Learner"], "Paired With": row["Teacher"], "Role": "Learner", "Skill": row["Skill"]})
                        paired_users.append({"User": row["Teacher"], "Paired With": row["Learner"], "Role": "Teacher", "Skill": row["Skill"]})
                    paired_df = pd.DataFrame(paired_users)
                    st.dataframe(paired_df)

                    st.markdown("#### ❌ Unpaired Users")
                    unpaired_users = all_users[~all_users["Name"].isin(matched_names)]
                    st.dataframe(unpaired_users[["Name", "Email", "Gender", "SkillLevel", "Role", "CanTeach", "WantsToLearn", "Timestamp"]])

                all_users["Match Status"] = all_users["Name"].apply(lambda n: "Paired" if n in matched_names else "Unpaired")
                st.markdown("#### 🧾 Full User Match Status")
                st.dataframe(all_users[["Name", "Email", "Gender", "SkillLevel", "Role", "CanTeach", "WantsToLearn", "Timestamp", "Match Status"]])
        else:
            st.warning("Incorrect password. Access denied.")
