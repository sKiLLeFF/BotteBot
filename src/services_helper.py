import ast
import json
import logging

from slack.web.slack_response import SlackResponse

import food_bot
import help_bot
import image_bot
import random_bot
import weather_bot
from constants import insult_triggers, no_imaginelab_triggers, food_triggers, \
    menu_triggers, resto_triggers, image_triggers, joke_triggers, weather_triggers, \
    notification_channel, help_triggers, ignored_words

logger = logging.getLogger()
client = bot_id = user_ids = public_channel_ids = last_message_ts = last_channel_id = is_imaginelab = None


def init(slack_client):
    global client, bot_id, user_ids, public_channel_ids, is_imaginelab
    client = slack_client
    # Get all user IDs and channel IDs
    bot_id = client.auth_test()["user_id"]
    user_ids = [element["id"] for element in client.users_list()["members"]]
    public_channel_ids = [element["id"] for element in client.channels_list()["channels"]]
    is_imaginelab = False


def receive_message(user_id, text_received, channel_read):
    attachments = blocks = None
    if user_id != bot_id:
        user_name = get_user_info(user_id)["user"]["name"]
        words_received = text_received.lower().split()
        message, channel = random_bot.joke_second()

        if message is None or channel is None:
            [channel, words_received] = check_channel(words_received, channel_read)
            [words_received, mention] = filter_ignore_words(words_received)
            if not message and (mention or (channel not in public_channel_ids)):
                message, channel, attachments, blocks = mention_question(user_name, words_received, channel, message)
            if not message:
                message, channel = check_random_keywords(user_name, words_received, channel, message)
        if message or attachments or blocks:
            if blocks is not None:
                blocks = json.dumps(blocks["blocks"])
            send_message(channel, message, attachments, blocks)
    return None


def send_message(channel, text, attachments, blocks):
    global last_message_ts, last_channel_id
    if channel is None:
        logger.error('Channel is not initialized!')
        return
    if text is None and blocks is None:
        logger.error('Cannot send as both text and blocks are not initialized!')
        return
    if text is not None:  # text has priority over blocks
        blocks = None
    # todo: check whether this is still needed
    data = ast.literal_eval(SlackResponse.__str__(
        client.chat_postMessage(as_user="true", channel=channel, text=text, attachments=attachments, blocks=blocks)))
    last_message_ts = data["ts"]
    last_channel_id = data["channel"]
    logger.debug('Message sent to {}'.format(channel))


def update_message(timestamp=None, channel=None, text=None, blocks=None):
    if channel is None:
        if last_channel_id is None:
            logger.error('Channel (of last message) is not initialized!')
            return
        else:
            channel = last_channel_id
    if timestamp is None:
        if last_message_ts is None:
            logger.error('Timestamp (of last message) is not initialized!')
            return
        else:
            timestamp = last_message_ts
    if text is None and blocks is None:
        logger.error('Cannot update as both text and blocks are not initialized!')
        return
    if text is not None:  # text has priority over blocks
        blocks = None
    client.chat_update(as_user="true", ts=timestamp, channel=channel, text=text, blocks=blocks)


def open_view(trigger_id, view):
    client.views_open(trigger_id=trigger_id, view=view)


def get_user_info(user_id):
    return client.users_info(user=user_id)


def filter_ignore_words(words_received):
    mentioned = False
    relevant_words = []
    for word in words_received:
        if '@{}'.format(bot_id.lower()) in word:
            mentioned = True
        elif word not in ignored_words:
            relevant_words.append(word)
    return relevant_words, mentioned


def check_channel(text_words, channel):
    """Check whether a channel got mentioned"""
    for channel_id in public_channel_ids:
        for word in text_words:
            if '#{}'.format(channel_id.lower()) in word:
                logger.critical(channel_id)
                text_words.remove(word)
                channel = channel_id
                break
    return channel, text_words


