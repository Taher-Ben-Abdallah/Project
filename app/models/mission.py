import uuid
from datetime import datetime
from enum import Enum

from mongoengine import ValidationError, DoesNotExist, OperationError
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError

from app.utils.database import db

from .user import User
from .pocs import Poc


# TODO Create document / Embedded document of target containing information : IP address(es) or URL(s) or os/app(s) and version(s)


class Test(db.EmbeddedDocument):
    poc = db.ReferenceField(Poc)
    target = db.StringField()
    result = db.StringField()


class Status(Enum):
    ONGOING = "ongoing"
    COMPLETED = "completed"

    CANCELLED = "cancelled"


class Mission(db.Document):
    mission_id = db.StringField(required=True, default=str(uuid.uuid4()))
    name = db.StringField()
    team_leader = db.ReferenceField(User)
    description = db.StringField()
    targets = db.ListField(db.StringField())
    team = db.ListField(db.ReferenceField(User))
    start_date = db.DateTimeField(default=datetime.utcnow)
    status = db.EnumField(Status, required=True, default=Status.ONGOING)
    end_date = db.DateTimeField()

    # TODO: REWRITE Test Sub-document store Tests, reference Vulnerabilities, and pocs for  test results (as subdocument)


    @classmethod
    def create_mission(cls, data):
        try:
            team_leader_id = data.get("team_leader")
            team_ids = data.get("team")

            team_leader = User.objects.filter(public_id=team_leader_id, status=Status.ACTIVE).first()
            if not team_leader:
                raise NotFound("Team leader not found or not active.")

            team_members = User.objects.filter(public_id__in=team_ids, status=Status.ACTIVE)

            #could be removed
            if len(team_members) != len(team_ids):
                not_found_users = set(team_ids) - {user.public_id for user in team_members}
                raise NotFound(f"Users not found or not active: {', '.join(not_found_users)}")

            mission = cls(
                name=data.get("name"),
                team_leader=team_leader,
                description=data.get("description"),
                targets=data.get("targets", []),
                team=team_members,
                status=Status.ONGOING,
            )
            mission.save()

            return mission

        except DoesNotExist as e:
            raise NotFound(str(e))
        except ValidationError as e:
            raise BadRequest(str(e))
        except Exception as e:
            raise InternalServerError(f"An error occurred: {str(e)}")


    #TODO: Write this method
    @classmethod
    def update_mission(cls, mission_id, data):

        try:
            mission = cls.objects.get(mission_id=mission_id)
        except DoesNotExist:
            raise NotFound('mission not found')

        try:
            mission.update(**data)
        except (ValidationError, OperationError) as e:
            raise BadRequest(str(e))

        return mission.to_dict()




    @classmethod
    def get_missions_overview(cls, member_id=None):
        """

        :param member_id:
        :return:
        """
        try:
            if member_id:
                user = User.objects.filter(public_id=member_id).first()
                if not user:
                    raise NotFound("User not found.")

                missions = cls.objects(team__contains=user)
            else:
                missions = cls.objects.all()

            missions_overview = []
            for mission in missions:
                mission_data = {
                    "mission_id": mission.mission_id,
                    "name": mission.name,
                    "description": mission.description,
                    "team": [
                        {"public_id": member.public_id,
                         "first_name": member.first_name,
                         "last_name": member.last_name}
                        for member in mission.team
                    ]
                }
                missions_overview.append(mission_data)
            return missions_overview

        except DoesNotExist:
            raise NotFound("Mission not found.")
        except Exception as e:
            raise InternalServerError(f"An error occurred: {str(e)}")


    @classmethod
    def update_team(cls, mission_id, members: list, remove=None, assign=None):
        """

        :param mission_id:
        :param members:
        :param remove:
        :param assign:
        :return:
        """
        try:
            mission = Mission.objects.get(mission_id=mission_id)
        except DoesNotExist:
            raise NotFound("Mission not found.")

        if assign and remove:
            raise BadRequest("Either 'assign' or 'remove' should be specified, not both.")

        try:
            not_found_or_inactive_users = []
            if assign:
                for member_id in members:
                    try:
                        member = User.objects.get(public_id=member_id)
                        if member.status == Status.ACTIVE.value:
                            mission.team.append(member)
                        else:
                            not_found_or_inactive_users.append(member_id)
                    except DoesNotExist:
                        not_found_or_inactive_users.append(member_id)

            elif remove:
                mission.team = [member for member in mission.team if member.public_id not in members]

            if not_found_or_inactive_users:
                raise NotFound(
                    f"Users not found or not active: {', '.join(not_found_or_inactive_users)}, rest of users processed successfully")

            mission.save()
        except Exception:
            raise InternalServerError("Something went wrong")

    @classmethod
    def delete_mission(cls, mission_id):
        try:
            mission = cls.objects.get(mission_id=mission_id)
            mission.delete()
        except DoesNotExist:
            raise NotFound('Mission not found')


