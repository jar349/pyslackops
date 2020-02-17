import re

from slack import RTMClient

from pyslackops import RegistrationError
from pyslackops.handlers import NamespaceHandler, PBotHandler


class PBot:
    CMD_EXPR = re.compile(r"^\.(?P<namespace>[\w|-]+)\s?(?P<command>.*)")

    @staticmethod
    def default_pbot(slack_client, config):
        default_pbot = PBot(slack_client, config)
        default_pbot.register_handler(PBotHandler(default_pbot))
        return default_pbot

    def __init__(self, slack_client, config):
        self.slack = slack_client
        self.config = config
        self.handlers = {}

    def handle_message_event(self, **payload):
        event = payload['data']
        web_client = payload['web_client']

        # let's not handle subtypes right now
        if 'subtype' in event:
            return

        # pull the text of the message event
        msg_text = event.get('text') or ''

        # see if the message text matches our command expression
        match_result = re.fullmatch(PBot.CMD_EXPR, msg_text)

        if not match_result:
            return

        # we can now assume that we have a command
        namespace = match_result.group('namespace')
        command = match_result.group('command')

        # get some context from the message event
        channel_id = event['channel']
        thread_ts = event['ts']
        user = event['user']

        # figure out which handler should handle this command
        namespace_handler = self.handlers.get(namespace)

        if not namespace_handler:
            web_client.chat_postMessage(
                channel=channel_id,
                text=F":warning: <@{user}> I don't know about that command (try `.pbot help` to get help)"
            )
            return

        try:
            response = namespace_handler.get_response(command, event)
            web_client.chat_postMessage(
                channel=channel_id,
                text=response["message"]
            )
        except Exception as ex:
            web_client.chat_postMessage(
                channel=channel_id,
                text=F":warning: <@{user}> The handler for that command had an exception: {repr(ex)}"
            )

    def register_handler(self, handler):
        if not isinstance(handler, NamespaceHandler):
            raise RegistrationError("Handlers must inherit from pyslackops.handlers.NamespaceHandler. " +
                                    F"{handler.__module__}.{handler.__class__.__name__} does not.")

        # we can now treat it like a NamespaceHandler
        if handler.namespace in self.handlers:
            raise RegistrationError(F"A handler is already registered for namespace '{handler.namespace}'")

        self.handlers[handler.namespace] = handler

    def get_namespaces(self):
        return self.handlers.keys()

    def start(self):
        RTMClient.on(event="message", callback=self.handle_message_event)
        self.slack.start()
