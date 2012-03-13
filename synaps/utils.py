# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Samsung SDS
# All Rights Reserved.

import os
import sys
import uuid
import datetime
import pyclbr
import inspect
import socket
import re

from synaps import flags
from synaps import exception
from synaps import log as logging
from synaps.openstack.common import cfg

LOG = logging.getLogger(__name__)
PERFECT_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
FLAGS = flags.FLAGS

FLAGS.register_opt(
    cfg.BoolOpt('disable_process_locking', default=False,
                help='Whether to disable inter-process locks'))

def gen_uuid():
    return uuid.uuid4()

def utcnow():
    """Overridable version of utils.utcnow."""
    if utcnow.override_time:
        return utcnow.override_time
    return datetime.datetime.utcnow()

utcnow.override_time = None

def parse_strtime(timestr, fmt=PERFECT_TIME_FORMAT):
    """Turn a formatted time back into a datetime."""
    return datetime.datetime.strptime(timestr, fmt)

def strtime(at=None, fmt=PERFECT_TIME_FORMAT):
    """Returns formatted utcnow."""
    if not at:
        at = utcnow()
    return at.strftime(fmt)

def utf8(value):
    """Try to turn a string into utf-8 if possible.

    Code is directly from the utf8 function in
    http://github.com/facebook/tornado/blob/master/tornado/escape.py

    """
    if isinstance(value, unicode):
        return value.encode('utf-8')
    assert isinstance(value, str)
    return value

def import_class(import_str):
    """Returns a class from a string including module and class."""
    mod_str, _sep, class_str = import_str.rpartition('.')
    try:
        __import__(mod_str)
        return getattr(sys.modules[mod_str], class_str)
    except (ImportError, ValueError, AttributeError), exc:
        LOG.debug(_('Inner Exception: %s'), exc)
        raise exception.ClassNotFound(class_name=class_str, exception=exc)

def monkey_patch():
    """  If the Flags.monkey_patch set as True,
    this function patches a decorator
    for all functions in specified modules.
    You can set decorators for each modules
    using FLAGS.monkey_patch_modules.
    The format is "Module path:Decorator function".
    Example: 'nova.api.ec2.cloud:nova.notifier.api.notify_decorator'

    Parameters of the decorator is as follows.
    (See nova.notifier.api.notify_decorator)

    name - name of the function
    function - object of the function
    """
    # If FLAGS.monkey_patch is not True, this function do nothing.
    if not FLAGS.monkey_patch:
        return
    # Get list of modules and decorators
    for module_and_decorator in FLAGS.monkey_patch_modules:
        module, decorator_name = module_and_decorator.split(':')
        # import decorator function
        decorator = import_class(decorator_name)
        __import__(module)
        # Retrieve module information using pyclbr
        module_data = pyclbr.readmodule_ex(module)
        for key in module_data.keys():
            # set the decorator for the class methods
            if isinstance(module_data[key], pyclbr.Class):
                clz = import_class("%s.%s" % (module, key))
                for method, func in inspect.getmembers(clz, inspect.ismethod):
                    setattr(clz, method,
                        decorator("%s.%s.%s" % (module, key, method), func))
            # set the decorator for the function
            if isinstance(module_data[key], pyclbr.Function):
                func = import_class("%s.%s" % (module, key))
                setattr(sys.modules[module], key,
                    decorator("%s.%s" % (module, key), func))


def default_flagfile(filename='synaps.conf', args=None):
    if args is None:
        args = sys.argv
    for arg in args:
        if arg.find('flagfile') != -1:
            return arg[arg.index('flagfile') + len('flagfile') + 1:]
    else:
        if not os.path.isabs(filename):
            # turn relative filename into an absolute path
            script_dir = os.path.dirname(inspect.stack()[-1][1])
            filename = os.path.abspath(os.path.join(script_dir, filename))
        if not os.path.exists(filename):
            filename = "./synaps.conf"
            if not os.path.exists(filename):
                filename = '/etc/synaps/synaps.conf'
        if os.path.exists(filename):
            flagfile = '--flagfile=%s' % filename
            args.insert(1, flagfile)
            return filename
                
def find_config(config_path):
    """Find a configuration file using the given hint.

    :param config_path: Full or relative path to the config.
    :returns: Full path of the config, if it exists.
    :raises: `synaps.exception.ConfigNotFound`

    """
    possible_locations = [
        config_path,
        os.path.join(FLAGS.state_path, "etc", "synaps", config_path),
        os.path.join(FLAGS.state_path, "etc", config_path),
        os.path.join(FLAGS.state_path, config_path),
        "/etc/synaps/%s" % config_path,
    ]

    for path in possible_locations:
        if os.path.exists(path):
            return os.path.abspath(path)

    raise exception.ConfigNotFound(path=os.path.abspath(config_path))     

def cleanup_file_locks():
    """clean up stale locks left behind by process failures

    The lockfile module, used by @synchronized, can leave stale lockfiles
    behind after process failure. These locks can cause process hangs
    at startup, when a process deadlocks on a lock which will never
    be unlocked.

    Intended to be called at service startup.

    """

    # NOTE(mikeyp) this routine incorporates some internal knowledge
    #              from the lockfile module, and this logic really
    #              should be part of that module.
    #
    # cleanup logic:
    # 1) look for the lockfile modules's 'sentinel' files, of the form
    #    hostname.[thread-.*]-pid, extract the pid.
    #    if pid doesn't match a running process, delete the file since
    #    it's from a dead process.
    # 2) check for the actual lockfiles. if lockfile exists with linkcount
    #    of 1, it's bogus, so delete it. A link count >= 2 indicates that
    #    there are probably sentinels still linked to it from active
    #    processes.  This check isn't perfect, but there is no way to
    #    reliably tell which sentinels refer to which lock in the
    #    lockfile implementation.

    if  FLAGS.disable_process_locking:
        return

    hostname = socket.gethostname()
    sentinel_re = hostname + r'\..*-(\d+$)'
    lockfile_re = r'synaps-.*\.lock'
    files = os.listdir(FLAGS.lock_path)

    # cleanup sentinels
    for filename in files:
        match = re.match(sentinel_re, filename)
        if match is None:
            continue
        pid = match.group(1)
        LOG.debug(_('Found sentinel %(filename)s for pid %(pid)s' %
                    {'filename': filename, 'pid': pid}))
        if not os.path.exists(os.path.join('/proc', pid)):
            delete_if_exists(os.path.join(FLAGS.lock_path, filename))
            LOG.debug(_('Cleaned sentinel %(filename)s for pid %(pid)s' %
                        {'filename': filename, 'pid': pid}))

    # cleanup lock files
    for filename in files:
        match = re.match(lockfile_re, filename)
        if match is None:
            continue
        try:
            stat_info = os.stat(os.path.join(FLAGS.lock_path, filename))
        except OSError as (errno, strerror):
            if errno == 2:  # doesn't exist
                continue
            else:
                raise
        msg = _('Found lockfile %(file)s with link count %(count)d' %
                {'file': filename, 'count': stat_info.st_nlink})
        LOG.debug(msg)
        if stat_info.st_nlink == 1:
            delete_if_exists(os.path.join(FLAGS.lock_path, filename))
            msg = _('Cleaned lockfile %(file)s with link count %(count)d' %
                    {'file': filename, 'count': stat_info.st_nlink})
            LOG.debug(msg)
            
def delete_if_exists(pathname):
    """delete a file, but ignore file not found error"""

    try:
        os.unlink(pathname)
    except OSError as (errno, strerror):
        if errno == 2:  # doesn't exist
            return
        else:
            raise                       
