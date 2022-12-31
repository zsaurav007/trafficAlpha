from werkzeug.security import generate_password_hash

from .models import *


def add_user(email, password):
    user = User.query.filter_by(email=email).first()
    result = False
    if not user:
        db.session.add(User(email=email, password=generate_password_hash(
                password, method='sha256')))
        db.session.commit()
        result = True
    return result
