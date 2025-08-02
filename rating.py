# rating.py

import os
import pandas as pd
from datetime import datetime

# --- Paths ---
DATA_DIR = "data"
RATING_FILE = os.path.join(DATA_DIR, "ratings.csv")

# --- Load Ratings ---
def load_ratings():
    if os.path.exists(RATING_FILE):
        return pd.read_csv(RATING_FILE)
    else:
        return pd.DataFrame(columns=["Learner", "Teacher", "Rating", "Timestamp"])

# --- Save Ratings ---
def save_rating(new_rating):
    ratings_df = load_ratings()
    ratings_df = pd.concat([ratings_df, new_rating], ignore_index=True)
    ratings_df.to_csv(RATING_FILE, index=False)

# --- Add Rating Entry ---
def add_rating(learner_name, teacher_name, rating_value):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = pd.DataFrame([{
        "Learner": learner_name,
        "Teacher": teacher_name,
        "Rating": rating_value,
        "Timestamp": timestamp
    }])
    save_rating(new_entry)

# --- Get Average Ratings ---
def get_average_ratings():
    df = load_ratings()
    if df.empty:
        return pd.DataFrame(columns=["Teacher", "Average Rating"])
    return df.groupby("Teacher")["Rating"].mean().reset_index(name="Average Rating")
