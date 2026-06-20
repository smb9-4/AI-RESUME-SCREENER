from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client["resume_screener"]

students = db["students"]
hr = db["hr"]
applications = db["applications"]