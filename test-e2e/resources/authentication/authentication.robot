*** Settings ***
Library    String
Library    RequestsLibrary
Library    JSONLibrary
Resource   ../../env.robot

*** Keywords ***
Get authentication header
    [Arguments]    ${email}  ${password}   ${http-status-code}
    ${response}=    Get token  ${email}  ${password}  ${http-status-code}
    ${token}=    Get Value From Json  ${response.json()}  access_token
    ${authentication-header}=    Create Dictionary  Authorization=Bearer ${token}[0]
    [Return]    ${authentication-header}

Get token
    [Arguments]    ${email}  ${password}   ${http-status-code}
    Create Session    ${SESSION-ALIAS}   ${API-URL}
    ${token-data}=    Create Dictionary  grant_type=password  username=${email}   password=${password}
    ${response}=    Post On Session  ${SESSION-ALIAS}  ${TOKEN-ENDPOINT}  data=${token-data}  expected_status=${http-status-code}
    [Return]    ${response}

Validate incorrect username or password
    [Arguments]  ${email}  ${password}  ${http-status-code}
    ${response}=  Get user  ${email}  ${password}  ${http-status-code}
    ${email-saved}=    Get Value From Json  ${response.json()}  email
    ${id}=    Get Value From Json  ${response.json()}  id
    Should be equal  ${email-saved}[0]  ${email}
    Should not be empty  ${id}[0]
