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

# --- Setup: File Paths & Ratings Initialization ---
RATINGS_FILE = "data/ratings.csv"
MATCHED_FILE = "data/matched_users.csv"
USER_FILE = "data/users.csv"
PAIRED_FILE = "data/paired_users.csv"
UNPAIRED_FILE = "data/unpaired_users.csv"
UNMATCHED_FILE = "data/unmatched_learners.csv"

# Function to reload users
@st.cache_data(ttl=10, show_spinner=False)
def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    return pd.DataFrame(columns=["Name", "Role", "WantsToLearn", "CanTeach"])

# Function to reload matched users
@st.cache_data(ttl=10, show_spinner=False)
def load_matched():
    if os.path.exists(MATCHED_FILE):
        return pd.read_csv(MATCHED_FILE)
    return pd.DataFrame(columns=["Learner", "Matched Teacher", "Confidence Score", "Learner Message", "Teacher Message"])

# Function to reload unmatched users
@st.cache_data(ttl=10, show_spinner=False)
def load_unmatched():
    if os.path.exists(UNMATCHED_FILE):
        return pd.read_csv(UNMATCHED_FILE)
    return pd.DataFrame(columns=["Name"])

# Function to reload ratings
@st.cache_data(ttl=10, show_spinner=False)
def load_ratings():
    if os.path.exists(RATINGS_FILE):
        return pd.read_csv(RATINGS_FILE)
    return pd.DataFrame(columns=["User", "Rating", "Feedback"])

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
        st.session_state.refresh_matches = True
        st.session_state.refresh_users = True
        st.session_state.matches = match_df
    else:
        pd.DataFrame(unmatched_learners).to_csv(UNMATCHED_FILE, index=False)
        st.session_state.refresh_matches = True
        st.session_state.refresh_users = True

# Lazy loading to reduce startup time
users = load_users() if st.session_state.refresh_users else pd.DataFrame()
matched_df = load_matched() if st.session_state.refresh_matches else pd.DataFrame()
unmatched_df = load_unmatched()
rating_df = load_ratings() if st.session_state.refresh_ratings else pd.DataFrame()

# --- Streamlit Setup ---
st.set_page_config(page_title="GetSkilled Admin", layout="centered")
st.title("💡 GetSkilled Platform")
st.markdown("""
    <div style='text-align:center; font-style:italic; font-weight:bold; font-size:20px;'>
        Connect. Learn. Grow. 🚀
    </div>
""", unsafe_allow_html=True)

# --- Cache Resources ---
# Load model only once (efficient memory use)
@st.cache_resource(show_spinner=False)
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

# Load CSV data with caching
@st.cache_data(show_spinner=False)
def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame()
    

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

if menu == "Admin":
    st.subheader("🔐 Admin Dashboard")

    admin_username = st.text_input("Admin Username")
    admin_password = st.text_input("Admin Password", type="password")

    # --- Admin Authentication Guard ---
