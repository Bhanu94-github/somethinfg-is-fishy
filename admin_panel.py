import streamlit as st
import pandas as pd
from bson.objectid import ObjectId
from utils import db

reg_col = db["student_registrations"]
access_col = db["access_students"]
not_access_col = db["not_access_students"]
course_col = db["courses"]
logs_col = db["instructor_logs"]

def admin_login():
    st.markdown("""
        <div style='text-align:center; padding: 1rem;'>
            <h2 style='color:#2c3e50;'>🛡️ Admin Login</h2>
        </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Admin Username", key="admin_username_input")
    password = st.text_input("Admin Password", type="password", key="admin_password_input")

    if st.button("Login", key="admin_login_btn"):
        if username == "admin" and password == "admin123":
            st.session_state["admin_logged_in"] = True
            st.session_state["admin_user"] = username
            st.success("✅ Logged in as Admin")
            st.rerun()
        else:
            st.error("❌ Invalid admin credentials.")

def admin_panel():
    if not st.session_state.get("admin_logged_in"):
        admin_login()
        return

    # Admin Dashboard
    st.markdown("""
        <div style='text-align:center; padding: 1rem;'>
            <h1 style='color:#2c3e50;'>🛡️ Admin Dashboard</h1>
            <p style='color:#7f8c8d;'>Manage student and course approvals efficiently</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("📈 Dashboard Summary")
    st.metric("📝 Pending Students", len(list(reg_col.find({}))))
    st.metric("✅ Approved Students", len(list(access_col.find({}))))
    st.metric("❌ Rejected Students", len(list(not_access_col.find({}))))

    st.markdown("<hr>", unsafe_allow_html=True)
    pending = list(reg_col.find({}))
    if not pending:
        st.info("🎉 No new registrations to approve.")
    else:
        st.markdown("### 📋 Pending Student Approvals")
        for i, user in enumerate(pending):
            with st.expander(f"👤 {user['name']} ({user['email']})"):
                name = st.text_input("Name", user["name"], key=f"name_{user['_id']}_{i}")
                email = st.text_input("Email", user["email"], key=f"email_{user['_id']}_{i}")
                phone = st.text_input("Phone", user["phone"], key=f"phone_{user['_id']}_{i}")
                username = st.text_input("Username", user["username"], key=f"username_{user['_id']}_{i}")

                if st.button("💾 Save Changes", key=f"save_{user['_id']}_{i}"):
                    reg_col.update_one(
                        {"_id": ObjectId(user["_id"])},
                        {"$set": {
                            "name": name,
                            "email": email,
                            "phone": phone,
                            "username": username
                        }}
                    )
                    st.success("✅ Student details updated successfully.")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve", key=f"approve_{user['_id']}_{i}"):
                        access_col.insert_one(user)
                        reg_col.delete_one({"_id": ObjectId(user["_id"])})
                        st.toast(f"✅ Approved: {user['username']}")

                with col2:
                    if st.button("❌ Reject", key=f"reject_{user['_id']}_{i}"):
                        not_access_col.insert_one(user)
                        reg_col.delete_one({"_id": ObjectId(user["_id"])})
                        st.warning(f"{user['name']} has been rejected.")

    st.markdown("<hr>", unsafe_allow_html=True)
    with st.expander("✅ Approved Students"):
        approved = list(access_col.find({}))
        for user in approved:
            st.markdown(f"- **{user['name']}** ({user['email']})")
        if approved:
            df = pd.DataFrame(approved)
            df = df.drop(columns=["_id"]) if "_id" in df.columns else df
            st.download_button("📥 Download CSV", df.to_csv(index=False), "approved_students.csv", "text/csv")

    with st.expander("❌ Rejected Students"):
        rejected = list(not_access_col.find({}))
        for user in rejected:
            st.markdown(f"- **{user['name']}** ({user['email']})")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("📘 Course Management")
    pending_courses = list(course_col.find({"status": "pending"}))
    approved_courses = list(course_col.find({"status": "approved"}))
    rejected_courses = list(course_col.find({"status": "rejected"}))

    if pending_courses:
        st.markdown("### ⏳ Pending Course Approvals")
        for i, course in enumerate(pending_courses):
            with st.expander(f"{course['title']} by {course['instructor']}"):
                st.write(course.get("description", "No description provided."))
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve Course", key=f"approve_course_{course['_id']}_{i}"):
                        course_col.update_one({"_id": ObjectId(course["_id"])}, {"$set": {"status": "approved"}})
                        st.success(f"Approved course: {course['title']}")
                with col2:
                    if st.button("❌ Reject Course", key=f"reject_course_{course['_id']}_{i}"):
                        course_col.update_one({"_id": ObjectId(course["_id"])}, {"$set": {"status": "rejected"}})
                        st.warning(f"Rejected course: {course['title']}")
    else:
        st.info("✅ No pending courses for approval.")

    with st.expander("📗 Approved Courses"):
        for course in approved_courses:
            st.markdown(f"- **{course['title']}** by {course['instructor']}")

    with st.expander("📕 Rejected Courses"):
        for course in rejected_courses:
            st.markdown(f"- **{course['title']}** by {course['instructor']}")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("📜 Instructor Activity Logs")
    logs = list(logs_col.find().sort("timestamp", -1))
    for log in logs[:50]:
        st.markdown(f"🕒 [{log['timestamp']}] **{log['username']}** - {log['action']}")

    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("🔒 Logout", key="admin_logout"):
        st.session_state.pop("admin_logged_in", None)
        st.session_state.pop("admin_user", None)
        st.success("👋 Logged out successfully.")
        st.rerun()
