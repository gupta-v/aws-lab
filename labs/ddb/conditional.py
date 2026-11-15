import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from utils.ddb_utils import get_ddb, new_job_id  # noqa: E402
from labs.ddb.jobs_repo import (create_job, claim_job, safe_update_status,  # noqa: E402
                                update_status, get_job, delete_job)

ddb = get_ddb()
user = "u-vaibhav"
job = {"user_id": user, "job_id": new_job_id(), "query": "conditional writes", "status": "pending"}

# 1. CREATE only if new
print("1. Create first time :", create_job(ddb, job))              # True
print("   Create same again :", create_job(ddb, job))              # False, not overwritten

# 2. Two workers race for the same job, at the same moment
def worker(name):
    return name, claim_job(ddb, user, job["job_id"], worker=name)

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(worker, ["worker-A", "worker-B"]))
print("\n2. Race:", results)                                       # exactly one True
print("   Job now:", get_job(ddb, user, job["job_id"]))           # status=running, worker=<winner>

# 3. A late duplicate (e.g. SQS delivered the message twice)
print("\n3. Late claim by worker-C:", claim_job(ddb, user, job["job_id"], worker="worker-C"))   # False

# 4. Fake id: old update creates junk, safe update refuses
update_status(ddb, user, "fake-id", "done")
print("\n4. Old update_status on fake-id created:", get_job(ddb, user, "fake-id"))
delete_job(ddb, user, "fake-id")                                    # clean up the junk
try:
    safe_update_status(ddb, user, "fake-id", "done")
except LookupError as e:
    print("   safe_update_status on fake-id:", e)
print("   Junk item exists?", get_job(ddb, user, "fake-id") is not None)   # False

# clean up the demo job
delete_job(ddb, user, job["job_id"])