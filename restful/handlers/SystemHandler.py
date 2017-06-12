# -*- coding: UTF-8 -*-
import json
import re

from flask_restful import Resource, request
from werkzeug.exceptions import BadRequest

from app import db
from app.models import DataSource, DataSourceType, Operation, TradeSystem


class SystemApi(Resource):
    def get(self, **kwargs):
        sys = TradeSystem.find(**kwargs)
        if sys:
            return {
                "message": 'system({}) found succeefully.'.format(sys.name.encode('utf-8')),
                "data": sys.to_json()
            }
        else:
            return {'message': 'system not found'}, 404

    def put(self, **kwargs):
        sys = TradeSystem.find(**kwargs)
        if sys:
            try:
                data = request.get_json(force=True)
            except BadRequest:
                return {'message': 'Invalid JSON data'}, 400
            else:
                sys.name = data.get('name', sys.name)
                sys.user = data.get('username', sys.user)
                sys.password = data.get('password', sys.password)
                sys.ip = data.get('ip', sys.ip)
                sys.description = data.get('description', sys.description)
                sys.version = data.get('version', sys.version)
                for op in Operation.query.filter(
                        Operation.sys_id == sys.id
                    ):
                    details = json.loads(json.dumps(op.detail))
                    params = details['remote']['params']
                    params['ip'] = sys.ip
                    params['user'] = sys.user
                    params['password'] = sys.login_pwd
                    op.detail = details
                    db.session.add(op)
                for ds in DataSource.query.filter(
                        DataSource.src_type == DataSourceType.FILE
                    ):
                    source = json.loads(json.dumps(ds.source))
                    source['uri'] = re.sub(
                        '^(?P<header>[^:]+)://([^:]+):([^@]+)@([^:]+):(?P<tailer>.+)$',
                        lambda matchs: matchs.group('header') + \
                            "://" + sys.user + ":" + sys.login_pwd + \
                            "@" + sys.ip + ":" + matchs.group('tailer'),
                        source['uri']
                    )
                    ds.source = source
                    db.session.add(ds)
                db.session.add(sys)
                db.session.commit()
                return {
                    'message': 'system ({}) updated successfully.'.format(sys.name),
                    'data': sys.to_json()
                }, 200
        else:
            return {'message': 'system not found'}, 404

class SystemListApi(Resource):
    def get(self):
        systems = TradeSystem.query.filter(TradeSystem.parent_sys_id==None).all()
        if systems:
            return {
                'message': 'all systems listed.',
                'data': {
                    'count': len(systems),
                    'records': [
                        sys.to_json() for sys in systems
                    ]
                }
            }
        else:
            return {
                'message': 'no systems.'
            }, 204
