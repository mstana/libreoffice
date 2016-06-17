# -*- coding: UTF-8 -*-
from . import wait_until
from behave import step
from dogtail.rawinput import keyCombo
from dogtail.predicate import GenericPredicate
from dogtail.utils import doDelay
import pyatspi
from common_steps import get_showing_node_name

@step(u'Folder select dialog with name "{name}" is displayed')
def has_folder_select_dialog_with_name(context, name):
    has_files_select_dialog_with_name(context, name)


@step(u'Folder select dialog is displayed')
def has_folder_select_dialog(context):
    context.execute_steps(
        u'Then folder select dialog with name "Select Folder" is displayed')


@step(u'In folder select dialog choose "{name}"')
def select_folder_in_dialog(context, name):
    select_file_in_dialog(context, name)


@step(u'file select dialog with name "{name}" is displayed')
def has_files_select_dialog_with_name(context, name):
    context.app.dialog = context.app.instance.child(name=name,
                                                    roleName='file chooser')


@step(u'File select dialog is displayed')
def has_files_select_dialog(context):
    context.execute_steps(
        u'Then file select dialog with name "Select Files" is displayed')


@step(u'In file select dialog select "{name}"')
def select_file_in_dialog(context, name):
    location_button = context.app.dialog.child('Enter Location')
    if pyatspi.STATE_ARMED not in location_button.getState().getStates():
        location_button.click()

    location_text = context.app.dialog.child(roleName='text')
    location_text.set_text_contents(name)
    doDelay(0.2)
    location_text.grab_focus()
    keyCombo('<Enter>')


@step(u'In file save dialog save file to "{path}" clicking "{button}"')
def file_save_to_path(context, path, button):
    context.app.dialog.childLabelled('Name:').set_text_contents(path)
    get_showing_node_name(button, context.app.dialog).click()
