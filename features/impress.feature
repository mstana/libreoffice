Feature: LibreOffice Impress tests

  @impress_change_layout_of_presentation
  Scenario Outline: Change Impress presentation layout
    * Start soffice via command with Impress parameter
    Then Impress document named like "Untitled" is displayed
    * Select "Format -> Slide Layout..." menu
    * Change Impress presentation layout to <layout name>
    Then Slide should contain <number of items> items

  Examples: Layouts
    | layout name                  | number of items |
    | Title, Content               | 2               |
    | Title and 2 Content          | 3               |
    | Title, 2 Content and Content | 4               |
    | Title, 4 Content             | 5               |
    | Title, 6 Content             | 7               |

  @impress_duplicate_slide
  Scenario: Duplicate Impress slide
    * Start soffice via command with Impress parameter
    Then Impress document named like "Untitled" is displayed
    And Total number of slides is 1
    * Set current slide title to "Unique slide title"
    * Select "Insert -> Duplicate Slide" menu
    Then Current slide title is "Unique slide title"
    And Total number of slides is 2

  @impress_insert_slide
  Scenario: Insert Impress slide
    * Start soffice via command with Impress parameter
    Then Impress document named like "Untitled" is displayed
    And Total number of slides is 1
    * Select "Insert -> Slide" menu
    Then Total number of slides is 2

  @impress_start_slideshow
  Scenario: Start presentation mode
    * Start soffice via command with Impress parameter
    Then Impress document named like "Untitled" is displayed
    * Set current slide title to "Slide one"
    * Select "Slide Show -> Start from first Slide" menu
    Then Presentation window is open
    * Move to the following slide
    Then Presentation window is open
    * Move to the following slide
    Then Presentation window is closed

  @impress_wizard
  Scenario: Create a new presentation using a wizard
    * Start soffice via command with Impress parameter
    Then Impress document named like "Untitled" is displayed
    * Select "File -> Wizards -> Presentation..." menu
    Then Window named "Presentation Wizard" is displayed
    * Create presentation from template titled "Presentation from template"
    Then Current slide title is "Presentation from template"

  @export_odp_to_ppt
  Scenario: Exporting Non-English MS PowerPoint format
    * Start soffice via command with Impress parameter
    Then Impress document named like "Untitled" is displayed
    * Select "Insert -> Slide" menu
    Then Total number of slides is 2
    * Insert to slide "1" text "Доброе утро!"
    * Insert to slide "2" text "コンサート"
    * Save document and close "tmp" with path "/tmp/test_files" as extension "(.ppt)"
    Then soffice shouldn't be running anymore
    * Start soffice via command with impress parameter
    * Select "File -> Open..." menu
    Then Dialog window named "Open" is displayed
    * In Open dialog select "tmp.ppt" from "/tmp/test_files"
    Then Impress document named like "tmp" is displayed
    Then Slide "1" include text "Доброе утро!"
    Then Slide "2" include text "コンサート"
