import streamlit as st
from utils import db
from datetime import datetime

# MongoDB collections
reg_col = db["student_registrations"]
access_col = db["access_students"]

def student_login():
    st.subheader("🔐 Student Login")
    username = st.text_input("Username", key="stu_login_user")
    password = st.text_input("Password", type="password", key="stu_login_pass")

    if st.button("Login", key="stu_login_btn"):
        user = access_col.find_one({"username": username, "password": password})
        if user:
            access_col.update_one(
                {"username": username},
                {"$set": {"last_login": datetime.utcnow(), "is_logged_in": True}}
            )
            st.session_state.student_logged_in = True
            st.session_state.student_username = username
            st.success(f"✅ Welcome {username}!")
            st.rerun()
        else:
            st.error("❌ Invalid credentials or not approved yet.")


def student_register():
    st.subheader("📝 Student Registration")
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    role = "student"

    if st.button("Register"):
        if not all([name, email, phone, username, password, confirm_password]):
            st.warning("⚠️ Please fill in all fields.")
        elif password != confirm_password:
            st.error("❌ Passwords do not match.")
        elif reg_col.find_one({"email": email}):
            st.error("❌ Email already registered.")
        elif reg_col.find_one({"username": username}):
            st.error("❌ Username already taken.")
        else:
            reg_col.insert_one({
                "name": name,
                "email": email,
                "phone": phone,
                "username": username,
                "password": password,
                "role": role
            })
            st.success("✅ Registration successful! Await admin approval.")
            st.balloons()


def student_forgot_password():
    st.subheader("🔄 Reset Password")
    username = st.text_input("Enter your username", key="forgot_user")
    new_password = st.text_input("New Password", type="password", key="forgot_pass")
    confirm_new = st.text_input("Confirm New Password", type="password", key="forgot_conf")

    if st.button("Reset Password"):
        user = access_col.find_one({"username": username})
        if not user:
            st.error("❌ Username not found or not approved.")
        elif new_password != confirm_new:
            st.error("❌ Passwords do not match.")
        else:
            access_col.update_one(
                {"username": username},
                {"$set": {"password": new_password}}
            )
            st.success("✅ Password reset successfully.")
st.balloons()