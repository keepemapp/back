*** Settings ***
Library    String
Library    RequestsLibrary
Library    JSONLibrary
Library    FakerLibrary
Resource   ../env.robot
Resource   ../resources/authentication/authentication.robot
Resource   ../resources/user/user.robot
Resource   ../resources/asset/asset.robot

*** Test Cases ***
Create asset
    Create asset data
    ${authentication-header}=    Get authentication header  ${email}  ${password}  ${HTTP-200}
    ${user}=    Get user  ${email}  ${password}  ${HTTP-200}
    ${user-id}=    Get user id  ${user}
    @{owner-list}=   Create list  ${user-id}
    ${response}=    Add asset  ${title}  ${description}   @{owner-list}  ${type}  ${file-name}  ${authentication-header}  ${HTTP-200}

*** Keyword ***
Create asset data
     ${title}=  Pystr
     ${description}=  Text
     ${type}=  File extension
     ${file-name}=  File name
     Set global variable  ${title}
     Set global variable  ${description}
     Set global variable  ${type}
     Set global variable  ${file-name}


