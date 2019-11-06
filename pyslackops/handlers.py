from abc import ABC, abstractmethod

import requests


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
    def __init__(self, namespace, base_url, cert, private_key, ca_cert):
        super().__init__(namespace)
        self.base_url = base_url
        self.cert = cert
        self.private_key = private_key
        self.ca_cert = ca_cert

    def _do_get(self, url, extract_func):
        headers = {"Accept": "application/json"}
        res = requests.get(url, headers=headers, cert=(self.cert, self.private_key), verify=self.ca_cert)
        if res.status_code != 200:
            raise HandlerException(F"Handler for namespace {self.namespace} returned HTTP Status {res.status_code}")

        return extract_func(res)

    def get_basic_help(self):
        return self._do_get(self.base_url + "/help", lambda res: res.json())

    def get_metadata(self):
        return self._do_get(self.base_url + "/metadata", lambda res: res.json())

    def get_response(self, command, event):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        res = requests.post(
            self.base_url + "/handle",
            {"command": command, "event": event},
            headers=headers,
            cert=(self.cert, self.private_key),
            verify=self.ca_cert
        )
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
        self.cmd_map = {
            "help": self.get_basic_help,
            "ping": self.ping,
            "list": self.list_namespaces
        }

    def get_response(self, command, event):
        cmd_parts = command.split(' ')
        cmd = cmd_parts.pop(0)  # this leaves only arguments

        func = self.cmd_map.get(cmd, None)
        if not func:
            return ":warning: I don't know about that command (try `.pbot help` for help)"

        return func(cmd_parts)

    def get_metadata(self):
        return {}

    def get_basic_help(self, args):
        return """.pbot commands:
```
 - help: the command you've just run
 - ping: pbot will respond PONG!; good for testing pbot
 - list: shows the list of registered namespaces
 
example usage:
  .pbot ping
```"""

    def ping(self, args):
        return "PONG!"

    def list_namespaces(self, args):
        response = [
            "The following namespaces are registered with pbot: ",
            "_(For each of the following namespaces try `.namespace help`)_"
            "```"
        ]
        for namespace in self.pbot.get_namespaces():
            response.append(F" - {namespace}")
        response.append("```")
        return '\n'.join(response)
