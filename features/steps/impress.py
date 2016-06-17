# -*- coding: UTF-8 -*-

from behave import step

from dogtail import predicate
from dogtail.tree import root
from common_steps.app import *
from common_steps.appmenu import *
from common_steps.dialogs import *
from dogtail.rawinput import keyCombo, typeText, pressKey
from general import window_is_displayed, select_menuitem, select_file_in_dialog, file_save_to_path, start_app_component_via_command


@step(u'Change Impress presentation layout to {layout_name}')
def change_presentation_layout(context, layout_name):

    current_window = context.app.get_current_window()
    # check if panel is showing and then click!
    properies_button = current_window.findChildren(lambda x: x.roleName == 'radio button' and x.name == 'Properties')[0]
    if not properies_button.checked:
        properies_button.click()
    current_window.child(name=layout_name, roleName='list item').click()


@step(u'Slide should contain {number_of_items} items')
def number_of_items_in_slide(context, number_of_items):
    current_window = context.app.get_current_window()
    document = current_window.child(roleName='document presentation')

    # Number of items (paragraphs) in current slide
    items = document.findChildren(lambda x: x.roleName == 'paragraph')
    assert int(number_of_items) == len(items),\
        "Expected %s items and %s was present" % (number_of_items, len(items))


@step(u'Set current slide title to "{title}"')
def set_current_slide_title(context, title):
    current_window = context.app.get_current_window()
    title_field = current_window.child(name='PresentationTitle ', roleName='shape')
    title_field.click()
    typeText(title)
    pressKey('esc')


@step(u'Current slide title is "{title}"')
def check_current_slide_title(context, title):
    current_window = context.app.get_current_window()
    title_field = current_window.child(name='PresentationTitle ', roleName='shape')
    title_paragraph = title_field.child(roleName='paragraph')
    assert title == title_paragraph.text


@step(u'Total number of slides is {number_of_slides}')
def total_number_of_slides(context, number_of_slides):
    current_window = context.app.get_current_window()
    current_total = current_window.child(name='Slides View', roleName='document frame').childCount
    assert current_total == int(number_of_slides), "There is %s slides, should be %s slides." % (current_total, number_of_slides)


@step(u'Presentation window is {window_state}')
def presentation_window_state(context, window_state):
    soffice = root.application('soffice')
    all_frames = [x.name for x in soffice.findChildren(lambda x: x.roleName == 'frame')]

    if window_state == 'open':
        assert '' in all_frames
    elif window_state == 'closed':
        assert '' not in all_frames


@step(u'Move to the {direction} slide')
def move_to_slide(context, direction):
    if direction == 'following':
        pressKey('Right')
    elif direction == 'previous':
        pressKey('Left')


@step(u'Create presentation from template titled "{presentation_title}"')
def presentation_from_template(context, presentation_title):
    current_window = context.app.get_current_window()

    # step one
    template_rb = current_window.child(name='From template', roleName='radio button')
    template_rb.click()
    # workaround for the radio button not being checked:
    if not template_rb.checked:
        pressKey('Tab')
        pressKey('Tab')
        pressKey('Down')

    current_window.button('Next').click()

    # step two and three
    current_window.button('Next').click()
    current_window.button('Next').click()

    # step four
    current_window.childLabelled('What is the subject of your presentation?').click()
    typeText(presentation_title)
    current_window.button('Create').click()


@step(u'Insert to slide "{number_of_slide}" text "{text}"')
def insert_text_to_slide(context, number_of_slide, text):


    current_window = context.app.get_current_window()
    # choose right slide
    current_window.child(name='Slides View', roleName='document frame')[int(number_of_slide)-1].click()

    # find paragraph, and write the text
    paragraph = current_window.findChildren(lambda x: x.name == 'Paragraph 0')[0]
    paragraph.text = text

    #click in the end to change the focus back to main window
    current_window.click()


@then(u'Slide "{number_of_slide}" include text "{text}"')
def slide_include_text(context, number_of_slide, text):

    sleep(3)
    current_window = context.app.get_current_window()
    current_window.child(name='Slides View', roleName='document frame')[int(number_of_slide)-1].click()

    # get the text from slide (Text should be in unicode)
    text_from_slide = current_window.findChildren(lambda x: x.name == 'Paragraph 0')[0].text

    assert text_from_slide.decode("utf-8") == text,\
        "Text are not consistent in slide number %s, is: %s should be: %s"\
         % (number_of_slide, text_from_slide.decode("utf-8"), text)

    #click in the end to change the focus back to main window
    current_window.click()
