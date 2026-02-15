# fittracker.py
import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from streamlit_extras.let_it_rain import rain

# -------------------------
# Database Setup
# -------------------------
conn = sqlite3.connect("fittracker.db", check_same_thread=False)
c = conn.cursor()

# Users table
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    points INTEGER DEFAULT 0,
    weekly_goal INTEGER DEFAULT 150
)
""")

# Workouts table
c.execute("""
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    date TEXT,
    workout_type TEXT,
    duration INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# Achievements table
c.execute("""
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    badge TEXT,
    date TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")
conn.commit()

# -------------------------
# Helper Functions
# -------------------------
def get_user(username):
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    return c.fetchone()

def create_user(username, password):
    c.execute("INSERT INTO users (username, password, points, weekly_goal) VALUES (?, ?, ?, ?)",
              (username, password, 0, 150))
    conn.commit()

def log_workout(user_id, workout_type, duration):
    date = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO workouts (user_id, date, workout_type, duration) VALUES (?, ?, ?, ?)",
              (user_id, date, workout_type, duration))
    conn.commit()
    add_points(user_id, duration)
    check_achievements(user_id)

def add_points(user_id, duration):
    points = duration // 10
    c.execute("UPDATE users SET points = points + ? WHERE id=?", (points, user_id))
    conn.commit()

def get_workouts(user_id):
    c.execute("SELECT date, workout_type, duration FROM workouts WHERE user_id=?", (user_id,))
    return c.fetchall()

def check_achievements(user_id):
    c.execute("SELECT COUNT(*) FROM workouts WHERE user_id=?", (user_id,))
    count = c.fetchone()[0]
    if count == 1:
        award_badge(user_id, "First Workout Logged")

    # 7-day streak badge
    today = datetime.now().date()
    streak = 0
    for i in range(7):
        day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        c.execute("SELECT * FROM workouts WHERE user_id=? AND date=?", (user_id, day))
        if c.fetchone():
            streak += 1
        else:
            break
    if streak == 7:
        award_badge(user_id, "7-Day Streak")

def award_badge(user_id, badge_name):
    c.execute("SELECT * FROM achievements WHERE user_id=? AND badge=?", (user_id, badge_name))
    if not c.fetchone():
        date = datetime.now().strftime("%Y-%m-%d")
        c.execute("INSERT INTO achievements (user_id, badge, date) VALUES (?, ?, ?)", (user_id, badge_name, date))
        conn.commit()
        st.balloons()
        st.success(f"🏆 Congrats! You earned a badge: {badge_name}")

def get_achievements(user_id):
    c.execute("SELECT badge, date FROM achievements WHERE user_id=?", (user_id,))
    return c.fetchall()

def get_weekly_progress(user_id):
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    c.execute("SELECT SUM(duration) FROM workouts WHERE user_id=? AND date>=?", (user_id, week_ago))
    result = c.fetchone()[0]
    return result if result else 0

def update_weekly_goal(user_id, new_goal):
    c.execute("UPDATE users SET weekly_goal=? WHERE id=?", (new_goal, user_id))
    conn.commit()

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="FitTracker", layout="wide")
st.title("🎯 FitTracker - University Edition")

# Sidebar Menu
menu = ["Login", "Sign Up"]
choice = st.sidebar.selectbox("Menu", menu)

# --- Sign Up ---
if choice == "Sign Up":
    st.subheader("Create an Account")
    new_user = st.text_input("Username")
    new_password = st.text_input("Password", type="password")
    if st.button("Sign Up"):
        if get_user(new_user):
            st.warning("Username already exists!")
        else:
            create_user(new_user, new_password)
            st.success("Account created! Please log in.")

# --- Login ---
elif choice == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = get_user(username)
        if user and user[2] == password:
            st.session_state['user'] = user
            st.success(f"Welcome back, {username}!")

# --- Dashboard ---
if 'user' in st.session_state:
    user_id = st.session_state['user'][0]
    st.header("📊 Dashboard")

    # Refresh user info
    st.session_state['user'] = get_user(st.session_state['user'][1])
    workouts = get_workouts(user_id)
    total_workouts = len(workouts)
    total_points = st.session_state['user'][3] or 0
    weekly_goal = st.session_state['user'][4] or 150
    weekly_progress = get_weekly_progress(user_id)

    # --- Metrics ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Workouts", total_workouts, "💪")
    col2.metric("Points", total_points, "⭐")
    col3.metric("Weekly Goal Progress", f"{weekly_progress}/{weekly_goal} min", "🔥")

    # --- Update Weekly Goal ---
    st.subheader("⚡ Set Your Weekly Goal")
    new_goal = st.number_input("Set your weekly goal (minutes)", min_value=10, max_value=1000, value=weekly_goal)
    if st.button("Update Goal"):
        update_weekly_goal(user_id, new_goal)
        st.session_state['user'] = get_user(username)
        st.success(f"Weekly goal updated to {new_goal} minutes!")
        st.experimental_rerun()

    # --- Log a Workout ---
    st.subheader("🏋️ Log a Workout")
    workout_types = {"Cardio": "🏃‍♂️", "Strength": "🏋️‍♀️", "Yoga": "🧘", "Other": "⚡"}
    workout_type = st.selectbox("Workout Type", list(workout_types.keys()))
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=180)
    if st.button("Log Workout"):
        log_workout(user_id, workout_type, duration)
        st.session_state['user'] = get_user(username)
        st.experimental_rerun()

    # --- Workout History ---
    st.subheader("📅 Workout History")
    if workouts:
        df = pd.DataFrame(workouts, columns=["Date", "Workout Type", "Duration (min)"])
        df["Icon"] = df["Workout Type"].map(workout_types)
        st.dataframe(df)
        st.line_chart(df.set_index("Date")["Duration (min)"])
    else:
        st.info("No workouts logged yet!")

    # --- Weekly Goal Progress Bar ---
    st.subheader("🎯 Weekly Goal Tracker")
    progress_percent = min(int((weekly_progress / weekly_goal) * 100), 100)
    st.progress(progress_percent)
    if progress_percent == 100:
        rain(["🎉", "🏆", "💪"])

    # --- Achievements ---
    st.subheader("🏆 Achievements")
    badges = get_achievements(user_id)
    if badges:
        for badge in badges:
            st.write(f"🎖️ {badge[0]} - {badge[1]}")
    else:
        st.info("No badges earned yet! Keep going!")

    # --- Leaderboard ---
    st.subheader("🏅 University Leaderboard")
    c.execute("SELECT id, username, points FROM users ORDER BY points DESC LIMIT 10")
    top_users = c.fetchall()
    leaderboard_data = []
    for idx, user_row in enumerate(top_users, start=1):
        uid, uname, pts = user_row
        c.execute("SELECT COUNT(*) FROM achievements WHERE user_id=?", (uid,))
        badge_count = c.fetchone()[0]
        emoji = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else ""
        leaderboard_data.append([f"{emoji} {uname}", pts, f"🎖️ {badge_count}"])
    leaderboard_df = pd.DataFrame(leaderboard_data, columns=["Username", "Points", "Badges"])
    st.table(leaderboard_df)

    # Current user rank
    c.execute("SELECT COUNT(*)+1 FROM users WHERE points>?", (total_points,))
    user_rank = c.fetchone()[0]
    st.info(f"Your Rank: #{user_rank} with {total_points} points")

    # --- Logout ---
    if st.button("Logout"):
        del st.session_state['user']
        st.experimental_rerun()
