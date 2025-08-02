# rating.py

import pandas as pd
import os
from datetime import datetime

DATA_DIR = "data"
RATINGS_FILE = os.path.join(DATA_DIR, "ratings.csv")

def load_ratings():
    """Load ratings from the CSV file."""
    if os.path.exists(RATINGS_FILE):
        return pd.read_csv(RATINGS_FILE)
    else:
        return pd.DataFrame(columns=["Learner", "Teacher", "Rating"])

def save_rating(df):
    """Save ratings DataFrame to file."""
    df.to_csv(RATINGS_FILE, index=False)

def add_rating(learner, teacher, rating):
    """Add a new rating or update if one already exists."""
    df = load_ratings()
    # Check if learner has already rated this teacher
    existing = df[(df["Learner"] == learner) & (df["Teacher"] == teacher)]
    if not existing.empty:
        df.loc[existing.index, "Rating"] = rating  # Update rating
    else:
        new_row = pd.DataFrame([{"Learner": learner, "Teacher": teacher, "Rating": rating}])
        df = pd.concat([df, new_row], ignore_index=True)
    save_rating(df)

def get_average_ratings():
    """Return average ratings per teacher with star visualizations."""
    df = load_ratings()
    if df.empty:
        return pd.DataFrame(columns=["Teacher", "Average Rating", "Stars"])
    avg_df = df.groupby("Teacher")["Rating"].mean().reset_index()
    avg_df.columns = ["Teacher", "Average Rating"]
    avg_df["Stars"] = avg_df["Average Rating"].apply(lambda x: "⭐" * int(round(x)))
    return avg_df

def generate_study_targets(users_df):
    """Simulate weekly study target per user based on their selected study days."""
    targets = users_df[["Name", "StudyDays"]].copy()
    targets["TargetMinutes"] = targets["StudyDays"] * 30  # Assume 30 mins per day
    return targets
