from pymongo import MongoClient

#MongoDB URI 
client = MongoClient("mongodb+srv://HumanRightsMIS:MISProject@clusterhumanrights.quwsprj.mongodb.net/?retryWrites=true&w=majority&appName=ClusterHumanRights")

#Database
db = client["human_rights_mis"]

#Collections
cases = db["cases"]
case_status_history = db["case_status_history"]
incident_reports = db["incident_reports"]
report_evidence = db["report_evidence"]