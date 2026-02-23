"""
Description
"""

import csv
from json import dumps
from pathlib import Path
from typing import Dict, Any, Iterator, Optional
# from time import time

POST_COLUMNS = [
    "id",
    "title",
    "description",
    "language",
    "code",
    "tags",
    "feedback_type",
    "visibility",
    "created_at",
    "user_id",
]


def parse_tags(tags_value: Optional[str]) -> list[str]:

    """
    tags is varchar(200) in your schema.
    Decide on ONE format going forward.
    This parser supports:
      - None / NULL
      - 'python, flask, web'
      - "['python','flask']" (stringified list)
    """

    if not tags_value:
        return []
    s = tags_value.strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1].replace("'", "").replace('"', "")

    return [t.strip() for t in s.split(",") if t.strip()]


def iter_posts(dump_path: str | Path) -> Iterator[Dict[str, Any]]:

    """
    Stream posts rows from a pg_dump .sql file (COPY public.posts ... FROM stdin; block).
    Yields dicts with raw fields; you choose what to keep.
    """

    def nullify(v: str) -> Optional[str]:

        """pg_dump uses \\N to represent SQL NULL in COPY data."""

        return None if v == r"\N" else v


    with Path(dump_path).open("r", encoding = "utf-8", errors = "replace", newline = "") as f:
        for line in f:
            if line.startswith("COPY public.posts"):
                break
        else:
            raise RuntimeError("COPY public.posts section not found in the dump file.")

        reader = csv.reader(
            f,
            delimiter = "\t",
            quoting = csv.QUOTE_NONE,
            escapechar = "\\",
        )

        for row in reader:
            if not row:
                continue

            first = row[0].strip()
            if first in (r"\.", "."):
                break

            # Robustness: if row length doesn't match expected, skip it.
            # (Usually means dump corruption or odd formatting.)
            if len(row) != len(POST_COLUMNS):
                continue

            rec = dict(zip(POST_COLUMNS, row))

            # Convert types & NULLs
            pid = int(rec["id"])  # id is NOT NULL in your schema

            yield {
                "id": pid,
                "title": nullify(rec["title"]) or "",
                "description": nullify(rec["description"]) or "",
                "tags": parse_tags(nullify(rec["tags"])),
                # keep extra fields if you want:
                "language": nullify(rec["language"]) or "",
                "visibility": nullify(rec["visibility"]) or "",
                "created_at": nullify(rec["created_at"]) or "",
                "user_id": int(rec["user_id"]) if nullify(rec["user_id"]) else None,
            }


def write_json(dump_path: str | Path, outpath: str | Path = "posts.json") -> None:

    """
    Writes posts as:
    {
      "5": {"title": ..., "description": ..., "tags": [...]},
      ...
    }
    (keys as strings are typical JSON style)
    """

    posts: Dict[str, Dict[str, Any]] = {}
    for p in iter_posts(dump_path):
        posts[str(p["id"])] = {
            "title": p["title"],
            "description": p["description"],
            "tags": p["tags"],

            # optional

            # "language": p["language"],
            # "created_at": p["created_at"],
            # "user_id": p["user_id"],
            # "visibility": p["visibility"],
        }

    Path(outpath).write_text(dumps(posts, ensure_ascii = False, indent = 2), encoding = "utf-8")
    # print("Extracted")
