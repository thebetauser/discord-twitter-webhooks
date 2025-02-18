"""Delete old rules and add new rules.

delete_old_rules - Delete old rules from Twitter.
new_rule - Add new rules to Twitter.
"""
import sys

import tweepy
from loguru import logger
from tweepy import StreamRule
from tweepy.streaming import StreamingClient

from discord_twitter_webhooks.send_webhook import send_error_webhook


def delete_old_rules(stream: StreamingClient) -> None:
    """Check if we have any old rules and delete them if we do.

    Args:
        stream: The tweepy stream object
    """
    # Check Twitter app for rules that already have been created.
    old_rules = stream.get_rules()
    logger.debug("Old rules: {}", old_rules)

    # Get rules and add to list, so we can delete them later.
    rules_to_delete = []

    if old_rules.data is not None:  # type: ignore
        rules_data: list[StreamRule] = old_rules.data  # type: ignore
        for old_rule in rules_data:
            logger.debug("Added {} - {} for deletion", old_rule.value, old_rule.id)
            rules_to_delete.append(old_rule.id)

    # TODO: Only remove rule if the user list has changed?
    # If the app already has rules, delete them first before adding our own
    if rules_to_delete:
        logger.debug("Deleting rules: {}", rules_to_delete)
        stream.delete_rules(rules_to_delete)
    else:
        logger.debug("App had no rules to delete")


def new_rule(rule: str, rule_tag: str, stream: StreamingClient) -> str:
    """Add rule to Twitter. If error, exit.

    Args:
        rule: The rule to add.
        rule_tag: The tag label. This is a free-form text you can use to identify the rules.
        stream: The tweepy stream object.
    """
    logger.info("Adding rule: {} to Twitter", rule)
    if rule:
        rule_to_add: StreamRule = tweepy.StreamRule(value=rule, tag=rule_tag)
        rule_response = stream.add_rules(add=rule_to_add)

        if rule_response.errors:  # type: ignore
            for error in rule_response.errors:  # type: ignore
                if error["title"] == "DuplicateRule":
                    logger.error(
                        (
                            "\nRule already exists '{}'. Each rule must be unique, if you want to send the same rule to"
                            " two different servers you can append another rule to the webhook by typing"
                            " first_webhook,second_webhook"
                        ),
                        rule,
                    )
                    sys.exit("Rule already exists.")
                if error:
                    error_value: str = error["value"] or "Error_value_not_found"
                    error_title: str = error["title"] or "Error_title_not_found"
                    error_details: str = error["details"][0] or "Error_details_not_found"
                    error_msg: str = f"Error adding rule: {error_value}{error_title} - Error details: {error_details}"
                    send_error_webhook(error_msg)
            sys.exit("Error adding rule.")

        rule_data = rule_response.data  # type: ignore
        logger.debug("Rule data: {} for rule: {}", rule_data, rule)

        return rule_data[0].id
    sys.exit("No rule to add. You must add a rule to the config file.")
