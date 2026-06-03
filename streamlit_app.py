import streamlit as st
import requests
import os
import pandas as pd

st.set_page_config(page_title="KnowThyself", page_icon="🧠", layout="centered")

# API_URL = "http://localhost:8000"

# Read the backend URL from environment variables if running in Docker, otherwise fallback to localhost
# API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

API_URL = os.getenv("BACKEND_URL", "https://knowthyself-backend-799604771720.us-central1.run.app")
# API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
GCS_BUCKET = os.getenv("GCS_BUCKET", "knowthyself-data")

def show_login():
    st.title("KnowThyself")
    name = st.text_input("Enter your User ID")
    if st.button("Submit"):
        if name:
            st.session_state.user_id = name
            st.rerun()
        else:
            st.error("User ID cannot be blank.")

def show_track_selection():
    st.title("Choose your Track")
    track = st.selectbox("Pick one track", ["Fitness", "Habits", "Relationships"])
    if st.button("Submit"):
        if track:
            st.session_state.track = track
            requests.post(f"{API_URL}/user", json={
                "user_id": st.session_state.user_id,
                "track": track.lower()
            })
            st.rerun()
        else:
            st.error("One track has to be chosen.")


def show_data_form():
    if "form_key" not in st.session_state:
        st.session_state.form_key = 0
    if st.session_state.track.lower() == "fitness":
        with st.form(f"Fitness Data {st.session_state.form_key}"):
            date = st.date_input("Date")
            exercise = st.selectbox("Exercise", ["Squat", "Deadlift", "Bench Press", "Pull up", "Other"])
            sets = st.number_input("Sets", min_value=0, step=1, format="%d", value=None, placeholder="0")
            reps = st.number_input("Reps", min_value=0, step=1, format="%d", value=None, placeholder="0")
            weight_kg = st.number_input("Weight (kgs)", min_value=0.0, step=0.5, format="%.1f", value=None, placeholder="0.0")
            body_weight = st.number_input("Body weight (kgs)", min_value=0.0, step=0.1, format="%.1f", value=None, placeholder="0.0")
            sleep_hours = st.number_input("Sleep Hours", min_value=0, max_value=24, step=1, format="%d", value=None, placeholder="0")
            energy_level = st.number_input("Energy level (0-10)", min_value=0, max_value=10, step=1, format="%d", value=None, placeholder="0")
            submitted = st.form_submit_button("Submit")
            if submitted:
                if not date or sets == 0 or reps == 0 or weight_kg == 0.0 or body_weight == 0.0:
                    st.error("Please fill all required fields.")
                else:
                    data = {
                        "date": str(date),
                        "exercise": exercise,
                        "sets": sets,
                        "reps": reps,
                        "weight_kg": weight_kg,
                        "body_weight": body_weight,
                        "sleep_hours": sleep_hours,
                        "energy_level": energy_level
                    }
                    response = requests.post(f"{API_URL}/data/fitness", json={
                        "user_id": st.session_state.user_id,
                        "track": st.session_state.track.lower(),
                        "data": data
                    })
                    if response.status_code == 200:
                        st.session_state.data_logged = True
                        st.session_state.form_key += 1
                        st.rerun()
                    else:
                        st.error("Failed to log data.")

    if st.session_state.track.lower() == "habits":
        
        # Try to read existing habits
        csv_path = f"gs://{GCS_BUCKET}/habits/{st.session_state.user_id}.csv"
        try:
            df = pd.read_csv(csv_path, skipinitialspace=True, on_bad_lines='skip')
            existing_habits = df["habit"].unique().tolist()
            existing_habits.append("Add new habit")
            habit_choice = st.selectbox("Habit", existing_habits)
            if habit_choice == "Add new habit":
                habit = st.text_input("Enter new habit name")
            else:
                habit = habit_choice
        except Exception:
            habit = st.text_input("Habit")
            
        with st.form(f"Habits Data {st.session_state.form_key}"):
            date = st.date_input("Date")
            completed = st.number_input("Completed (0 or 1)", min_value=0, max_value=1, step=1, format="%d", value=None, placeholder="0")
            score = st.number_input("Score (0-10)", min_value=0, max_value=10, step=1, format="%d", value=None, placeholder="0")
            notes = st.text_input("Notes")
            submitted = st.form_submit_button("Submit")
            if submitted:
                if not date or not habit or completed is None:
                    st.error("Please fill all required fields.")
                else:
                    data = {"date": str(date),
                            "habit": habit,
                            "completed": completed, 
                            "score": score, 
                            "notes": notes
                        }
                    response = requests.post(f"{API_URL}/data/habits", json={
                        "user_id": st.session_state.user_id,
                        "track": st.session_state.track.lower(),
                        "data": data
                    })
                    if response.status_code == 200:
                        st.session_state.data_logged = True
                        st.session_state.form_key += 1
                        st.rerun()
                    else:
                        st.error("Failed to log data.")


