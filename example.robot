*** Settings ***
Library         SeleniumLibrary
*** Variables ***
${browser}  chrome
${baseurl}  https://the-internet.herokuapp.com/tables
${url}      %{url=https://openiap.io}
*** Test Cases ***
Page Test
    open browser    ${url}  ${browser}
    maximize browser window
    Sleep    1s
    capture page screenshot
    close browser
Table Test
    open browser    ${baseurl}  ${browser}
    maximize browser window
#Capture the data of a specific cell
    ${data}=    get text    xpath://table[@id='table1']/tbody/tr[2]/td[5]
#get the count of columns in a specific row
    ${Columns}=     get element count  xpath://table[@id='table1']/tbody/tr[2]/td
#get the total number of rows in the table
    ${Rows}=    get element count    xpath://table[@id='table1']/tbody/tr
Validations
#Validate header
    table header should contain     xpath://table[@id='table1']     Action
#Validate row
    table row should contain        xpath://table[@id='table1']     3       http://www.jdoe.com
#Validate column
    table column should contain    xpath://table[@id='table1']  5   Web Site
#Validate cell
    table cell should contain    xpath://table[@id='table1']    4   3   jdoe@hotmail.com
    capture page screenshot
    close browser
