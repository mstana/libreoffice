# -- FILE: features/steps/example_steps.py
import logging
import os
import subprocess
from time import sleep

from behave import then, step  # pylint: disable=E0611
from dogtail.rawinput import typeText, click, pressKey, keyCombo
from dogtail.tree import root, SearchError
from gi.repository import GLib, Gdk  # pylint: disable=E0611

from . import wait_until


@step(u'Press "{sequence}"')
def press_button_sequence(context, sequence):  # pylint: disable=W0613
    keyCombo(sequence)
    sleep(0.5)


def wait_for_app_to_appear(context, app, timeout):
    # Waiting for a window to appear
    for i in range(0, timeout):
        try:
            context.app.instance = root.application(context.app.a11yAppName)
            context.app.instance.child(roleName='frame')
            break
        except (GLib.GError, SearchError):
            sleep(1)
            continue
    context.execute_steps(u"Then %s should start" % app)


@step(u'Start {app} via {app_type:w}')
def start_app_via_command(context, app, app_type):
    for attempt in range(0, 10):
        try:
            if app_type == 'command':
                context.app.startViaCommand()
            if app_type == 'menu':
                context.app.startViaMenu()
            break
        except GLib.GError:
            sleep(1)
            if attempt == 6:
                # Killall the app processes if app didn't show up
                # after 5 seconds
                subprocess.call(['pkill', '-f', context.app.internCommand])
                context.app.cleanup()
                context.execute_steps(u"* Start %s via command" % app.lower())
            continue


@step(u'Close app via gnome panel')
def close_app_via_gnome_panel(context):
    context.app.closeViaGnomePanel()


@step(u'Make sure that {app} is running')
@step(u'Make sure that {app} is running waiting for {timeout} seconds')
def ensure_app_running(context, app, timeout=10):
    start_app_via_command(context, app, 'menu')
    wait_for_app_to_appear(context, app, timeout)
    logging.debug("app = %s", root.application(context.app.a11yAppName))


@then(u'{app} should start')
def test_app_started(context, app):  # pylint: disable=W0613
    logging.debug('app = {}'.format(context.app.a11yAppName))
    for i in range(0, 10):
        try:
            root.application(context.app.a11yAppName).child(roleName='frame')
            break
        except SearchError:
            raise RuntimeError("App '%s' is not running" % context.app.a11yAppName)
        except GLib.GError:
            continue


@then(u"{app} shouldn't be running anymore")
def then_app_is_dead(context, app):  # pylint: disable=W0613
    isRunning = True
    for i in range(0, 10):
        try:
            root.application(context.app.a11yAppName).child(roleName='frame')
            sleep(1)
        except SearchError:
            isRunning = False
            break
        except GLib.GError:
            continue
    if isRunning:
        raise RuntimeError("App '%s' is running" % context.app.a11yAppName)


@step(u'Help section "{name}" is displayed')
def help_is_displayed(context, name):
    try:
        context.yelp = root.application('yelp')
        frame = context.yelp.child(roleName='frame')
        wait_until(lambda x: x.showing, frame)
        sleep(1)
        context.assertion.assertEquals(name, frame.name)
    finally:
        os.system("killall yelp")


def isKDEAppRunning(self):
    """
    Is the app running?
    """
    print("isKDEAppRunning: start")
    if self.a11yAppName is None:
        self.a11yAppName = self.internCommand

    # Trap weird bus errors
    for i in xrange(0, 30):
        try:
            print("isKDEAppRunning: Attempt #%d:" % i)
            child = root.child(name=self.a11yAppName, roleName='application', retry=False, recursive=False)
            print("isKDEAppRunning: Bingo! Got %s, exiting" % child)
            return child
        except Exception as e:
            print('isKDEAppRunning: exception "%s"' % e)
            sleep(1)
            continue
    return False


@step(u'Start {app} via KDE command')
def start_app_via_kde_command(context, app):
    context.app.startViaCommand()
    assert wait_until(lambda x: isKDEAppRunning(x), context.app, timeout=30),\
        "Application failed to start"
    context.app.instance = root.application(context.app.a11yAppName)


@step(u'Start {app} via KDE menu')
def startViaKDEMenu(context, app):
    """ Will run the app through the standard application launcher """
    corner_distance = 10
    height = Gdk.Display.get_default().get_default_screen().get_root_window().get_height()
    click(corner_distance, height - corner_distance)
    plasma = root.application('plasma-desktop')
    plasma.child(name='Search:', roleName='label').parent.child(roleName='text').text = context.app.appCommand
    sleep(0.5)
    pressKey('enter')
    assert wait_until(lambda x: isKDEAppRunning(x), context.app, timeout=30),\
        "Application failed to start"
    context.app.instance = root.application(context.app.a11yAppName)


@step(u'Launch {app} via KRunner')
def startViaKRunner(context, app):
    """ Simulates running app through Run command interface (alt-F2...)"""
    os.system('krunner')
    assert wait_until(lambda x: x.application('krunner'), root),\
        "KRunner didn't start"
    typeText(context.app.appCommand)
    sleep(1)
    pressKey('enter')
    assert wait_until(lambda x: isKDEAppRunning(x), context.app, timeout=30),\
        "Application failed to start"
    context.app.instance = root.application(context.app.a11yAppName)


@step(u'Close {app} via menu in KDE')
@step(u'Close {app} via menu "{menu}" in KDE')
@step(u'Close {app} via menu "{menu}" item "{menuitem}" in KDE')
def closeViaMenu(context, app, menu='File', menuitem='Quit', dialog=False):
    """ Does execute 'Quit' item in the main menu """
    if not wait_until(lambda x: isKDEAppRunning(x), context.app, timeout=5):
        return False
    context.app.instance.child(name=menu, roleName='menu item').click()
    sleep(1)
    context.app.instance.child(name=menuitem, roleName='menu item').click()
