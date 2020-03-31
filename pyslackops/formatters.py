import re


# see Slack docs: https://api.slack.com/reference/surfaces/formatting#retrieving-messages
class SlackFormattedSubstring:
    SLACK_FORMAT_RE = re.compile("<(.*?)>")

    def init(self, raw):
        self.raw = raw

    @staticmethod
    def is_slack_formatted(raw_string):
        return SlackFormattedSubstring.SLACK_FORMAT_RE.match(raw_string) is not None

    def get_content_or_none(self):
        if not SlackFormattedSubstring.is_slack_formatted(self.raw):
            return None

        # since we now know that this is slack formatted, strip the leading and ending < > from the raw string
        return self.raw[1:-1]

    def get_raw(self):
        return self.raw
    
    def is_channel_link(self):
        content = self.get_content_or_none()

        if not content:
            return False

        return content.startswith("#C")

    def is_user_mention(self):
        content = self.get_content_or_none()

        if not content:
            return False

        return content.startswith("@U") or content.startswith("@W")

    def is_subteam_mention(self):
        content = self.get_content_or_none()

        if not content:
            return False

        return content.startswith("!subteam")

    def is_special_mention(self):
        content = self.get_content_or_none()

        if not content:
            return False

        a_subteam_mention = self.is_subteam_mention()
        return content.startswith("!") and not a_subteam_mention

    def is_url_link(self):
        content = self.get_content_or_none()

        if not content:
            return False

        if self.is_channel_link():
            return False

        if self.is_user_mention():
            return False

        if self.is_subteam_mention():
            return False

        if self.is_special_mention():
            return False

        return True
