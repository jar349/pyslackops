from abc import ABC, abstractmethod


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
    def get_response(self, command, event):
        pass


class PBotHandler(NamespaceHandler):
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
