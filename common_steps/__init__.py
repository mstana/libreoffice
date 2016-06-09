# -*- coding: utf-8 -*-
from __future__ import print_function
from dogtail.utils import isA11yEnabled, enableA11y
if isA11yEnabled() is False:
    enableA11y(True)
import datetime
import glob
import logging
import os
import re
import pty
import shlex
import types
from functools import wraps, partial
from os import strerror, errno
from signal import signal, alarm, SIGALRM
from subprocess import Popen, PIPE
from time import time, sleep, localtime, strftime
from unittest import TestCase

import iniparse
import fcntl
from dogtail.config import config
from dogtail.predicate import GenericPredicate
from dogtail.rawinput import keyCombo, absoluteMotion, pressKey, typeText
from dogtail.tree import root, SearchError
from dogtail.utils import GnomeShell
from gi.repository import GnomeKeyring  # pylint: disable=E0611

log = logging.getLogger('common_steps')


# Create a dummy unittest class to have nice assertions
class dummy(TestCase):
    def runTest(self):  # pylint: disable=R0201
        assert True

def get_showing_node_name(name, parent, rolename=None, timeout=30, step=0.25):
    wait = 0
    nodes = []
    while True:
        if rolename:
            nodes = parent.findChildren(lambda x: x.name == name and x.roleName == rolename and x.showing and x.sensitive)
        else:
            nodes = parent.findChildren(lambda x: x.name == name and x.showing and x.sensitive)
        if len(nodes) != 0:
            break
        sleep(step)
        wait += step
        if wait == timeout:
            raise Exception("Timeout: Node %s wasn't found showing" %name)

    return nodes[0]

def wait_until(tested, element=None, timeout=30, period=0.25, params_in_list=False):
    """
    This function keeps running lambda with specified params until the
    result is True or timeout is reached. Instead of lambda, Boolean variable
    can be used instead.
    Sample usages:
     * wait_until(lambda x: x.name != 'Loading...', context.app.instance)
       Pause until window title is not 'Loading...'.
       Return False if window title is still 'Loading...'
       Throw an exception if window doesn't exist after default timeout

     * wait_until(lambda element, expected: x.text == expected,
           (element, 'Expected text'), params_in_list=True)
       Wait until element text becomes the expected (passed to the lambda)

     * wait_until(dialog.dead)
       Wait until the dialog is dead

    """
    if isinstance(tested, bool):
        curried_func = lambda: tested
    # or if callable(tested) and element is a list or a tuple
    elif isinstance(tested, types.FunctionType) and (isinstance(element, tuple) or isinstance(element, list)) and params_in_list:
        curried_func = partial(tested, *element)
    # or if callable(tested) and element is not None?
    elif isinstance(tested, types.FunctionType) and element is not None:
        curried_func = partial(tested, element)
    else:
        curried_func = tested

    exception_thrown = None
    mustend = int(time()) + timeout
    while int(time()) < mustend:
        try:
            if curried_func():
                return True
        except Exception as e:  # pylint: disable=broad-except
            # If lambda has thrown the exception we'll re-raise it later
            # and forget about if lambda passes
            exception_thrown = e
        sleep(period)
    if exception_thrown is not None:
        raise exception_thrown  # pylint: disable=raising-bad-type
    else:
        return False


class TimeoutError(Exception):
    """
    Timeout exception class for limit_execution_time_to function
    """
    pass


def limit_execution_time_to(seconds=10, error_message=strerror(errno.ETIME)):
    """
    Decorator to limit function execution to specified limit
    """
    def decorator(func):
        def _handle_timeout(signum, frame):  # pylint: disable=W0613
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal(SIGALRM, _handle_timeout)
            alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator


