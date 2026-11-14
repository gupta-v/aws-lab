import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from utils.ddb_utils import TABLE, get_ddb, to_ddb, from_ddb  # noqa: E402

ddb = get_ddb()

# 1. SCAN with a filter: reads EVERYTHING, keeps only pending
resp = ddb.scan(
    TableName=TABLE,
    FilterExpression="#s = :p",
    ExpressionAttributeNames={"#s": "status"},          # reserved word again
    ExpressionAttributeValues=to_ddb({":p": "pending"}),
)
print(f"Scan  'pending'   : read {resp['ScannedCount']:>3} → returned {resp['Count']:>3}")

# 2. QUERY one drawer: reads only Vaibhav's items
resp = ddb.query(
    TableName=TABLE,
    KeyConditionExpression="user_id = :u",
    ExpressionAttributeValues=to_ddb({":u": "u-vaibhav"}),
)
print(f"Query 'u-vaibhav' : read {resp['ScannedCount']:>3} → returned {resp['Count']:>3}")

# 3. QUERY + filter: read the drawer, then drop non-pending
resp = ddb.query(
    TableName=TABLE,
    KeyConditionExpression="user_id = :u",
    FilterExpression="#s = :p",
    ExpressionAttributeNames={"#s": "status"},
    ExpressionAttributeValues=to_ddb({":u": "u-vaibhav", ":p": "pending"}),
)
print(f"Query + filter    : read {resp['ScannedCount']:>3} → returned {resp['Count']:>3}")

# 4. TRAP: Limit + Filter
resp = ddb.scan(
    TableName=TABLE, Limit=5,
    FilterExpression="#s = :p",
    ExpressionAttributeNames={"#s": "status"},
    ExpressionAttributeValues=to_ddb({":p": "pending"}),
)
print(f"Scan Limit=5      : read {resp['ScannedCount']:>3} → returned {resp['Count']:>3}  (not 5!)")
print("More pages?       :", "LastEvaluatedKey" in resp)