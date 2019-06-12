"""Create a bot that responds on requests with 'help' keywords. List all available commands and features."""
import configparser
import logging

# Read config file
config = configparser.ConfigParser()
config.read('init.ini')

# Create global logger
logger = logging.getLogger('helpbot')
formatstring = "%(asctime)s - %(name)s:%(funcName)s:%(lineno)i - %(levelname)s - %(message)s"
logging.basicConfig(format=formatstring, level=logging.DEBUG)


def get_list_of_commands():
    response = """ >Need help :question: Here is a list of available features and corresponding commands. 
    You can use synonyms of these words as trigger words.\n
    For the following features, you need to mention me, using `@BotteBot`:
    
                    \u2022 Get the current weather: `weather in <city>`
                    \u2022 Get the menu of a restaurant: `menu <restaurant> top <number>`
                    \u2022 Order food: `help food`
                    \u2022 Image search: `image of <text>` or `animation of <text>`
                    \u2022 Get help: `help`
                    
    For these features, there is no need to mention me, unless you really want spam in the channel:\n
                    \u2022 Insulting people: `insult <name> in <channel>`
                    \u2022 Let Me Google This For You (LMGTFY): `lmgtfy <text>`
                    \u2022 Define words: `define <word>`
                    \u2022 Repeat text in a channel: `repeat <text> in <channel>`
                    \u2022 Get a list of restaurants that are able to deliver @ iMagineLab: `restaurant top <number>`
                    \u2022 Let the bot tell a random joke: _Sit back, relax and wait for the joke. If nothing happens, type_ `joke`
                   
                """
    return response


def get_list_of_food_commands():
    response = """ >Need help :question: Here is a list of available commands related to food. 
    You can use synonyms of these words as trigger words.\n
    Be sure to mention me, using `@BotteBot`:

                    \u2022 View current restaurant and all current orders: `food list`
                    \u2022 Place a food order: `food order <meal>`
                    \u2022 Remove a food order: `food order remove <meal>`
                    \u2022 View ImagineLab schedule: `food schedule`
                    \u2022 Add date to ImagineLab schedule: `food schedule add <date>`
                    \u2022 Remove date from ImagineLab schedule: `food schedule remove <date>`
                    \u2022 Set a new current restaurant: `food set <restaurant>`
                """
    return response


def get_help_with_features():
    pass
