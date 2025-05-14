import streamlit as st
import pandas as pd
import plotly.express as px
from utils import db
from datetime import datetime

def log_token_history(student_username, instructor_username, action, tokens_changed):
    db["token_logs"].insert_one({
        "student": student_username,
        "instructor": instructor_username,
        "action": action,
        "tokens_changed": tokens_changed,
        "timestamp": datetime.utcnow()
    })

def instructor_dashboard():
    access_col = db["access_students"]
    results_col = db["results"]

    if "instructor_logged_in" not in st.session_state or not st.session_state.instructor_logged_in:
        st.title("👨‍🏫 Instructor Panel")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            instructor = db["instructors"].find_one({"username": username, "password": password})
            if instructor:
                st.session_state.instructor_logged_in = True
                st.session_state.instructor_username = username
                st.success(f"Welcome, {username}")
                st.rerun()
            else:
                st.error("Invalid credentials.")
        return

    instructor_username = st.session_state["instructor_username"]
    st.title(f"🎧️ Instructor Dashboard - {instructor_username}")

    tab1, tab2, tab3 = st.tabs(["🎯 Token Management", "📊 Token Logs", "📈 Analytics"])

    # --------------------- Token Management ---------------------
    with tab1:
        st.subheader("👥 Approved Students")
        students = list(access_col.find({}))
        if not students:
            st.info("No approved students found.")
            return

        search_query = st.text_input("Search student by name or username").lower()
        filtered_students = [s for s in students if
                             search_query in s.get("username", "").lower() or
                             search_query in s.get("name", "").lower()]

        if st.button("🔁 Bulk Reset All Tokens to 10"):
            for s in filtered_students:
                username = s["username"]
                access_col.update_one(
                    {"username": username},
                    {
                        "$set": {"tokens": 10},
                        "$inc": {"exam_attempts": 1}
                    }
                )
                log_token_history(username, instructor_username, "Bulk Reset to 10", 10)
            st.success("All filtered students reset to 10 tokens.")
            st.rerun()

        for student in filtered_students:
            username = student["username"]
            name = student.get("name", "Unknown")
            tokens = student.get("tokens", 0)
            attempts = student.get("exam_attempts", 0)

            with st.expander(f"👤 {name} ({username})"):
                st.write(f"🎯 **Tokens**: `{tokens}`")
                st.write(f"🧪 **Exam Attempts**: `{attempts}`")
                col1, col2, col3 = st.columns([1, 1, 2])
                if col1.button("➕", key=f"inc_{username}"):
                    access_col.update_one({"username": username}, {"$inc": {"tokens": 1}})
                    log_token_history(username, instructor_username, "Token Increment", 1)
                    st.success(f"{username}: +1 token")
                    st.rerun()
                if col2.button("➖", key=f"dec_{username}"):
                    if tokens > 0:
                        access_col.update_one({"username": username}, {"$inc": {"tokens": -1}})
                        log_token_history(username, instructor_username, "Token Decrement", -1)
                        st.warning(f"{username}: -1 token")
                    else:
                        st.warning("Token already at 0.")
                    st.rerun()
                if col3.button("🔁 Reset to 10", key=f"reset_{username}"):
                    access_col.update_one(
                        {"username": username},
                        {
                            "$set": {"tokens": 10},
                            "$inc": {"exam_attempts": 1}
                        }
                    )
                    log_token_history(username, instructor_username, "Reset to 10", 10)
                    st.success(f"{username}: Reset and attempt incremented")
                    st.rerun()

    # --------------------- Token Logs ---------------------
    with tab2:
        st.subheader("📄 Token Action Logs")
        logs = list(db["token_logs"].find({"instructor": instructor_username}).sort("timestamp", -1).limit(50))
        if not logs:
            st.info("No logs found.")
        else:
            for log in logs:
                st.write(
                    f"🕒 `{log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}` | "
                    f"👤 **{log['student']}** | ✍️ {log['action']} | 🔢 Changed: `{log['tokens_changed']}`"
                )

    # --------------------- Analytics ---------------------
    with tab3:
        st.subheader("📈 Token Usage & Performance Analytics")

        token_data = [{"username": s["username"], "tokens_left": s.get("tokens", 0)} for s in students]
        token_df = pd.DataFrame(token_data)
        fig1 = px.bar(token_df, x="username", y="tokens_left", title="🎯 Tokens Left Per Student")
        st.plotly_chart(fig1, use_container_width=True)

        result_docs = list(results_col.find({}))
        if result_docs:
            score_data = []
            for r in result_docs:
                score_data.append({
                    "username": r.get("username", "unknown"),
                    "score": r.get("score", 0),
                    "timestamp": r.get("timestamp", datetime.utcnow()),
                    "skill": r.get("skill", "Unknown Skill")
                })

            score_df = pd.DataFrame(score_data)
            score_df["timestamp"] = pd.to_datetime(score_df["timestamp"])

            fig2 = px.line(score_df, x="timestamp", y="score", color="username",
                           title="📈 Assessment Scores Over Time")
            st.plotly_chart(fig2, use_container_width=True)

            st.markdown("### 🌝 Student Ranking (by Average Score)")
            summary_df = score_df.groupby("username").agg({
                "score": ["count", "mean", "max"]
            }).reset_index()
            summary_df.columns = ["Username", "Attempts", "Average Score", "Max Score"]
            summary_df = summary_df.sort_values(by="Average Score", ascending=False)
            st.dataframe(summary_df, use_container_width=True)

            st.markdown("### 🧐 Per-Student Skill Breakdown (Pie Chart)")
            selected_student = st.selectbox("Select a student", score_df["username"].unique())
            student_skill_df = score_df[score_df["username"] == selected_student]
            skill_summary = student_skill_df.groupby("skill")["score"].mean().reset_index()
            fig3 = px.pie(skill_summary, names="skill", values="score",
                          title=f"🎯 {selected_student} - Average Score Per Skill")
            st.plotly_chart(fig3, use_container_width=True)

            st.markdown("### ⚔️ Compare Two Students' Performance")
            students_unique = score_df["username"].unique().tolist()
            col1, col2 = st.columns(2)
            with col1:
                student1 = st.selectbox("Select Student 1", students_unique, key="student1")
            with col2:
                remaining_students = [s for s in students_unique if s != student1]
                student2 = st.selectbox("Select Student 2", remaining_students, key="student2")

            comp_df = score_df[score_df["username"].isin([student1, student2])]
            fig4 = px.bar(comp_df, x="skill", y="score", color="username", barmode="group",
                          title=f"🔍 Comparison: {student1} vs {student2} - Skill Scores")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No assessment results found in the database.")

    st.sidebar.markdown("---")
    if st.sidebar.button("🔒 Logout"):
        st.session_state.clear()
        st.switch_page("app.py")