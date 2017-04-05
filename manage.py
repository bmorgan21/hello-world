# coding: utf-8

import argparse
import logging
import os
import shlex
import subprocess
import sys

logger = logging.getLogger(__name__)


BASEDIR = os.path.dirname(os.path.abspath(__file__))
NS = 'hello'
NAME = 'hw'


ENABLE_CELERY = os.getenv('CELERY') == 'enabled'


def _check_call(command, show_stdout=True, show_stderr=True):
    with open(os.devnull, 'w') as devnull:
        stdout = sys.stdout if show_stdout else devnull
        stderr = sys.stderr if show_stderr else devnull
        subprocess.check_call(shlex.split(command), stdout=stdout, stderr=stderr)


def _check_output(command, show_stderr=True):
    with open(os.devnull, 'w') as devnull:
        stderr = sys.stderr if show_stderr else devnull
        return subprocess.check_output(shlex.split(command), stderr=stderr, universal_newlines=True)


def _popen(command, wait=True, show_stdout=True, show_stderr=True):
    with open(os.devnull, 'w') as devnull:
        stdout = sys.stdout if show_stdout else devnull
        stderr = sys.stderr if show_stderr else devnull

        proc = subprocess.Popen(shlex.split(command), stdout=stdout, stderr=stderr)
        if wait:
            return proc.wait()
        return proc


def _docker_compose(cmd, check_call=False):
    additional_compose_files = []
    if ENABLE_CELERY:
        additional_compose_files.append('hello-celery.yml')

    docker_call = 'docker-compose -f hello.yml {} -p {} {}'.format(' '.join(
        ['-f {}'.format(x) for x in additional_compose_files]), NAME, cmd)

    if check_call:
        _check_call(docker_call)
    else:
        _popen(docker_call)


def hash_path(path):
    output = _check_output('git log --oneline --color=never --abbrev=7 -n1 -- {}'.format(path))
    return output.strip().split(' ')[0] or 'default'


def _check_local_requirements():
    local_pip_deps = set(_check_output('pip3 freeze', show_stderr=False).splitlines())

    with open('requirements.txt', 'r') as requirements_file:
        file_pip_deps = [x.replace(' ', '').strip() for x in requirements_file.readlines()]
        file_pip_deps = set([x for x in file_pip_deps if x and not x.startswith('#')])

        missing_deps = file_pip_deps - local_pip_deps

        if missing_deps:
            details = []
            for dep in missing_deps:
                split_dep = dep.split('==', 1)
                name = split_dep[0]
                version = '??'
                if len(split_dep) == 2:
                    version = split_dep[1]

                for dep2 in local_pip_deps:
                    if dep2.startswith('-'):
                        continue
                    name2, version2 = dep2.split('==', 1)
                    if name == name2:
                        break
                else:
                    version2 = '??'

                details.append('{} ({} => {})'.format(name, version, version2))

            logger.error('Missing Requirements: {}'.format(', '.join(details)))
            logger.error('Run `pip3 install -r requirements.txt` locally to resolve.')
            sys.exit(1)


def up(args):
    _docker_compose('up')


def kill(args):
    _docker_compose('kill', check_call=True)


def nuke(args):
    _docker_compose('rm -vf', check_call=True)


def build(args):
    hello_version = hash_path("hello")
    print('BUILDING: {}'.format(hello_version))
    _check_call('docker build -t {}/hello:{} hello'.format(NS, hello_version))

    _check_call('sed -i "s#image: hello/hello:.*#image: hello/hello:{}#" hello.yml'.format(hello_version))


def _assure_clean(path):
    r = _check_output('git status --porcelain {}'.format(path)).strip()
    if r:
        raise Exception('{} is dirty, please commit changes before attempting to push image:\n{}'.format(path, r))


def push(args):
    build(args)

    if not args.images or 'hello' in args.images:
        _assure_clean('hello')
        hello_version = hash_path("hello")
        _check_call(r'docker push {}/hello:{}'.format(NS, hello_version))


def test(args):
    logger.debug('Running Tests')

    _check_local_requirements()

    try:
        _check_call('flake8 .')
    except Exception:
        sys.exit(1)

    logger.info('Tests passed')


def envtest(args):
    pass


def shell(args):
    _popen('docker exec -it {}_web_1 /bin/bash {}'.format(NAME, '-c "{}"'.format(args.command) if args.command else ''))


def db(args):
    if args.args[0] == 'shell':
        _popen('docker exec -it {}_db_1 /bin/bash -c \'mysql -u root -p"$MYSQL_ROOT_PASSWORD" hw_app\''.format(NAME))
    else:
        _popen('docker exec -it {}_web_1 flask db {}'.format(NAME, ' '.join(args.args)))

        if args.args[0] == 'migrate':
            # use this to help create merge conflicts
            with open('hello/migrations/head', 'w') as f:
                f.write(_check_output('docker exec {}_web_1 flask db heads'.format(NAME)))


def py(args):
    if args.args[0] == 'shell':
        _popen('docker exec -it {}_web_1 flask shell {}'.format(NAME, ' '.join(args.args[1:])))


def main():
    os.chdir(BASEDIR)

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', help='Add verbose logging', dest='verbose', action='store_true')

    subparsers = parser.add_subparsers(dest='cmdstr')

    up_parser = subparsers.add_parser('up', help='Start')
    up_parser.set_defaults(cmd=up)

    nuke_parser = subparsers.add_parser('nuke', help='Destroy containers and volumes')
    nuke_parser.set_defaults(cmd=nuke)

    build_parser = subparsers.add_parser('build', help='Build images')
    build_parser.set_defaults(cmd=build)

    push_parser = subparsers.add_parser('push', help='push images')
    push_parser.set_defaults(cmd=push)
    push_parser.add_argument('images', nargs='*', help='Specific images to push')

    test_parser = subparsers.add_parser('test', help='test')
    test_parser.set_defaults(cmd=test)

    envtest_parser = subparsers.add_parser('envtest', help='Validation tests that check the environment are correct')
    envtest_parser.set_defaults(cmd=envtest)

    shell_parser = subparsers.add_parser('shell', help='Launch a bash shell on the web instance')
    shell_parser.set_defaults(cmd=shell)
    shell_parser.add_argument('-c', dest='command')

    db_parser = subparsers.add_parser('db', help='Launch db commands')
    db_parser.set_defaults(cmd=db)
    db_parser.add_argument('args', nargs=argparse.REMAINDER)

    py_parser = subparsers.add_parser('py', help='Launch python commands')
    py_parser.set_defaults(cmd=py)
    py_parser.add_argument('args', nargs=argparse.REMAINDER)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    args.cmd(args)


if __name__ == '__main__':
    main()
