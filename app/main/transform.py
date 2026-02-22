import re
import csv
import io
from json import dump
# from rank_bm25 import BM25Okapi
# from time import time

# === FILLER ===

# SQL_PATH = "db_backup_2026-02-06_23-43-02.sql"
# OUT_PATH = "posts.json"

# ==============

def edit_data(s):

    """
    Unescape a field from a PostgreSQL COPY output
    """

    if s == r"\N":
        return None

    return (s.replace(r"\\", "\\")
             .replace(r"\t", "\t")
             .replace(r"\n", "\n")
             .replace(r"\r", "\r"))


def write_data(data, temp):

    """
    Docstring for write_data

    :param data: Description
    :param temp: Description
    """

    print("Reading SQL...")

    with open(data, "r", encoding = "utf-8", errors = "ignore") as f:
        sql = f.read()

    m = re.search(r"COPY public\.posts \((.*?)\) FROM stdin;\n", sql, flags = re.DOTALL)
    start = m.end()
    end = sql.find("\n\\.\n", start)

    reader = csv.reader(io.StringIO(sql[start:end]), delimiter = "\t", quoting= csv.QUOTE_NONE)

    print("COPY block found, processing...")

    posts = {}
    for row in reader:
        row = [edit_data(x) for x in row]
        rec = dict(zip([c.strip() for c in m.group(1).split(",")], row))

        post_id = rec.pop("id")  # key
        rec["tags"] = [t.strip() for t in (rec.get("tags") or "").split(",") if t.strip()]

        posts[str(post_id)] = rec

    print("Writing...")

    with open(temp, "w", encoding = "utf-8") as f:
        dump(posts, f, ensure_ascii = False, indent = 2)

    print(f"Done. Saved to {temp}")
