# -*- coding: UTF-8 -*-
from flask_restful import Resource
from app.models import OperationBook, ScriptType, TradeSystem, PlatformType, OperationCatalog
from flask import request
from werkzeug.exceptions import BadRequest
from app import db
from ..errors import DataNotJsonError, DataUniqueError, DataNotNullError, DataEnumValueError, PlatFormNotFoundError
from ..output import Output
import paramiko


class OperationBookAddApi(Resource):
    def __init__(self):
        super(OperationBookAddApi, self).__init__()

    def get(self):
        script_type_name = {'Checker': '检查',
                            'Executor': '执行',
                            'Interactivator': '交互',
                            'Execute_Checker': '检查和执行',
                            'Interactive_Checker': '检查和交互'}
        script_types = ScriptType._member_names_
        systems = TradeSystem.query.all()
        catalogs = OperationCatalog.query.all()
        system_list = []
        for sys in systems:
            system_list.append(dict(sys_id=sys.id, sys_name=sys.name))
        catalog_list = []
        for cl in catalogs:
            catalog_list.append(dict(catalog_id=cl.id, catalog_name=cl.name))
        script_type_list = []
        for name in script_types:
            script_type_list.append(dict(alias=script_type_name[name], name=name))
            # script_type_list.append(dict(name=name, type=ScriptType[name].value))
        return {'message': 'All data listed',
                'error_code': 0,
                'data': {'systems': system_list, 'script_types': script_type_list,
                         'catalogs': catalog_list}}

    def post(self):
        try:
            data = request.get_json(force=True)
        except BadRequest:
            try:
                raise DataNotJsonError
            except DataNotJsonError:
                return Output(DataNotJsonError())
        else:
            try:
                if not data.get('name') or not data.get('sys_id') or not data.get('mod'):
                    raise DataNotNullError
                elif OperationBook.query.filter_by(name=data.get('name')).first() is not None:
                    raise DataUniqueError
                elif data.get('type') is not None:
                    try:
                        ScriptType[data.get('type')]
                    except KeyError:
                        raise DataEnumValueError
                ob = OperationBook()
                ob.name = data.get('name')
                ob.description = data.get('description')
                ob.type = ScriptType[data.get('type')]
                # ob.order = data.get('order')
                ob.catalog_id = data.get('catalog_id')
                ob.sys_id = data.get('sys_id')
                ob.is_emergency = data.get('is_emergency')

                system = TradeSystem.find(id=data.get('sys_id'))
                if system:
                    if system.servers.first().platform is not None:
                        if system.servers.first().platform == PlatformType.Linux or data.get(
                                        'remote_name' == 'SSHConfig'):
                            params_dict = dict(ip=system.ip, user=system.user, password=system.password)
                            remote_dict = dict(name='SSHConfig', params=params_dict)
                            mod_list = []
                            mod_data = data.get('mod')
                            for j in xrange(len(mod_data)):
                                if mod_data[j].get('chdir'):
                                    mod_list.append(dict(name='shell',
                                                         shell=mod_data[j].get('shell'),
                                                         args=dict(chdir=mod_data[j].get('chdir'))))
                                else:
                                    mod_list.append(dict(name='shell', shell=mod_data[j].get('shell')))
                            detail_dict = dict(remote=remote_dict, mod=mod_list)
                    else:
                        return Output(PlatFormNotFoundError())

                    ob.detail = detail_dict
                else:
                    return {'message': 'System not found.'}, 404

            except DataNotNullError:
                return Output(DataNotNullError())
            except DataUniqueError:
                return Output(DataUniqueError())
            except DataEnumValueError:
                return Output(DataEnumValueError())
            else:
                db.session.add(ob)
                db.session.commit()
                return Output(ob)


class OperationBookCheckApi(Resource):
    def __init__(self):
        super(OperationBookCheckApi, self).__init__()

    '''def get(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('192.168.101.126', 22, 'qdam', 'qdam')
        chdir = ''
        file_name = 'startall'
        if chdir:
            stdin, stdout, stderr = ssh.exec_command(
                'cd {0};if [ -f {1} ];then echo 0;else echo 1;fi'.format(chdir, file_name))
        else:
            stdin, stdout, stderr = ssh.exec_command(
                'ls'.format(file_name))

        ans = stdout.readlines()
        ssh.close()

        return ans'''

    def post(self):
        try:
            data = request.get_json(force=True)
        except BadRequest:
            try:
                raise DataNotJsonError
            except DataNotJsonError:
                return Output(DataNotJsonError())
        else:
            try:
                if not data.get('shell'):
                    raise DataNotNullError
            except DataNotNullError:
                return Output(DataNotNullError())
            else:
                file_name, chdir = data.get('shell'), data.get('chdir')
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect('192.168.101.126', 22, 'qdam', 'qdam')
                if chdir:
                    stdin, stdout, stderr = ssh.exec_command(
                        'cd {0};if [ -f {1} ];then echo 0;else echo 1;fi'.format(chdir, file_name))
                else:
                    stdin, stdout, stderr = ssh.exec_command(
                        'if [ -f {0} ];then echo 0;else echo 1;fi'.format(file_name))
                ans = stdout.readlines()[0]
                ssh.close()
                return ans


class OperationBookAdjustApi(Resource):
    def __init__(self):
        super(OperationBookAdjustApi, self).__init__()

    def get(self, **kwargs):
        op_book = OperationBook.find(**kwargs)
        if op_book is not None:
            return Output(op_book)
        else:
            return {'message': 'Not found'}, 404

    def put(self, **kwargs):
        op_book = OperationBook.find(**kwargs)
        if op_book is not None:
            try:
                data = request.get_json(force=True)
            except BadRequest:
                try:
                    raise DataNotJsonError
                except DataNotJsonError:
                    return Output(DataNotJsonError())
            else:
                try:
                    if op_book.name != data.get('name') and OperationBook.query.filter_by(
                            name=data.get('name')).first() is not None:
                        raise DataUniqueError
                    elif data.get('type') is not None:
                        try:
                            ScriptType[data.get('type')]
                        except KeyError:
                            raise DataEnumValueError
                except DataUniqueError:
                    return Output(DataUniqueError())
                except DataEnumValueError:
                    return Output(DataEnumValueError())
                else:
                    op_book.name = data.get('name', op_book.name)
                    op_book.description = data.get('description', op_book.description)
                    op_book.type = ScriptType[data.get('type')] or op_book.type
                    op_book.catalog_id = data.get('catalog_id', op_book.catalog_id)
                    op_book.sys_id = data.get('sys_id', op_book.sys_id)
                    op_book.is_emergency = data.get('is_emergency', op_book.is_emergency)
                    db.session.add(op_book)
                    db.session.commit()
                    return Output(op_book)
        else:
            return {'message': 'Not found'}, 404