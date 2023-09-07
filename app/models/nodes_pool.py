import uuid

from mongoengine import DoesNotExist
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError

from app.utils.database import db


class NodesPool(db.Document):
    node_id = db.StringField(required=True, default=str(uuid.uuid4()))
    hostname = db.StringField(required=True, unique=True)
    max_conns = db.IntField(required=True)
    services = db.ListField(db.StringField())
    tools = db.ListField(db.StringField())
    username = db.StringField(required=True)
    password = db.StringField(required=True)
    ports = db.DictField()

    @classmethod
    def add_node(cls, hostname, max_conns, services, tools, username, password, ports):
        try:
            node_pool = cls(
                hostname=hostname,
                max_conns=max_conns,
                services=services,
                tools=tools,
                username=username,
                password=password,
                ports=ports
            )
            node_pool.save()
            return node_pool
        except Exception as e:
            raise BadRequest(f"Failed to create a node pool: {str(e)}")

    @classmethod
    def get_nodes(cls):
        try:
            nodes = cls.objects()
            return nodes
        except Exception:
            raise InternalServerError

    @classmethod
    def get_node(cls, hostname):
        try:
            node_pool = cls.objects.get(hostname=hostname)
            return node_pool
        except DoesNotExist:
            raise NotFound("Node pool not found.")
        except Exception as e:
            raise BadRequest(f"Failed to retrieve node pool: {str(e)}")

    @classmethod
    def update_node(cls, hostname, field_name, field_value):
        try:
            node_pool = cls.objects.get(hostname=hostname)
            setattr(node_pool, field_name, field_value)
            node_pool.save()
            return node_pool
        except DoesNotExist:
            raise NotFound("Node pool not found.")
        except Exception as e:
            raise BadRequest(f"Failed to update node pool: {str(e)}")

    @classmethod
    def delete_node(cls, hostname):
        try:
            node_pool = cls.objects.get(hostname=hostname)
            node_pool.delete()
            return True
        except DoesNotExist:
            raise NotFound("Node pool not found.")
        except Exception as e:
            raise BadRequest(f"Failed to delete node pool: {str(e)}")
