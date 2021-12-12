*** Settings ***
Library    String
Library    RequestsLibrary
Library    JSONLibrary
Resource   ../../env.robot
Resource   ../authentication/authentication.robot


*** Keywords ***
Create user
    [Arguments]  ${username}  ${email}  ${password}  ${http-status-code}
    Create Session    ${SESSION-ALIAS}   ${API-URL}
    ${user-data}=    Create Dictionary  username=${username}  email=${email}   password=${password}
    ${user-data-json}=    evaluate    json.dumps(${user-data})    json
    ${response}=    Post On Session  ${SESSION-ALIAS}  ${USER-ENDPOINT}  data=${user-data-json}  expected_status=${http-status-code}
    [Return]  ${response}

Get user
    [Arguments]  ${email}  ${password}  ${http-status-code}
    ${authentication-header}=    Get authentication header  ${email}  ${password}  ${http-status-code}
    ${response}=    Get on session   ${SESSION-ALIAS}  ${USER-ENDPOINT}/me  headers=${authentication-header}  expected_status=${http-status-code}
    [Return]  ${response}

Get user id
    [Arguments]  ${user}
    ${user-id}=    Get Value From Json  ${user.json()}  id
    [Return]  ${user-id}

Validate user
    [Arguments]  ${email}  ${password}  ${http-status-code}
    ${response}=  Get user  ${email}  ${password}  ${http-status-code}
    ${email-saved}=    Get Value From Json  ${response.json()}  email
    ${id}=    Get Value From Json  ${response.json()}  id
    Should be equal  ${email-saved}[0]  ${email}
    Should not be empty  ${id}[0]

Validate user response detail
    [Arguments]  ${response}  ${expected-response}
    ${detail}=    Get Value From Json  ${response.json()}  detail
    Should be equal  ${detail}[0]  ${expected-response}