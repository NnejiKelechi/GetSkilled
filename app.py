# ✅ Optimized version of main.py
import streamlit as st
import pandas as pd
import os
import time
from sentence_transformers import SentenceTransformer
from admin_users import admin_dashboard
from match_engine import find_matches
from habit_tracker import (
    load_users, get_study_targets, log_study_activity,
    simulate_checkins, get_weekly_summary, get_defaulters
)

# --- File Paths ---
DATA_DIR = "data"
USER_DATA_PATH = os.path.join(DATA_DIR, "users.csv")
MATCHED_FILE = os.path.join(DATA_DIR, "matched_results.csv")
UNMATCHED_FILE = os.path.join(DATA_DIR, "unmatched_learners.csv")
RATINGS_FILE = os.path.join(DATA_DIR, "ratings.csv")

DATA_DIR = "data"
USER_FILE = os.path.join(DATA_DIR, "users.csv")  # ✅ Ensure this line comes early

def get_users_hash():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "rb") as f:
            return hash(f.read())
    return None

# --- Optimized Lazy Loaders ---
@st.cache_data(show_spinner=False)
def load_csv(path, columns):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=columns)

# Loaders for specific files
def load_users(): return load_csv(USER_FILE, ["Name", "Role", "WantsToLearn", "CanTeach"])
def load_matched(): return load_csv(MATCHED_FILE, ["Learner", "Matched Teacher", "Confidence Score", "Learner Message", "Teacher Message"])
def load_unmatched(): return load_csv(UNMATCHED_FILE, ["Name"])
def load_ratings(): return load_csv(RATINGS_FILE, ["User", "Rating", "Feedback"])
def load_paired(): return load_csv(PAIRED_FILE, ["Name", "Role", "Skill"])
def load_unpaired(): return load_csv(UNPAIRED_FILE, ["Name", "Role", "Skill"])

# --- Dynamic Refreshable States ---
if 'refresh_users' not in st.session_state:
    st.session_state.refresh_users = True
if 'refresh_matches' not in st.session_state:
    st.session_state.refresh_matches = True
if 'refresh_ratings' not in st.session_state:
    st.session_state.refresh_ratings = True

# --- Auto-run Matching When New Users Detected ---
import hashlib

@st.cache_data(ttl=10)
def get_users_hash():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    return None

if 'last_user_hash' not in st.session_state:
    st.session_state.last_user_hash = get_users_hash()

current_hash = get_users_hash()
if current_hash != st.session_state.last_user_hash:
    st.session_state.last_user_hash = current_hash
    users = pd.read_csv(USER_FILE)
    from match_engine import find_matches
    matches, unmatched_learners = find_matches(users, threshold=0.6)
    if matches:
        match_data = [{
            "Learner": m["Learner"],
            "Matched Teacher": m["Teacher"],
            "Confidence Score": round(m["Confidence"], 2),
            "Learner Message": m["LearnerMessage"],
            "Teacher Message": m["TeacherMessage"]
        } for m in matches]
        match_df = pd.DataFrame(match_data)
        match_df.to_csv(MATCHED_FILE, index=False)
        pd.DataFrame(unmatched_learners).to_csv(UNMATCHED_FILE, index=False)

        # Save paired/unpaired summary data
        paired = users[users['Name'].isin(match_df['Learner'].tolist() + match_df['Matched Teacher'].tolist())]
        paired.to_csv(PAIRED_FILE, index=False)
        unpaired = users[~users['Name'].isin(paired['Name'])]
        unpaired.to_csv(UNPAIRED_FILE, index=False)

        st.session_state.refresh_matches = True
        st.session_state.refresh_users = True
        st.session_state.matches = match_df
    else:
        pd.DataFrame(unmatched_learners).to_csv(UNMATCHED_FILE, index=False)
        st.session_state.refresh_matches = True
        st.session_state.refresh_users = True

# --- Lazy loading to reduce startup time ---
users = load_users() if st.session_state.refresh_users else pd.DataFrame()
matched_df = load_matched() if st.session_state.refresh_matches else pd.DataFrame()
unmatched_df = load_unmatched() if st.session_state.refresh_matches else pd.DataFrame()
rating_df = load_ratings() if st.session_state.refresh_ratings else pd.DataFrame()

