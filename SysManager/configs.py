# -*- coding: UTF-8 -*-
import logging
import sys
from os import path, environ
import ConfigParser
from enum import Enum
sys.path.append(path.join(path.dirname(sys.argv[0]), '../'))
from excepts import ConfigInvalid
from flask import current_app
from Common import AESCrypto
import re

SECRET_KEY = environ.get('FLASK_SECRET_KEY') or 'SOMEthing-you-WILL-never-Guess'

class GlobalConfig:
    default_ssh_user = None
    default_ssh_key = None

    def __init__(self):
        global_file = path.join(
            path.dirname(sys.argv[0]),
            'Conf',
            'Global.ini'
        )
        if path.exists(global_file):
            ini = ConfigParser.ConfigParser()
            ini.read(global_file)
            for key in [x for x in dir(self) if not x.startswith('_')]:
                try:
                    setattr(self, key, ini.get('Global', key))
                except ConfigParser.NoSectionError:
                    logging.warning(
                        'No section[Global] in INI file({})'\
                            .format(global_file)
                    )
                    break
                except ConfigParser.NoOptionError:
                    continue

class RemoteConfig(object):
    def __init__(self, ip, user, password, port):
        self._reg = re.compile('^[0-9a-f]{32}$')
        self.remote_host = ip
        self.remote_port = port
        self.remote_user = user
        if self._reg.match(password):
            self.remote_password = AESCrypto.decrypt(
                password,
                SECRET_KEY
            )
        else:
            self.remote_password = password

    @staticmethod
    def Create(sub_class, params):
        return globals()[sub_class](**params)

class SSHConfig(RemoteConfig):
    def __init__(self, ip, user, password=None, port=22, pKey=None, key_pass=None):
        if not password and not pKey:
            raise ConfigInvalid('Either "password" or "pKey" must be specified.')
        self.ssh_key = pKey
        self.ssh_key_pass = key_pass
        RemoteConfig.__init__(self, ip, user, password, port)

class WinRmConfig(RemoteConfig):
    def __init__(self, ip, user, password, port=5986):
        RemoteConfig.__init__(self, ip, user, password, port)

class HttpConfig(RemoteConfig):
    def __init__(self, ip, user=None, password=None, port=8080, **kwargs):
        RemoteConfig.__init__(self, ip, user, password, port)
        self.cookies = kwargs.get('cookies')

class Result:
    destination = None
    module = None
    return_code = 0
    error_msg = ""
    data = {}
    lines = []

if __name__ == '__main__':
    conf = GlobalConfig()
    print conf.__dict__