def setup_gnome_keyring():
    """
    Provide clean login Gnome keyring (removes the previous one
    beforehand, if there is a one).
    """
    try:
        # Delete originally stored password
        (response, keyring) = GnomeKeyring.get_default_keyring_sync()
        log.debug('get_info default: %s, %s' % (response, keyring))
        if response == GnomeKeyring.Result.OK:
            if keyring is not None:
                delete_response = GnomeKeyring.delete_sync(keyring)
                log.debug('delete default: %s' % delete_response)
                assert delete_response == GnomeKeyring.Result.OK, \
                    "Delete failed: %s" % delete_response
            response, keyring = GnomeKeyring.get_info_sync('login')
            if response == GnomeKeyring.Result.OK:
                if keyring is not None:
                    delete_response = GnomeKeyring.delete_sync('login')
                    log.debug('delete login: %s' % delete_response)
                    assert delete_response == GnomeKeyring.Result.OK, \
                        "Delete failed: %s" % delete_response
            elif response != GnomeKeyring.Result.NO_SUCH_KEYRING:
                raise IOError(
                    'Unexpected error when manipulating login keyring')

            # This is result of the underlying DBus error:
            # CKR_WRAPPED_KEY_INVALID, CKR_WRAPPED_KEY_LEN_RANGE,
            # CKR_MECHANISM_PARAM_INVALID
            # So, failed either
            # * egg_padding_pkcs7_unpad
            #   (gnome-keyring/egg/egg-padding.c)
            # * gkm_aes_mechanism_unwrap
            #   (gnome-keyring/pkcs11/gkm/gkm-aes-mechanism.c)
            # * gkm_dh_mechanism_derive
            #   (gnome-keyring/pkcs11/gkm/gkm-dh-mechanism.c)
            # * gkm_null_mechanism_unwrap or gkm_null_mechanism_wrap
            #   (gnome-keyring/pkcs11/gkm/gkm-null-mechanism.c)
            create_response = GnomeKeyring.create_sync('login', 'redhat')
            log.debug('create login: %s' % create_response)
            if create_response != GnomeKeyring.Result.OK:
                raise IOError(
                    'Create failed: %s\n%s' %
                    (create_response,
                     GnomeKeyring.result_to_message(create_response)))

            set_default_response = \
                GnomeKeyring.set_default_keyring_sync('login')
            assert set_default_response == GnomeKeyring.Result.OK, \
                "Set default failed: %s" % set_default_response
        unlock_response = GnomeKeyring.unlock_sync("login", 'redhat')
        assert unlock_response == GnomeKeyring.Result.OK, \
            "Unlock failed: %s" % unlock_response
    except Exception as e:
        log.error("Exception while unlocking a keyring: %s", e.message)
        raise  # We shouldn’t let this exception evaporate


