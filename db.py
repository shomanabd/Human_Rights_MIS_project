from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "human_rights_mis")

client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]

#Collections
cases = db["cases"]
case_status_history = db["case_status_history"]
incident_reports = db["incident_reports"]
report_evidence = db["report_evidence"]
individuals_collection = db["individuals"]  # Changed from "victims" to "individuals"
users_collection = db["users"]
victim_risk_assessments = db["victim_risk_assessments"]