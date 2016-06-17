# -*- coding: UTF-8 -*-
import codecs

from behave import step

from dogtail import predicate
from dogtail.tree import root
from common_steps.app import *
from common_steps.appmenu import *
from common_steps.dialogs import *
from dogtail.rawinput import keyCombo, typeText, pressKey, drag
from general import select_menuitem
from dogtail.procedural import FocusWidget

VALUES = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
CELLS = {}
DATA = []
TABLE_LENGTH = 1024
CELL_TRANSLATION = {
    "Cell A1": 0,
    "Cell A2": 1,
    "Cell B1": 1024,
    "Cell B2": 1025
}

# README!
# Do not try to access table directly without recursion set to False because
# it stuck the program and spend all memory.


@step(u'Insert values to table and create sum under them')
def insert_values_and_create_sum(context):
    context.frame = context.app.get_current_window().child(roleName='document spreadsheet')
    context.frame.child(roleName='table')[0].grabFocus()
    for value in VALUES:
        typeText(value)
        pressKey('enter')
    context.sum_string = '='
    for i in range(1, len(VALUES) + 1):
        if i == len(VALUES):
            context.sum_string = context.sum_string + 'A' + str(i)
        else:
            context.sum_string = context.sum_string + 'A' + str(i) + '+'

    typeText(context.sum_string)
    pressKey('enter')


@then(u'Correct sum under values')
def correct_sum_under_values(context):
    context.frame.child(roleName='table')[0].grabFocus()

    for i in range(0, len(VALUES)):
        pressKey('enter')

    text_input = context.app.get_current_window().child(
        roleName='document spreadsheet').parent.parent.findChildren(
        lambda x: x.roleName == 'tool bar' and x.name == 'Formula Tool Bar', recursive=False)[0]
    tx = text_input.child(roleName="paragraph").text
    assert context.sum_string == tx, \
        "Incorrect panel name, expected '%s' but was '%s'" % (context.sum_string, tx)


@step(u'Remove values with shortcut ctrl+z')
def remove_values_from_table(context):
    pass


@step(u'Select "{num_of_columns}" columns and "{num_of_rows}" rows on table')
def select_two_to_two_table(context, num_of_columns, num_of_rows):
    context.frame = context.app.get_current_window().child(roleName='document spreadsheet')
    context.index_of_first_cell = 0
    cell1 = context.frame.child(roleName='table')[context.index_of_first_cell]

    store_cells_from_table_index(context, context.index_of_first_cell, int(num_of_columns), int(num_of_rows))
    select_on_table(cell1, context.index_of_first_cell, int(num_of_columns), int(num_of_rows))


def select_on_table(from_cell, from_cell_index, number_of_columns, number_of_rows):
    """
    Select part of table defined by number_of_columns and number_of_rows from particular cell
    """

    CELLS[from_cell_index] = from_cell
    from_cell.grabFocus()

    for i in range(0, number_of_columns - 1):
        keyCombo("<SHIFT><Right>")

    for i in range(0, number_of_rows - 1):
        keyCombo("<SHIFT><Down>")


def store_cells_from_table_index(context, from_table_index, number_of_columns, number_of_rows):
    """
    store cells selected by test for assertion at the end of test
    """
    for row_number in range(0, number_of_rows):
        row_index = from_table_index + (row_number * TABLE_LENGTH)

        for item_number in range(0, number_of_columns):
            CELLS[row_index + item_number] = context.frame.child(roleName='table')[row_index + item_number]


def get_under_cell(context, cell_index, shift):
    """
    return cell which is under specified cell - method
    do not expect end of table!!! - in future the table lenght can change and method should be updated
    """
    return context.frame.child(roleName='table')[cell_index + shift + TABLE_LENGTH]


def get_right_cell_with_shift(context, cell_index, shift):
    """
    return cell which is on right from specified cell - method
    do not expect end of table!!! - in future the table lenght can change and method should be updated
    """
    return context.frame.child(roleName='table')[cell_index + shift]


def type_text_to_cell(text, cell):
    cell.grabFocus()
    typeText(text)


