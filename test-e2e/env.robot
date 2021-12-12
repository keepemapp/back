*** Variables ***
${SESSION-ALIAS}  emo-test
${API-URL}  http://127.0.0.1:8000/
${TOKEN-ENDPOINT}   ${API-URL}api/v1/token
${USER-ENDPOINT}    ${API-URL}api/v1/users
${ASSET-ENDPOINT}   ${API-URL}api/v1/assets
${HTTP-200}  200
${HTTP-400}  400
${HTTP-401}  401
${MESSAGE-USER-ALREADY-EXISTS}  Email already exists
${MESSAGE-INCORRECT-USERNAME-PASSWORD}  Incorrect username or password