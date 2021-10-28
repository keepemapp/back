*** Settings ***
Library    String
Library    RequestsLibrary
Library    JSONLibrary
Library    FakerLibrary
Resource   ../env.robot
Resource   ../resources/user/user.robot

*** Test Cases ***
Register user
    Create user data
    ${response}=  Create user  ${username}  ${email}  ${password}  ${HTTP-200}
    Validate user  ${email}  ${password}  ${HTTP-200}

Register user that aready exists
    ${response}=  Create user  ${username}  ${email}  ${password}  ${HTTP-400}
    Validate user response detail  ${response}  ${MESSAGE-USER-ALREADY-EXISTS}

Login with non existing user
    ${response}=    Get token  incorrect@incorrect.com  123456  ${HTTP-401}
    ${detail}=    Get Value From Json  ${response.json()}  detail
    Should be equal  ${detail}[0]  ${MESSAGE-INCORRECT-USERNAME-PASSWORD}

Login with incorrect password
    ${response}=    Get token  ${email}  123456  ${HTTP-401}
    ${detail}=    Get Value From Json  ${response.json()}  detail
    Should be equal  ${detail}[0]  ${MESSAGE-INCORRECT-USERNAME-PASSWORD}

*** Keyword ***
Create user data
     ${username}=  First name
     ${username}=  Convert to lower case  ${username}
     ${email}=  Free email
     ${password}=  Password
     Set global variable  ${username}
     Set global variable  ${email}
     Set global variable  ${password}