class App(object):
    """
    This class does all basic events with the app
    """
    def __init__(self, appName, shortcut='<Control><Q>', desktopFileName=None,
                 timeout=5, a11yAppName=None, forceKill=True, parameters='',
                 recordVideo=False, recordVideoName=None):
        """
        Initialize object App
        appName     command to run the app
        shortcut    default quit shortcut
        a11yAppName app's a11y name is different than binary
        timeout     timeout for starting and shuting down the app
        forceKill   is the app supposed to be kill before/after test?
        parameters  has the app any params needed to start? (only for
                    startViaCommand)
        recordVideo start gnome-shell recording while running the app
        recordVideoName filename template for renaming the screencast video
        desktopFileName = name of the desktop file if other than
                          appName (without .desktop extension)
        """
        self.appCommand = appName
        self.shortcut = shortcut
        self.timeout = timeout
        self.forceKill = forceKill
        self.parameters = parameters
        self.internCommand = self.appCommand.lower()
        self.a11yAppName = a11yAppName
        self.recordVideo = recordVideo
        self.recordVideoName = recordVideoName
        self.pid = None

        # a way of overcoming overview autospawn when mouse in 1,1 from start
        pressKey('Esc')
        absoluteMotion(100, 100, 2)

        # set correct desktop file name
        if desktopFileName is None:
            desktopFileName = self.appCommand
        self.desktopFileName = desktopFileName

        # attempt to make a recording of the test
        if self.recordVideo:
            # Screencasts stop after 30 secs by default, see https://bugzilla.redhat.com/show_bug.cgi?id=1163186#c1
            cmd = "gsettings set org.gnome.settings-daemon.plugins.media-keys max-screencast-length 600"
            Popen(cmd, shell=True, stdout=PIPE).wait()
            keyCombo('<Control><Alt><Shift>R')

    # Making this property so that in future we can make it more easily
    # memoized (e.g., see https://pypi.python.org/pypi/functools32 and
    # https://pypi.python.org/pypi/backports.functools_lru_cache)
    # That’s also the reason, why it is not @staticmethod.
    @property
    def accounts_configuration(self):  # pylint: disable=no-self-use
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        try:
            accounts_cfg = iniparse.ConfigParser()
            accounts_cfg.read(os.path.join(cur_dir, 'accounts.cfg'))
        except:
            log.error('I cannot load configuration of the online accounts. ' +
                      'I cannot continue!')
            raise
        return accounts_cfg

    def get_account_configuration(self, acc_name_full, acc_type):
        """
        Return configuration for the particular account.

        * acc_name is either just name of the account as show in the
          listbox of the Empathy New Account dialog, or combination of
          such name and ID of the particular account separated by slash.
          E.g., it should be either "Jabber" or
          "Jabber/somebody@example.com"
        * acc_type is either 'telepathy' or 'GOA'
        """
        acc_cfg = self.accounts_configuration
        out = []
        acc_id = None

        acc_name_list = acc_name_full.split('/', 1)
        if len(acc_name_list) > 1:
            acc_name, acc_id = acc_name_list
        else:
            acc_name = acc_name_list[0]

        for sec in acc_cfg.sections():
            cfg = dict(acc_cfg.items(sec))
            if cfg['name'] == acc_name and cfg['type'] == acc_type:
                out.append(cfg)

        if len(out) == 1:
            return out[0]
        elif len(out) > 1:
            if acc_id is not None:
                for acc in out:
                    if acc['id'] == acc_id:
                        return acc
            else:
            # When more Jabber accounts w/o acc_id defined
                return out[-1]

        # If we haven't returned yet, we are missing the configuration
        # for this account.
        log.error('acc_cfg:\n%s\n', acc_cfg.data)
        raise ValueError(('Configuration for the account of type {} ' +
                         'has not been found!').format(acc_name))

    def parseDesktopFile(self):
        """
        Getting all necessary data from *.dektop file of the app
        """
        cmd = "rpm -qlf $(which %s)" % self.appCommand
        cmd += '| grep "^/usr/share/applications/.*%s.desktop$"' \
            % self.desktopFileName
        proc = Popen(cmd, shell=True, stdout=PIPE)
        # !HAVE TO check if the command and its desktop file exist
        if proc.wait() != 0:
            raise Exception("*.desktop file of the app not found")
        output = proc.communicate()[0].rstrip()
        desktopConfig = iniparse.ConfigParser()
        desktopConfig.read(output)
        return desktopConfig

    @staticmethod
    def getName(desktopConfig):
        return desktopConfig.get('Desktop Entry', 'name')

    def getExec(self, desktopConfig):
        try:
            return (
                desktopConfig.get(
                    'Desktop Entry',
                    'exec').split()[0].split('/')[-1]
            )
        except iniparse.NoOptionError:
            return self.getName(desktopConfig)

    def isRunning(self):
        """
        Is the app running?
        """
        if self.a11yAppName is None:
            self.a11yAppName = self.internCommand

        # Trap weird bus errors
        for i in xrange(0, 10):
            try:
                return self.a11yAppName in \
                    [x.name for x in root.applications()]
            except Exception as e:
                print("isRunning: got exception %s" % str(e))
                sleep(1)
                continue
        raise Exception("10 at-spi errors, seems that bus is blocked")

    def kill(self):
        """
        Kill the app via 'killall'
        """
        try:
            # first try to quit graciously
            GnomeShell().clickApplicationMenuItem(
                self.getName(self.parseDesktopFile()), "Quit")
            assert wait_until(lambda x: not x.isRunning(), self, timeout=30)
        except (AssertionError, SearchError):
            try:
                # okay, didn't work. Kill by pid
                self.process.kill()
                assert wait_until(lambda x: not x.isRunning(),
                                  self, timeout=30)
            except:  # pylint: disable=bare-except
                # send SIGKILL if sigterm didn't work
                Popen("killall -9 " + self.appCommand + " > /dev/null",
                      shell=True).wait()
        self.pid = None

        if self.recordVideo:
            keyCombo('<Control><Alt><Shift>R')
            if self.recordVideoName is not None:
                # Rename the last screencast according to the template in
                # self.recordVideoName
                scrcast_list = sorted(glob.glob(
                    os.path.join(os.path.expanduser('~/Videos'),
                                 'Screencast*')))
                last_scrcast = scrcast_list[-1]
                curtime = datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
                os.rename(last_scrcast,
                          os.path.expanduser('~/Videos/%s_%s.webm' %
                                             (self.recordVideoName, curtime)))

    def startViaCommand(self):
        """
        Start the app via command
        """
        if self.forceKill and self.isRunning():
            self.kill()
            assert not self.isRunning(), "Application cannot be stopped"

        self.process = Popen(shlex.split(self.appCommand) +
                             shlex.split(self.parameters),
                             stdout=PIPE, stderr=PIPE, bufsize=0)
        self.pid = self.process.pid

        assert wait_until(lambda x: x.isRunning(), self, timeout=30),\
            "Application failed to start"

    def closeViaShortcut(self):
        """
        Close the app via shortcut
        """
        if not self.isRunning():
            raise Exception("App is not running")

        keyCombo(self.shortcut)
        assert wait_until(lambda x: not x.isRunning(), self, timeout=30),\
            "Application cannot be stopped"

    def startViaMenu(self, throughCategories=False):  # pylint: disable=W0613
        """
        Start the app via Gnome Shell menu
        """
        desktopConfig = self.parseDesktopFile()

        if self.forceKill and self.isRunning():
            self.kill()
            assert wait_until(lambda x: not x.isRunning(), self, timeout=30),\
                "Application cannot be stopped"

        # panel button Activities
        gnomeShell = root.application('gnome-shell')
        os.system("dbus-send --session --type=method_call " +
                  "--dest='org.gnome.Shell' " +
                  "'/org/gnome/Shell' " +
                  "org.gnome.Shell.FocusSearch")
        textEntry = gnomeShell.textentry('')
        assert wait_until(lambda x: x.showing, textEntry), \
            "Can't find gnome shell search textbar"

        app_name = self.getName(desktopConfig)
        typeText(app_name)
        sleep(1)
        icons = gnomeShell.findChildren(GenericPredicate(roleName='label',
                                                         name=app_name))
        visible_icons = [x for x in icons if x.showing]
        assert wait_until(lambda x: len(x) > 0, visible_icons), \
            "Can't find gnome shell icon for '%s'" % app_name
        visible_icons[0].click()

        assert wait_until(lambda x: x.isRunning(), self, timeout=30),\
            "Application failed to start"

    def getStdout(self):
        if hasattr(self, "process"):
            return non_block_read(self.process.stdout)
        else:
            return ""

    def getStderr(self):
        if hasattr(self, "process"):
            return non_block_read(self.process.stderr)
        else:
            return ""


