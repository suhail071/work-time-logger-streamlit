import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import json

tz = pytz.timezone("Asia/Dubai")
current_time = datetime.now(tz).time()
spreadsheet_name = st.secrets["google"]["sheet_name"]

# ------------------ Google Sheets Auth ------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["google"]["service_account"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)
sheet = client.open(spreadsheet_name).sheet1

# ------------------ Data Helpers ------------------
def get_data():
    records = sheet.get_all_records()
    return pd.DataFrame(records)

def save_row(entry):
    sheet.append_row([entry[col] for col in ["Date", "From", "To", "Activity", "Description", "Status"]])

def delete_row(index):
    sheet.delete_rows(index + 2)  # +2 to account for header row and 0-index

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

# ------------------ Streamlit UI ------------------
st.set_page_config(page_title="Work Time Logger", layout="centered")
st.title("🕒 Work Time Logger")

# Toast after refresh
if "just_refreshed" not in st.session_state:
    st.session_state.just_refreshed = False

col1, col2 = st.columns([1, 9])
with col1:
    if st.button("🔁 Refresh"):
        st.session_state.just_refreshed = True
        st.rerun()

if st.session_state.just_refreshed:
    st.success("🥂 Cheers Sameh")
    st.session_state.just_refreshed = False

# Load data
df = get_data()
today = datetime.now(tz).date()
log_date = st.date_input("Select Date to View or Log", today)
df_day = df[df["Date"] == log_date.strftime("%Y-%m-%d")]
time_options = generate_time_options()
current_24h = current_time.strftime("%H:%M")

# ------------------ Check-in / Check-out ------------------
checkin_exists = not df_day[df_day["Activity"] == "Check-in"].empty
checkout_exists = not df_day[df_day["Activity"] == "Check-out"].empty

with st.expander("🕐 Check-in / Check-out"):
    if not checkin_exists:
        checkin_12h = st.selectbox("Check-in Time", [t["12h"] for t in time_options],
                                   index=[t["24h"] for t in time_options].index(current_24h), key="checkin")
        if st.button("✔️ Save Check-in"):
            save_row({
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
        checkout_12h = st.selectbox("Check-out Time", [t["12h"] for t in time_options],
                                    index=[t["24h"] for t in time_options].index(current_24h), key="checkout")
        if st.button("✔️ Save Check-out"):
            save_row({
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

# ------------------ Work Log Form ------------------
with st.form("log_form"):
    selected_from = st.selectbox("From Time", [t["12h"] for t in time_options],
                                 index=[t["24h"] for t in time_options].index(current_24h), key="from_time")

    selected_to = st.selectbox("To Time", [t["12h"] for t in time_options],
                               index=[t["24h"] for t in time_options].index(current_24h), key="to_time")

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
        save_row({
            "Date": log_date.strftime("%Y-%m-%d"),
            "From": datetime.strptime(selected_from, "%I:%M %p").strftime("%H:%M"),
            "To": datetime.strptime(selected_to, "%I:%M %p").strftime("%H:%M"),
            "Activity": activity,
            "Description": description,
            "Status": status
        })
        st.success("✅ Entry saved.")
        st.rerun()

# ------------------ View & Delete Logs ------------------
st.header("📋 Logs for " + log_date.strftime("%Y-%m-%d"))
df_day = get_data()
df_day = df_day[df_day["Date"] == log_date.strftime("%Y-%m-%d")]

if not df_day.empty:
    df_display = df_day.copy()
    df_display["From"] = pd.to_datetime(df_display["From"], format="%H:%M", errors="coerce").dt.strftime("%I:%M %p")
    df_display["To"] = pd.to_datetime(df_display["To"], format="%H:%M", errors="coerce").dt.strftime("%I:%M %p")

    csv = df_display.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", data=csv,
                       file_name=f"work_log_{log_date.strftime('%Y_%m_%d')}.csv", mime="text/csv")

    delete_row_id = None
    for idx, row in df_display.iterrows():
        with st.expander(f"{row['From']} – {row['To']} | {row['Activity']} [{row['Status']}]"):
            st.write(f"**Description:** {row['Description']}")
            if st.button("❌ Delete This Entry", key=f"del_{idx}"):
                delete_row_id = idx

    if delete_row_id is not None:
        delete_row(delete_row_id)
        st.success("✅ Entry deleted.")
        st.rerun()
else:
    st.info("No logs found for the selected date.")
