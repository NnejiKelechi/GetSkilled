
import streamlit as st  
import plotly as plt
import pandas as pd
import os
from PIL import Image
import altair as alt
from datetime import datetime
from match_engine import find_matches
from habit_tracker import load_users, get_study_targets, simulate_checkins, log_study_activity
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
        users = users[base_columns]
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

# --- Streamlit UI ---
menu = st.sidebar.selectbox("Choose an option:", ["Submit Info", "View Match", "Log Study", "Insights", "Admin"])
st.title("🔗 GetSkilled - Connect Learners & Teachers")
st.sidebar.markdown("""
---
#### 👋 Welcome to **GetSkilled**  
Connect with learners and teachers.  
Submit your info, match up, and start learning!
""")

# --- Submit Info Section ---
if menu == "Submit Info":
    st.subheader("📋 Register as a Teacher or Learner")
    st.markdown("""
    Fill out the form below to register as a teacher or learner.
    - **Learners**: Select a skill you want to learn.
    - **Teachers**: Select a skill you can teach.
    """)

    name = st.text_input("Your Full Name")
    email = st.text_input("Email Address")
    contact_number = st.text_input("Contact Number (optional)")
    if contact_number and not contact_number.isdigit():
        st.error("Contact number must contain only digits.")
    if contact_number and len(contact_number) < 11:
        st.error("Contact number must be at least 11 digits long.")
    if contact_number and len(contact_number) > 15:
        st.error("Contact number must not exceed 15 digits.")
    if email and "@" not in email:
        st.error("Please enter a valid email address.")
    gender = st.selectbox("Gender", ["Male", "Female", "Prefer not to tell"])
    age_range = st.selectbox("Age Range", ["18-24", "25-34", "35-44", "45-54", "55+"])
    no_of_days = st.slider("How many days per week can you commit?", 1, 7, 3)
    preferred_time = st.selectbox("Preferred Time for Learning", ["Morning", "Afternoon", "Evening"])
    preferred_days = st.multiselect("Preferred Days for Learning", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
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
                "Email": email.strip().lower(),  # Lowercase for consistency
                "Gender": gender,
                "AgeRange": age_range,
                "ContactNumber": contact_number.strip(),
                "NoOfDays": no_of_days,
                "PreferredTime": preferred_time,
                "PreferredDays": ", ".join(preferred_days),
                "SkillLevel": skill_level,
                "Role": role,
                "CanTeach": can_teach,
                "WantsToLearn": wants_to_learn,
                "Timestamp": timestamp
            }])

            if os.path.exists(USER_FILE):
                existing = pd.read_csv(USER_FILE)
                # Check if email already exists
                if email.strip().lower() in existing['Email'].str.lower().values:
                    st.warning("🚫 This email has already been registered.")
                else:
                    updated = pd.concat([existing, new_user], ignore_index=True)
                    updated.to_csv(USER_FILE, index=False)
                    st.success(f"🎉 Successfully registered as a {role.lower()}!")
                    auto_generate_matches()
            else:
                # First registration
                new_user.to_csv(USER_FILE, index=False)
                st.success(f"🎉 Successfully registered as a {role.lower()}!")
                auto_generate_matches()
                        # Send confirmation email
                confirmation_body = f"""Hello {name},
                Thank you for registering as a {role.lower()} on GetSkilled. We will notify you when a match is found!"""
                if send_email(email.strip().lower(), "Registration Confirmation", confirmation_body):
                            st.success("📧 Confirmation email sent successfully!")
                            
                            
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

elif menu == "Log Study":
    st.subheader("📚 Log Your Study Activity")
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

elif menu == "Insights":
    st.subheader("📊 Insights and Analytics")
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

            if os.path.exists(RATINGS_FILE):
                st.markdown("### 📊 Submitted Ratings")
                ratings_df = pd.read_csv(RATINGS_FILE)
                st.dataframe(ratings_df)

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
