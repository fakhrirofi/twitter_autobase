# Ref: https://gist.github.com/codingjester/3497868
import json
import oauth2
import urllib


def get_xauth_access_token(consumer_key, consumer_secret, username, password) -> dict:
    '''
    :return: dict of access_key and access_secret
    '''
    acces_token_url = 'https://api.twitter.com/oauth/access_token'
    consumer = oauth2.Consumer(consumer_key, consumer_secret)
    client = oauth2.Client(consumer)
    client.add_credentials(username, password)
    client.set_signature_method = oauth2.SignatureMethod_HMAC_SHA1()

    resp, token = client.request(
        acces_token_url,
        method="POST",
        body=urllib.parse.urlencode({
            'x_auth_username'   : username,
            'x_auth_password'   : password,
            'x_auth_mode'       : 'client_auth'
        })
    )
    access_token = dict(urllib.parse.parse_qsl(token.decode()))
    return dict(
        access_key=access_token['oauth_token'],
        access_secret=access_token['oauth_token_secret']
    )

if __name__ == "__main__":
    from getpass import getpass
    
    consumer_key = input("consumer_key: ")
    consumer_secret = input("consumer_secret: ")
    username = input("username: ")
    password = getpass(prompt="password: ")
    
    token = get_xauth_access_token(consumer_key, consumer_secret, username, password)
    for i in token:
        print(f'{i}: {token[i]}')
