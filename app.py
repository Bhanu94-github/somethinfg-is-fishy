import streamlit as st
st.set_page_config(page_title="Course App", layout="wide")
from student_dashboard import student_dashboard
from instructor_panel import instructor_dashboard
from admin_panel import admin_panel
from student_panel import student_login, student_register, student_forgot_password

# --------- Custom CSS for Glassmorphism ----------
st.markdown("""
    <style>
        body {
            background: url("https://images.unsplash.com/photo-1531746790731-6c087fecd65a?auto=format&fit=crop&w=1500&q=80") no-repeat center center fixed;
            background-size: cover;
        }

        .glass-container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.18);
            margin-top: 30px;
        }

        .main-title {
            text-align: center;
            font-size: 44px;
            font-weight: 700;
            color: #ffffff;
            text-shadow: 1px 1px 5px rgba(0, 0, 0, 0.6);
        }

        .subtitle {
            text-align: center;
            font-size: 20px;
            color: #ecf0f1;
            margin-top: -10px;
        }

        .section-title {
            text-align: center;
            font-size: 24px;
            color: #ecf0f1;
            margin-top: 30px;
            margin-bottom: 10px;
        }

        .stButton>button {
            background-color: rgba(255, 255, 255, 0.25);
            color: white;
            font-weight: 600;
            padding: 0.6rem 1rem;
            border-radius: 12px;
            border: none;
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
            transition: all 0.3s ease;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
        }

        .stButton>button:hover {
            background-color: rgba(255, 255, 255, 0.4);
            transform: scale(1.05);
        }

        .stRadio > div {
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

def main_app():
    # Redirect to respective dashboards if already logged in
    if st.session_state.get("student_logged_in"):
        student_dashboard()
        return
    elif st.session_state.get("instructor_logged_in"):
        instructor_dashboard()
        return
    elif st.session_state.get("admin_logged_in"):
        admin_panel()
        return

    # ---------- Header ----------
    st.markdown("<div class='main-title'>📚 Skill-Based Course Platform</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Empowering Students, Instructors, and Admins — All in One Place</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top: 10px;'>", unsafe_allow_html=True)

    # ---------- Panel Selector ----------
    st.markdown("<div class='section-title'>🔍 Choose Your Panel</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🎓 Student Panel", use_container_width=True):
            st.session_state["selected_panel"] = "student"

    with col2:
        if st.button("👨‍🏫 Instructor Panel", use_container_width=True):
            st.session_state["selected_panel"] = "instructor"

    with col3:
        if st.button("🛡️ Admin Panel", use_container_width=True):
            st.session_state["selected_panel"] = "admin"

    # ---------- Panel UI Display ----------
    panel = st.session_state.get("selected_panel")

    if panel:
        st.markdown("<div class='glass-container'>", unsafe_allow_html=True)

        if panel == "student":
            st.markdown("<h4 style='color:#A3E635;'>🎓 Student Access</h4>", unsafe_allow_html=True)
            nav = st.radio("Select Action", ["Login", "Register", "Forgot Password"], horizontal=True)
            if nav == "Login":
                student_login()
            elif nav == "Register":
                student_register()
            elif nav == "Forgot Password":
                student_forgot_password()

        elif panel == "instructor":
            st.markdown("<h4 style='color:#60A5FA;'>👨‍🏫 Instructor Access</h4>", unsafe_allow_html=True)
            instructor_dashboard()

        elif panel == "admin":
            st.markdown("<h4 style='color:#FB7185;'>🛡️ Admin Access</h4>", unsafe_allow_html=True)
            admin_panel()

        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main_app()
