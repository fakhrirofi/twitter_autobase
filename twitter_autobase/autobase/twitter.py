# Original code by Prieyudha Akadita S.
#     Source: https://https://github.com/ydhnwb/autodm_base
# Re-code by Fakhri Catur Rofi
#     Source: https://github.com/fakhrirofi/twitter_autobase

from .async_upload import MediaUpload
from .clean_dm_autobase import count_emoji, get_list_media_ids
from .watermark import app as watermark
from html import unescape
from os import remove
from time import sleep
from tweepy import OAuthHandler, API
from tweepy.binder import bind_api
from typing import NoReturn
import logging
import re
import requests
import traceback

logger = logging.getLogger(__name__)

class EditedAPI(API):
    '''
    Add quick reply support
    Ref: https://developer.twitter.com/en/docs/twitter-api/v1/direct-messages/quick-replies/api-reference/options
    '''
    def send_direct_message(self, recipient_id, text, quick_reply_type=None, quick_reply_data=None,
                            attachment_type=None, attachment_media_id=None):
        """
        Send a direct message to the specified user from the authenticating
        user
        """
        json_payload = {
            'event': {'type': 'message_create',
                      'message_create': {
                          'target': {'recipient_id': recipient_id},
                          'message_data': {'text': text}
                      }
            }
        }
        message_data = json_payload['event']['message_create']['message_data']
        if quick_reply_type is not None:
            message_data['quick_reply'] = {'type': quick_reply_type}
            message_data['quick_reply'][quick_reply_type] = quick_reply_data
        if attachment_type is not None and attachment_media_id is not None:
            message_data['attachment'] = {'type': attachment_type}
            message_data['attachment']['media'] = {'id': attachment_media_id}
        return self._send_direct_message(json_payload=json_payload)

    @property
    def _send_direct_message(self):
        """ :reference: https://developer.twitter.com/en/docs/direct-messages/sending-and-receiving/api-reference/new-event
            :allowed_param: 'recipient_id', 'text', 'quick_reply_type', 'quick_reply_data',
                            'attachment_type', attachment_media_id'
        """
        return bind_api(
            api=self,
            path='/direct_messages/events/new.json',
            method='POST',
            payload_type='direct_message',
            allowed_param=['recipient_id', 'text', 'quick_reply_type', 'quick_reply_data',
                           'attachment_type', 'attachment_media_id'],
            require_auth=True
        )


