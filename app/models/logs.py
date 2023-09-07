from mongoengine import Q

from app.utils.database import  db
from enum import Enum
from datetime import datetime
import uuid

from user import User


# Change these to some dict format
class Category(Enum):
    ERROR= "error"

class ActionType(Enum):
    LOGIN = "Login"
    LOGOUT = "Logout"



class Logs(db.Document):
    timestamp = db.DateTimeField(required=True)
    log_id = db.StringField(required=True)
    user = db.ReferenceField(User)
    category = db.EnumField(ActionType)
    action = db.DictField()

    meta = {
        'collection': 'activity_logs'
    }

    @classmethod
    def create_log(cls, user, category, action_details=None):
        timestamp = datetime.now()
        log_id = str(uuid.uuid4())
        log = cls(
            timestamp=timestamp,
            log_id=log_id,
            user=user,
            category=category,
            action=action_details
        )
        log.save()
        return log

    @classmethod
    def get_logs(cls, user=None, category=None):
        query = {}
        if user:
            query['user'] = user
        if category:
            query['category'] = category
        logs = cls.objects(**query)
        return logs

    @classmethod
    def get_log_by_id(cls, log_id):
        log = cls.objects(log_id=log_id).first()
        return log

    @classmethod
    def get_user_logs(cls, user):
        logs = cls.objects(user=user)
        return logs

    @classmethod
    def get_category_logs(cls, category):
        logs = cls.objects(category=category)
        return logs

    @classmethod
    def get_mission_logs(cls,mission):
        logs = cls.objects(Q(action__mission=mission))
        return logs