if "admin_authenticated" not in st.session_state or not st.session_state.admin_authenticated:
    st.error("Access denied. Please log in as an admin.")
    st.stop()

    if st.button("Login"):
        if admin_username == "admin" and admin_password == "admin123":
            st.success("✅ Login successful! Welcome, Admin.")
            st.session_state.admin_authenticated = True
            

            # --- Organized Tabs ---
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "👥 Users", "⭐ Ratings", "🔗 Match Results", "🧠 AI Matching", "📊 Summary"
            ])

                    # --- Tab 1: User Data ---
        # --- Tab 1: User Data ---
        with tab1:
            st.markdown("### 👤 All Registered Users")

            if users.empty:
                st.warning("No users registered yet.")
            else:
                if "Role" in users.columns:
                    role_filter = st.selectbox("Filter by Role", ["All"] + sorted(users["Role"].dropna().unique().tolist()), key="role_filter_users")
                else:
                    st.warning("🛑 'Role' column not found.")
                    role_filter = "All"

            search_query = st.text_input("🔍 Search by Name or Skill", key="search_input_users")
            filtered_users = users.copy()

            # Role filter
            if role_filter != "All" and "Role" in filtered_users.columns:
                filtered_users = filtered_users[filtered_users["Role"] == role_filter]

            # Search filter
            filters = []
            if "Name" in filtered_users.columns:
                filters.append(filtered_users["Name"].str.contains(search_query, case=False, na=False))
            if "WantsToLearn" in filtered_users.columns:
                filters.append(filtered_users["WantsToLearn"].str.contains(search_query, case=False, na=False))
            if "CanTeach" in filtered_users.columns:
                filters.append(filtered_users["CanTeach"].str.contains(search_query, case=False, na=False))

            if filters:
                combined_filter = filters[0]
                for f in filters[1:]:
                    combined_filter |= f
                filtered_users = filtered_users[combined_filter]
            else:
                st.info("No valid search filters applied.")

                st.dataframe(filtered_users, use_container_width=True)

        # --- Tab 2: Ratings ---
        with tab2:
            st.markdown("### ⭐ User Ratings")
            if rating_df.empty:
                st.info("No ratings submitted yet.")
            else:
                st.dataframe(rating_df, use_container_width=True)

        # --- Tab 3: Match Summary ---
        with tab3:
            st.markdown("### 📊 Match Summary")

            st.markdown("#### ✅ All Matched Users")
            if matched_df.empty:
                st.warning("No matched users found.")
            else:
                st.dataframe(matched_df, use_container_width=True)

                st.markdown("#### ❌ All Unmatched Users")
                if unmatched_df.empty:
                    st.info("No unmatched learners found.")
                else:
                    st.dataframe(unmatched_df, use_container_width=True)

        # --- Tab 4: AI Match Engine ---
        with tab4:
            st.markdown("### 🤖 AI Match Engine")
            st.caption("Uses sentence similarity to match learners with teachers")

            threshold = st.slider("Matching Confidence Threshold", 0.5, 0.9, 0.6, key="threshold_slider")
            if st.button("Run Matching", key="run_matching_button"):
                with st.spinner("Running AI Matching Engine..."):
                    users = pd.read_csv(USER_FILE)  # reload fresh user data
                    matches, unmatched_learners = find_matches(users, threshold=threshold)

                    if matches:
                        match_data = [{
                            "Learner": m["Learner"],
                            "Matched Teacher": m["Teacher"],
                            "Confidence Score": round(m["Confidence"], 2),
                            "Learner Message": m["LearnerMessage"],
                            "Teacher Message": m["TeacherMessage"]
                        } for m in matches]

                        match_df = pd.DataFrame(match_data)
                        st.success("Matching Complete ✅")
                        st.dataframe(match_df, use_container_width=True)

                        match_df.to_csv(MATCHED_FILE, index=False)
                        pd.DataFrame(unmatched_learners).to_csv(UNMATCHED_FILE, index=False)

                        matched_df = match_df.copy()
                        st.session_state.refresh_matches = True
                        st.session_state.refresh_users = True
                        st.session_state.matches = match_df
                    else:
                        st.warning("No suitable matches found at this threshold.")

                    if unmatched_learners:
                        st.markdown("#### ❌ Unmatched Learners")
                        unmatched_df = pd.DataFrame(unmatched_learners)
                        st.dataframe(unmatched_df, use_container_width=True)

        # --- Tab 5: Unmatched Learners (Optional UI Split) ---
        with tab5:
            st.markdown("### ❌ Unmatched Learners (All Time)")
            if unmatched_df.empty:
                st.info("No unmatched learners found.")
            else:
                st.dataframe(unmatched_df, use_container_width=True)

        # --- Safe access to matches variable ---
        if "matches" in st.session_state:
            name_input = st.text_input("🔍 Search for Match by Learner Name", key="match_name_input")
            if name_input:
                name_matches = st.session_state.matches[
                st.session_state.matches["Learner"].str.lower() == name_input.lower()
                ]
                st.dataframe(name_matches, use_container_width=True)
        else:
            st.info("Run the AI Match Engine to view matches by name.")

        
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
