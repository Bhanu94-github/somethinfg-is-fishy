import streamlit as st
from utils import db
from bson import ObjectId
import uuid
import random
import spacy
import PyPDF2
import docx
from db_utils import get_all_questions
from datetime import datetime

def student_dashboard():
    access_col = db["access_students"]
    course_col = db["courses"]
    content_col = db["course_content"]
    enrollments_col = db["enrollments"]
    purchases_col = db["purchases"]
    usage_log_col = db["token_usage_logs"]

    username = st.session_state.get("student_username")
    user = access_col.find_one({"username": username})

    if not user:
        st.error("User not found. Please login again.")
        st.stop()

    # Initialize token field if missing
    if "tokens" not in user:
        access_col.update_one({"username": username}, {"$set": {"tokens": 10}})
        user["tokens"] = 10

    st.sidebar.title("📚 Student Panel")
    menu = st.sidebar.radio("Menu", ["Home", "Courses", "My Courses", "AI Modules", "Settings"])

    st.markdown(f"""
        <h2 style='text-align:center;'>🎓 Welcome, {user['name']}</h2>
        <hr>
    """, unsafe_allow_html=True)

    if menu == "Home":
        st.subheader("🏠 Dashboard Overview")
        st.write("### 📧 Email:", user["email"])
        st.write("### 👤 Username:", user["username"])
        st.write("### 📞 Phone:", user.get("phone", "N/A"))
        st.write(f"### 🎯 AI Tokens Remaining: `{user.get('tokens', 0)}`")

    elif menu == "Courses":
        st.subheader("📘 Browse Available Courses")
        courses = list(course_col.find({}))
        for course in courses:
            with st.expander(f"{course['title']} by {course['instructor']}"):
                st.write(course.get("description", "No description provided."))
                is_paid = course.get("price", 0) > 0
                enrollment = enrollments_col.find_one({"username": username, "course_id": course["_id"]})

                if not enrollment:
                    if is_paid:
                        st.button("Coming Soon (Paid)", key=f"coming_soon_{course['_id']}", disabled=True)
                    else:
                        if st.button("Enroll (Free)", key=f"enroll_{course['_id']}"):
                            enrollments_col.insert_one({
                                "username": username,
                                "course_id": course["_id"],
                                "course_title": course["title"],
                                "instructor": course["instructor"],
                                "status": "approved",
                                "enrolled_on": datetime.now()
                            })
                            st.success("✅ Enrolled in free course.")
                            st.rerun()
                else:
                    if enrollment["status"] == "approved":
                        st.info("✅ Enrolled")
                    elif enrollment["status"] == "pending":
                        st.warning("⏳ Awaiting instructor approval")
                    elif enrollment["status"] == "rejected":
                        st.error("❌ Enrollment Rejected")

    elif menu == "My Courses":
        st.subheader("📂 My Enrolled Courses")
        enrollments = list(enrollments_col.find({"username": username, "status": "approved"}))
        if not enrollments:
            st.info("You haven't enrolled in any courses yet.")
        else:
            for enrollment in enrollments:
                course = course_col.find_one({"_id": enrollment["course_id"]})
                if not course:
                    continue
                with st.expander(f"{course['title']} by {course['instructor']}"):
                    st.write(f"📅 Enrolled on: {enrollment.get('enrolled_on', 'N/A')}")
                    contents = list(content_col.find({"course_id": course["_id"]}))
                    for content in contents:
                        if content["access"] == "free":
                            st.write(f"📄 {content['title']} (Free)")
                            st.markdown(f"[Download]({content['file_url']})")
                        else:
                            purchased = purchases_col.find_one({"username": username, "content_id": content["_id"]})
                            if purchased:
                                st.write(f"🔐 {content['title']} (Paid) ✅ Purchased")
                                st.markdown(f"[Download]({content['file_url']})")
                            else:
                                st.write(f"🔐 {content['title']} (Paid)")
                                if st.button("Buy", key=f"buy_{content['_id']}"):
                                    purchases_col.insert_one({"username": username, "content_id": content["_id"]})
                                    st.success("Purchase successful!")
                                    st.rerun()

    elif menu == "AI Modules":
        nlp = spacy.load("en_core_web_sm")
        ALL_SKILLS = ["python", "sql", "java", "javascript", "html", "css", "c++", "mongodb"]

        for key, default in {
            "page": "upload",
            "selected_skill": None,
            "difficulty": None,
            "questions": [],
            "index": 0,
            "score": 0,
            "responses": [],
            "session_id": str(uuid.uuid4()),
        }.items():
            if key not in st.session_state:
                st.session_state[key] = default

        def extract_text_from_resume(uploaded_file):
            text = ""
            if uploaded_file.type == "text/plain":
                text = uploaded_file.read().decode("utf-8")
            elif uploaded_file.type == "application/pdf":
                reader = PyPDF2.PdfReader(uploaded_file)
                for page in reader.pages:
                    text += page.extract_text()
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = docx.Document(uploaded_file)
                for para in doc.paragraphs:
                    text += para.text + "\n"
            return text

        def extract_skills(text):
            doc = nlp(text.lower())
            return list({token.text for token in doc if token.text in ALL_SKILLS})

        if st.session_state.page == "upload":
            st.subheader("📄 Resume Skill Extractor & Assessment")
            uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "txt", "docx"])
            if uploaded_file:
                text = extract_text_from_resume(uploaded_file)
                extracted_skills = extract_skills(text)

                if extracted_skills:
                    st.success("Skills found in resume:")
                    for skill in extracted_skills:
                        col1, col2 = st.columns([3, 1])
                        col1.write(skill.title())
                        if col2.button(f"Take Assessment: {skill}", key=skill):
                            st.session_state.selected_skill = skill
                            st.session_state.page = "assessment"
                            st.rerun()
                else:
                    st.warning("No predefined skills found in your resume.")

        elif st.session_state.page == "assessment":
            skill = st.session_state.selected_skill
            st.title(f"🧠 {skill.title()} Skill Assessment")

            if st.session_state.difficulty is None:
                difficulty = st.radio("Choose difficulty level:", ["easy", "medium", "hard"], key=f"q_{st.session_state.index}")
                if st.button("Start Assessment"):
                    if user["tokens"] <= 0:
                        st.error("❌ You have no tokens left. Please contact admin.")
                        return

                    all_questions = get_all_questions(skill, difficulty)
                    if len(all_questions) < 15:
                        st.error("Insufficient questions for this skill and difficulty level.")
                        st.session_state.page = "upload"
                        st.rerun()

                    # Deduct token
                    access_col.update_one({"username": username}, {"$inc": {"tokens": -1}})
                    usage_log_col.insert_one({
                        "username": username,
                        "module": "AI Assessment",
                        "skill": skill,
                        "difficulty": difficulty,
                        "used_on": datetime.utcnow()
                    })
                    user["tokens"] -= 1  # reflect change locally for current session

                    st.session_state.questions = random.sample(all_questions, 15)
                    random.shuffle(st.session_state.questions)
                    st.session_state.index = 0
                    st.session_state.score = 0
                    st.session_state.responses = []
                    st.session_state.difficulty = difficulty
                    st.session_state.page = "exam"
                    st.rerun()

        elif st.session_state.page == "exam" and st.session_state.index < len(st.session_state.questions):
            question = st.session_state.questions[st.session_state.index]
            q_num = st.session_state.index + 1
            st.markdown(f"*Question {q_num}:* {question['question']}")

            if question["type"] == "coding":
                for key in ["constraints", "input", "output", "explanation"]:
                    if key in question:
                        st.markdown(f"**{key.title()}**: {question[key]}")

            if question["type"] in ["mcqs", "blanks"] and "options" in question:
                answer = st.radio("Options:", question["options"], index=None, key=f"q_{st.session_state.index}")
            else:
                answer = st.text_area("Your answer:", key=f"q_{st.session_state.index}")

            if len(st.session_state.responses) <= st.session_state.index:
                st.session_state.responses.append({"selected": ""})

            st.session_state.responses[st.session_state.index].update({
                "question": question["question"],
                "type": question["type"],
                "selected": answer,
                "correct": question.get("answer")
            })

            col1, col2, col3 = st.columns([1, 1, 2])
            if col1.button("⬅ Previous", disabled=st.session_state.index == 0):
                st.session_state.index -= 1
                st.rerun()

            if col2.button("➡ Next", disabled=st.session_state.index == len(st.session_state.questions) - 1):
                st.session_state.index += 1
                st.rerun()

            if st.session_state.index == len(st.session_state.questions) - 1:
                if col3.button("✅ Submit"):
                    st.session_state.page = "submit"
                    st.rerun()

        elif st.session_state.page == "submit":
            score = 0
            for resp in st.session_state.responses:
                selected = resp.get("selected")
                correct = resp.get("correct")
                if isinstance(selected, str) and isinstance(correct, str):
                    if selected.strip().lower() == correct.strip().lower():
                        score += 1

            st.session_state.score = score

            db["results"].insert_one({
                "session_id": st.session_state.session_id,
                "username": username,
                "skill": st.session_state.selected_skill,
                "difficulty": st.session_state.difficulty,
                "score": st.session_state.score,
                "total": len(st.session_state.questions),
                "responses": st.session_state.responses
            })

            st.subheader("🎉 Assessment Completed!")
            st.success(f"✅ Score: {st.session_state.score} / {len(st.session_state.questions)}")
            st.balloons()

            if st.button("Back to Home"):
                for key in ["page", "selected_skill", "difficulty", "questions", "index", "score", "responses"]:
                    st.session_state[key] = None
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.page = "upload"
                st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🔒 Logout"):
        st.session_state.clear()
        st.switch_page("app.py")
