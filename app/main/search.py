""" Docstring for app.main.search """

from sqlalchemy import func, desc
from app import db
from app.models import Post, User

def _post_vector():
    return func.to_tsvector(
        "simple",
        func.coalesce(Post.title, "") + " " +
        func.coalesce(Post.description, "") + " " +
        func.coalesce(Post.tags, "")
    )

def _user_vector():
    return func.to_tsvector(
        "simple",
        func.coalesce(User.username, "") + " " +
        func.coalesce(User.bio, "")
    )

def search_posts(query: str, limit: int = 20, include_private_for_user_id: int | None = None):

    """
    Docstring for search_posts
    :return: Description
    :rtype: list
    """

    if not query or not query.strip():
        return []

    tsquery = func.websearch_to_tsquery("simple", query)

    rank = func.ts_rank_cd(_post_vector(), tsquery)

    q = Post.query.filter(_post_vector().op("@@")(tsquery))

    # visibility rule (MVP: public only)
    if include_private_for_user_id is None:
        q = q.filter(Post.visibility == "public")
    else:
        q = q.filter(
            (Post.visibility == "public") |
            (Post.user_id == include_private_for_user_id)
        )

    return (
        q.order_by(desc(rank), desc(Post.created_at))
         .limit(limit)
         .all()
    )

def search_users(query: str, limit: int = 20):

    """
    Docstring for search_users
    :return: Description
    :rtype: list
    """

    if not query or not query.strip():
        return []

    tsquery = func.websearch_to_tsquery("simple", query)
    rank = func.ts_rank_cd(_user_vector(), tsquery)

    q = User.query.filter(_user_vector().op("@@")(tsquery))

    return q.order_by(desc(rank), User.username.asc()).limit(limit).all()
