*** Settings ***
Library    String
Library    RequestsLibrary
Library    JSONLibrary
Resource   ../../env.robot
Resource   ../user/user.robot
Resource   ../authentication/authentication.robot


*** Keywords ***
Add asset
    [Arguments]  ${title}  ${description}  ${owners}  ${type}  ${file-name}  ${authentication-header}  ${http-status-code}
    Create Session    ${SESSION-ALIAS}   ${API-URL}
    ${asset-data}=    Create Dictionary  title=${title}  description=${description}  type=${type}  file_name=${file-name}  owners_id=${owners}
    ${asset-data-json}=    evaluate    json.dumps(${asset-data})    json
    ${response}=    Post On Session  ${SESSION-ALIAS}  ${ASSET-ENDPOINT}  data=${asset-data-json}  headers=${authentication-header}  expected_status=${http-status-code}
    [Return]  ${response}