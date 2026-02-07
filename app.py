import streamlit as st
import json
import os

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return {"water": 0, "steps": 0, "sleep": 0}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

st.title("💪 Fitness Tracker")

data = load_data()

water = st.number_input("Water Intake (L):", min_value=0.0, step=0.1)
steps = st.number_input("Daily Steps:", min_value=0, step=1)
sleep = st.number_input("Sleep Hours:", min_value=0.0, step=0.1)

if st.button("Add Entry"):
    data["water"] += water
    data["steps"] += steps
    data["sleep"] += sleep
    save_data(data)
    st.success("Entry added!")

st.subheader("Today's Summary")
st.write(f"💧 Water: {data['water']} L")
st.write(f"👟 Steps: {data['steps']}")
st.write(f"🛌 Sleep: {data['sleep']} hrs")

if st.button("Reset Day"):
    data = {"water": 0, "steps": 0, "sleep": 0}
    save_data(data)
    st.warning("Data reset!")
