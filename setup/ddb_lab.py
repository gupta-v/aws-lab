from utils.ddb_utils import get_ddb, create_jobs_table, describe

ddb = get_ddb()
created = create_jobs_table(ddb)
name, status, keys = describe(ddb)
print(("Created" if created else "Already exists"), "->", name, "|", status, "|", keys)