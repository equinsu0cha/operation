# -*- coding: UTF-8 -*-


def run(client, module):
    command = module.get('shell')
    args = module.get('args')
    if args and 'chdir' in args:
        base_dir = args.get('chdir')
        command = (
            'PATH=$PATH:.:/bin:/sbin;'
            'PATH=$PATH:/usr/local/bin:/usr/local/sbin;'
            'PATH=$PATH:/usr/bin:/usr/sbin;'
            'PATH=$PATH:~/bin;'
            'export PATH;'
            'export LD_LIBRARY_PATH=.:$LD_LIBRARY_PATH;'
            'export LANG=en_US.UTF-8;'
            '[ -f .bash_profile ] && source .bash_profile;'
            'cd "{}";{}'
        ).format(base_dir, command)
    else:
        command = (
            'PATH=$PATH:.:/bin:/sbin;'
            'PATH=$PATH:/usr/local/bin:/usr/local/sbin;'
            'PATH=$PATH:/usr/bin:/usr/sbin;'
            'PATH=$PATH:~/bin;'
            'export PATH;'
            'export LD_LIBRARY_PATH=.:$LD_LIBRARY_PATH;'
            'export LANG=en_US.UTF-8;'
            '[ -f .bash_profile ] && source .bash_profile;'
            '{}'
        ).format(command)
    stdin, stdout, stderr = client.exec_command(command)
    stdout.read = change_read_encoding(stdout.read())
    stdout.readlines = change_readlines_encoding(stdout.read())
    stderr.read = change_read_encoding(stderr.read())
    stderr.readlines = change_readlines_encoding(stderr.read())
    return stdout, stderr


def change_read_encoding(cache):
    def _read():
        try:
            return cache.decode('utf-8').replace('\r\n', '\n')
        except UnicodeDecodeError:
            return cache.decode('gbk', 'ignore').replace('\r\n', '\n')

    return _read


def change_readlines_encoding(cache):
    def _readlines():
        for line in cache.split('\n'):
            if line != "":
                yield line

    return _readlines
