from .twitivity import Event, Activity
from pyngrok import ngrok
from time import sleep
from typing import NoReturn
import logging
import json

logger = logging.getLogger(__name__)

# Connect ngrok
def connect_ngrok(ngrok_auth_token: str) -> str:
    '''
    :return: ngrok url
    '''
    try:
        ngrok.set_auth_token(ngrok_auth_token)
        ngrok_tunnel = ngrok.connect(8080, bind_tls=True)
    except:
        logger.warning("waiting ngrok... Make sure you have disconnected another client session!")
        sleep(15)
        ngrok.set_auth_token(ngrok_auth_token)
        ngrok_tunnel = ngrok.connect(8080, bind_tls=True)

    print("NGROK URL: {}".format(ngrok_tunnel.public_url))
    
    return ngrok_tunnel.public_url

# Register webhook
def register_webhook(url: str, name: str, credential: object, delLastWeb: bool=True) -> object:
    '''
    Register webhook to twitter
    '''
    activity = Activity(
        {
            'consumer_key'      : credential.CONSUMER_KEY,
            'consumer_secret'   : credential.CONSUMER_SECRET,
            'access_token'      : credential.ACCESS_KEY,
            'access_token_secret': credential.ACCESS_SECRET,
            'env_name'          : credential.ENV_NAME
        }
    )
    # delete the last active webhook
    if delLastWeb:
        for environment in activity.webhooks()['environments']:
            if environment['environment_name'] == activity.env_name:
                if len(environment['webhooks']):
                    webhook_id = environment['webhooks'][0]['id']
                    activity.delete(webhook_id)
                    break

    url += "/{}".format(name)
    print(activity.register_webhook(url))
    return activity.subscribe()

# Webhook server
class StreamEvent(Event):
    '''
    :param func_data: dict of function(one arg) that will be called when webhook receives data, user_id (str) as a key       
        func_data = {
            'username': function,
        }

    :param subscribe: list of (str) subscriptions that will be subscribed.\
    see more on: https://developer.twitter.com/en/docs/twitter-api/enterprise/account-activity-api/guides/account-activity-data-objects
    '''
    
    def __init__(self, func_data: dict, subscribe: list):
        self.func_data = func_data
        self.subcriptions = subscribe
    
    @classmethod
    def set_callback(cls, callback_url: str) -> NoReturn:
        cls.CALLBACK_URL = callback_url
    
    @classmethod
    def update_credential_id(cls, credential_id: dict) -> NoReturn:
        cls.credential_id.update(credential_id)

    def on_data(self, data: json) -> NoReturn:
        if data is None:
            return
        if any(i in data for i in self.subcriptions):
            user_id = data['for_user_id']
            self.func_data[user_id](data)


def server_config(url, dict_credential: dict, dict_func: dict, subscribe: list) -> object:
    '''
    :param dict_credential: dict of consumer secret, username as a key
    dict_credential={
        'username': 'consumer_secret'
    }
    :param dict_func: dict of function (one arg) that will be called when webhook receives data, user_id (str) as a key
    dict_func={
        'user_id': function
    }
    :return: stream event object
    '''
    stream_event = StreamEvent(dict_func, subscribe)
    stream_event.set_callback(url)
    stream_event.update_credential_id(dict_credential)

    return stream_event
