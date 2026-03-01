"""
Docstring for SearchEngine
"""

import re
import unicodedata
import numpy as np
from rank_bm25 import BM25Okapi


# import numpy as np
# from transform import write_data

# EXCLUDE = {
#     "a","an","the","of","to","in","on","for","and","or","but","is","are","was","were",
#     "be","been","being","with","as","at","by","from","that","this","these","those",
#     "it","its","into","about","over","under","than","then","so","such","not","no"
# }
# patt = re.compile(r"[a-z0-9]+")


# def tokenize(s: str):

#     """
#     Docstring for tokenize

#     :param s: Description
#     :type s: str
#     :return: Description
#     :rtype: list[Any]
#     """

#     toks = patt.findall((s or "").lower())
#     return [t for t in toks if t not in EXCLUDE]


# def tokenize_tag(tag: str):

#     """
#     Docstring for tokenize_tag

#     :param tag: Description
#     :type tag: str
#     :return: Description
#     :rtype: list[Any]
#     """

#     tag = (tag or "").replace("-", " ").replace("_", " ")
#     return tokenize(tag)


# def build_index(posts_by_id: dict, title_weight: int = 2):

#     """
#     Docstring for build_index

#     :param posts_by_id: Description
#     :type posts_by_id: dict
#     :param title_weight: Description
#     :type title_weight: int
#     :return: Description
#     :rtype: tuple[list, list, list, BM25Okapi]
#     """

#     ids = []
#     posts = []
#     tag_sets = []
#     corpus = []

#     for pid, p in posts_by_id.items():
#         title = p.get("title", "")
#         desc = p.get("description", "")
#         tags = p.get("tags") or []

#         # simple field weighting: title counts more
#         doc_tokens = tokenize(title) * title_weight + tokenize(desc)
#         if not doc_tokens:
#             continue

#         # precompute tag tokens as a set
#         ts = set()
#         for t in tags:
#             ts.update(tokenize_tag(str(t)))

#         ids.append(pid)
#         posts.append(p)
#         corpus.append(doc_tokens)
#         tag_sets.append(ts)

#     bm25 = BM25Okapi(corpus)
#     return ids, posts, tag_sets, bm25


# def search(query: str, ids, posts, tag_sets, bm25, top_k: int = 10, detailed: bool = False):

#     """
#     Docstring for search

#     :param query: Description
#     :type query: str
#     :param ids: Description
#     :param posts: Description
#     :param tag_sets: Description
#     :param bm25: Description
#     :param top_k: Description
#     :type top_k: int
#     :param tag_bonus: Description
#     :type tag_bonus: float
#     :return: Description
#     :rtype: list | list[tuple[Any, Any, float]]
#     """

#     q_tokens = tokenize(query)
#     if not q_tokens:
#         return []

#     qset = set(q_tokens)
#     scores = bm25.get_scores(q_tokens).astype(float)

#     for i, ts in enumerate(tag_sets):
#         if ts:
#             hit = len(ts & qset)
#             if hit:
#                 scores[i] += (hit / len(ts)) * 0.3

#     idx = np.argsort(scores)[::-1][:top_k]
#     if detailed:
#         return [(ids[i], posts[i], float(scores[i])) for i in idx if scores[i] > 0]

#     return sorted(
#         [(ids[i], float(scores[i])) for i in idx if scores[i] > 0],
#         key=lambda x: x[1], reverse=True)


# --- stopwords per language (small starter sets; extend later) ---
STOPWORDS = {
    "en": {
        "a","an","the","of","to","in","on","for","and","or","but","is","are","was","were",
        "be","been","being","with","as","at","by","from","that","this","these","those",
        "it","its","into","about","over","under","than","then","so","such","not","no",
    }
}

# Unicode-friendly token pattern (letters+digits, no underscores)
TOKEN_RE = re.compile(r"[^\W_]+", flags=re.UNICODE)


def _normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    # split camelCase / PascalCase: "TimSort" -> "Tim Sort"
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    # split digit/letter boundaries: "python3" -> "python 3"
    s = re.sub(r"([A-Za-zА-Яа-яІіЇїЄєҐґ])(\d)", r"\1 \2", s)
    s = re.sub(r"(\d)([A-Za-zА-Яа-яІіЇїЄєҐґ])", r"\1 \2", s)
    return s.lower()


