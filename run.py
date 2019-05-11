import json
from flask import Flask, jsonify, request
# from flask_peewee.rest import RestAPI, UserAuthentication, RestResource
# from flask_peewee.auth import Auth
from flask_peewee.db import Database
from models import *  # Zone, Route, Group, IntermediaryZoneGroup
from playhouse.shortcuts import model_to_dict
# from flask_api import status
# from flasgger import Swagger
from flask_cors import CORS, cross_origin

import logging
# logger = logging.getLogger('peewee')
#logger = logging.getLogger('flask_cors')
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())

DATABASE = {
    'name': 'schedit',
    'engine': 'peewee.MySQLDatabase',
    'user': 'schedit',
    'password': 'schedit'
}
DEBUG = True
SECRET_KEY = 'shhhh'


app = Flask(__name__)
CORS(app)
# CORS(app, resources={r"*": {"origins": "*"}})
# swagger = Swagger(app)
app.config.from_object(__name__)

db = Database(app)


# auth = Auth(app, db)
# user_auth = UserAuthentication(auth)

# api = RestAPI(app, default_auth=user_auth)

# api.register(Zone, allowed_methods=['GET', 'POST'])
# api.register(Route, allowed_methods=['GET', 'POST'])
# api.register(Group, allowed_methods=['GET', 'POST'])
# api.register(ZoneGroup, allowed_methods=['GET', 'POST'])

# api.setup()


# db.create_tables([Zone, Route, Group, ZoneGroup, User])
Group.create_table(fail_silently=True)
ZoneGroup.create_table(fail_silently=True)
Route.create_table(fail_silently=True)
Pin.create_table(fail_silently=True)

# CORS(app)


@app.route('/pin/<string:query>', methods=['GET'])
@app.route('/pin', methods=['GET'])
def pin(query=None):
    pins = []
    print "getting pins"
    print query

    if not query:
        _pins = Pin.select(Pin.id, Pin.name, Pin.number, Zone.id.is_null().alias('is_free')).join(
            Zone, join_type='LEFT', on=(Pin.number == Zone.pin, )).dicts()
        print type(_pins)
        for p in _pins:
            print type(p)
            pins.append(p)
        return jsonify(pins)

    elif query == 'free':
        _pins = Pin.select().join(Zone, join_type='LEFT',
                                  on=(Pin.number == Zone.pin), ).where(Zone.id == None)
        print 'free'

    elif query == 'used':
        _pins = Pin.select().join(Zone,
                                  on=(Pin.number == Zone.pin))
        print 'used'

    elif int(query):
        _pins = Pin.get(query)
        print type(_pins)
        print 'single'
        pins.append(model_to_dict(_pins))
        return jsonify(pins)

    for p in _pins:
        pins.append(model_to_dict(p))
    print pins
    return jsonify(pins)


@app.route('/zone/<int:id_>', methods=['GET'])
@app.route('/zone', methods=['GET', 'POST', 'PUT'])
# @cross_origin(origins="http://localhost:3000")
def zone(id_=None):
    print "Incoming {} request".format(request.method)
    print "Params: " + json.dumps(request.json)
    """
        This is the Zone API
        Call this api passing params for a zone
        ---
        tags:
            - Zone API
        parameters:
          - name: id_
          - type: string
          - required: false
          - description: id of the zone
        responses:
          500:
            description: server error
          200:
            description: Here's your zone
            schema:
              id: zone
              properties:
                name:
                  type: string
                  description: name of the zone
                  default: A friendly zone name
                category:
                  type: array
                  description: zone category
                  items:
                    type: string
                  default: ["primary", "secondary"]
                description:
                  type: string
                  description: description of the zone
                  default: A friendly zone description
                pin:
                  type: int
                  description: pin number
                  default: 1
    """

    if request.method == 'GET':
        if id_:
            zone = Zone[id_]
            out = model_to_dict(zone)
        else:
            zones = Zone.select()
            out = []
            for zone in zones:
                out.append(model_to_dict(zone))
        return jsonify(out)

    elif request.method == 'PUT':
        data = request.json
        id = data['id']
        zone = Zone.get(Zone.id == id)
        print "zone found: ", model_to_dict(zone)
        query = Zone.update(
            name=data['name'],
            description=data['description'],
            category=data['category'],
            pin=data['pin']
        ).where(Zone.id == id)
        query.execute()

        zone = Zone.get(Zone.id == id)
        return jsonify(model_to_dict(zone))
    elif request.method == 'POST':
        zone = Zone.create(**request.json)
        zone.save()
        return jsonify(model_to_dict(zone))
    # elif request.method == 'OPTIONS':
    #     return "hello zone"


