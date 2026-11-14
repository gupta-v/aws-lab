import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.ddb_utils import get_ddb, create_jobs_table, describe  # noqa: E402

ddb = get_ddb()
created = create_jobs_table(ddb)
name, status, keys = describe(ddb)
print(("Created" if created else "Already exists"), "->", name, "|", status, "|", keys)