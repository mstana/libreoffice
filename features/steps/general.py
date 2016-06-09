# -*- coding: UTF-8 -*-

from behave import step

from dogtail import predicate
from dogtail.tree import root
from common_steps.app import *
from common_steps.appmenu import *
from common_steps.dialogs import *
from dogtail.rawinput import keyCombo, typeText, pressKey


@step(u'Start {app} via {type:w} with {component:w} parameter')
def start_app_component_via_command(context, app, component, type):
    context.app.parameters = '--' + component.lower()
    context.app.desktopFileName = 'libreoffice-' + component.lower()

    if type == 'command':
        context.app.startViaCommand()
    if type == 'menu':
        context.app.startViaMenu()



@then(u'{component:w} document named like "{name}" is displayed')
def document_is_displayed(context, component, name):
    for attempt in xrange(0, 10):
        try:
            current_window = context.app.get_current_window()
            window_title = current_window.name.decode('utf-8')
            assert component in window_title and name in window_title
            return
        except AssertionError:
            sleep(1)
            continue
    raise AssertionError("Window title is %s, should be %s"\
        %(window_title,name))


@step(u'Select "{menu}" menu')
def select_menuitem(context, menu):
    menu_item = menu.split(' -> ')
    # First level menu
    context.app.instance = root.application('soffice')
    current = context.app.instance.menu(menu_item[0])
    current.click()
    if len(menu_item) == 1:
        return
    # Intermediate menus
    for item in menu_item[1:-1]:
        current = context.app.instance.menu(item)
        current.click()
    # Last level menu item
    current.menuItem(menu_item[-1]).doActionNamed('click')


@step(u'About dialog is displayed')
def about_dialog_displayed(context):
    current_window = context.app.get_current_window()
    version_txt = current_window.child(roleName='text').text
    assert 'Version:' in version_txt

def set_root_location(context, dialog):
    dialog.findChildren(lambda x: x.roleName=='label' and x.name=='Other Locations')[0].click()
    dialog.findChildren(lambda x: x.name == 'Computer')[0].click()

@step(u'In Open dialog select "{name}" from "{path}"')
def select_file_in_dialog(context, name, path):
    # click search button
    context.app.dialog.findChildren(lambda x: x.roleName == 'toggle button' and x.showing)[0].click()

    full_path = os.path.join(path, name)
    typeText(full_path)
    keyCombo('<enter>')


@step(u'In dialog fill out path "{path}", name "{name}" and confirm')
def file_save_to_path(context, path, name):

    full_path = os.path.join(path, name)
    context.app.dialog = context.app.get_current_window()
    context.app.dialog.findChildren(lambda x: x.roleName == 'text')[0].set_text_contents(full_path)
    context.app.dialog.findChildren(lambda x: x.roleName == 'text')[0].grab_focus()
    keyCombo('<Enter>')
    sleep(1)


@step(u'In open dialog fill out path "{path}", name "{name}" and confirm')
def file_open_on_path(context, path, name):

    full_path = os.path.join(path, name)
    context.app.dialog = context.app.get_current_window()
    context.app.dialog.findChildren(lambda x: x.name == 'Type a file name')[0].click()
    context.app.dialog.childLabelled('Location:').set_text_contents(full_path)
    context.app.dialog.childLabelled('Location:').grab_focus()
    keyCombo('<Enter>')
    sleep(1)


@step(u'In Rename dialog set new name to "{new_name}"')
def rename_to(context, new_name):
    context.app.dialog = context.app.get_current_window()
    context.app.dialog.findChildren(lambda x: x.name == 'Name:' and x.roleName == 'text')[0].set_text_contents(new_name)
    context.app.dialog.childNamed('OK').click()


@step(u'In Special Character dialog select "{character}" character')
def select_special_char(context, character):
    context.app.dialog = context.app.get_current_window()

    table = context.app.dialog.child(name='Select special characters in this area.', roleName='table')
    table.child(name=character, roleName='table cell').click()

    context.app.dialog.childNamed('Insert').click()