class Twitter:
    '''
    Control twitter account
    Attributes:
        - credential
        - api
        - me
    :param credential: object that contains attributes like config
    '''
    def __init__(self, credential: object):
        '''
        initialize twitter with tweepy
        :param credential: object that contains attributes like config
        '''
        self.credential = credential
        self._auth = OAuthHandler(credential.CONSUMER_KEY, credential.CONSUMER_SECRET)
        self._auth.set_access_token(credential.ACCESS_KEY, credential.ACCESS_SECRET)
        self.api = EditedAPI(self._auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
        try:
            self.me = self.api.me()
        except:
            logger.error("Check your twitter credentials in config")
            exit()
        print(f"Initializing twitter... ({self.me.screen_name})")
    
    def send_dm(self, recipient_id: str, text: str, quick_reply_type: str=None, quick_reply_data: list=None,
                attachment_type: str=None, attachment_media_id: str=None) -> NoReturn:
        '''
        :param recipient_id: account target
        :param quick_reply_type: 'options'
        :param quick_reply_data: list of json quick reply object
        :param attachment_type: 'media'
        :param attachment_media_id: media id that returned from upload_media method
        '''
        try:
            self.api.send_direct_message(recipient_id, text, quick_reply_type, quick_reply_data,
                attachment_type, attachment_media_id)
        except:
            logger.error(traceback.format_exc())

    def get_user_screen_name(self, id: str) -> str:
        '''
        :param id: account id
        :return: username
        '''
        try:
            user = self.api.get_user(id)
            return user.screen_name

        except:
            logger.error(traceback.format_exc())
            return "Exception"

    def download_media(self, media_url: str, filename: str=None) -> str:
        '''Download media from url
        :param media_url: url
        :param filename: None (default) or filename
        :return: file name (if filename==None)
        '''
        print("Downloading media...")
        r = requests.get(media_url, auth=self._auth.apply_auth())
        if filename == None:
            for i in re.sub("[/?=]", " ", media_url).split():
                if re.search(r"\.mp4$|\.gif$|\.jpg$|\.jpeg$|\.png$|\.webp$", i):
                    filename = i
                    break
            else:
                raise Exception("filename is not supported, please check the link")

        with open(filename, 'wb') as f:
            f.write(r.content)
            f.close()

        return filename
    
    def add_watermark(self, filename: str, output: str=None) -> str:
        '''Add watermark to photo, then save as output. Only support photo type
        :returns: output file name
        '''
        try:
            if output == None:
                output = filename

            file_type = filename.split('.')[-1]
            if file_type in "jpg jpeg png webp":
                print("Adding watermark...")
                i = self.credential.Watermark_data
                watermark.watermark_text_image(filename, text=i['text'], font=i['font'],
                ratio=i['ratio'], pos=i['position'], output=output, color=i['textColor'],
                stroke_color=i['textStroke'], watermark=i['image'])
            
            return output

        except:
            logger.error(traceback.format_exc())
            return filename

    def upload_media_tweet(self, media_tweet_url: str) -> list:
        '''Upload media from media tweet url
        Usually when sender wants to post more than one media, he will attachs media tweet url.
        But the sender's username is mentioned on the bottom of the media. This method intended to make sender anonym.
        you can add media_ids to other method. This method contains watermark module
        :param media_tweet_url: media tweet url i.e. https://twitter.com/username/status/123/photo/1
        :return: [(media_id, media_type),] a.k.a media_idsAndTypes
        '''
        try:
            postid = re.sub(r"[/\.:]", " ", media_tweet_url).split()[-3]
            status = self.api.get_status(postid)
            media_idsAndTypes = list()

            if 'extended_entities' not in status._json:
                return list()
            print("Uploading media tweet...")
            
            for media in status._json['extended_entities']['media']:
                media_type = media['type']

                if media_type == 'photo':
                    media_url = media['media_url']

                elif media_type == 'video':
                    media_urls = media['video_info']['variants']
                    temp_bitrate = list()
                    for varian in media_urls:
                        if varian['content_type'] == "video/mp4":
                            temp_bitrate.append((varian['bitrate'], varian['url']))
                    # sort to choose the highest bitrate
                    temp_bitrate.sort()
                    media_url = temp_bitrate[-1][1]

                elif media_type == 'animated_gif':
                    media_url = media['video_info']['variants'][0]['url']

                filename = self.download_media(media_url)

                # Add watermark
                if self.credential.Watermark is True:
                    self.add_watermark(filename)

                media_id, media_type = self.upload_media(filename)
                remove(filename)
                media_idsAndTypes.append((media_id, media_type))
        
            return media_idsAndTypes # e.g [(media_id, media_type), (media_id, media_type), ]

        except:
            logger.error(traceback.format_exc())
            return list()

    def upload_media(self, filename: str, media_category: str='tweet') -> tuple:
        '''Upload media using twitter api v1.1
        This method are needed when you want to use media to do something on twitter
        :param media_category: 'tweet' or 'dm'. default to 'tweet'
        :return: media id, media_type
        '''
        mediaupload = MediaUpload(self._auth.apply_auth(), filename, media_category)
        media_id, media_type = mediaupload.upload_init()
        mediaupload.upload_append()
        mediaupload.upload_finalize()
        del mediaupload
        return media_id, media_type

    def post_tweet(self, tweet: str, sender_id: str, media_url: str=None, attachment_url: str=None,
                media_idsAndTypes: list=list(), possibly_sensitive: bool=False) -> dict:
        '''Post a tweet, contains watermark module
        Per tweet delay is 36s + self.credential.Delay_time
        :param tweet: message
        :param media_url: url of the media that sent from dm
        :param attachment_url: url that will be attached to twett (retweet)
        :param media_idsAndTypes: [(media_ids, media_type),]
        :param possibly_sensitive: True if menfess contains sensitive contents
        :return: {'postid': str, 'list_postid_thread': list} -> dict
        '''
        try:
            sleep(36+self.credential.Delay_time)
            #### ADD MEDIA_ID AND MEDIA_TYPE TO LIST_MEDIA_IDS ####
            # media_idsAndTypes e.g. [(media_id, media_type), (media_id, media_type), ]
            if media_url != None:
                tweet = tweet.split(" ")
                tweet = " ".join(tweet[:-1])
                filename = self.download_media(media_url)

                # Add watermark
                if self.credential.Watermark:
                    self.add_watermark(filename)

                media_id, media_type = self.upload_media(filename)
                # Add attachment media from DM to the first order
                media_idsAndTypes.insert(0, (media_id, media_type))
                remove(filename)

            list_media_ids = get_list_media_ids(media_idsAndTypes) #[[media_ids],[media_ids],[media_ids]]
            
            #### POST TWEET ####
            postid = 0
            list_postid_thread = list() # used for #delete command
            # postid is the first tweet of the tweets thread
            while len(tweet) + round(count_emoji(tweet) / 2) > 280:
            # Making a Thread.
                limit = 272
                # some emoticons are counted as 2 char
                limit -= round(count_emoji(tweet[:limit]) / 2)

                check = tweet[:limit].split(" ")                             
                if len(check) == 1:
                    # avoid error when user send 272 char in one word
                    separator = 0
                else:
                    separator = len(check[-1])

                tweet_thread = unescape(tweet[:limit-separator]) + '-cont-'
                
                if postid == 0:
                    print("Making a thread...")
                    # postid is static after first update.
                    postid = self.api.update_status(
                        tweet_thread, attachment_url=attachment_url, media_ids=list_media_ids[:1][0],
                        possibly_sensitive=possibly_sensitive).id
                    postid_thread = str(postid)
                else:
                    postid_thread = self.api.update_status(
                        tweet_thread, in_reply_to_status_id=postid_thread, auto_populate_reply_metadata=True,
                        media_ids=list_media_ids[:1][0], possibly_sensitive=possibly_sensitive).id
                    
                    list_postid_thread.append(postid_thread)
                
                list_media_ids = list_media_ids[1:] + [[]]
                sleep(36+self.credential.Delay_time)
                # tweet are dynamic here
                tweet = tweet[limit-separator:]
            
            # Above and below operation differences are on tweet_thread and unescape(tweet), also tweet[limit-separator:]
            # It's possible to change it to be one function
            if postid == 0:
                # postid is static after first update.
                postid = self.api.update_status(
                        unescape(tweet), attachment_url=attachment_url, media_ids=list_media_ids[:1][0],
                        possibly_sensitive=possibly_sensitive).id
                postid_thread = str(postid)        
            else:
                postid_thread = self.api.update_status(
                    unescape(tweet), in_reply_to_status_id=postid_thread, auto_populate_reply_metadata=True,
                    media_ids=list_media_ids[:1][0], possibly_sensitive=possibly_sensitive).id
                
                list_postid_thread.append(postid_thread)
            
            list_media_ids = list_media_ids[1:] + [[]]

            # When media_ids still exists, It will be attached to the subsequent tweets
            while len(list_media_ids[0]) != 0: # Pay attention to the list format, [[]]
                sleep(36+self.credential.Delay_time)

                print("Posting the rest of media...")
                postid_thread = self.api.update_status(
                    in_reply_to_status_id=postid_thread,
                    auto_populate_reply_metadata=True, media_ids=list_media_ids[:1][0],
                    possibly_sensitive=possibly_sensitive).id
                
                list_postid_thread.append(postid_thread)

                list_media_ids = list_media_ids[1:] + [[]]

            print(f'Menfess is posted -> postid: {postid}')            
            return {'postid': str(postid), 'list_postid_thread': list_postid_thread}

        except:
            logger.error(traceback.format_exc())
            return {'postid': None}
