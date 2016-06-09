# -*- coding: UTF-8 -*-
import pyatspi
from subprocess import Popen
from behave import step
from dogtail.predicate import GenericPredicate
from dogtail.rawinput import pressKey, keyCombo, typeText
from dogtail.tree import root
from dogtail.utils import doDelay
from common_steps import wait_until, get_showing_node_name
from gi.repository import GLib
from time import sleep


@step(u'Open {panel} panel')
def open_panel(context, panel):
    Popen('gnome-control-center %s' % panel, shell=True)
    context.app.instance = root.application('gnome-control-center')
    sleep(3)
    # context.execute_steps(
    #     u'When Make sure that gnome-control-center is running')

def add_google_account(context, user, password):
    dialog = get_showing_node_name('Google account', context.app.instance)
    #idialog = context.app.instance.dialog('Google account')


    # Input credentials
    entry = get_showing_node_name('Enter your email', dialog)
    if entry.text != user:
        entry.click()
        typeText(user)
    if dialog.findChildren(lambda x: x.roleName == 'password text') == []:
        dialog.child('Next').click()
    get_showing_node_name('Password', dialog).click()
    typeText(password)
    keyCombo('<Enter>')
    #get_showing_node_name('Sign in', dialog).click()

    # Wait for Allow to appear
    third_party_icon_pred = GenericPredicate(roleName='push button',
                                             name='Allow')
    for attempts in range(0, 40):  # pylint: disable=W0612
        if dialog.findChild(third_party_icon_pred,
                            retry=False,
                            requireResult=False) is not None:
            break
        else:
            doDelay(0.5)

    allow_button = dialog.child("Allow", roleName='push button')
    if not allow_button.showing:
        # Scroll to confirmation button
        scrolls = dialog.findChildren(
            GenericPredicate(roleName='scroll bar'))
        scrolls[-1].value = scrolls[-1].maxValue
        pressKey('space')
        pressKey('space')

    # Wait for button to become enabled
    for attempts in range(0, 10):
        if pyatspi.STATE_SENSITIVE in \
                allow_button.getState().getStates():
            break
        else:
            doDelay(0.5)

    sleep(1)
    allow_button.click()
    assert wait_until(lambda x: x.dead, dialog), \
        "Dialog was not closed"


def add_windows_live_account(context, user, password):
    dialog = context.app.instance.dialog('Windows Live account')

    # Input credentials
#    assert wait_until(
#        lambda x: x.findChildren(
    #        GenericPredicate(roleName='entry')) != [], dialog,
    #    timeout=90), "Windows Live auth window didn't appear"
    entry = dialog.child(roleName='entry', description="Email or phone")
    if entry.text != user:
        entry.click()
        typeText(user)
        pressKey('Tab')
        typeText(password)
    doDelay(2)

    dialog.button('Sign in').click()
    doDelay(5)

    # Wait for GNOME icon to appear
    third_party_icon_pred = GenericPredicate(roleName='document web',
                                             name='Let this app access your info?')
    for attempts in range(0, 10):  # pylint: disable=W0612
        if dialog.findChild(third_party_icon_pred,
                            retry=False,
                            requireResult=False) is not None:
            break
        else:
            doDelay(2)

    doDelay(1)
    allow_button = dialog.child("Yes", roleName='push button')
    if not allow_button.showing:
        # Scroll to confirmation button
        scrolls = dialog.findChildren(
            GenericPredicate(roleName='scroll bar'))
        scrolls[-1].value = scrolls[-1].maxValue
        pressKey('space')
        pressKey('space')

    # Wait for button to become enabled
    for attempts in range(0, 10):
        if pyatspi.STATE_SENSITIVE in \
                allow_button.getState().getStates():
            break
        else:
            doDelay(1)
    allow_button.click()
    assert wait_until(lambda x: x.dead, dialog), \
        "Dialog was not closed"


def add_facebook_account(context, user, password):
    dialog = context.app.instance.dialog('Facebook account')
    # Input credentials
    assert wait_until(lambda x: x.findChildren(
        GenericPredicate(roleName='entry')) != [],
        dialog, timeout=90), \
        "Facebook auth window didn't appear"
    entry = dialog.child(roleName='entry')
    if entry.text != user:
        entry.text = user
    dialog.child(roleName='password text').text = password
    doDelay(1)
    dialog.child(roleName='password text').grabFocus()
    pressKey('Enter')
    assert wait_until(lambda x: x.dead, dialog), \
        "Dialog was not closed"


