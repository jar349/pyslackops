- mTLS between pyslackops and other services

- other services trust pyslackops's certificate
  - and can therefore trust the slack user issuing op

- the response from handlers shouldn't simply be the 
message to post.  Other information may need to be passed.
So for now, expect json to come back with a 'message' key.

- metadata should have versioned schema

### CURL commands for deployment creation, retrieval,  and completion
- `curl --request GET -H "Authorization: token github-pat" https://api.github.com/repos/jar349/pyslackops/deployments`
- `curl --request POST -H "Authorization: token github-pat" --data '{"ref":"test-deploys", "payload": "this is the payload", "description": "Branch Deploy"}' https://api.github.com/repos/jar349/pyslackops/deployments`
- `curl --request POST -H "Authorization: token github-pat" --data '{"state": "success", "description": "this describes the status"}' https://api.github.com/repos/jar349/pyslackops/deployments/195620169/statuses`
