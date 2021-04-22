from twitter_autobase import Autobase
from twitter_autobase import webhook_manager as webMan
from threading import Thread
import config
from requests import post
from time import sleep

# if you want to run multiple account, create a copy of config.py. example: config2.py , etc.
# then follow these ## template...

## import config2

prevent_loop = list()
# list of all bot_id (str) (that runs using this bot) to prevent loop messages from each account

User = Autobase(config, prevent_loop)
if config.Database:
    User.start_database(config.Github_database)

prevent_loop.append(User.bot_id)

autobase = Thread(target=User.start_autobase)
autobase.start()

## User2 = Autobase(config2, prevent_loop)
## if config2.Database:
##     User2.start_database(config2.Github_database)

## prevent_loop.append(User2.bot_id)

## autobase2 = Thread(target=User2.start_autobase)
## autobase2.start()

# SETTING NGROK AND WEBHOOK SERVER
url = webMan.connect_ngrok(config.NGROK_AUTH_TOKEN)
server = webMan.server_config(
    url=url+"/listener",
    dict_credential={
        User.bot_username : config.CONSUMER_SECRET,
        ## User2.bot_username : config2.CONSUMER_SECRET
    },
    dict_func={
        User.bot_id : User.webhook_connector,
        ## User2.bot_id : User2.webhook_connector
    },
    subscribe=[
        'direct_message_events',
        'follow_events',
    ]
)
webhook = Thread(target=server.listen)
webhook.start()

# TEST SERVER
while post(url+"/listener/test").status_code != 200:
    sleep(1)

# REGISTER WEBHOOK
webMan.register_webhook(url+"/listener", User.bot_username, config)
## webMan.register_webhook(url+"/listener", User2.bot_username, config2)
