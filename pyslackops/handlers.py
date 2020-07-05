from abc import ABC, abstractmethod
import logging
import json
import requests
import uuid
import validators

from pyslackops import RegistrationError
from pyslackops.formatters import SlackFormattedSubstring


class HandlerException(Exception):
    pass


class NamespaceHandler(ABC):
    def __init__(self, namespace):
        if not namespace:
            raise ValueError("namespace cannot be empty")
        self.namespace = namespace.lower()

    def handles(self, proposed_namespace):
        if not proposed_namespace:
            return False
        return self.namespace == proposed_namespace.lower()

    @abstractmethod
    def get_basic_help(self):
        pass

    @abstractmethod
    def get_ping(self):
        pass

    @abstractmethod
    def get_metadata(self):
        pass

    @abstractmethod
    def get_response(self, command, event):
        pass


class APIHandler(NamespaceHandler):
    """
    This class acts as a proxy for some web API out there on the webs.  Any API that wishes to provide commands must
    provide at least 3 endpoints:
     - GET /help
     - GET /metadata
     - POST /handle
    """

    def __init__(self, namespace, base_url, cert=None, private_key=None, ca_cert=None):
        super().__init__(namespace)
        self.base_url = base_url
        self.cert = cert
        self.private_key = private_key
        self.ca_cert = ca_cert
        self.log = logging.getLogger(__name__)
        
    def _do_get(self, request_url, headers, extract_func):
        res = requests.get(request_url, headers=headers, cert=(self.cert, self.private_key), verify=self.ca_cert)
        if res.status_code != 200:
            raise HandlerException(F"Handler for namespace {self.namespace} returned HTTP Status {res.status_code}")

        return extract_func(res)

    def get_basic_help(self):
        headers = {"Accept": "plain/text"}
        return self._do_get(self.base_url + "/help", headers, lambda res: res.text)

    def get_metadata(self):
        headers = {"Accept": "application/json"}
        return self._do_get(self.base_url + "/metadata", headers, lambda res: res.json())

    def get_ping(self):
        headers = {"Accept": "plain/text"}
        return self._do_get(self.base_url + "/ping", headers, lambda res: res.text)

    def get_response(self, command, event):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        body = {
            "namespace": self.namespace,
            "command": command,
            "event": json.dumps(event)
        }
        request_url = self.base_url + "/handle"

        self.log.debug(f"Sending POST to {request_url} with headers {headers} and body {body}")

        res = requests.post(request_url, None, body, headers=headers)
        if res.status_code != 200:
            raise HandlerException(F"Handler for namespace {self.namespace} returned HTTP Status {res.status_code}")
        return res.json()


class PBotHandler(NamespaceHandler):
    """
    The PBotHandler is special because it gets a reference back to PBot
    """

    def __init__(self, pbot):
        super().__init__("pbot")
        self.pbot = pbot
        self.log = logging.getLogger(__name__)

    def get_response(self, command, event):
        self.log.debug(F"Will get a response to command: {command}")
        cmd_parts = command.split(' ')
        cmd = cmd_parts.pop(0).lower()  # this leaves only arguments

        if cmd == "help":
            return self.get_basic_help()
        elif cmd == "list":
            return self.list_namespaces()
        elif cmd == "ping":
            return self.get_ping()
        elif cmd == "register":
            return self.register_namespace(cmd_parts)
        elif cmd == "test":
            return self.report_test_result(cmd_parts)
        else:
            return {"message": ":warning: I don't know about that command (try `.pbot help` for help)"}

    def get_metadata(self):
        return {
            "protocol_version": "0.1"
        }

    def get_basic_help(self):
        return """.pbot commands:
```
 - help:     the command you've just run
 - ping:     pbot will respond PONG!; good for testing pbot
 - list:     shows the list of registered namespaces
 - test:     tests a URL for conformance and readiness for registration 
 - register: registers an ops handler for a namespace

example usage:
  .pbot ping
```"""

    def get_ping(self):
        return "pong"

    def list_namespaces(self):
        response = [
            "The following namespaces are registered with pbot: ",
            "_(For each of the following namespaces try `.namespace help`)_"
            "```"
        ]
        for namespace in self.pbot.get_namespaces():
            response.append(F" - {namespace}")
        response.append("```")
        return {"message": '\n'.join(response)}

    def register_namespace(self, cmd_args):
        # expected cmd_args: ["the_namespace", "the_handler_URL"]
        if len(cmd_args) != 2:
            return {"message": ":red_circle: register requires two arguments: namespace and handler URL"}

        namespace = cmd_args[0]
        raw_url = cmd_args[1]

        if namespace.startswith("."):
            return {"message": ":red_circle: The registered namespace must not start with a dot"}

        # slack sends links surrounded by angle brackets (<, >) if it recognizes a URL, so we need to extract the URL
        substring = SlackFormattedSubstring(raw_url)
        handler_url = substring.get_content_or_none() if substring.is_url_link() else substring.get_raw()

        test_result = self.test_handler(handler_url)
        if not test_result["passed"]:
            return {"message": ":red_circle: the provided handler does not seem to be valid. Try: `.pbot test [URL]`"}

        try:
            self.pbot.register_handler(APIHandler(namespace, handler_url))
        except RegistrationError as re:
            return {"message": F":red_circle: Unable to register handler: {re.message}"}

        return {"message": f":tada: :white_check_mark: New handler for namespace `.{namespace}` registered"}

    def test_handler(self, handler_url):
        result = {"passed": True}
        
        if not handler_url:
            result["passed"] = False
            result["problem"] = "test requires a URL as an argument"
            return result
        
        if not validators.url(handler_url):
            result["passed"] = False
            result["problem"] = (F"{handler_url} is not a valid URL. see: " +
                                 "https://validators.readthedocs.io/en/latest/index.html#module-validators.url")
            return result

        self.log.info(F"Will test URL: {handler_url}")
        test_handler = APIHandler(str(uuid.uuid4()), handler_url)
        
        try:
            result["metadata"] = test_handler.get_metadata()
        except Exception as ex:
            result["passed"] = False
            result["problem"] = "The metadata endpoint failed"
            result["metadata"] = repr(ex)

        try:
            result["basic_help"] = test_handler.get_basic_help()
        except Exception as ex:
            result["passed"] = False
            result["problem"] = "The basic help endpoint failed"
            result["basic_help"] = repr(ex)

        try:
            result["ping"] = test_handler.get_ping()
            if result["ping"] != "pong":
                raise Exception("/ping endpoint responded but not with: pong")
        except Exception as ex:
            result["passed"] = False
            result["problem"] = "The ping endpoint failed"
            result["ping"] = repr(ex)

        return result

    def report_test_result(self, cmd_args):
        if not cmd_args:
            return {"message": F":red_circle: test requires a URL as an argument"}

        # the only expected argument is the url of the service, so ignore any others.  In addition, slack sends links
        # surrounded by angle brackets (<, >) if it recognizes a URL, so we need to extract the URL from that.
        substring = SlackFormattedSubstring(cmd_args[0])
        ns_url = substring.get_content_or_none() if substring.is_url_link() else substring.get_raw()

        test_result = self.test_handler(ns_url)

        if test_result["passed"]:
            return {"message": F":tada: :white_check_mark: `{ns_url}` passes!\n{str(test_result)}"}
        else:
            return {"message": F":red_circle: {test_result['problem']}\n{str(test_result)}"}
