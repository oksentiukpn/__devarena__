from app.models import Battle, Reaction, User

def count_battles(current_user:User):
    count = 0
    user_battles = Battle.query.filter_by(user_id=current_user.id).all()
    for _ in user_battles:
        count+=1
    return count

def count_reactions(current_user:User):
    user_reactions = Reaction.query.filter_by(user_id = current_user.id)
    count = 0
    for _ in user_reactions:
        count +=1
    return count
