import logging
import os

from slack import RTMClient

from pyslackops.pbot import PBot


def get_config():
    return {
        "log_level": os.environ.get("PBOT_LOG_LEVEL", "INFO"),
        "pbot_slack_token": os.environ["PBOT_SLACK_TOKEN"]
    }


def main():
    # get config
    config = get_config()

    # configure logging
    logging.basicConfig(
        level=config["log_level"],
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%e%b%Y %l:%M:%S %p %Z"
    )

    # instantiate Slack client
    slack_client = RTMClient(token=config["pbot_slack_token"], connect_method="rtm.start")

    # get the default PBot (uses default built-in PBotHandler)
    pbot = PBot.default_pbot(slack_client, config)
    pbot.start()


if __name__ == "__main__":
    main()