def fill_in_credentials(context, cfg):
    user = cfg['id']
    pswd = cfg['password']
    acc_name = cfg['name']

    if acc_name == 'Google':
        add_google_account(context, user, pswd)
    if acc_name == 'Owncloud':
        dialog = get_showing_node_name('ownCloud account', context.app.instance, 'dialog')
        dialog.childLabelled('Server').text = cfg['server']
        dialog.childLabelled('Username').text = user
        dialog.childLabelled('Password').text = pswd
        dialog.button('Connect').click()
        assert wait_until(lambda x: x.dead, dialog), \
            "Dialog was not closed"
    if 'Exchange' in acc_name:
        dialog = get_showing_node_name('Microsoft Exchange account', context.app.instance, 'dialog')
        dialog.childLabelled("E-mail").text = '%s' % cfg['email']
        dialog.childLabelled("Password").text = 'RedHat1!'
        get_showing_node_name('Custom', dialog).click()
        dialog.childLabelled("Server").text = cfg['server']
        get_showing_node_name('Connect', dialog).click()
        get_showing_node_name('Error connecting to Microsoft Exchange server:\nThe signing certificate authority is not known.', dialog)
        sleep(0.5)
        get_showing_node_name('Ignore', dialog).click()
        assert wait_until(lambda x: x.dead, dialog), \
            "Dialog was not closed"

    if acc_name == 'Facebook':
        add_facebook_account(context, user, pswd)
    if acc_name == 'Windows Live':
        add_windows_live_account(context, user, pswd)


@step(u'Add account "{acc_type}" via GOA')
def add_account_via_goa(context, acc_type):
    account_cfg = context.app.get_account_configuration(acc_type, 'GOA')

    def get_account_string(acc_type):
        if acc_type in ['Google', 'Facebook', 'Windows Live']:
            return '%s\n%s' % (account_cfg['provider'], account_cfg['id'])
        elif acc_type in ['Exchange 2010', 'Exchange 2013']:
            return '%s\n%s' % (account_cfg['provider'], account_cfg['email'])
        elif acc_type == 'Owncloud':
            return '%s\n%s@%s' % (account_cfg['provider'], account_cfg['id'], account_cfg['server'])
        else:
            raise Exception("Cannot form account string for '%s' type" % acc_type)

    account_string = get_account_string(acc_type)
    get_showing_node_name("Online Accounts", context.app.instance, 'frame')
    sleep(5)
    account_exists = context.app.instance.findChild(
        GenericPredicate(account_string),
        retry=False, requireResult=False)
    if not account_exists:
        if context.app.instance.findChild(
        GenericPredicate('No online accounts configured'),
        retry=False, requireResult=False).showing:
            get_showing_node_name("Add an online account", context.app.instance, 'push button').click(); sleep(2)

        else:
            btn = context.app.instance.child('Add Account', roleName='push button')
            if not btn.sensitive:
                btn = get_showing_node_name("Add an online account", context.app.instance, 'push button')
            btn.grabFocus()
            btn.click(); sleep(2)
        dialog = get_showing_node_name('Add Account', context.app.instance, rolename="dialog")
        get_showing_node_name(account_cfg['provider'], dialog).click(); sleep(2)
        fill_in_credentials(context, account_cfg)
        assert get_showing_node_name(account_string,context.app.instance) is not None,\
            "GOA account was not added"



@step(u'Handle authentication window with password "{password}"')
def handle_authentication_window_with_custom_password(context, password):
    handle_authentication_window(context, password)


@step(u'Handle authentication window')
def handle_authentication_window(context, password='redhat'):
    # Get a list of applications
    app_names = []
    for attempt in range(0, 15):
        try:
            app_names = map(lambda x: x.name, root.applications())
            break
        except GLib.GError:
            sleep(1)
            continue
    if 'gcr-prompter' in app_names:
        # Non gnome shell stuf
        passprompt = root.application('gcr-prompter')
        continue_button = passprompt.findChild(
            GenericPredicate(name='Continue'),
            retry=False, requireResult=False)
        if continue_button:
            passprompt.findChildren(GenericPredicate(roleName='password text'))[-1].grab_focus()
            sleep(0.5)
            typeText(password)
            # Don't save passwords to keyring
            keyCombo('<Tab>')
            # Click Continue
            keyCombo('<Tab>')
            keyCombo('<Tab>')
            keyCombo('<Enter>')
    elif 'gnome-shell' in app_names:
        shell = root.application('gnome-shell')
        # if wait_until(lambda x: x.findChildren(
        #         lambda x: x.roleName == 'password text' and x.showing) != [], shell):
        #     pswrd = shell.child(roleName='password text')
        #     pswrd.text = password
        #     st = shell.child('Add this password to your keyring')
        #     if not st.parent.parent.checked:
        #         st.click()
        #     continue_button = shell.button('Continue')
        #     shell.button('Continue').click()
        #     sleep(3)
        if wait_until(lambda x: x.findChildren(
                lambda x: x.roleName == 'password text' and x.showing) != [], shell):
            st = shell.child('Add this password to your keyring')
            if not st.parent.parent.checked:
                st.click()
            pswrd = shell.child(roleName='password text')
            pswrd.click()
            typeText(password)
            keyCombo('<Enter>')
            wait_until(st.dead)
            sleep(1)