# --- Lazy Run Matching ---
@st.cache_data(show_spinner="Running AI match engine...")
def run_matching(df):
    matched_df, unmatched_df = find_matches(df, threshold=0.6, show_progress=False)
    matched_df.to_csv(MATCHED_FILE, index=False)
    unmatched_df.to_csv(UNMATCHED_FILE, index=False)
    return matched_df, unmatched_df

# --- Streamlit Setup ---
st.set_page_config(page_title="GetSkilled Admin", layout="centered")
st.title("💡 GetSkilled Platform")
st.markdown("""
    <div style='text-align:center; font-style:italic; font-weight:bold; font-size:20px;'>
        Connect. Learn. Grow. 🚀
    </div>
""", unsafe_allow_html=True)

if not users.empty:
    get_study_targets(users)

# --- Sidebar Menu ---
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

# --- Load User Data ---
if os.path.exists(USER_DATA_PATH):
    users = pd.read_csv(USER_DATA_PATH)
    users.columns = users.columns.str.strip().str.lower()  # Normalize column names
else:
    st.error("❌ No user data found. Please upload 'users.csv' in the 'data/' directory.")
    st.stop()

# --- Run Matching Automatically on Load ---
matches, unmatched = pd.DataFrame(), pd.DataFrame()
if "role" in users.columns:
    matches, unmatched = find_matches(users, threshold=0.6, show_progress=True)
    matches.to_csv(MATCHED_FILE, index=False)
    unmatched.to_csv(UNMATCHED_FILE, index=False)
else:
    st.error("❌ The uploaded data is missing the required 'Role' column.")
    st.stop()

# --- Ensure Required Column Exists ---
if "role" not in users.columns:
    st.error("❌ The uploaded data is missing the required 'Role' column.")
    st.stop()

# --- Admin Section ---
if menu == "Admin":
    st.subheader("🔐 Admin Dashboard")

    # --- Initialize session state for admin login ---
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        admin_username = st.text_input("Admin Username")
        admin_password = st.text_input("Admin Password", type="password")

        if st.button("Login"):
            if admin_username == "admin" and admin_password == "admin123":
                st.session_state.admin_authenticated = True
                st.success("✅ Login successful! Welcome, Admin.")
            else:
                st.error("❌ Invalid admin credentials")

    # --- Authenticated Admin View ---
    if st.session_state.admin_authenticated:
        # --- Tabs ---
        tabs = st.tabs(["👥 Learner View", "🛠 Admin View"])

        # --- Learner View Tab ---
        with tabs[0]:
            st.header("🔍 Find Your Match")
            name_input = st.text_input("Enter your name to view your match:").strip().lower()
            if name_input:
                matches, _ = run_matching(users)
                display_learner_match(matches, name_input, RATINGS_FILE)

        # --- Admin Dashboard Tab ---
        with tabs[1]:
            tab1, tab2, tab3 = st.tabs(["📁 All Users", "✅ Matched", "❌ Unmatched"])

            with tab1:
                st.subheader("📁 Registered Users")
                if st.button("Load Users"):
                    st.dataframe(users)

            with tab2:
                st.subheader("✅ Matched Learners and Teachers")
                if st.button("Load Matches"):
                    matches, _ = run_matching(users)
                    st.dataframe(matches)

            with tab3:
                st.subheader("❌ Unmatched Learners")
                if st.button("Load Unmatched"):
                    _, unmatched = run_matching(users)
                    st.dataframe(unmatched)

            if os.path.exists(RATINGS_FILE):
                if st.checkbox("📊 Show Match Ratings"):
                    ratings = pd.read_csv(RATINGS_FILE)
                    st.subheader("⭐ Match Ratings")
                    avg_ratings = ratings.groupby("partner")["rating"].mean().reset_index()
                    avg_ratings.columns = ["Teacher", "Average Rating"]
                    st.dataframe(avg_ratings.sort_values(by="Average Rating", ascending=False))
            else:
                st.info("ℹ️ No ratings available yet.")

        
