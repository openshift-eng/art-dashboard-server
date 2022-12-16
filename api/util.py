import asyncio
from typing import Union, Tuple, List

import cachetools
import datetime
import re
import requests
from fcntl import fcntl, F_GETFL, F_SETFL
import koji
import logging
import os
import shlex
import subprocess
from threading import RLock
import time
from api.kerberos import do_kinit
import functools
import traceback

logger = logging.getLogger()


def cmd_gather(cmd, set_env=None, cwd=None, realtime=False):
    """
    Runs a command and returns rc,stdout,stderr as a tuple.

    If called while the `Dir` context manager is in effect, guarantees that the
    process is executed in that directory, even if it is no longer the current
    directory of the process (i.e. it is thread-safe).

    :param cmd: The command and arguments to execute
    :param cwd: The directory from which to run the command
    :param set_env: Dict of env vars to set for command (overriding existing)
    :param realtime: If True, output stdout and stderr in realtime instead of all at once.
    :return: (rc,stdout,stderr)
    """

    if not isinstance(cmd, list):
        cmd_list = shlex.split(cmd)
    else:
        cmd_list = cmd

    cmd_info = '[cwd={}]: {}'.format(cwd, cmd_list)

    env = os.environ.copy()
    if set_env:
        cmd_info = '[env={}] {}'.format(set_env, cmd_info)
        env.update(set_env)

    # Make sure output of launched commands is utf-8
    env['LC_ALL'] = 'en_US.UTF-8'

    logger.debug("Executing:cmd_gather {}".format(cmd_info))
    try:
        proc = subprocess.Popen(
            cmd_list, cwd=cwd, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        logger.error("Subprocess errored running:\n{}\nWith error:\n{}\nIs {} installed?".format(
            cmd_info, exc, cmd_list[0]
        ))
        return exc.errno, "", "Subprocess errored running:\n{}\nWith error:\n{}\nIs {} installed?".format(
            cmd_info, exc, cmd_list[0]
        )

    if not realtime:
        out, err = proc.communicate()
        rc = proc.returncode
    else:
        out = b''
        err = b''

        # Many thanks to http://eyalarubas.com/python-subproc-nonblock.html
        # setup non-blocking read
        # set the O_NONBLOCK flag of proc.stdout file descriptor:
        flags = fcntl(proc.stdout, F_GETFL)  # get current proc.stdout flags
        fcntl(proc.stdout, F_SETFL, flags | os.O_NONBLOCK)
        # set the O_NONBLOCK flag of proc.stderr file descriptor:
        flags = fcntl(proc.stderr, F_GETFL)  # get current proc.stderr flags
        fcntl(proc.stderr, F_SETFL, flags | os.O_NONBLOCK)

        rc = None
        while rc is None:
            output = None
            try:
                output = os.read(proc.stdout.fileno(), 256)
                logger.info(f'{cmd_info} stdout: {out.rstrip()}')
                out += output
            except OSError:
                pass

            error = None
            try:
                error = os.read(proc.stderr.fileno(), 256)
                logger.warning(f'{cmd_info} stderr: {error.rstrip()}')
                out += error
            except OSError:
                pass

            rc = proc.poll()
            time.sleep(0.0001)  # reduce busy-wait

    # We read in bytes representing utf-8 output; decode so that python recognizes them as unicode strings
    out = out.decode('utf-8')
    err = err.decode('utf-8')
    logger.debug(
        "Process {}: exited with: {}\nstdout>>{}<<\nstderr>>{}<<\n".
        format(cmd_info, rc, out, err))
    return rc, out, err


def koji_client_session():
    koji_api = koji.ClientSession('https://brewhub.engineering.redhat.com/brewhub')
    koji_api.hello()  # test for connectivity
    return koji_api


LOCK = RLock()
CACHE = cachetools.LRUCache(maxsize=2000)


def cached(func):
    """decorator to memoize functions"""

    @cachetools.cached(CACHE, lock=LOCK)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


CACHE_TTL = cachetools.TTLCache(maxsize=100, ttl=3600)  # expire after an hour


def cached_ttl(func):
    """decorator to memoize functions"""

    @cachetools.cached(CACHE_TTL, lock=LOCK)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def refresh_krb_auth(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        do_kinit()
        func_ret = func(*args, **kwargs)
        return func_ret

    return wrapper


def get_ga_version():
    """
    Get the latest GA version from https://github.com/openshift/cincinnati-graph-data/tree/master/channels
    The highest version in the fast channel is considered GA.
    """
    headers = {"Authorization": f"token {os.environ['GITHUB_PERSONAL_ACCESS_TOKEN']}"}
    response = requests.get(
        "https://api.github.com/repos/openshift/cincinnati-graph-data/git/trees/master?recursive=1",
        headers=headers
    )

    versions = []

    for data in response.json()['tree']:
        path: str = data['path']

        regex = r"channels/fast-(?P<version>\d+.\d+).yaml"

        if path.startswith("channels/fast"):
            m = re.match(regex, path)
            if m:
                version: str = m.groupdict()['version']
                versions.append(tuple(map(int, version.split("."))))
    ga_version = sorted(versions, key=lambda x: (-x[0], -x[1]))[0]

    return f"{ga_version[0]}.{ga_version[1]}"
