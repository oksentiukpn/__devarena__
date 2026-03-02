from sqlalchemy import or_

from app.models import Battle, Reaction, User


def count_battles(current_user: User):
    return Battle.query.filter(
        or_(Battle.user_id == current_user.id, Battle.opponent_id == current_user.id)
    ).count()


def count_reactions(current_user: User):
    return Reaction.query.filter_by(user_id=current_user.id).count()
