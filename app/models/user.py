import uuid
from enum import Enum

from werkzeug.exceptions import NotFound, Forbidden, BadRequest, Conflict, InternalServerError

from app import db
from mongoengine.errors import NotUniqueError, ValidationError, DoesNotExist, OperationError
from werkzeug.security import generate_password_hash, check_password_hash


class Role(Enum):
    ADMIN = "admin"
    TEAM_LEADER = "team-leader"
    PENTESTER = "pentester"


class Status(Enum):
    CREATED = 'created'
    ACTIVE = 'activated'
    DEACTIVATED = 'deactivated'
    DELETED = 'deleted'


class User(db.Document):
    public_id = db.StringField(required=True, default=str(uuid.uuid4()))
    email = db.StringField(required=True, unique=True)
    password = db.StringField(required=True)
    first_name = db.StringField()
    last_name = db.StringField()
    phone = db.ListField(db.StringField())
    roles = db.ListField(db.EnumField(Role, required=True, default=Role.PENTESTER))
    status = db.EnumField(Status, required=True)
    old_passwords = db.ListField(db.StringField)

    @classmethod
    def get_user(cls, public_id):
        try:
            user = User.objects.exclude("_id", "password", "old_passwords").get(public_id=public_id)
        except DoesNotExist:
            raise NotFound('User does not exist')
        return user

    @classmethod
    def get_users(cls):
        try:
            users = cls.objects.all().exclude("_id", "password", "old_passwords")
            return users
        except OperationError:
            raise InternalServerError

    @classmethod
    def create_user(cls, email, first_name, last_name, roles):
        try:
            user = cls(email=email,
                       firts_name=first_name, last_name=last_name, roles=roles, status=Status.CREATED)
            user.save()
            return user.to_dict()
        except NotUniqueError:
            # Change to raise a Werkzeug HTTP exception
            raise BadRequest('Email address already exists')

    @classmethod
    def update_user(cls, public_id, data):

        try:
            user = cls.objects.get(public_id=public_id)
        except DoesNotExist:
            raise NotFound('User not found')

        # Exclude password from update_data
        if 'password' in data:
            del data['password']

        # Update the user data
        try:
            user.update(**data)
        except NotUniqueError as e:
            raise BadRequest('Email already in use ')
        except ValidationError as e:
            raise BadRequest(f'Validation error: {str(e)}')
        except OperationError as e:
            raise InternalServerError(str(e))

        return user.to_dict()

    @classmethod
    def delete_user(cls, public_id):
        try:
            user = cls.objects.get(public_id=public_id)
            user.delete()
        except DoesNotExist:
            raise NotFound('User not found')

    def to_dict(self):
        user_dict = {
            'public_id': self.public_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'roles': self.roles,
            'status': self.status
        }

        return user_dict

    def check_password(self, password):
        return check_password_hash(self.password, password)
