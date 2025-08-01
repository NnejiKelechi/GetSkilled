# app.py

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from match_engine import find_matches, display_learner_match
from habit_tracker import load_users, get_study_targets, simulate_checkins, log_study_activity

# --- Constants and Setup ---
st.set_page_config(page_title="GetSkilled", layout="centered")
DATA_DIR = "data"
USER_FILE = os.path.join(DATA_DIR, "users.csv")
MATCH_FILE = os.path.join(DATA_DIR, "matches.csv")
UNMATCHED_FILE = os.path.join(DATA_DIR, "unmatched.csv")
RATINGS_FILE = os.path.join(DATA_DIR, "ratings.csv")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

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
users_df = load_users(USER_FILE)

# --- Trigger Matching if New Users Detected ---
if os.path.exists(MATCH_FILE):
    previous_matches = pd.read_csv(MATCH_FILE)
    previous_hash = get_users_hash(pd.read_csv(USER_FILE))
    current_hash = get_users_hash(users_df)
else:
    previous_matches = pd.DataFrame()
    previous_hash = None
    current_hash = get_users_hash(users_df)

if previous_hash != current_hash:
    matched_df, unmatched_df = find_matches(users_df, threshold=0.6, show_progress=True)
    matched_df.to_csv(MATCH_FILE, index=False)
    unmatched_df.to_csv(UNMATCHED_FILE, index=False)
else:
    matched_df = pd.read_csv(MATCH_FILE)
    unmatched_df = pd.read_csv(UNMATCHED_FILE)

# --- Streamlit Tabs ---
tabs = st.tabs(["📋 User Data", "💬 Ratings", "🤝 Matches", "⚙️ AI Match Engine", "📊 Match Summary"])
with tabs[0]:
    st.subheader("📋 Registered Users")
    st.dataframe(users_df)

with tabs[1]:
    st.subheader("⭐ Ratings Given")
    ratings_df = load_ratings()
    st.dataframe(ratings_df)

    # Average rating per teacher
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
        display_learner_match(matched_df, name_input, RATINGS_FILE)

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
