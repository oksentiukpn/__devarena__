"""
Search Engine Prototype
"""

# posts = Post.query.filter(
#         Post.visibility == 'public',
#         or_(
#             Post.title.ilike(search_pattern),       # Заголовок (case-insensitive)
#             Post.description.ilike(search_pattern), # Опис
#             Post.tags.ilike(search_pattern),        # Теги
#             Post.language.ilike(search_pattern),    # Мова програмування
#             # Post.code.ilike(search_pattern)
#         )
#     ).order_by(Post.created_at.desc()).all()
