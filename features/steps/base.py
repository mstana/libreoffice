# -*- coding: UTF-8 -*-

from behave import step

from dogtail import predicate
from dogtail.tree import root
from common_steps.app import *
from common_steps.appmenu import *
from common_steps.dialogs import *
from dogtail.rawinput import keyCombo, typeText, pressKey, drag
from general import window_is_displayed, select_menuitem
from dogtail.procedural import FocusWidget, FocusWindow


# TABLE_FIELDS and TABLE_RECORDS are strictli connected to each other!

TABLE_FIELDS = [

    {'name': 'name',
     'type': 'Text [ VARCHAR ]',
     'description': 'name description'},
    {'name': 'address',
     'type': 'Text [ VARCHAR ]',
     'description': 'address description'},
    {'name': 'phoneNumber',
     'type': 'Text [ VARCHAR ]',
     'description': 'phone number description'}
]

TABLE_RECORDS = [

    {'id': '7',
     'name': 'Spider man',
     'address': 'Some address 225',
     'phone': '123'},
    {'id': '8',
     'name': 'Batman',
     'address': 'Some address 11',
     'phone': '124'},
    {'id': '9',
     'name': 'Thor',
     'address': 'Some address 22',
     'phone': '12353'},
    {'id': '25',
     'name': 'Thor sister',
     'address': 'Some address 3',
     'phone': '999'}
]

TABLE_RECORDS_NON_ENGLISH = [

    {'id': '7',
     'name': '昨夜, 最高',
     'address': 'Доброе утро!',
     'phone': '3'},
    {'id': '8',
     'name': 'コンサート',
     'address': 'でした',
     'phone': '2'},
    {'id': '9',
     'name': 'サー',
     'address': 'утро',
     'phone': '5'},
    {'id': '10',
     'name': '最高',
     'address': 'ř',
     'phone': '1'}
]


@step(u'Create database')
def create_database(context):
    context.app.get_current_window().findChildren(
        lambda x: x.roleName == 'push button' and x.name == 'Finish' and x.showing)[0].click()


@step(u'Create table with name "{name}" in database with name "{dbname}" in design mode')
def create_table_in_design_mode(context, name, dbname):
    select_menuitem(context, "Insert -> Table Design...")
    window_is_displayed(context, dbname + ".odb : " + "Table1" + " - LibreOffice Base: Table Design")
    # fill out values for table
    create_table_window = context.app.get_current_window()
    master_table = create_table_window.findChildren(lambda x: x.roleName == 'table' and x.name == 'Table')[0]

    # this part is kind of magic - it uses TAB for moving in table and grabFocus
    # and typeText because original type text on object of table is not implemented in current version of dogtail
    master_table[1].grabFocus()
    typeText(TABLE_FIELDS[0]['name'])

    pressKey('\t')
    pressKey('\t')
    typeText(TABLE_FIELDS[0]['description'])

    pressKey('\t')

    typeText(TABLE_FIELDS[1]['name'])
    pressKey('\t')
    pressKey('\t')
    typeText(TABLE_FIELDS[1]['description'])

    pressKey('\t')

    typeText(TABLE_FIELDS[2]['name'])
    pressKey('\t')
    pressKey('\t')
    typeText(TABLE_FIELDS[2]['description'])

    # click na save as
    create_table_window.findChildren(lambda x: x.roleName == 'push button' and x.name == 'Save' and x.showing)[
        0].click()
    dialog = context.app.get_current_window()
    sleep(2)
    assert dialog.name == 'Save As', "probably bad dialog because name of dialog should be Save as, but was '%s'" % (
        dialog.name)
    dialog.textentry('Table Name').typeText(name)
    dialog.button('OK').click()

    if context.app.get_current_window().name == 'LibreOffice Base':
        context.app.get_current_window().button('Yes').click()
    # close edit table window
    keyCombo('<Control>w')


