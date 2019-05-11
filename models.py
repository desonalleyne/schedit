from peewee import MySQLDatabase, Model, ForeignKeyField, \
    AutoField, TextField, CharField, IntegerField, BooleanField, DateTimeField, TimeField
import pymysql
from flask_peewee.auth import BaseUser
from playhouse.shortcuts import model_to_dict
import datetime
import json
import logging
logger = logging.getLogger(__name__)


mysqlj_db = {'host': 'localhost', 'database': 'schedit', 'user': 'schedit', 'password': 'schedit'
             }


def _init():
    print "initting"
    conn = pymysql.connect(
        host="localhost", user='schedit', password='schedit')
    conn.cursor().execute("CREATE DATABASE {}".format(mysql_db['database']))
    conn.close()


db = MySQLDatabase('schedit', host="localhost",
                   port=3306, user='schedit', password='schedit')


class BaseModel(Model):
    class Meta:
        database = db


class Pin(BaseModel):
    id = AutoField(primary_key=True)
    name = TextField()
    number = IntegerField()


class Zone(BaseModel):
    id = AutoField(primary_key=True)
    name = TextField()
    description = TextField()
    category = TextField()
    pin = IntegerField(unique=True)


class Group(BaseModel):
    id = AutoField(primary_key=True)
    name = TextField()
    description = TextField()


class ZoneGroup(BaseModel):
    id = AutoField(primary_key=True)
    zone = ForeignKeyField(Zone)
    group = ForeignKeyField(Group)


class Route(BaseModel):
    id = AutoField(primary_key=True)
    name = TextField()
    description = TextField()
    source_zone = ForeignKeyField(Zone)
    passthrough_group = ForeignKeyField(Group)
    target_group = ForeignKeyField(Group)


class Schedule(BaseModel):
    id = AutoField(primary_key=True)
    name = TextField()
    description = TextField()
    route = ForeignKeyField(Route)
    days = TextField()
    duration = IntegerField()
    start_time = TimeField()
    is_enabled = BooleanField(default=True)


class User(BaseModel, BaseUser):
    username = CharField()
    password = CharField()
    email = CharField()
    join_date = DateTimeField(default=datetime.datetime.now)
    active = BooleanField(default=True)
    admin = BooleanField(default=False)


def get_group_zones(id_):
    """ Returns list of zones that are in group id_
    """
    logger.debug("getting group zones")
    out = []
    group = (Zone.select()
             .join(ZoneGroup, on=(ZoneGroup.zone == Zone.id))
             .join(Group, on=(ZoneGroup.group == Group.id))
             .where(ZoneGroup.group == id_)
             )
    for g in group:
        out.append(model_to_dict(g))
        logger.debug(json.dumps(out, sort_keys=True, indent=4))
    return out


# _init()
db.init('schedit')

db.create_tables([Schedule])
