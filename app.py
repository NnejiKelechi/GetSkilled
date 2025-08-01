import streamlit as st
import pandas as pd
import os
from datetime import datetime
from match_engine import find_matches, display_learner_match, get_unmatched_learners
from habit_tracker import load_users, get_study_targets, simulate_checkins, log_study_activity

# --- Constants and Setup ---
st.set_page_config(page_title="GetSkilled", layout="centered")
DATA_DIR = "data"
USER_FILE = os.path.join(DATA_DIR, "users.csv")
MATCH_FILE = os.path.join(DATA_DIR, "matches.csv")
UNMATCHED_FILE = os.path.join(DATA_DIR, "unmatched.csv")
RATINGS_FILE = os.path.join(DATA_DIR, "ratings.csv")

os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(UNMATCHED_FILE):
    pd.DataFrame(columns=["Name", "WantsToLearn", "Reason"]).to_csv(UNMATCHED_FILE, index=False)

# --- Session Init ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "name" not in st.session_state:
    st.session_state.name = None

# --- Helper: Load ratings ---
def load_ratings():
    if os.path.exists(RATINGS_FILE):
        return pd.read_csv(RATINGS_FILE)
    else:
        return pd.DataFrame(columns=["user", "partner", "skill", "rating"])

# --- Helper: Hash users to detect changes ---
def get_users_hash(users_df):
    return hash(pd.util.hash_pandas_object(users_df, index=True).sum())

# --- Load Users ---
users_df = load_users()

# --- Auto-Match Logic ---
if os.path.exists(MATCH_FILE):
    previous_hash = get_users_hash(pd.read_csv(USER_FILE))
    current_hash = get_users_hash(users_df)
    if previous_hash != current_hash:
        matched_df, unmatched_names = find_matches(users_df, threshold=0.6)
        unmatched_df = get_unmatched_learners(unmatched_names)
        matched_df.to_csv(MATCH_FILE, index=False)
        unmatched_df.to_csv(UNMATCHED_FILE, index=False)
    else:
        matched_df = pd.read_csv(MATCH_FILE)
        unmatched_df = pd.read_csv(UNMATCHED_FILE)
else:
    matched_df, unmatched_names = find_matches(users_df, threshold=0.6)
    unmatched_df = get_unmatched_learners(unmatched_names)
    matched_df.to_csv(MATCH_FILE, index=False)
    unmatched_df.to_csv(UNMATCHED_FILE, index=False)

# --- Auth Views ---
def show_login():
    st.title("🔐 Login to GetSkilled")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = users_df[(users_df["Email"] == email) & (users_df["Password"] == password)]
        if not user.empty:
            st.success("Login successful!")
            st.session_state.authenticated = True
            st.session_state.name = user.iloc[0]["Name"]
            st.session_state.user_role = user.iloc[0].get("Role", "Learner")
            st.experimental_rerun()
        else:
            st.error("Invalid email or password.")

def show_register():
    st.title("📝 Register for GetSkilled")
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Register as", ["Learner", "Teacher"])
    if st.button("Register"):
        if not name or not email or not password:
            st.warning("Please fill in all fields.")
        elif email in users_df["Email"].values:
            st.warning("User already exists.")
        else:
            new_user = pd.DataFrame([{
                "Name": name,
                "Email": email,
                "Password": password,
                "Role": role
            }])
            users_df_updated = pd.concat([users_df, new_user], ignore_index=True)
            users_df_updated.to_csv(USER_FILE, index=False)
            st.success("Registration successful! Please login.")
            st.experimental_rerun()

# --- App View Routing ---
if not st.session_state.authenticated:
    page = st.sidebar.radio("Navigate", ["Login", "Register"])
    if page == "Login":
        show_login()
    else:
        show_register()
else:
    st.sidebar.title(f"👋 Welcome, {st.session_state.name}")
    nav = st.sidebar.radio("Menu", ["Dashboard", "Logout"])

    if nav == "Logout":
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

    elif nav == "Dashboard":
        tabs = st.tabs(["📋 User Data", "💬 Ratings", "🤝 Matches", "⚙️ AI Match Engine", "📊 Match Summary"])

        with tabs[0]:
            st.subheader("📋 Registered Users")
            st.dataframe(users_df)

        with tabs[1]:
            st.subheader("⭐ Ratings Given")
            ratings_df = load_ratings()
            st.dataframe(ratings_df)

            if not ratings_df.empty:
                st.markdown("### 📈 Average Ratings per Teacher")
                avg_ratings = ratings_df.groupby("partner")["rating"].mean().reset_index()
                avg_ratings.columns = ["Teacher", "Avg Rating"]
                avg_ratings["Stars"] = avg_ratings["Avg Rating"].apply(lambda x: "⭐" * int(round(x)))
                st.dataframe(avg_ratings)

        with tabs[2]:
            st.subheader("✅ Matches")
            st.dataframe(matched_df)

            st.markdown("### ❌ Unmatched Learners")
            st.dataframe(unmatched_df)

        with tabs[3]:
            st.subheader("⚙️ AI Match Engine (Learner View)")
            name_input = st.text_input("🔍 Enter your name to see your match", "").strip().lower()
            if name_input:
                learner_match = display_learner_match(name_input, matched_df)
                if not learner_match.empty:
                    st.success("Match found!")
                    st.dataframe(learner_match)
                else:
                    st.warning("No match found for this name.")

        with tabs[4]:
            st.subheader("📊 Match Summary by Skill")

            if not matched_df.empty:
                skill_counts = matched_df["Skill"].value_counts().reset_index()
                skill_counts.columns = ["Skill", "Matches"]
                st.bar_chart(skill_counts.set_index("Skill"))

                st.markdown("### 📌 Total Learners Matched")
                st.metric("Learners", len(matched_df))

                st.markdown("### 📌 Total Unmatched Learners")
                st.metric("Unmatched", len(unmatched_df))
            else:
                st.info("ℹ️ No match data available.")
