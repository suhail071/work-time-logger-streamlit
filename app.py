import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz

# === Config ===
FILE = "work_log.xlsx"
PASSWORD = "sameh@5233"

# === Timezone ===
tz = pytz.timezone("Asia/Dubai")
current_time = datetime.now(tz).time()

# === Session State ===
if "just_refreshed" not in st.session_state:
    st.session_state.just_refreshed = False
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# === Auth ===
def password_prompt():
    st.title("🔒 Work Time Logger Login")
    password_input = st.text_input("Enter password", type="password")
    if st.button("🔓 Login"):
        if password_input == PASSWORD:
            st.session_state.authenticated = True
            st.success("✅ Logged in successfully. Please click anywhere or refresh.")
        else:
            st.error("Incorrect password. Try again.")

if not st.session_state.authenticated:
    password_prompt()
    st.stop()

# === App Functions ===
def generate_time_options():
    times = []
    for h in range(24):
        for m in range(60):
            t = datetime.strptime(f"{h}:{m}", "%H:%M")
            times.append({"24h": t.strftime("%H:%M"), "12h": t.strftime("%I:%M %p")})
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

# === UI ===
st.set_page_config(page_title="Sameh's Work Time Logger", layout="centered")
st.title("🕒 Sameh's Work Time Logger")

col1, col2 = st.columns([1, 9])
with col1:
    if st.button("🔁 Refresh"):
        st.session_state.just_refreshed = True
        st.rerun()

if st.session_state.just_refreshed:
    st.success("🥂 Cheers Sameh")
    st.session_state.just_refreshed = False

# === Main Logic ===
today = datetime.now(tz).date()
log_date = st.date_input("Select Date to View or Log", today)
df = load_data()
filtered_df = df[df["Date"] == log_date.strftime("%Y-%m-%d")]
time_options = generate_time_options()
current_24h = current_time.strftime("%H:%M")
time_labels = [t["12h"] for t in time_options]
default_time = datetime.strptime(current_24h, "%H:%M").strftime("%I:%M %p")

# === Check-in/out ===
df_day = df[df["Date"] == log_date.strftime("%Y-%m-%d")]
checkin_exists = not df_day[df_day["Activity"] == "Check-in"].empty
checkout_exists = not df_day[df_day["Activity"] == "Check-out"].empty

with st.expander("🕐 Check-in / Check-out"):
    if not checkin_exists:
        checkin_12h = st.select_slider("Check-in Time", options=time_labels, value=default_time, key="checkin")
        if st.button("✔️ Save Check-in"):
            add_entry({
                "Date": log_date.strftime("%Y-%m-%d"),
                "From": datetime.strptime(checkin_12h, "%I:%M %p").strftime("%H:%M"),
                "To": datetime.strptime(checkin_12h, "%I:%M %p").strftime("%H:%M"),
                "Activity": "Check-in",
                "Description": "User checked in",
                "Status": "Closed"
            })
            st.success("✅ Check-in saved.")
            st.rerun()
    else:
        st.info("✅ Check-in already saved.")

    if not checkout_exists:
        checkout_12h = st.select_slider("Check-out Time", options=time_labels, value=default_time, key="checkout")
        if st.button("✔️ Save Check-out"):
            add_entry({
                "Date": log_date.strftime("%Y-%m-%d"),
                "From": datetime.strptime(checkout_12h, "%I:%M %p").strftime("%H:%M"),
                "To": datetime.strptime(checkout_12h, "%I:%M %p").strftime("%H:%M"),
                "Activity": "Check-out",
                "Description": "User checked out",
                "Status": "Closed"
            })
            st.success("✅ Check-out saved.")
            st.rerun()
    else:
        st.info("✅ Check-out already saved.")

# === Work log form ===
with st.form("log_form"):
    selected_from = st.select_slider("From Time", options=time_labels, value=default_time, key="from_time")
    selected_to = st.select_slider("To Time", options=time_labels, value=default_time, key="to_time")

    excluded = ["Check-in", "Check-out"]
    activity_pool = sorted(df[~df["Activity"].isin(excluded)]["Activity"].dropna().unique().tolist())
    activity_options = activity_pool + ["➕ Add New Activity"]

    activity_choice = st.selectbox("Select Activity", activity_options)
    activity = activity_choice
    if activity_choice == "➕ Add New Activity":
        activity = st.text_input("Enter New Activity").strip()

    description = st.text_input("Description")
    status = st.selectbox("Status", ["Open", "Closed", "Pending"])
    submitted = st.form_submit_button("✅ Save Entry")

    if submitted and activity:
        add_entry({
            "Date": log_date.strftime("%Y-%m-%d"),
            "From": datetime.strptime(selected_from, "%I:%M %p").strftime("%H:%M"),
            "To": datetime.strptime(selected_to, "%I:%M %p").strftime("%H:%M"),
            "Activity": activity,
            "Description": description,
            "Status": status
        })
        st.success("✅ Entry saved.")
        st.rerun()

# === View logs ===
st.header("📋 Logs for " + log_date.strftime("%Y-%m-%d"))
filtered_df = load_data()
filtered_df = filtered_df[filtered_df["Date"] == log_date.strftime("%Y-%m-%d")]

if not filtered_df.empty:
    display_df = filtered_df.copy()
    display_df["From"] = pd.to_datetime(display_df["From"], format="%H:%M", errors="coerce").dt.strftime("%I:%M %p")
    display_df["To"] = pd.to_datetime(display_df["To"], format="%H:%M", errors="coerce").dt.strftime("%I:%M %p")

    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", data=csv,
                       file_name=f"work_log_{log_date.strftime('%Y_%m_%d')}.csv", mime="text/csv")

    delete_row_id = None
    for idx, row in display_df.iterrows():
        with st.expander(f"{row['From']} – {row['To']} | {row['Activity']} [{row['Status']}]"):
            st.write(f"**Description:** {row['Description']}")
            if st.button("❌ Delete This Entry", key=f"del_{idx}"):
                delete_row_id = row.name

    if delete_row_id is not None:
        df = df.drop(index=delete_row_id)
        save_data(df)
        st.success("✅ Entry deleted.")
        st.rerun()
else:
    st.info("No logs found for the selected date.")