@step(u'Open random number dialog')
def open_random_number_dialog(context):
    menu_item_edit = context.app.get_current_window().child(roleName='menu bar')[1]
    menu_item_edit.click()
    menu_item_edit_fill = menu_item_edit.child(name='Fill')
    menu_item_edit_fill.click()
    menu_item_edit_fill.child(name="Random Number...").click()
    context.dialog_random = context.app.get_current_window()


@then(u'Dialog openned')
def dialog_openned(context):
    assert context.dialog_random.name == "Random Number Generator", "Name of dialog is: %s, should be %s" % (
        context.dialog_random.name, "Random Number Generator")


@step(u'Select vaules from "{from_number}" and to "{to_number}" in random number dialog and confirm')
def selec_values_from_and_to_in_random_number_dialog_and_confirm(context, from_number, to_number):
    parameters_section = context.dialog_random.child(name="Random Number Generator")

    minimum_text_field = parameters_section.child(roleName="text", name="Minimum")
    minimum_text_field.grabFocus()
    keyCombo("<CTRL>a")
    pressKey("del")
    minimum_text_field.typeText(from_number)

    maximum_text_field = parameters_section.child(roleName="text", name="Maximum")
    maximum_text_field.grabFocus()
    keyCombo("<CTRL>a")
    pressKey("del")
    maximum_text_field.typeText(to_number)

    context.dialog_random.child(name="Apply").click()
    context.dialog_random.child(name="OK").click()


@then(u'Correct from "{from_number}" and to "{to_number}" values in table')
def correct_values_in_table(context, from_number, to_number):
    context.frame = context.app.get_current_window().child(roleName='document spreadsheet')
    context.frame.child(roleName='table')[0].grabFocus()

    for cell in CELLS.values():

        assert float(cell.text) < float(to_number), "Value in cell %s is %s, should be less than %s" % (
            cell.name, cell.text, to_number)
        assert float(cell.text) > float(from_number), "Value in cell%s  is %s, should be greater than %s" % (
            cell.name, cell.text, from_number)
        for c in CELLS.values():
            if cell.name != c.name:
                assert float(cell.text) != float(c.text), "Two same values in table (Cell: %s, Cell: %s)! Value: %s" % (
                    cell.name, c.name, cell.text)


@step(u'Add "{string_to_add}" to cell "{table_cell_name}" table')
def add_value_to_cell(context, string_to_add, table_cell_name):
    # reuse of array so has to be empty!

    context.frame = context.app.get_current_window().child(roleName='document spreadsheet')
    try:
        cell = context.frame.child(roleName='table')[CELL_TRANSLATION[table_cell_name]]
        type_text_to_cell(string_to_add, cell)
        pressKey("enter")
        context.CELLS_INDEX_TEXT[CELL_TRANSLATION[table_cell_name]] = cell.text
    except KeyError:
        assert False, "%s is not supported character for this test!" % table_cell_name


@then(u'Data "{added_string}" added to cell "{table_cell_name}"')
def corrcet_values_in_table_cell(context, added_string, table_cell_name):
    context.frame = context.app.get_current_window().child(roleName='document spreadsheet')
    cell = context.frame.child(roleName='table')[CELL_TRANSLATION[table_cell_name]]
    try:
        assert float(unicode(cell.text, 'utf-8')) == float(
            added_string), "text in cell is incorrect, is: %s, should be: %s" % (cell.text, added_string)
    except (UnicodeEncodeError, ValueError):
        assert unicode(cell.text, 'utf-8') == added_string, "text in cell is incorrect, is: %s, should be: %s" % (
            cell.text, added_string)


@then(u'Save icon avaiable')
def save_icon_avaiable(context):
    menu_item_file = context.app.get_current_window().child(roleName='menu bar')[0]
    menu_item_file.click()
    menu_item_save = menu_item_file.child(name='Save')
    assert menu_item_save.sensitive, "Save menu is not avaiable but it should be"


