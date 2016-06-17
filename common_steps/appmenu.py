# -*- coding: UTF-8 -*-
from behave import step  # pylint: disable=E0611
from dogtail.utils import doDelay, GnomeShell


# GApplication menu steps
@step(u'Open GApplication menu')
def get_gmenu(context):
    desktopConfig = context.app.parseDesktopFile()
    GnomeShell().getApplicationMenuButton(
        context.app.getName(desktopConfig)).click()


@step(u'Close GApplication menu')
def close_gmenu(context):
    desktopConfig = context.app.parseDesktopFile()
    GnomeShell().getApplicationMenuButton(
        context.app.getName(desktopConfig)).click()
    doDelay(2)


@step(u'Click "{name}" in GApplication menu')
def click_menu(context, name):
    desktopConfig = context.app.parseDesktopFile()
    app_name = context.app.getName(desktopConfig)
    GnomeShell().clickApplicationMenuItem(app_name, name)
    doDelay(2)
