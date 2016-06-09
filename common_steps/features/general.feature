Feature: Generic package checks

  Scenario: Binary has a man page
    When package has man pages
    Then all binary files from this package have a man page
     And all config files from this package have a man page
     And binaries are placed in section 1 or 8
     And configs are placed in section 5
     And no unused man page files are supplied
     And lexgrog for each man page parsing passes

   Scenario: rpmlint
    * rpmlint produces no errors

   Scenario: Selinux alerts
    * no selinux alerts found

   Scenario: ABRT alerts
    * no abrt alerts found