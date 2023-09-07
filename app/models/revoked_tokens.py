from mongoengine import NotUniqueError, DoesNotExist
from werkzeug.exceptions import BadRequest

from app import db
from enum import Enum


class Category(Enum):
    USER_TOKEN = "user"
    CLIENT_APP_TOKEN = "client app"


#### MODEL ####
class RevokedToken(db.Document):
    jti = db.StringField(unique=True, required=True)
    expired_at = db.DateTimeField(required=True)
    issued_at = db.DateTimeField(required=True)
    category = db.EnumField(Category, default=Category.USER_TOKEN)

    #### Methods ####
    @classmethod
    def revoke_token(cls, jti, issued_at, expired_at, category=None):
        try:
            revoked_token = cls(jti=jti, issued_at=issued_at, expired_at=expired_at, category=category)
            revoked_token.save()
        except NotUniqueError:
            raise BadRequest("Token already revoked")

    @classmethod
    def is_token_revoked(cls, jti):
        return cls.objects(jti=jti).first() is not None
