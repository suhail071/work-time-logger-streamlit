import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz

FILE = "work_log.xlsx"
tz = pytz.timezone("Asia/Dubai")
current_time = datetime.now(tz).time()


def generate_time_options():
    times = []
    for h in range(24):
        for m in range(60):
            t = datetime.strptime(f"{h}:{m}", "%H:%M")
            times.append(t.strftime("%I:%M %p"))
    return times


def load_data():
    if os.path.exists(FILE):
        return pd.read_excel(FILE)
    else:
        df = pd.DataFrame(columns=["Date", "From", "To", "Activity", "Description", "Status"])
        df.to_excel(FILE, index=False)
        return df


def save_data(df):
    df.to_excel(FILE, index=False)


def add_entry(entry):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    save_data(df)


# Streamlit UI
st.set_page_config(page_title="Work Time Logger", layout="centered")
st.title("🕒 Work Time Logger")

today = datetime.now(tz).date()
log_date = st.date_input("Select Date to View or Log", today)

df = load_data()
filtered_df = df[df["Date"] == log_date.strftime("%Y-%m-%d")]
time_options = generate_time_options()
current_formatted = current_time.strftime("%I:%M %p")

# ----------------- CHECK-IN / CHECK-OUT -----------------
checkin_exists = not filtered_df[filtered_df["Activity"] == "Check-in"].empty
checkout_exists = not filtered_df[filtered_df["Activity"] == "Check-out"].empty

with st.expander("🕐 Check-in / Check-out"):
    if not checkin_exists:
        selected_checkin = st.selectbox("Check-in Time", time_options, index=time_options.index(current_formatted), key="checkin")
        if st.button("✔️ Save Check-in"):
            entry = {
                "Date": log_date.strftime("%Y-%m-%d"),
                "From": selected_checkin,
                "To": selected_checkin,
                "Activity": "Check-in",
                "Description": "User checked in",
                "Status": "Closed"
            }
            add_entry(entry)
            st.success("✅ Check-in saved.")
            st.rerun()
    else:
        st.info("✅ Check-in already saved for this date.")

    if not checkout_exists:
        selected_checkout = st.selectbox("Check-out Time", time_options, index=time_options.index(current_formatted), key="checkout")
        if st.button("✔️ Save Check-out"):
            entry = {
                "Date": log_date.strftime("%Y-%m-%d"),
                "From": selected_checkout,
                "To": selected_checkout,
                "Activity": "Check-out",
                "Description": "User checked out",
                "Status": "Closed"
            }
            add_entry(entry)
            st.success("✅ Check-out saved.")
            st.rerun()
    else:
        st.info("✅ Check-out already saved for this date.")

# ----------------- MAIN WORK LOG FORM -----------------
with st.form("log_form"):
    selected_from = st.selectbox("From Time", time_options, index=time_options.index(current_formatted))
    selected_to = st.selectbox("To Time", time_options, index=time_options.index(current_formatted))

    existing_activities = sorted(df["Activity"].dropna().unique().tolist())
    activity_options = existing_activities + ["➕ Add New Activity"]
    activity_choice = st.selectbox("Select Activity", options=activity_options, key="activity_select")

    new_activity = ""
    if activity_choice == "➕ Add New Activity":
        new_activity = st.text_input("Enter New Activity", key="new_activity_input")
        activity = new_activity.strip()
    else:
        activity = activity_choice

    description = st.text_input("Description")
    status = st.selectbox("Status", options=["Open", "Closed", "Pending"])
    submitted = st.form_submit_button("✅ Save Entry")

    if submitted:
        if not activity:
            st.error("Please select or enter an activity.")
        else:
            entry = {
                "Date": log_date.strftime("%Y-%m-%d"),
                "From": selected_from,
                "To": selected_to,
                "Activity": activity,
                "Description": description,
                "Status": status
            }
            add_entry(entry)
            st.success("✅ Entry saved successfully!")
            st.rerun()

# ----------------- VIEW & MANAGE -----------------
st.header("📋 Logs for " + log_date.strftime("%Y-%m-%d"))
filtered_df = load_data()
filtered_df = filtered_df[filtered_df["Date"] == log_date.strftime("%Y-%m-%d")]

if not filtered_df.empty:
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Logs as CSV",
        data=csv,
        file_name=f"work_log_{log_date.strftime('%Y_%m_%d')}.csv",
        mime='text/csv',
    )

    delete_target = None
    for display_idx, row in filtered_df.iterrows():
        real_idx = row.name
        with st.expander(f"{row['From']} – {row['To']} | {row['Activity']} [{row['Status']}]"):
            st.write(f"**Description:** {row['Description']}")
            if st.button("❌ Delete This Entry", key=f"delete_{real_idx}"):
                delete_target = real_idx

    if delete_target is not None:
        df.drop(index=delete_target, inplace=True)
        save_data(df)
        st.success("✅ Entry deleted.")
        st.rerun()
else:
    st.info("No logs found for the selected date.")