def _stem_en_simple(tok: str) -> str:
    # super-light stemming (no extra deps)
    for suf in ("ing", "edly", "edly", "edly", "ed", "ly", "ies", "s"):
        if tok.endswith(suf) and len(tok) >= 4:
            if suf == "ies":
                return tok[:-3] + "y"
            if suf == "s" and tok.endswith("ss"):
                return tok
            return tok[: -len(suf)]
    return tok


def tokenize(s: str, lang: str = "en") -> list[str]:
    s = _normalize_text(s)
    toks = TOKEN_RE.findall(s)

    stop = STOPWORDS.get(lang, STOPWORDS["en"])

    out: list[str] = []
    for t in toks:
        if t in stop:
            continue
        # optional stemming for English only
        if lang == "en":
            t = _stem_en_simple(t)
        out.append(t)

    # Add “joined bigrams” to help with compounds:
    # "tim sort" produces "timsort" so it matches "TimSort"/"timsort"
    if len(out) >= 2:
        out += [out[i] + out[i + 1] for i in range(len(out) - 1)]

    return out


def _tags_to_list(tags) -> list[str]:
    # Accept list[str], set[str], tuple[str], or "a, b, c"
    if not tags:
        return []
    if isinstance(tags, (list, tuple, set)):
        return [str(t) for t in tags if str(t).strip()]
    if isinstance(tags, str):
        return [t.strip() for t in tags.split(",") if t.strip()]
    return [str(tags)]


def tokenize_tag(tag: str, lang: str = "en") -> list[str]:
    # tags may include separators like '-' '_' '#'
    tag = (tag or "").replace("-", " ").replace("_", " ").replace("#", " ")
    return tokenize(tag, lang=lang)


def build_index(posts_by_id: dict, *, lang: str = "en", title_weight: int = 3, tag_weight: int = 4):
    ids = []
    posts = []
    tag_sets = []
    corpus = []

    for pid, p in posts_by_id.items():
        title = p.get("title", "") or ""
        desc = p.get("description", "") or ""
        tags_raw = p.get("tags")

        tags = _tags_to_list(tags_raw)

        title_tokens = tokenize(title, lang=lang)
        desc_tokens = tokenize(desc, lang=lang)

        # include tags in the document tokens too
        tag_tokens: list[str] = []
        ts = set()
        for t in tags:
            toks = tokenize_tag(str(t), lang=lang)
            tag_tokens.extend(toks)
            ts.update(toks)

        # field weighting
        doc_tokens = (title_tokens * title_weight) + desc_tokens + (tag_tokens * tag_weight)

        if not doc_tokens:
            continue

        ids.append(pid)
        posts.append(p)
        corpus.append(doc_tokens)
        tag_sets.append(ts)

    bm25 = BM25Okapi(corpus)
    return ids, posts, tag_sets, bm25


def search(query: str, ids, posts, tag_sets, bm25, *, lang: str = "en", top_k: int = 10, detailed: bool = False):
    q_tokens = tokenize(query, lang=lang)
    if not q_tokens:
        return []

    qset = set(q_tokens)
    scores = bm25.get_scores(q_tokens).astype(float)

    # if query hits tag tokens, boost more aggressively for small docs
    for i, ts in enumerate(tag_sets):
        if not ts:
            continue
        hit = len(ts & qset)
        if hit:
            # scale by hit count, but cap
            scores[i] += min(0.8, 0.25 + 0.25 * hit)

    # phrase/substr bonus
    q_norm = _normalize_text(query)
    for i, p in enumerate(posts):
        title = _normalize_text(p.get("title", "") or "")
        desc = _normalize_text(p.get("description", "") or "")
        if q_norm and (q_norm in title):
            scores[i] += 0.8
        elif q_norm and (q_norm in desc):
            scores[i] += 0.3

    idx = np.argsort(scores)[::-1][:top_k]

    if detailed:
        return [(ids[i], posts[i], float(scores[i])) for i in idx if scores[i] > 0]

    # return in descending order
    return [(ids[i], float(scores[i])) for i in idx if scores[i] > 0]
