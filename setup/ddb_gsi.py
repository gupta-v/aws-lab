import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.ddb_utils import get_ddb, add_status_index, TABLE  # noqa: E402

ddb = get_ddb()
created = add_status_index(ddb)
print("Created" if created else "Already exists", "-> status-index")

for g in ddb.describe_table(TableName=TABLE)["Table"]["GlobalSecondaryIndexes"]:
    keys = [(k["AttributeName"], k["KeyType"]) for k in g["KeySchema"]]
    print(" ", g["IndexName"], "|", g["IndexStatus"], "|", keys)