@step(u'Click the "{button}" button in dialog window')
def click_button_in_dialog_window(context, button):
    current_window = context.app.get_current_window()
    current_window.childNamed(button).click()


@step(u'Check file "{name}" in "{path}" exists')
def file_exists(context, name, path):
    for attempt in xrange(0, 10):
        try:
            full_path = os.path.join(path, name)
            assert os.path.isfile(full_path)
            return
        except AssertionError:
            sleep(1)
            continue
    raise AssertionError("%s file in %s not found." % (name, path))


@then(u'Dialog window named "{dialog_name}" is displayed')
def dialog_window_is_displayed(context, dialog_name):

    for attempt in xrange(0, 10):
        try:
            dialog_window = context.app.get_current_window()
            assert dialog_window.name == dialog_name
            context.app.dialog = dialog_window
            return
        except AssertionError:
            sleep(1)
            continue
    raise AssertionError("Dialog window with expected title not found.")


@then(u'Dialog window named like "{dialog_name}" is displayed')
def dialog_window_like_is_displayed(context, dialog_name):

    for attempt in xrange(0, 10):
        try:
            dialog_window = context.app.get_current_window()
            assert dialog_name in dialog_window.name
            context.app.dialog = dialog_window
            return
        except AssertionError:
            sleep(1)
            continue
    raise AssertionError("Dialog window with expected title not found.")


@step(u'Window named "{window_name}" is displayed')
def window_is_displayed(context, window_name):
    for attempt in xrange(0, 15):
        try:
            current_window = context.app.get_current_window()
            assert current_window.name == window_name
            return
        except AssertionError:
            sleep(1)
            continue
    raise AssertionError("Window with expected title not found.")


@step(u'Insert example data into {component} document')
def insert_example_data(context, component):
    if component in ['Writer', 'Calc']:
        typeText('Example text')
        pressKey('Enter')
    elif component == 'Impress':
        context.execute_steps(u'''* Set current slide title to "Example"''')
    elif component == 'Draw':
        context.execute_steps(u'''* Select "Insert -> Fields -> File Name" menu''')


@step(u'Make sure the {toolbar_name} toolbar is visible')
def toolbar_is_visible(context, toolbar_name):
    current_window = context.app.get_current_window()
    try:
        toolbar = current_window.child(name=toolbar_name, roleName='tool bar')
    except SearchError:
        context.execute_steps(u'''* Select "View -> Toolbars -> %s" menu''' % toolbar_name)


@step(u'Select {tool_name} tool from {toolbar_name} toolbar')
def select_tool_from_toolbar(context, tool_name, toolbar_name):
    current_window = context.app.get_current_window()
    toolbar = current_window.child(name=toolbar_name, roleName='tool bar')
    toolbar.child(name=tool_name, roleName='toggle button').click()


@then(u'Document contains an image called "{item_name}"')
def document_contains_image(context, item_name):
    current_window = context.app.get_current_window()
    assert current_window.child(name=item_name, roleName='image').showing


@then(u'Document contains an item called "{item_name}"')
def document_contains_item(context, item_name):
    current_window = context.app.get_current_window()
    assert current_window.child(name=item_name, roleName='shape').showing


@then(u'Document contains a table called "{table_name}"')
def document_contains_table(context, table_name):
    current_window = context.app.get_current_window()
    assert current_window.child(name=table_name, roleName='table').showing


@step(u'Save document and close "{document_name}" with path "{document_path}" as extension "{extension}"')
def save_and_close_document(context, document_name, document_path, extension):

    select_menuitem(context, "File -> Save As...")
    sleep(1)

    context.dialog = context.app.get_current_window()
    combo_box = context.dialog.findChildren(lambda x: x.name == 'All Formats' and x.roleName == 'combo box')[0]
    value = combo_box.findChildren(lambda x: extension in x.name)[0].name
    combo_box.combovalue = value

    file_save_to_path(context, document_path, document_name)

    # click dialog if you are sure that you want use extension format
    context.app.get_current_window().findChildren(lambda x: x.roleName == 'push button')[-1].click()
    sleep(1)
    select_menuitem(context, "File -> Exit LibreOffice")