@then(u'All data in table are consistent')
def all_data_in_table_are_consistent(context):
    context.frame = context.app.get_current_window().child(roleName='document spreadsheet')
    for key, value in context.CELLS_INDEX_TEXT.iteritems():
        assert context.frame.child(roleName='table')[key].text == value,\
            "Data in cell are incorrect, is: %s, should be: %s"\
            % (context.frame.child(roleName='table')[int(key)], value)


@then(u'Dialog frame window named "{dialog_frame_name}" is displayed')
def dialog_frame_window_is_displayed(context, dialog_frame_name):
    sleep(5)
    context.dialog = context.app.get_current_window()
    assert context.dialog.name == dialog_frame_name, "Name of dialog is: %s, should be %s" % (
        context.dialog.name, dialog_frame_name)


@step(u'Add sheet named "{sheet_name}"')
def add_sheet_in_spreadsheet(context, sheet_name):
    menu_item_insert = context.app.get_current_window().child(roleName='menu bar')[3]
    menu_item_insert.click()
    menu_item_insert.child(name='Sheet...').click()
    context.dialog = context.app.get_current_window()
    assert context.dialog.name == "Insert Sheet", "Name of dialog is: %s, should be %s" % (
        context.dialog.name, "Insert Sheet")

    context.dialog.child(roleName='text', name='Name:').grabFocus()
    keyCombo("<CTRL>a")
    pressKey("del")
    typeText(sheet_name)
    context.dialog.child(name='OK', roleName='push button').click()


@step(u'Add "{text_to_add}" to cell "{cell_name}" in table in sheet named "{sheet_name}"')
def add_text_to_sheet_in_spreadsheet_to_cell(context, text_to_add, cell_name, sheet_name):
    # click on right sheet
    page_tab_list = context.app.get_current_window().child(roleName='document spreadsheet').parent[-1].child(
        roleName='page tab list')
    try:
        sheet = page_tab_list.child(name=sheet_name)
        sheet.click()
    except KeyError:
        assert False, "Sheet with name %s is missing" % sheet_name
    # find right cell
    context.frame = context.app.get_current_window().child(roleName='document spreadsheet')
    try:
        cell = context.frame.child(roleName='table')[CELL_TRANSLATION[cell_name]]
        cell.grabFocus()
        # type text
        typeText(text_to_add)
        pressKey("enter")

        DATA.append(sheet_name)
        DATA.append(-1)
        DATA.append(text_to_add)
    except KeyError:
        assert False, "Missing implementation for cell name %s " % cell_name


@step(u'Type "{search_string}" and check option search in all sheets and confirm')
def type_search_and_check_option_in_find_dialog(context, search_string):
    context.dialog = context.app.get_current_window()
    search_for_panel = context.dialog.child(roleName='panel', name='Search For')
    search_for_panel.child(roleName='combo box').click()
    typeText(search_string)
    context.dialog.child(roleName='check box', name='Other options').click()
    context.dialog.child(roleName='check box', name='Search in all sheets').click()
    search_for_panel.child(roleName='push button', name='Find All').click()


@then(u'Data searched are consistent')
def data_in_searched_dialog_are_consistent(context):
    # get table
    context.dialog = context.app.get_current_window()
    table = context.dialog.findChildren(lambda x: x.roleName == 'table')[1].findChildren(
        lambda x: x.roleName == 'table cell')

    assert len(table) == 9, "Some entry is missing in serached! Is: %s, should be: %s" % (len(table), 9)

    for row_index in range(0, 9, 3):
        # because table content is: sheet_name | cell_name | value_in_cell

        # TO DO: this is too hacky - you should fix it
        assert table[6 - row_index].name == DATA[
            row_index], "Entry is not consistent in cell: %s, is: %s, should be: %s" % (
            table[row_index + 1], table[row_index], DATA[row_index])
        assert table[6 - row_index + 2].name == DATA[
            row_index + 2], "Entry is not consistent in cell: %s, is: %s, should be: %s" % (
            table[row_index + 1], table[row_index], DATA[row_index + 2])


