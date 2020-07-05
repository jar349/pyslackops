- mTLS between pyslackops and other services

- other services trust pyslackops's certificate
  - and can therefore trust the slack user issuing op

- the response from handlers shouldn't simply be the 
message to post.  Other information may need to be passed.
So for now, expect json to come back with a 'message' key.

- metadata should have versioned schema

### CURL commands for deployment creation, retrieval,  and completion
- `curl --request GET -H "Authorization: token $GITHUB_PAT" https://api.github.com/repos/jar349/pyslackops/deployments`
- `curl --request POST -H "Authorization: token $GITHUB_PAT" --data '{"ref":"test-deploys", "payload": "this is the payload", "description": "Branch Deploy"}' https://api.github.com/repos/jar349/pyslackops/deployments`
- `curl --request POST -H "Authorization: token $GITHUB_PAT" --data '{"state": "success", "description": "this describes the status"}' https://api.github.com/repos/jar349/pyslackops/deployments/195620169/statuses`

### Protocol Design
in order to handle unknown chatops consistently, each chatop must implement its
end of the pyslackops protocol.  The pyslackops protocol is versioned so that 
one instance of pyslackops can, if it chooses, interoperate with older chatops.

At the moment, there is only one version of the pyslackops protocol: Version 1.

Version 1 of the protocol expects that a chatop expose three web-based end 
points:
 - GET /help
 - GET /metadata
 - POST /handle

#### GET /help
pyslackops will send no payload, no query params.  The response should be of 
type `text/plain` and should explain how to use the chatop.

#### GET /metadata
pyslackops will send no payload, no query params.  The response should be of 
type `application/json` and contain the chatop metadata.  Version 1 of the 
pyslackops protocol knows about the following keys in the metadata response:

| key name | description |
| --- | --- |
| protocol_version | the version of the pyslackops protocol that the chatop implements |

The intent of this endpoint is to enable interoperability between pyslackops 
and chatops that implement differing versions of the pyslackops protocol.

#### GET /ping
pyslackops will send no payload, no query params.  The response should be of 
type `text/plain` and should contain the string `pong`.

#### POST /handle
pyslackops will post data of type `application/json`.  It will be a single 
JSON object with the following keys:
 
| key name | description |
| --- | --- |
| namespace | user types `.what time is it`: namespace is `what` |
| command | user types `.what time is it`: command is `time is it` |
| event | the raw event data from slack; see: https://api.slack.com/events/message |
 
pyslackops expects a response of type `application/json`.  It should be a JSON
object with the following keys:

| key name | description |
| --- | --- |
| message | this is what the user will see | 
