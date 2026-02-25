"""
BM25-based search engine for posts.

This module provides utilities to tokenize post titles, descriptions, and tags,
build a BM25Okapi index over those posts, and execute ranked search queries.
It exposes helper functions to create the index from a mapping of post IDs to
post metadata and to search that index, optionally returning detailed scoring
information for the top matching posts.
"""

# import json
import re
import numpy as np
from rank_bm25 import BM25Okapi
# from transform import write_data # important!

EXCLUDE = {
    "a","an","the","of","to","in","on","for","and","or","but","is","are","was","were",
    "be","been","being","with","as","at","by","from","that","this","these","those",
    "it","its","into","about","over","under","than","then","so","such","not","no"
}
patt = re.compile(r"[a-z0-9]+")


def tokenize(s: str):

    """
    Docstring for tokenize

    :param s: Description
    :type s: str
    :return: Description
    :rtype: list[Any]
    """

    toks = patt.findall((s or "").lower())
    return [t for t in toks if t not in EXCLUDE]


def tokenize_tag(tag: str):

    """
    Docstring for tokenize_tag

    :param tag: Description
    :type tag: str
    :return: Description
    :rtype: list[Any]
    """

    tag = (tag or "").replace("-", " ").replace("_", " ")
    return tokenize(tag)


def build_index(posts_by_id: dict, title_weight: int = 2):

    """
    Docstring for build_index

    :param posts_by_id: Description
    :type posts_by_id: dict
    :param title_weight: Description
    :type title_weight: int
    :return: Description
    :rtype: tuple[list, list, list, BM25Okapi]
    """

    ids = []
    posts = []
    tag_sets = []
    corpus = []

    for pid, p in posts_by_id.items():
        title = p.get("title", "")
        desc = p.get("description", "")
        tags = p.get("tags") or []

        # simple field weighting: title counts more
        doc_tokens = tokenize(title) * title_weight + tokenize(desc)
        if not doc_tokens:
            continue

        # precompute tag tokens as a set
        ts = set()
        for t in tags:
            ts.update(tokenize_tag(str(t)))

        ids.append(pid)
        posts.append(p)
        corpus.append(doc_tokens)
        tag_sets.append(ts)

    bm25 = BM25Okapi(corpus)
    return ids, posts, tag_sets, bm25


def search(query: str, ids, posts, tag_sets, bm25, top_k: int = 10, detailed: bool = False):

    """
    Docstring for search

    :param query: Description
    :type query: str
    :param ids: Description
    :param posts: Description
    :param tag_sets: Description
    :param bm25: Description
    :param top_k: Description
    :type top_k: int
    :param tag_bonus: Description
    :type tag_bonus: float
    :return: Description
    :rtype: list | list[tuple[Any, Any, float]]
    """

    q_tokens = tokenize(query)
    if not q_tokens:
        return []

    qset = set(q_tokens)
    scores = bm25.get_scores(q_tokens).astype(float)

    for i, ts in enumerate(tag_sets):
        if ts:
            hit = len(ts & qset)
            if hit:
                scores[i] += (hit / len(ts)) * 0.3

    idx = np.argsort(scores)[::-1][:top_k]
    if detailed:
        return [(ids[i], posts[i], float(scores[i])) for i in idx if scores[i] > 0]
    return sorted([(ids[i], float(scores[i])) for i in idx if scores[i] > 0], key = lambda x: x[1])

if __name__ == "__main__":

    data = {
    "101": {
        "title": "Graph algorithms: MST and shortest paths",
        "description":
            """Graph algorithms are essential for solving many network problems.
            A minimum spanning tree connects all vertices with minimal total weight.
            Prim and Kruskal are classic choices for building an MST efficiently.
            Shortest path problems are different and often use Dijkstra or Bellman-Ford.
            Understanding basic graph representations helps you implement these algorithms correctly.""",
        "tags": ["graphs", "algorithms", "mst"]
    },
    "102": {
        "title": "A practical Python text search prototype",
        "description":
            """A simple search prototype in Python usually starts with normalization and tokenization.
            To rank documents, you can build an inverted index mapping tokens to document IDs.
            With an index, searches touch only documents that share query words.
            Ranking is often done with BM25 or a TF-IDF style formula.
            This approach scales well for many short articles and is easy to maintain.""",
        "tags": ["python", "search", "bm25"]
    },
    "103": {
        "title": "Why database indexes matter",
        "description":
            """Database indexing can dramatically speed up query performance on large tables.
            An index helps the engine locate rows without scanning the entire dataset.
            However, indexes add overhead to writes because the index structure must be updated.
            Choosing the right columns to index depends on your workload and common filters.
            Regular monitoring helps prevent slow queries and unnecessary storage usage.""",
        "tags": ["databases", "indexing", "performance"]
    },
    "104": {
        "title": "Model evaluation metrics you should know",
        "description":
            """Evaluating a machine learning model requires more than just accuracy.
            Precision and recall are important when classes are imbalanced.
            F1-score balances precision and recall into one value.
            ROC-AUC summarizes how well a classifier separates classes across thresholds.
            Cross-validation provides a more reliable estimate of generalization performance.""",
        "tags": ["ml", "metrics", "evaluation"]
    },
    "105": {
        "title": "Web app authentication and session security",
        "description":
            """Authentication is a core component of web application security.
            OAuth is often used to delegate login to trusted identity providers.
            JWT tokens can simplify stateless authentication but must be handled carefully.
            Session fixation and CSRF are common risks when session management is weak.
            Secure cookies, proper expiration, and HTTPS help protect user sessions.""",
        "tags": ["web", "security", "auth"]
    },
    "106": {
        "title": "Gardening in small urban spaces",
        "description":
            """Urban gardening has become popular for people living in apartments.
            Balconies and windowsills can be used to grow herbs and small vegetables.
            Good soil and consistent watering are more important than expensive tools.
            Composting reduces waste and improves soil health over time.
            Many beginners start with basil, mint, or cherry tomatoes.""",
        "tags": ["gardening", "plants", "hobby"]
    },
}

    # id_, pst, tag_, bm_25 = build_index(data, title_weight = 2) # uncomment for tests

    queries = [
        "python text search bm25",
        "graph algorithms prim kruskal",
        "web security oauth jwt",
        "database indexing performance",
    ]

    # for q in queries: # run
    #     print("\nQUERY:", q)
    #     results = search(q, ids = id_, posts = pst, tag_sets = tag_, bm25 = bm_25, top_k = 5, detailed = True)
    #     for pid_, p_, score in results:
    #         print(f"  score={score:.3f} | id={pid_} | title={p_.get('title','')!r} | tags={p_.get('tags', [])}")

    # print(search("database indexing performance", ids = id_, posts = pst, tag_sets = tag_, bm25 = bm_25, top_k = 5))