def get_group_zones(id_):
    """ Returns list of zones that are in group id_
    """
    out = []
    group = (Zone.select()
             .join(ZoneGroup, on=(ZoneGroup.zone == Zone.id))
             .join(Group, on=(ZoneGroup.group == Group.id))
             .where(ZoneGroup.group == id_)
             )
    for g in group:
        out.append(model_to_dict(g))
    return out


@app.route('/group/<int:id_>', methods=['GET'])
@app.route('/group', methods=['GET', 'POST'])
def group(id_=None):
    if request.method == 'GET':
        if id_:
            out = get_group_zones(id_)
        return jsonify(out)

    elif request.method == 'POST':
        zone_group = request.json
        group = Group.create(**zone_group['group'])
        group.save()
        for zoneId in zone_group['zones']:
            zone_group_ = ZoneGroup.create(zone=zoneId, group=group)
            zone_group_.save()

        return jsonify(model_to_dict(group))


@app.route('/route/<int:id>', methods=['GET'])
@app.route('/route', methods=['GET', 'PUT', 'POST'])
def route(id=None):
    if request.method == 'GET':
        if id is None:
            # print "none"
            # output = {
            #    "error": "No results found. Check url again"
            #}
            routes = []
            r = Route.select()
            for r_ in r:
                out = model_to_dict(r_)
                out['passthrough_group']['zones'] = get_group_zones(
                    r_.passthrough_group.id)
                out['target_group']['zones'] = get_group_zones(
                    r_.target_group.id)
                routes.append(out)
            res = jsonify(routes)
            #res.status_code = 404
            return res

        print id
        out = []
        route = Route.get(id)
        # for g in group:
        #    out.append(model_to_dict(g))
        out = model_to_dict(route)
        print out
        out['passthrough_group']['zones'] = get_group_zones(
            route.passthrough_group.id)
        out['target_group']['zones'] = get_group_zones(
            route.target_group.id)
        return jsonify(out)
    elif request.method == 'PUT':
        print "Updating route"
        data = request.json
        print data
        id = data['id']
        route = Route.get(id)

        ZoneGroup.delete().where(ZoneGroup.group_id.in_([
            route.target_group.id, route.passthrough_group.id])).execute()

        target = data['target_group']
        t_group = Group.get(Group.id == route.target_group.id)

        for zone in target:
            t_zone_group = ZoneGroup.create(zone=zone, group=t_group)
            t_zone_group.save()

        passthrough = data['passthrough_group']
        p_group = Group.get(Group.id == route.passthrough_group.id)

        for zone in passthrough:
            p_zone_group = ZoneGroup.create(zone=zone, group=p_group)
            p_zone_group.save()

        print "updating route {} {}".format(type(id), id)
        query = Route.update(
            name=data['name'],
            description=data['description'],
            source_zone=data['source_zone']).where(Route.id == id)
        print query.execute()

        route = Route.get(id)
        out = model_to_dict(route)
        out['passthrough_group']['zones'] = get_group_zones(
            route.passthrough_group.id)
        out['target_group']['zones'] = get_group_zones(
            route.target_group.id)
        return jsonify(out)

    elif request.method == 'POST':
        """
        create group 
        for each zone in target:
            add to zonegroup
        for each zone in passthrough:
            add to zonegroup
        create route with source, target, passthrough IDs
        """
        data = request.json
        print data
        target = data['target_group']
        passthrough = data['passthrough_group']

        t_group = Group.create(name='aGroup', description='aDescription')
        t_group.save()

        for zone in target:
            t_zone_group = ZoneGroup.create(zone=zone, group=t_group)
            t_zone_group.save()

        p_group = Group.create(name='aGroup', description='aDescription')
        p_group.save()

        for zone in passthrough:
            p_zone_group = ZoneGroup.create(zone=zone, group=p_group)
            p_zone_group.save()

        route = Route.create(
            name=data['name'],
            description=data['description'],
            source_zone=data['source_zone'],
            target_group=t_group,
            passthrough_group=p_group)
        route.save()
        out = model_to_dict(route)
        out['passthrough_group']['zones'] = get_group_zones(
            route.passthrough_group.id)
        out['target_group']['zones'] = get_group_zones(
            route.target_group.id)
        return jsonify(out)


if __name__ == '__main__':
    app.run("0.0.0.0", 5000, debug=True)
