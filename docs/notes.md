- mTLS between pyslackops and other services

- other services trust pyslackops's certificate
  - and can therefore trust the slack user issuing op

- the response from handlers shouldn't simply be the 
message to post.  Other information may need to be passed.
So for now, expect json to come back with a 'message' key.

- metadata should have versioned schema