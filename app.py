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

# --- Constants ---
USER_FILE = "data/users.csv"
RATINGS_FILE = "data/ratings.csv"
MATCH_FILE = "data/matches.csv"
PAIRED_FILE = "data/paired_users.csv"
UNPAIRED_FILE = "data/unpaired_users.csv"

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
    
# Use the same function to load different datasets
users = load_data(USER_FILE)
ratings = load_data(RATINGS_FILE)
matches = load_data(MATCH_FILE)
paired_df = load_data(PAIRED_FILE)
unpaired_df = load_data(UNPAIRED_FILE)

if not users.empty:
    get_study_targets(users)

# --- Sidebar Menu ---
menu = st.sidebar.selectbox("Menu", ["Home", "Admin"])

if menu == "Admin":
    st.sidebar.title("🔐 Admin Panel")
    st.sidebar.markdown("Welcome, Admin!")

    admin_username = st.sidebar.text_input("Username")
    admin_password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if admin_username == "admin" and admin_password == "admin123":
            st.sidebar.success("✅ Logged in as Admin")

            admin_menu = st.sidebar.radio(
                "📂 Select Section",
                [
                    "👥 View Users",
                    "⭐ Ratings",
                    "🔗 Match Results",
                    "🧠 Run AI Match Engine",
                    "📊 Match Summary"
                ]
            )

            st.title("📊 Admin Dashboard")

            if admin_menu == "👥 View Users":
                st.subheader("👥 All Registered Users")

                if users.empty:
                    st.warning("No users registered yet.")
                else:
                    if "Role" in users.columns:
                        role_filter = st.selectbox("Filter by Role", ["All"] + sorted(users["Role"].dropna().unique()))
                    else:
                        st.warning("🛑 'Role' column not found.")
                        role_filter = "All"

                    search_query = st.text_input("🔍 Search by Name or Skill")
                    filtered_users = users.copy()

                    # Role filter
                    if role_filter != "All":
                        filtered_users = filtered_users[filtered_users["Role"] == role_filter]

                    # Search filter
                    filters = []
                    if "Name" in filtered_users:
                        filters.append(filtered_users["Name"].str.contains(search_query, case=False, na=False))
                    if "WantsToLearn" in filtered_users:
                        filters.append(filtered_users["WantsToLearn"].str.contains(search_query, case=False, na=False))
                    if "CanTeach" in filtered_users:
                        filters.append(filtered_users["CanTeach"].str.contains(search_query, case=False, na=False))

                    if filters and search_query:
                        combined_filter = filters[0]
                        for f in filters[1:]:
                            combined_filter |= f
                        filtered_users = filtered_users[combined_filter]

                    # Pagination
                    page_size = 10
                    total_pages = max(1, (len(filtered_users) - 1) // page_size + 1)
                    page = st.number_input("Page", 1, total_pages, 1)
                    start, end = (page - 1) * page_size, (page) * page_size

                    st.dataframe(filtered_users.iloc[start:end])

            elif admin_menu == "⭐ Ratings":
                st.subheader("⭐ User Ratings")

                if ratings.empty:
                    st.info("No ratings submitted yet.")
                else:
                    st.dataframe(ratings)

                    avg_rating = ratings.groupby("partner")["rating"].mean().reset_index()
                    avg_rating.columns = ["Teacher", "Avg Rating"]

                    def render_stars(r):
                        full = "⭐" * int(round(r))
                        return full + "☆" * (5 - int(round(r)))

                    avg_rating["Stars"] = avg_rating["Avg Rating"].apply(render_stars)

                    top_n = st.slider("Show Top Rated Teachers", 1, 10, 5)
                    top_teachers = avg_rating.sort_values("Avg Rating", ascending=False).head(top_n)

                    st.markdown("### 🌟 Top Rated Teachers")
                    st.dataframe(top_teachers)

                    if "timestamp" in ratings.columns:
                        last = pd.to_datetime(ratings["timestamp"]).max()
                        st.success(f"🕒 Last rating: {last}")

            elif admin_menu == "🔗 Match Results":
                st.subheader("🔗 Current Matches")
                st.dataframe(matches if not matches.empty else pd.DataFrame(columns=["learner", "teacher", "skill"]))

            elif admin_menu == "🧠 Run AI Match Engine":
                st.subheader("🧠 Run AI Match Engine")
                threshold = st.slider("Match Threshold", 0.5, 0.9, 0.6)

                if st.button("Run Matching"):
                    with st.spinner("Matching in progress..."):
                        matched_df, unmatched_df = find_matches(users, threshold=threshold, show_progress=True)

                        matched_df.to_csv(MATCH_FILE, index=False)
                        matched_df.to_csv(PAIRED_FILE, index=False)
                        unmatched_df.to_csv(UNPAIRED_FILE, index=False)

                        st.success("✅ Matching Complete")
                        st.dataframe(matched_df)

            elif admin_menu == "📊 Match Summary":
                st.subheader("📊 Match Summary Overview")

                st.markdown("#### ✅ Paired Users")
                st.dataframe(paired_df if not paired_df.empty else pd.DataFrame([{"Status": "No pairs yet."}]))

                st.markdown("#### ❌ Unpaired Users")
                st.dataframe(unpaired_df if not unpaired_df.empty else pd.DataFrame([{"Status": "All matched!"}]))
        else:
            st.sidebar.error("❌ Invalid credentials.")

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