@step(u'In dialog window set up curency and dollar format and confirm')
def set_up_currency_and_dollar_format(context):
    context.dialog = context.app.get_current_window()

    number_tab = context.dialog.child(roleName='page tab', name='Numbers')
    number_tab.click()
    number_tab.findChildren(lambda x: x.roleName == 'list item' and x.name == 'Currency')[0].select()
    number_tab.findChildren(lambda x: x.roleName == 'list' and x.name == 'Format')[0][0].select()
    context.dialog.child(name='OK').click()


@then(u'All data in table have dollar format consistent')
def data_in_searched_dialog_are_consistent(context):
    # get table
    context.dialog = context.app.get_current_window()
    table = context.dialog.findChildren(lambda x: x.roleName == 'table')[1].findChildren(
        lambda x: x.roleName == 'table cell')

    assert len(table) == 9, "Some entry is missing in serached! Is: %s, should be: %s" % (len(table), 9)

    for row_index in range(0, 9, 3):
        # because table content is: sheet_name | cell_name | value_in_cell

        # TO DO: this is too hacky - you should fix it
        assert table[6 - row_index].name == DATA[
            row_index], "Entry is not consistent in cell: %s, is: %s, should be: %s" % (
            table[row_index + 1], table[row_index], DATA[row_index])
        assert table[6 - row_index + 2].name == DATA[
            row_index + 2], "Entry is not consistent in cell: %s, is: %s, should be: %s" % (
            table[row_index + 1], table[row_index], DATA[row_index + 2])


@step(u'Make operation "{operation}" between cell "{cell1}" and cell "{cell2}" to cell "{cell_result}"')
def add_value_to_cell(context, operation, cell1, cell2, cell_result):
    # reuse of array so has to be empty!

    context.frame = context.app.get_current_window().child(roleName='document spreadsheet')
    try:
        string_to_add = cell1.split(" ")[1] + " " + operation + " " + cell2.split(" ")[1]

        cell = context.frame.child(roleName='table')[CELL_TRANSLATION[cell_result]]
        cell.grabFocus()

        tool_bar = context.frame.parent.parent[2]
        tool_bar.findChildren(lambda x: x.roleName == 'push button')[2].click()
        typeText(string_to_add)
        tool_bar.findChildren(lambda x: x.roleName == 'push button')[2].click()
    except KeyError:
        assert False, "%s is not supported character for this test!" % cell_result


@step(u'Make sheet as protected')
def make_sheet_protected(context):
    select_menuitem(context, "Tools -> Protect Document -> Sheet...")
    dialog_frame_window_is_displayed(context, "Protect Sheet")

    dialog = context.app.get_current_window()
    # fill password
    text_fields = dialog.findChildren(lambda x: x.roleName == 'password text')
    text_fields[0].grabFocus()
    typeText("red hat")
    text_fields[1].grabFocus()
    typeText("red hat")

    selector1 = dialog.child(roleName='check box', name='Select protected cells')
    selector2 = dialog.child(roleName='check box', name='Select unprotected cells')

    if not selector2.checked:
        selector1.doAction('click')
    if not selector2.checked:
        selector1.doAction('click')

    # confirm
    dialog.child(name='OK').click()
    dialog_frame_window_is_displayed(context, "Untitled 1 - LibreOffice Calc")


@then(u'Dialog frame window named like "{name}" is displayed')
def dialog_with_name_like_displayed(context, name):
    context.dialog = context.app.get_current_window()
    assert name in context.dialog.name, "Name of dialog is: %s, should be more like %s" % (context.dialog.name, name)


@step(u'Write "{text}" to cell in column "{column_name}" and row "{row_name}"')
def select_cell(context, text, column_name, row_name):

    keyCombo('<F5>')
    sleep(1)
    context.dialog = context.app.get_current_window()
    assert "Navigator" == context.dialog.name, "Name of dialog is: %s, should be: %s"\
                                               % (context.dialog.name, "Navigator")

    column_field = context.dialog.child(name='Column', roleName='text')
    row_field = context.dialog.child(name='Row', roleName='text')
    column_field.text = column_name
    row_field.text = row_name
    pressKey("enter")
    typeText(text)
