import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz

FILE = "work_log.xlsx"
tz = pytz.timezone("Asia/Dubai")
current_time = datetime.now(tz).time()

# Session state for refresh toast
if "just_refreshed" not in st.session_state:
    st.session_state.just_refreshed = False


def generate_time_options():
    times = []
    for h in range(24):
        for m in range(60):
            t = datetime.strptime(f"{h}:{m}", "%H:%M")
            times.append({
                "24h": t.strftime("%H:%M"),
                "12h": t.strftime("%I:%M %p")
            })
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

# 🔁 Manual Refresh Button
col1, col2 = st.columns([1, 9])
with col1:
    if st.button("🔁 Refresh"):
        st.session_state.just_refreshed = True
        st.rerun()

if st.session_state.just_refreshed:
    st.success("🥂 Cheers Sameh")
    st.session_state.just_refreshed = False

# ----------------- INIT -----------------
today = datetime.now(tz).date()
log_date = st.date_input("Select Date to View or Log", today)
df = load_data()
filtered_df = df[df["Date"] == log_date.strftime("%Y-%m-%d")]

time_options = generate_time_options()
current_24h = current_time.strftime("%H:%M")

# ----------------- CHECK-IN / CHECK-OUT -----------------
checkin_exists = not filtered_df[filtered_df["Activity"] == "Check-in"].empty
checkout_exists = not filtered_df[filtered_df["Activity"] == "Check-out"].empty

with st.expander("🕐 Check-in / Check-out"):
    if not checkin_exists:
        checkin_12h = st.selectbox("Check-in Time",
                                   [t["12h"] for t in time_options],
                                   index=[t["24h"] for t in time_options].index(current_24h),
                                   key="checkin")

        if st.button("✔️ Save Check-in"):
            entry = {
                "Date": log_date.strftime("%Y-%m-%d"),
                "From": datetime.strptime(checkin_12h, "%I:%M %p").strftime("%H:%M"),
                "To": datetime.strptime(checkin_12h, "%I:%M %p").strftime("%H:%M"),
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
        checkout_12h = st.selectbox("Check-out Time",
                                    [t["12h"] for t in time_options],
                                    index=[t["24h"] for t in time_options].index(current_24h),
                                    key="checkout")

        if st.button("✔️ Save Check-out"):
            entry = {
                "Date": log_date.strftime("%Y-%m-%d"),
                "From": datetime.strptime(checkout_12h, "%I:%M %p").strftime("%H:%M"),
                "To": datetime.strptime(checkout_12h, "%I:%M %p").strftime("%H:%M"),
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
    selected_from = st.selectbox("From Time",
                                 [t["12h"] for t in time_options],
                                 index=[t["24h"] for t in time_options].index(current_24h),
                                 key="from_time")

    selected_to = st.selectbox("To Time",
                               [t["12h"] for t in time_options],
                               index=[t["24h"] for t in time_options].index(current_24h),
                               key="to_time")

    excluded = ["Check-in", "Check-out"]
    activity_pool = df[~df["Activity"].isin(excluded)]["Activity"].dropna().unique().tolist()
    activity_options = sorted(activity_pool) + ["➕ Add New Activity"]

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
                "From": datetime.strptime(selected_from, "%I:%M %p").strftime("%H:%M"),
                "To": datetime.strptime(selected_to, "%I:%M %p").strftime("%H:%M"),
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
    display_df = filtered_df.copy()

    # Safely convert and format 'From' and 'To' columns
    display_df["From"] = pd.to_datetime(display_df["From"], format="%H:%M", errors="coerce")
    display_df["To"] = pd.to_datetime(display_df["To"], format="%H:%M", errors="coerce")
    display_df = display_df.dropna(subset=["From", "To"])

    display_df["From"] = display_df["From"].dt.strftime("%I:%M %p")
    display_df["To"] = display_df["To"].dt.strftime("%I:%M %p")

    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Logs as CSV",
        data=csv,
        file_name=f"work_log_{log_date.strftime('%Y_%m_%d')}.csv",
        mime='text/csv',
    )

    delete_target = None
    for display_idx, row in display_df.iterrows():
        real_idx = row.name
        with st.expander(f"{row['From']} – {row['To']} | {row['Activity']} [{row['Status']}]"):
            st.write(f"**Description:** {row['Description']}")
            if st.button("❌ Delete This Entry", key=f"delete_{real_idx}"):
                delete_target = real_idx

    if delete_target is not None:
        df = df.drop(index=delete_target)
        save_data(df)
        st.success("✅ Entry deleted.")
        st.rerun()
else:
    st.info("No logs found for the selected date.")
