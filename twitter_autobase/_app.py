from requests import post
from threading import Thread
from time import sleep
from autobase import Autobase
from autobase import webhook_manager as webMan
import _config
import logging
logging.basicConfig(level=logging.WARNING, format="%(name)s - %(levelname)s - %(message)s")

# if you want to run multiple account, create a copy of config.py. example: config2.py , etc.
# then follow these ## template...
# You only need one ngrok auth token

## import config2

prevent_loop = list()
# list of all bot_id (str) (that runs using this bot) to prevent loop messages from each account

User = Autobase(_config, prevent_loop)
## User2 = Autobase(config2, prevent_loop)

# SETTING NGROK AND WEBHOOK SERVER
url = webMan.connect_ngrok(_config.NGROK_AUTH_TOKEN)
server = webMan.server_config(
    url=url+"/listener",
    dict_credential={
        User.bot_username : _config.CONSUMER_SECRET,
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
webMan.register_webhook(url+"/listener", User.bot_username, _config)
## webMan.register_webhook(url+"/listener", User2.bot_username, config2)
