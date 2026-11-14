import os
import sys
import random
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from utils.ddb_utils import TABLE, get_ddb, new_job_id  # noqa: E402
from labs.ddb.jobs_repo import put_job, get_job, update_status, delete_job, list_user_jobs  # noqa: E402


ddb = get_ddb()

# CREATE
job = {"user_id": "u-vaibhav", "job_id": new_job_id(),
       "query": "what is RAG", "status": "pending", "tokens": 0}
put_job(ddb, job)
print("Put:", job["job_id"])

# READ
print("Get:", get_job(ddb, "u-vaibhav", job["job_id"]))
print("Missing:", get_job(ddb, "u-vaibhav", "nope"))

# UPDATE only the status
update_status(ddb, "u-vaibhav", job["job_id"], "done")
print("After update:", get_job(ddb, "u-vaibhav", job["job_id"]))

# DELETE
delete_job(ddb, "u-vaibhav", job["job_id"])
print("After delete:", get_job(ddb, "u-vaibhav", job["job_id"]))

users = ["u-vaibhav", "u-asha", "u-rohan"]
start = datetime(2026, 10, 1, tzinfo=timezone.utc)

# INSERT 50 jobs spread over Oct-Nov, only once (reruns would keep growing the table)
if ddb.scan(TableName=TABLE, Select="COUNT")["Count"] == 0:
    for n in range(50):
        user = random.choice(users)
        when = start + timedelta(days=random.randint(0, 60), minutes=n)
        put_job(ddb, {"user_id": user, "job_id": new_job_id(when),
                      "query": f"research topic #{n}",
                      "status": random.choice(["pending", "running", "done"])})
    print("Inserted 50 jobs")
else:
    print("Table already seeded, skipping insert")

# QUERY 1: newest 5 for one user
print("\nNewest 5 for u-asha:")
for j in list_user_jobs(ddb, "u-asha", limit=5):
    print(" ", j["job_id"], j["status"])

# QUERY 2: date range
nov = list_user_jobs(ddb, "u-asha", start="20261101", end="20261130")
print("\nu-asha jobs in November:", len(nov))