def non_block_read(output):
    fd = output.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    try:
        return output.read()
    except:
        return ""


def common_before_all(context):
    # Skip dogtail actions to print to stdout
    config.logDebugToStdOut = False
    config.typingDelay = 0.2

    os.system("touch ~/.config/gnome-initial-setup-done")

    # Include assertion object
    context.assertion = dummy()

    # Store scenario start time for session logs
    context.log_start_time = strftime("%Y-%m-%d %H:%M:%S", localtime())


def is_process_running(process):
    '''Gives true if process can be greped out of full ps dump '''
    s = Popen(["ps", "axw"], stdout=PIPE)
    s = Popen(["ps", "axw"], stdout=PIPE)
    for x in s.stdout:
        if re.search(process, x):
            return True
    return False


def wait_for_kde_splash_to_dissapear():
    '''Ends when no splash screen is found'''
    print("waiting for ksplash to dissappear")
    sleep(1)
    while is_process_running('ksplash'):
        sleep(1)
    print("ksplash is gone")


def kde_common_before_all(context):
    common_before_all(context)

    # Start ksnapshot for screenshots
    os.system("kstart -iconify ksnapshot")

    # Record video via recordmydesktop
    os.system("rm -rf /tmp/screencast.ogv")
    master, slave = pty.openpty()
    cmd = "recordmydesktop --no-sound --on-the-fly-encoding -o /tmp/screencast.ogv"
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=slave, stderr=slave, close_fds=True)
    context.recordvideo_stdout = os.fdopen(master)

    if isA11yEnabled() is False:
        print("Enabling a11y")
        enableA11y(True)
        if isA11yEnabled() is False:
            sleep(5)
            print("Warning: second attempt to enable a11y")
            enableA11y(True)

    # Wait for ksplash to dissappear
    wait_for_kde_splash_to_dissapear()