@then(u'Table with name "{name}" created')
def table_created(context, name):
    # assert here that on main page of app is table created
    assert context.app.get_current_window().child(roleName='tree item', name=name)


@step(u'Open table "{tbname}" from main view')
def open_table_from_main_view(context, tbname):
    context.app.get_current_window().findChildren(lambda x: x.roleName == 'tree item' and x.text == tbname)[0].doubleClick()


@step(u'Enter records to table')
def enter_records_to_table(context):
    table = context.app.get_current_window().findChildren(
        lambda x: x.roleName == 'table' and x.name == 'Table' and x.showing)[0]
    table[1].grabFocus()
    for record in TABLE_RECORDS:
        typeText(record['id'])
        pressKey('\t')
        typeText(record['name'])
        pressKey('\t')
        typeText(record['address'])
        pressKey('\t')
        typeText(record['phone'])
        pressKey('\t')
    context.app.get_current_window().findChildren(
        lambda x: x.roleName == 'push button' and x.name == 'Save current record' and x.showing)[0].click()
    # close edit table window
    keyCombo('<Control>w')


@step(u'Enter non-english records to table')
def enter_records_to_table(context):
    table = context.app.get_current_window().findChildren(
        lambda x: x.roleName == 'table' and x.name == 'Table' and x.showing)[0]
    table[1].grabFocus()
    for record in TABLE_RECORDS_NON_ENGLISH:
        typeText(record['id'])
        pressKey('\t')
        typeText(record['name'])
        pressKey('\t')
        typeText(record['address'])
        pressKey('\t')
        typeText(record['phone'])
        pressKey('\t')
    sleep(10)
    context.app.get_current_window().findChildren(
        lambda x: x.roleName == 'push button' and x.name == 'Save current record' and x.showing)[0].click()
    # close edit table window
    keyCombo('<Control>w')


@then(u'Assert "{type_of_records}" records in table with name "{tbname}" in db "{dbname}"')
def table_created(context, type_of_records, tbname, dbname):
    button = context.app.get_current_window().findChildren(lambda x: x.roleName == 'tree item' and x.text == tbname)[0]
    button.doubleClick()

    if button.showing:
        button.doubleClick()

    w = context.app.get_current_window()
    table = w.findChildren(lambda x: x.roleName == 'table' and x.name == 'Table' and x.showing)[0]
    i = 1

    tab_rec = []
    if type_of_records == "non-english":
        tab_rec = TABLE_RECORDS_NON_ENGLISH
    if type_of_records == "english":
        tab_rec = TABLE_RECORDS

    for record in tab_rec:

        assert table[i].text == record['id'],\
            "Incorrect text in column " + "id" + " and row " + str(i) + ", expected '%s' but was '%s'" % (
            record['id'], table[i].text)
        assert table[i + 1].text == record['name'],\
            "Incorrect text in column " + "name" + " and row " + str(i) + ", expected '%s' but was '%s'" % (
            record['name'], table[i + 1].text)
        assert table[i + 2].text == record['address'],\
            "Incorrect text in column " + "address" + " and row " + str(i) + ", expected '%s' but was '%s'" % (
            record['address'], table[i + 2].text)
        # there is commented assert for last column in table because thrue the accessibility its imposible to reach it
        # assert table[i+3].text == record['phone'], "Incorrect text in paragraph,\
        #  expected '%s' but was '%s'" % (record['phone'], table[i+3].text)
        i += len(record)

    j = 1
    for record in tab_rec:
        table[j].grabFocus()
        for i in range(0, len(tab_rec[0])-1):
            pressKey('\t')
        keyCombo('<Control>c')
        table[j+1].grabFocus()
        keyCombo('<Control>a')
        keyCombo('<Control>v')
        keyCombo('<Enter>')
        assert table[j+1].text == record['phone'], "Incorrect text in paragraph, expected '%s' but was '%s'" % (
            record['phone'], table[j+1].text)

        j += len(tab_rec[0])
