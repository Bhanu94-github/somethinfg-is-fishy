from pymongo import MongoClient

# MongoDB connection
client = MongoClient("mongodb+srv://Bhanu_9999:Thanuja@562994@cluster0.yyrj4au.mongodb.net/")
db = client["instructor"]  # your DB name
