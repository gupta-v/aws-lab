import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from utils.ddb_utils import TABLE, get_ddb, to_ddb  # noqa: E402
from labs.ddb.jobs_repo import list_by_status, update_status  # noqa: E402

ddb = get_ddb()

# 1. OLD way: Scan + filter (reads everything)
resp = ddb.scan(TableName=TABLE, FilterExpression="#s = :p",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues=to_ddb({":p": "pending"}))
print(f"Scan  'pending' : read {resp['ScannedCount']:>3} → returned {resp['Count']:>3}")

# 2. NEW way: Query the GSI (reads only the 'pending' drawer)
resp = ddb.query(TableName=TABLE, IndexName="status-index",
                 KeyConditionExpression="#s = :p",
                 ExpressionAttributeNames={"#s": "status"},
                 ExpressionAttributeValues=to_ddb({":p": "pending"}))
print(f"GSI   'pending' : read {resp['ScannedCount']:>3} → returned {resp['Count']:>3}")

# 3. Newest 3 pending jobs across ALL users
print("\nNewest 3 pending (any user):")
newest = list_by_status(ddb, "pending", limit=3)
for j in newest:
    print(" ", j["job_id"], j["user_id"])

# 4. Move one job pending -> done and watch it leave the 'pending' drawer
j = newest[0]
before = len(list_by_status(ddb, "pending"))
update_status(ddb, j["user_id"], j["job_id"], "done")     # write to the TABLE only
after = len(list_by_status(ddb, "pending"))
print(f"\nPending before: {before} | after flipping one to done: {after}")