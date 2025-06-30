import streamlit as st
import pandas as pd
import os
from datetime import datetime

FILE = "work_log.xlsx"

# Load or create Excel file
def load_data():
    if os.path.exists(FILE):
        return pd.read_excel(FILE)
    else:
        df = pd.DataFrame(columns=["Date", "From", "To", "Activity", "Notes"])
        df.to_excel(FILE, index=False)
        return df

def save_data(df):
    df.to_excel(FILE, index=False)

def add_entry(entry):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    save_data(df)

# Page setup
st.set_page_config(page_title="Work Time Logger", layout="centered")
st.title("🕒 Work Time Logger")

# Input Section
with st.form("log_form"):
    today = datetime.now().date()
    date = st.date_input("Date", today)
    from_time = st.time_input("From Time")
    to_time = st.time_input("To Time")

    df = load_data()
    existing_activities = sorted(df["Activity"].dropna().unique().tolist())
    activity_options = existing_activities + ["➕ Add New Activity"]
    activity_choice = st.selectbox("Select Activity", options=activity_options, key="activity_select")

    new_activity = ""
    if activity_choice == "➕ Add New Activity":
        new_activity = st.text_input("Enter New Activity", key="new_activity_input")
        activity = new_activity.strip()
    else:
        activity = activity_choice

    notes = st.text_input("Notes (optional)")
    submitted = st.form_submit_button("✅ Save Entry")

    if submitted:
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
            add_entry(entry)
            st.success("✅ Entry saved successfully!")

# View & Delete Section
st.header("📋 View & Manage Logs")

log_date = st.date_input("Select Date to View Logs", today, key="log_date")
df = load_data()
filtered_df = df[df["Date"] == log_date.strftime("%Y-%m-%d")]

# Download CSV button
if not filtered_df.empty:
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Logs as CSV",
        data=csv,
        file_name=f"work_log_{log_date.strftime('%Y_%m_%d')}.csv",
        mime='text/csv',
    )

# Safe deletion handling
delete_target = None

if not filtered_df.empty:
    for display_idx, row in filtered_df.iterrows():
        real_idx = row.name
        with st.expander(f"{row['From']} – {row['To']} | {row['Activity']}"):
            st.write(f"**Notes:** {row['Notes']}")
            if st.button("❌ Delete This Entry", key=f"delete_{real_idx}"):
                delete_target = real_idx

    if delete_target is not None:
        df.drop(index=delete_target, inplace=True)
        save_data(df)
        st.success("✅ Entry deleted.")
        st.rerun()
else:
    st.info("No logs found for the selected date.")