def check_random_keywords(user_name, words_received, channel, message):
    """To check for words used in normal conversation, adding insults and gifs/images"""
    if not message and any(word in words_received for word in insult_triggers):
        for user_id_mention in user_ids:
            if '<@{}>'.format(user_id_mention.lower()) in words_received:
                first_name = get_user_info(user_id_mention)["user"]["real_name"].split(" ")[0]
                message = random_bot.insult(first_name)
                logger.debug('{} insulted someone in {}'.format(user_name, channel))
                break
    if not message:
        message = random_bot.definition(words_received)
        if message:
            logger.debug('{} asked for a definition a word in {}'.format(user_name, channel))
    if not message:
        message = random_bot.repeat(words_received)
        if message:
            logger.debug('{} repeated a word in {}'.format(user_name, channel))
    if not message:
        message, channel = random_bot.joke(channel, False)
    return message, channel


def check_general_keywords(user_name, words_received, channel, message):
    """Check for serious shit. Predefined commands etc."""
    attachments = blocks = None
    if not message and any(word in words_received for word in help_triggers):
        message = help_bot.get_list_of_commands()
        logger.debug('{} asked the HelpBot for info in channel {}'.format(user_name, channel))
    if not message:
        for food_trigger in food_triggers:
            if food_trigger in words_received:
                logger.debug('{} asked the FoodBot a request in channel {}'.format(user_name, channel))
                message, blocks = food_bot.process(user_name, words_received)
    if not message and any(word in words_received for word in menu_triggers):
        logger.debug('{} asked the Foodbot for menu in channel {}'.format(user_name, channel))
        message = food_bot.get_menu(words_received)
    if not message and any(word in words_received for word in resto_triggers):
        logger.debug('{} asked the Foodbot for restaurants in channel {}'.format(user_name, channel))
        message, restaurants = food_bot.get_restaurants(words_received)
    if not message and any((word in words_received for word in image_triggers)):
        logger.debug('{} asked the ImageBot a request in channel {}'.format(user_name, channel))
        message, attachments = image_bot.find_image(words_received, image_triggers)
    if not message and any((word in words_received for word in joke_triggers)):
        message, channel = random_bot.joke(channel, True)
    if not message and all(word in no_imaginelab_triggers for word in words_received):
        logger.debug('{} asked the bot to toggle ImagineLab for this week in channel {}'.format(user_name, channel))
        message = toggle_imaginelab()
    return message, channel, attachments, blocks


def mention_question(user_name, words_received, channel, message):
    """bot got mentioned or pm'd, answer the question"""
    logger.debug('BotteBot got mentioned in {}'.format(channel))
    attachments = blocks = None
    if not message:
        message, channel, attachments, blocks = check_general_keywords(user_name, words_received, channel, message)
    if not message and any(word in words_received for word in weather_triggers):
        message = weather_bot.get_weather_message()
    if not message:
        message = random_bot.lmgtfy(words_received)
    if not message:
        message = help_bot.report_bug(words_received, user_name)
    return message, channel, attachments, blocks


def print_where_food_notification():
    if is_imaginelab:
        send_message(notification_channel, "<!channel> Where are we going to order today?", None, None)


def print_what_food_notification():
    global is_imaginelab
    if is_imaginelab:
        send_message(notification_channel, "<!channel> What do you all want to order?", None, None)
        blocks = food_bot.get_order_overview(False)
        blocks = json.dumps(blocks["blocks"])
        send_message(notification_channel, None, None, blocks)
        client.pins_add(channel=last_channel_id, timestamp=last_message_ts)


def toggle_imaginelab():
    global is_imaginelab
    if is_imaginelab:
        send_message(notification_channel, "<!channel> iMagineLab is cancelled for this week!", None, None)
        is_imaginelab = False
        return "iMagineLab is cancelled for this week."
    else:
        send_message(notification_channel, "<!channel> iMagineLab has been rescheduled for this week!", None, None)
        is_imaginelab = True
        return "iMagineLab has been rescheduled for this week."
