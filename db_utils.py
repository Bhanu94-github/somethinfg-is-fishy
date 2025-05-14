# FINAL UPDATED db.py
import pymongo
from random import sample

# MongoDB Connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["skill_based"]

def get_all_questions(skill, difficulty):
    """
    Retrieves 15 questions: 8 MCQs, 2 coding, 5 blanks for the given skill and difficulty
    """
    collection = db[skill]

    # Fetch questions by type and difficulty
    mcqs = list(collection.find({"difficulty": difficulty, "type": "mcqs"}))
    coding = list(collection.find({"difficulty": difficulty, "type": "coding"}))
    blanks = list(collection.find({"difficulty": difficulty, "type": "blanks"}))

    # Sample from each group
    selected_mcqs = sample(mcqs, min(8, len(mcqs)))
    selected_coding = sample(coding, min(2, len(coding)))
    selected_blanks = sample(blanks, min(5, len(blanks)))

    # Combine and shuffle
    questions = selected_mcqs + selected_coding + selected_blanks
    return sample(questions, len(questions))
