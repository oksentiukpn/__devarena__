"""
Helping search service file
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
from app.models import Post
from app.main import search_engine


def _tags_to_list(tags: str | None) -> list[str]:
    if not tags:
        return []
    # DB stores tags as "python, flask, oop"
    return [t.strip() for t in tags.split(",") if t.strip()]


def _load_posts_for_index() -> dict[str, dict]:
    """
    Convert DB posts into the dict format your search_engine expects:
    {
      "12": {"title": "...", "description": "...", "tags": ["a","b"]}
    }
    """
    posts = Post.query.filter(Post.visibility == "public").all()

    posts_by_id: dict[str, dict] = {}
    for p in posts:
        posts_by_id[str(p.id)] = {
            "title": p.title or "",
            "description": p.description or "",
            "tags": _tags_to_list(p.tags),
        }
    return posts_by_id


@dataclass
class _Index:
    ids: list[str]
    posts: list[dict]
    tag_sets: list[set[str]]
    bm25: object


# Simple module-level
_INDEX: _Index | None = None
_INDEX_SIZE: int = -1


def get_index(force_rebuild: bool = False) -> _Index:
    global _INDEX, _INDEX_SIZE

    posts_by_id = _load_posts_for_index()
    size = len(posts_by_id)

    if force_rebuild or _INDEX is None or size != _INDEX_SIZE:
        ids, posts, tag_sets, bm25 = search_engine.build_index(posts_by_id)
        _INDEX = _Index(ids=ids, posts=posts, tag_sets=tag_sets, bm25=bm25)
        _INDEX_SIZE = size

    return _INDEX


def search_post_ids(query: str, limit: int = 30) -> list[int]:
    idx = get_index()
    results: list[Tuple[str, float]] = search_engine.search(
        query=query,
        ids=idx.ids,
        posts=idx.posts,
        tag_sets=idx.tag_sets,
        bm25=idx.bm25,
        top_k=limit,
        detailed=False,
    )
    # convert "12" -> 12
    return [int(pid) for pid, _score in results]
