import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Hustler OS", layout="wide")

# --- DARK THEME CUSTOM CSS ---
st.markdown("""
    <style>
    /* Force Dark Backgrounds */
    .stApp, [data-testid="stSidebar"] {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #FF4B4B; /* Red accents for a high-energy "Lock-In" feel */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Metric Card */
    .metric-card {
        background-color: #262730;
        padding: 25px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #464646;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }
    
    /* Checkbox Text */
    .stCheckbox label {
        color: #E0E0E0 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏹 Welcome Blaze " )


# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3022/3022215.png", width=100) # Optional icon
    month = st.selectbox("Current Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
    day = st.number_input("Day", min_value=1, max_value=31, value=datetime.now().day)
    st.markdown("---")
    st.info("No Mobile until 10 AM. No junk food. Total discipline.")

# --- HABITS ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 🕋 Spiritual")
    fajr = st.checkbox("Fajr Prayer")
    dhuhr = st.checkbox("Dhuhr Prayer")
    asr = st.checkbox("Asr Prayer")
    maghrib = st.checkbox("Maghrib Prayer")
    isha = st.checkbox("Isha Prayer")
    quran = st.checkbox("Quran (1 Para)")

with col2:
    st.markdown("#### 🥗 Nutrition (Bulk)")
    meal1 = st.checkbox("Morning Bulking Shake")
    meal2 = st.checkbox("University Lunch (Heavy)")
    meal3 = st.checkbox("Post-Gym Dinner")
    water = st.checkbox("3L Water Intake")

with col3:
    st.markdown("#### 💻 Grind & Strength")
    stretch = st.checkbox("Fresh & Stretching")
    skill1 = st.checkbox("PHP / Project (7pm)")
    cali = st.checkbox("Calisthenics Session")
    skill2 = st.checkbox("Deep Work (10pm)")

# --- CALCULATION ---
tasks = [fajr, dhuhr, asr, maghrib, isha, quran, meal1, meal2, meal3, water, stretch, skill1, cali, skill2]
score = int((sum(tasks) / len(tasks)) * 100)

st.markdown("---")

# --- VISUALIZATION ---
left, right = st.columns([1, 2])

with left:
    st.markdown(f"""
        <div class="metric-card">
            <p style='color: #888;'>DAILY DISCIPLINE</p>
            <h1 style='font-size: 60px; margin: 0;'>{score}%</h1>
        </div>
    """, unsafe_allow_html=True)

with right:
    # Gauge Chart for Dark Mode
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        gauge = {
            'axis': {'range': [None, 100], 'tickcolor': "white"},
            'bar': {'color': "#FF4B4B"},
            'bgcolor': "#262730",
            'steps': [
                {'range': [0, 50], 'color': '#444'},
                {'range': [50, 80], 'color': '#666'},
                {'range': [80, 100], 'color': '#888'}
            ],
        }
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=350)
    st.plotly_chart(fig, use_container_width=True)