elif menu == "Home":
    st.subheader("👋 Welcome to GetSkilled!")
    auth_option = st.radio("Choose an option", ["Login", "Register"])

    if auth_option == "Login":
        users = pd.read_csv(USER_FILE)  # 👈 This line ensures the latest user list is loaded
        with st.form("login_form"):
            name_input = st.text_input("Enter your Full Name").strip().lower()
            submitted = st.form_submit_button("Login")

        if submitted and name_input:
            user_row = users[users["name"].str.strip().str.lower() == name_input]
            if not user_row.empty:
                user_name = user_row.iloc[0]['name']
                st.success(f"✅ Welcome back, {user_name.title()}!")
                with st.spinner("Loading dashboard..."):
                    time.sleep(1)

                st.markdown("### 🎉 Your Match")
                name_matches = matches[
                    (matches["learner"].str.lower() == name_input) |
                    (matches["teacher"].str.lower() == name_input)
                ]
                if not name_matches.empty:
                    row = name_matches.iloc[0]
                    partner = row["teacher"] if row["learner"].lower() == name_input else row["learner"]
                    skill = row.get("skill", "Data Skill")
                    st.success(f"You have been paired with {partner.title()} to learn {skill}.")

                    # --- Show Match Explanation ---
                    explanation = row.get("Message_Learner", f"You have been paired with {partner.title()} to learn {skill}.")
                    st.info(f"💬 {explanation}")

                    # --- Rating Feature ---
                    st.markdown("### ⭐ Rate Your Match")
                    existing_rating = ratings[
                        (ratings["name"].str.lower() == name_input) &
                        (ratings["partner"].str.lower() == partner.lower())
                    ]

                    if not existing_rating.empty:
                        st.success("✅ You’ve already rated this match.")
                    else:
                        rating = st.slider("How would you rate this match?", 1, 5, 3)
                        if st.button("Submit Rating"):
                            new_rating = pd.DataFrame([{
                                "name": user_name,
                                "partner": partner,
                                "rating": rating,
                                "timestamp": datetime.now()
                            }])
                            ratings = pd.concat([ratings, new_rating], ignore_index=True)
                            ratings.to_csv(RATINGS_FILE, index=False)
                            st.success("✅ Rating submitted successfully!")

                    st.markdown("### 📈 Study Summary")
                    summary = get_weekly_summary(name_input)
                    if summary:
                        for day, val in summary.items():
                            st.write(f"{day}: {val}")
                    else:
                        st.warning("No activity recorded yet.")
                else:
                    st.info("⏳ No match yet. Please check back soon!")
            else:
                st.warning("User not found. Please register.")

    if auth_option == "Register":
        st.subheader("📝 Register")
        role = st.selectbox("Registering as:", ["Learner", "Teacher"])

        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                age = st.selectbox("Age Range", ["18 - 24", "25 - 34", "35 - 44", "55+"])
            with col2:
                skill = st.selectbox("Skill Level", ["Beginner", "Intermediate", "Advanced"])
                days = st.slider("Study days per week", 1, 7, 3)

            if role == "Teacher":
                teach = st.selectbox("What can you teach?", ["Python", "SQL", "Excel", "Communication"])
                learn = ""
            else:
                learn = st.selectbox("What do you want to learn?", ["Python", "SQL", "Excel", "Communication"])
                teach = ""

            register_submit = st.form_submit_button("Register")

        if register_submit:
            if email.lower() in users["email"].str.lower().values:
                st.warning("⚠️ Email already registered.")
            else:
                new_user = pd.DataFrame([{
                    "name": name, "email": email, "gender": gender, "agerange": age,
                    "skilllevel": skill, "role": role, "timestamp": pd.Timestamp.now(),
                    "canteach": teach, "wantstolearn": learn, "studydays": days
                }])
                users = pd.concat([users, new_user], ignore_index=True)
                users.to_csv(USER_FILE, index=False)
                users = pd.read_csv(USER_FILE)  # Refresh to include the new registration
                st.success("✅ Registered! Please log in.")