def show_coaching():
    st.title(f"{st.session_state.user_id} - {st.session_state.track.capitalize()}")
    
    st.markdown("""
<style>
[data-testid="stSidebar"] {
    transition: none !important;
}
.stSpinner {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 🧠 System State")
        st.write(f"**User:** {st.session_state.user_id}")
        st.write(f"**Track:** {st.session_state.track.capitalize()}")

        if st.session_state.get("messages"):
            try:
                ins_resp = requests.get(
                    f"{API_URL}/insights/{st.session_state.user_id}/{st.session_state.track.lower()}"
                )
                if ins_resp.status_code == 200:
                    data = ins_resp.json()
                    status = data.get("status", {})
                    insights = data.get("insights", "")

                    st.markdown("---")
                    st.markdown("#### 📊 Current Session")
                    st.write(f"Session: **{status.get('session_no', 1)}**")
                    st.write(f"Exchanges this session: **{status.get('exchange_count', 0)}/{status.get('n_exchanges', 5)}**")
                    st.write(f"Next summary in: **{status.get('exchanges_until_summary', 5)} messages**")

                    if insights and insights != "No relevant insight found.":
                        st.markdown("---")
                        st.markdown("#### 💡 Past Session Insights")
                        for line in insights.split("\n"):
                            if line.strip():
                                st.write(f"• {line}")
            except Exception as e:
                st.caption(f"Insights unavailable: {e}")

            try:
                mem_resp = requests.get(
                    f"{API_URL}/memory/{st.session_state.user_id}/{st.session_state.track.lower()}"
                )
                if mem_resp.status_code == 200:
                    memory = mem_resp.json().get("memory", "")
                    if memory and memory not in ["No past session memory found.", "Memory unavailable."]:
                        st.markdown("---")
                        st.markdown("#### 🗂 Past Session Memory")
                        st.caption(memory[:300] + "..." if len(memory) > 300 else memory)
            except Exception as e:
                st.caption(f"Memory unavailable: {e}")

        st.markdown("---")
        if st.button("Change Track"):
            del st.session_state.track
            st.rerun()

    if st.session_state.get("data_logged"):
        st.success("Data logged successfully!")
        st.session_state.data_logged = False

    if "messages" not in st.session_state:
        st.session_state.messages = []
    messages = st.session_state.messages
    if st.session_state.track.lower() in ["fitness", "habits"]:
        add_data = st.toggle("Add Data")
        if add_data:
            show_data_form()
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    if prompt := st.chat_input("Ask your coach anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Your coach is thinking..."):
            response = requests.post(f"{API_URL}/chat", json={
                "user_id": st.session_state.user_id,
                "track": st.session_state.track.lower(),
                "message": prompt
            })
            reply = response.json()["response"]
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()


# Main routing
if "user_id" not in st.session_state:
    show_login()
elif "track" not in st.session_state:
    show_track_selection()
else:
    show_coaching()
