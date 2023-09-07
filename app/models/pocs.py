import uuid

from werkzeug.exceptions import BadRequest, NotFound

from app.utils.database import db

from mongoengine.errors import ValidationError, DoesNotExist, OperationError


class Poc (db.Document):
    poc_id = db.StringField(default=str(uuid.uuid4()))
    name = db.StringField()
    description = db.StringField()
    category = db.StringField()
    payload = db.StringField(required=True)

    #poc is validated by TL


    @classmethod
    def create_poc(cls, name, vuln_id, description, payload):

        try:
            poc = cls(name=name, vuln_id=vuln_id,
                      description=description, payload=payload)
            poc.save()
        except ValidationError as e:
            raise BadRequest(f'Invalid user data: {e}')

        return poc.to_dict()

    @classmethod
    def update_poc(cls, poc_id, data):

        try:
            poc = cls.objects.get(poc_id=poc_id)
        except DoesNotExist:
            raise NotFound('PoC not found')

        try:
            poc.update(**data)
        except (ValidationError, OperationError) as e:
            raise BadRequest(str(e))

        return poc.to_dict()

