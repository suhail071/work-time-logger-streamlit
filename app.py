import streamlit as st
import pandas as pd
import os
from datetime import datetime

FILE = "work_log.xlsx"

# Load or create Excel
def load_data():
    if os.path.exists(FILE):
        return pd.read_excel(FILE)
    else:
        df = pd.DataFrame(columns=["Date", "From", "To", "Activity", "Notes"])
        df.to_excel(FILE, index=False)
        return df

def save_entry(entry):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_excel(FILE, index=False)

st.set_page_config(page_title="Work Time Logger", layout="centered")
st.title("🕒 Work Time Logger")

today = datetime.now().date()
date = st.date_input("Date", today)
from_time = st.time_input("From Time")
to_time = st.time_input("To Time")

df = load_data()
existing_activities = sorted(df["Activity"].dropna().unique().tolist())
activity = st.selectbox("Select Activity", options=existing_activities + ["➕ Add New Activity"])

if activity == "➕ Add New Activity":
    new_activity = st.text_input("Enter New Activity")
    if new_activity:
        activity = new_activity

notes = st.text_input("Notes (optional)")

if st.button("Save Entry"):
    if not activity:
        st.error("Please select or enter an activity.")
    else:
        entry = {
            "Date": date.strftime("%Y-%m-%d"),
            "From": from_time.strftime("%I:%M %p"),
            "To": to_time.strftime("%I:%M %p"),
            "Activity": activity,
            "Notes": notes,
        }
        save_entry(entry)
        st.success("✅ Entry saved successfully!")

with st.expander("📋 Show All Logs"):
    st.dataframe(load_data())
