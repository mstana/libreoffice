Feature: LibreOffice Writer tests

  @writer_insert_special_character
  Scenario Outline: Insert special character
    * Start soffice via command with Writer parameter
    Then Writer document named like "Untitled" is displayed
    * Select "Insert -> Special Character..." menu
    Then Window named "Special Characters" is displayed
    * In Special Character dialog select "<character label>" character
    Then Paragraph ends with "<character>" character

  Examples: Characters
    | character label | character |
    | @               | @         |
    | :               | :         |
    | $               | $         |
    | ^               | ^         |

  @writer_insert_table
  Scenario: Insert table
    * Start soffice via command with Writer parameter
    Then Writer document named like "Untitled" is displayed
    * Select "Table -> Insert Table..." menu
    Then Window named "Insert Table" is displayed
    * Click the "Insert" button in dialog window
    Then Document contains a table called "Table1-1"

  @writer_open_formula_editor
  Scenario: Opening the Formula Editor
    * Start soffice via command with Writer parameter
    Then Writer document named like "Untitled" is displayed
    * Select "Insert -> Object -> Formula..." menu
    Then Formula panels with names "Elements" and "Commands" for edit are displayed

  @writer_insert_formula
  Scenario: Insert formula
    * Start soffice via command with Writer parameter
    Then Writer document named like "Untitled" is displayed
    * Select "Insert -> Object -> Formula..." menu
    Then Formula panels with names "Elements" and "Commands" for edit are displayed
    * Insert "lllint from{1} to{x} (1 over sum from {k > j} (d_(j)+arccot(nroot{32 }X^{11})))+1" formula to panel with name "Commands"
    * Select "File -> Save As..." menu
    Then In dialog fill out path "/tmp/", name "formula" and confirm
    * Select "File -> Exit LibreOffice" menu
    * Start soffice via command with Writer parameter
    * Select "File -> Open..." menu
    * In open dialog fill out path "/tmp", name "formula.odt" and confirm
    Then Writer document named like "formula" is displayed
    Then Formula "lllint from{1} to{x} (1 over sum from {k > j} (d_(j)+arccot(nroot{32 }X^{11})))+1" is saved in document

  @search_and_replace_text
  Scenario: Search and Replace text
    * Start soffice via command with Writer parameter
    Then Writer document named like "Untitled" is displayed
    * Type text "foo" to paragraph
    * Replace text "foo" with text "bar"
    Then Undo replace text with ctrl+z

  @select_all_also_tables
  Scenario: Select all selects also tables
    * Start soffice via command with Writer parameter
    Then Writer document named like "Untitled" is displayed
    * Type text "Aky zivot, taka smrt!" to paragraph
    * Insert table
    * Select all text and delete
    Then No text displayed

  @export_odt_to_doc
  Scenario: Exporting Non-English MS word format
    * Start soffice via command with Writer parameter
    Then Writer document named like "Untitled" is displayed
    * Insert text "kiitos" to document
    * Save document and close "tmp" with path "/tmp/test_files" as extension "(.doc)"
    Then soffice shouldn't be running anymore
    * Start soffice via command with Writer parameter
    * Select "File -> Open..." menu
    Then Dialog window named "Open" is displayed
    * In Open dialog select "tmp.doc" from "/tmp/test_files"
    Then Writer document named like "tmp" is displayed
    Then Text "kiitos" is in document

  @launch_math_editor
  Scenario: Launch Math editor
    * Start soffice via command with Writer parameter
    Then Writer document named like "Untitled" is displayed
    * Select "File -> New -> Formula" menu
    Then Math Editor launched and displayed