def common_after_step(context, step):
    if step.status == 'failed':
        # Make screnshot if step has failed
        if hasattr(context, "embed"):
            os.system("gnome-screenshot -f /tmp/screenshot.jpg")
            context.embed('image/jpg', open("/tmp/screenshot.jpg", 'r').read(), caption="Screenshot")

        # Test debugging - set DEBUG_ON_FAILURE to drop to ipdb on step failure
        if os.environ.get('DEBUG_ON_FAILURE'):
            import ipdb; ipdb.set_trace()  # flake8: noqa

        # Wait a while to let screenshot app finish
        sleep(1)


def kde_common_after_step(context, step):
    if step.status == 'failed':
        try:
            os.system("sh /usr/bin/make_kde_screenshot.sh")
            context.embed('image/jpg', open("/tmp/screenshot.jpg", 'r').read(), caption="Screenshot")
        except Exception as e:
            print("after_step: %s" % str(e))


def common_after_scenario(context, scenario, kill=True):
    # Close possibly visible Shell Overview
    os.system("dbus-send --session --type=method_call --dest=org.gnome.Shell "
              "/org/gnome/Shell org.gnome.Shell.Eval string:'Main.overview.hide();'")

    if kill:
        # Stop app
        context.app.kill()

    if hasattr(context, "embed"):
        # Attach journalctl logs
        os.system("sudo journalctl /usr/bin/gnome-session --no-pager -o cat --since='%s'> /tmp/journal-session.log" % context.log_start_time)
        data = open("/tmp/journal-session.log", 'r').read()
        if data:
            context.embed('text/plain', data, caption="Session logs")

        # Attach stdout
        stdout = context.app.getStdout().strip()
        if stdout:
            context.embed('text/plain', stdout, caption="stdout")

        stderr = context.app.getStderr().strip()
        if stderr:
            context.embed('text/plain', stderr, caption="stderr")

        if hasattr(context, "app") and context.app.recordVideo:
            videos_dir = os.path.expanduser('~/Videos')
            onlyfiles = [f for f in os.listdir(videos_dir) if os.path.isfile(os.path.join(videos_dir, f))]
            onlyfiles.sort()
            if onlyfiles != []:
                video = os.path.join(videos_dir, onlyfiles[-1])
                if hasattr(context, "embed"):
                    context.embed('video/webm', open(video, 'r').read(), caption="Video")


def kde_common_after_scenario(context, scenario, kill=True):
    common_after_scenario(context, scenario, kill=kill)

    # Stop video recording
    keyCombo("<Control><Alt>s")

    line = context.recordvideo_stdout.readline()
    while line:
        if line == 'Goodbye!\r\n':
            break
        print(line)
        line = context.recordvideo_stdout.readline()

    if hasattr(context, "embed"):
        # Attach video in the report
        try:
            context.embed('video/webm', open("/tmp/screencast.ogv", 'r').read(), caption="Video")
        except Exception as e:
            print("Failed to attach the video to the report: %s" % str(e))
