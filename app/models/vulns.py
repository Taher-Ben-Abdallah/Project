from nvdlib import cve

from app import db


class Product(db.EmbeddedDocument):
    name = db.StringField
    version = db.ListField(db.StringField())


class Vuln (db.Document):
    cve_ref = db.StringField()
    year = db.IntField()
    description = db.StringField()
    products = db.ListField(Product)
    cvss = db.FloatField()
    # cvss_vector
    cwe_ref = db.StringField()
    mitigations = db. StringField()
    references = db.ListField(db.StringField())
