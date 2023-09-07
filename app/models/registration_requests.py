import uuid
from datetime import datetime

from mongoengine import NotUniqueError, OperationError, DoesNotExist
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound

from app.utils.database import db


class RegistrationRequest(db.Document):
    first_name = db.StringField(required=True)
    last_name = db.StringField(required=True)
    email = db.EmailField(required=True, unique=True)
    issued_at = db.DateTimeField(default=datetime.utcnow, required=True)
    registration_id = db.StringField(default=str(uuid.uuid4()),unique=True)

    @classmethod
    def deposit_registration(cls, first_name, last_name, email):
        try:
            registration = cls(first_name=first_name, last_name=last_name, email=email)
            registration.save()
            return registration
        except NotUniqueError:
            raise BadRequest("Registration request already filed")

    @classmethod
    def get_registration_by_email(cls, email):
        return cls.objects(email=email).first()

    @classmethod
    def get_registration_by_id(cls, registration_id):
        return cls.objects(registration_id=registration_id).first()

    @classmethod
    def get_registrations(cls):
        try:
            return cls.objects()
        except Exception as e:
            print(e)
            raise InternalServerError("error getting registrations")

    @classmethod
    def delete_registration(cls, registration_id):
        try:
            registration = cls.get_registration_by_id(registration_id)
            if registration:
                registration.delete()
            else:
                raise DoesNotExist("Registration not found")  # Raise DoesNotExist if registration is not found
        except DoesNotExist:
            raise NotFound("Registration not found")  # Raise NotFound if registration is not found
        except OperationError as e:
            # Handle other exceptions and provide meaningful error messages
            print(e)
            raise InternalServerError("An error occurred while deleting registration")
