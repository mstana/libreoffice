# -*- coding: UTF-8 -*-

from behave import step

from dogtail import predicate
from dogtail.tree import root
from common_steps.app import *
from common_steps.appmenu import *
from common_steps.dialogs import *
from dogtail.rawinput import keyCombo, typeText, pressKey
from general import click_button_in_dialog_window


@step(u'Paragraph ends with "{character}" character')
def par_ends_with(context, character):
    current_window = context.app.get_current_window()
    text = current_window.child(roleName='paragraph').text
    assert text.endswith(character), 'Expected text "%s" to end with "%s" character' % (text, character)

@step(u'Search and Replace text')
def search_and_replace_text(context):
    current_window = context.app.get_current_window()
    paragraph = current_window.child(roleName='paragraph')


@step(u'Type text "{text}" to paragraph')
def type_text_to_paragraph(context, text):
    current_window = context.app.get_current_window()
    context.paragraph = current_window.child(roleName='paragraph')
    context.paragraph.typeText(text)

    assert context.paragraph.text == text, \
        "Incorrect text in paragrap, expected '%s' but was '%s'" % (text, context.paragraph.text)

    # this is helper to assert undo changes
    context.original_paragraph_text = context.paragraph.text


@step(u'Replace text "{replaced_text}" with text "{replacement}"')
def type_text_to_paragraph(context, replaced_text, replacement):
    """
    In this method we use shortcut CTRL+h to fire replace dialog window,
    then submit changes.
    """
    # fire dialog with ctrl+h
    keyCombo('<Control>h')
    dialog = context.app.get_current_window()
    # Search Field
    dialog.findChildren(lambda x: x.name == 'Search For' and x.roleName=='panel')[0].\
        child(roleName='text').typeText(replaced_text)
    dialog.findChildren(lambda x: x.roleName == 'push button' and x.name == 'Find All' and x.showing)[0].click()
    # Replace Field
    dialog.findChildren(lambda x: x.name == 'Replace With' and x.roleName=='panel')[0].\
        child(roleName='text').typeText(replacement)
    dialog.findChildren(lambda x: x.roleName == 'push button' and x.name == 'Replace All' and x.showing)[0].click()

    # this is used for wait of alert - it takes some time to render and not in all situation its gets showed instantly
    sleep(1)
    alert_dialog = context.app.get_current_window()
    click_button_in_dialog_window(context, "OK")

    assert not alert_dialog.showing, "Alert Dialog is still showing and probably also have focus"
    assert context.paragraph.text == replacement, "Incorrect text in paragraph, expected '%s' but was '%s'" % (
        replacement, context.paragraph.text)

    dialog.findChildren(lambda x: x.roleName == 'push button' and x.name == 'Close' and x.showing)[0].click()


@then(u'Undo replace text with ctrl+z')
def undo_replace_text_with_shortcut(context):
    # this take context.paragraph.text which is stored on first place in type_text_to_paragraph
    # and compare if its the same with text after undo changes
    keyCombo('<Control>z')

    assert context.paragraph.text == context.original_paragraph_text, \
        "Incorrect text in paragraph, expected '%s' but was '%s'" % (
            context.original_paragraph_text, context.paragraph.text)


@step(u'Insert table')
def insert_table(context):
    keyCombo('<Control><F12>')
    context.app.get_current_window().findChildren(
        lambda x: x.roleName == 'push button' and x.name == 'Insert' and x.showing)[0].click()

    assert len(context.app.get_current_window().findChildren(
        lambda x: x.showing and x.roleName == 'table')) != 0, "In paragraph should be at least one table"


@step(u'Select all text and delete')
def select_all_text_and_delete(context):
    context.app.get_current_window().child(roleName='paragraph').grabFocus()
    keyCombo('<Control>a')
    pressKey('del')


@then(u'No text displayed')
def no_text_displayed(context):
    window = context.app.get_current_window()
    assert window.child(roleName='paragraph').text == '', \
        "Incorrect text in paragraph, expected empty but was '%s'" % window.child(roleName='paragraph').text


@then(u'Formula panels with names "{name1}" and "{name2}" for edit are displayed')
def panels_displayed(context, name1, name2):
    context.window = context.app.get_current_window()
    name1_included_and_showing = \
        context.window.findChildren(lambda x: x.roleName == 'panel' and x.name == name1)[0].showing
    assert name1_included_and_showing, "Panel with name %s is not showing and should be." % name1

    name2_included_and_showing = \
        context.window.findChildren(lambda x: x.roleName == 'panel' and x.name == name2)[0].showing
    assert name2_included_and_showing, "Panel with name %s is not showing and should be." % name2


@step(u'Insert "{formula}" formula to panel with name "{panelname}"')
def insert_formula_to_panel(context, formula, panelname):
    paragraph = context.window.findChildren(lambda x: x.roleName == 'paragraph' and x.name == 'Paragraph 0')[0]
    paragraph.typeText(formula)
    paragraph.click()


@then(u'Formula "{formula}" is saved in document')
def formula_in_opened_document(context, formula):
    paragraph = context.app.get_current_window().child(roleName='paragraph')
    paragraph.child(roleName='embedded').doubleClick()
    window = context.app.get_current_window().parent.findChildren(
        lambda x: x.roleName == 'frame' and x.name != "Elements")[0]
    commands = window.findChildren(lambda x: x.roleName == 'panel' and x.name == 'Commands')[0]
    text = commands.child(roleName='paragraph').text
    # from some reason writer always add ' }' at the end of formula
    # when writing formula to paragraph writer is making autocorrect sometimes on spaces so first delete all of them
    assert (formula + ' }').replace(" ", "") == text.replace(" ", ""), \
        "Incorrect panel name, expected '%s' but was '%s'" % (formula + ' }', text)


@step(u'Insert text "{text}" to document')
def insert_text_to_document(context, text):
    context.window = context.app.get_current_window()
    context.window.child(roleName='document text').child(roleName='paragraph').typeText(text)


@then(u'Text "{text}" is in document')
def inserted_text_is_in_document(context, text):
    context.window = context.app.get_current_window()
    text_in_paragraph = context.window.child(roleName='document text').child(roleName='paragraph').text
    assert unicode(text_in_paragraph, 'utf-8') == text, "Text in paragraph is: \"%s\", should be: \"%s\""\
                                                        % (unicode(text_in_paragraph, 'utf-8'), text)


@then(u'Math Editor launched and displayed')
def math_editor_launch_and_displayed(context):

    # for some reason Math window is taking some time to render
    sleep(5)
    window_name = context.app.get_current_window().name
    assert "LibreOffice Math" in unicode(window_name, 'utf-8'),\
        "Name of window is: \"%s\", should be like: \"%s\""\
        % (unicode(window_name, 'utf-8'), "LibreOffice Math")
