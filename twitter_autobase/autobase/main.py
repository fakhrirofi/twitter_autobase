# Original code by Prieyudha Akadita S.
#     Source: https://https://github.com/ydhnwb/autodm_base

# Re-code by Fakhri Catur Rofi under MIT License
#     Source: https://github.com/fakhrirofi/twitter_autobase

from .clean_dm_autobase import delete_trigger_word
from .process_dm import ProcessDM
from .twitter import Twitter
from datetime import datetime, timezone, timedelta
from threading import Thread, Lock
from time import sleep
from typing import NoReturn
import logging
import traceback

logger = logging.getLogger(__name__)

class Autobase(Twitter, ProcessDM):
    '''
    Attributes:
        - credential
        - bot_username
        - bot_id
        - db_sent
        - db_deleted
        - dms
        - prevent_loop
        - indicator

    :param credential: object that contains attributes like config.py
    :param prevent_loop: list of (str) bot_id
    '''
    def __init__(self, credential: object, prevent_loop: list):
        '''
        :param credential: object that contains attributes like config.py
        :param prevent_loop: list of (str) bot_id
        '''
        super().__init__(credential)
        self.bot_username = self.me.screen_name
        self.bot_id = str(self.me.id)
        self.db_intervalTime = dict()
        self.db_sent = dict() # { 'sender_id': {'postid': [list_postid_thread],}, }
        self.db_deleted = dict() # { 'sender_id': ['postid',] }
        self.dms = list() # list of filtered dms that processed by process_dm
        self._tmp_dms = list() # used if Verify_beforeSent is True
        self.prevent_loop = prevent_loop # list of all bot_id (str) that runs using this bot to prevent loop messages from each accounts
        self.indicator = {
            'day': (datetime.now(timezone.utc) + timedelta(hours=credential.Timezone)).day,
            'automenfess': 0,
        }
        self._lock = Lock()
        prevent_loop.append(self.bot_id)


    def notify_follow(self, follow_events: dict) -> NoReturn:
        '''
        Notify user when he follows the bot and followed by the bot
        :param follow_events: dict of 'follow_events' from self.webhook_connector
        '''
        if follow_events['follow_events'][0]['type'] != 'follow':
            return

        # id of the user who clicks 'follow' buttons
        source_id = follow_events['follow_events'][0]['source']['id']
        
        # Greet to new follower
        if source_id not in self.prevent_loop: # user is not bot
            if self.credential.Greet_newFollower:
                self.send_dm(source_id, self.credential.Notif_newFollower)

        # Notify user followed by bot, (admin of the bot clicks follow buttons on user profile)
        # elif source_id in self.prevent_loop:
        elif self.credential.Greet_followed:
            target_id = follow_events['follow_events'][0]['target']['id']

            if target_id not in self.prevent_loop:
                self.send_dm(target_id, self.credential.Notif_followed)


    def db_sent_updater(self, action: str, sender_id=str(), postid=str(), list_postid_thread=list()) -> NoReturn:
        '''Update self.db_sent and self.db_deleted
        :param action: 'update','add_sent', 'add_deleted' or 'delete_sent'
        :param sender_id: sender id who has sent the menfess
        :param postid: main post id
        :param list_postid_thread: list of post id after the main post id (if user sends menfess that contains characters > 280)
        '''
        try:
            if action == 'update':
                day = (datetime.now(timezone.utc) + timedelta(hours=self.credential.Timezone)).day
                if day != self.indicator['day']:
                    self.indicator['day'] = day
                    self.db_sent.clear()
                    self.db_deleted.clear()
            
            elif action == 'add_sent':
                if sender_id not in self.db_sent: # require sender_id, postid, list_postid_thread
                    self.db_sent[sender_id] = {postid: list_postid_thread}
                else: self.db_sent[sender_id][postid] = list_postid_thread
            
            elif action == 'add_deleted': # require sender_id and postid
                if sender_id not in self.db_deleted:
                    self.db_deleted[sender_id] = [postid]
                else: self.db_deleted[sender_id] += [postid]

            elif action == 'delete_sent': # require sender_id and postid
                del self.db_sent[sender_id][postid]
                if len(self.db_sent[sender_id]) == 0:
                    del self.db_sent[sender_id]

        except:
            logger.error(traceback.format_exc())

    
    def notify_queue(self, dm: dict, queue: int) -> NoReturn:
        """Notify the menfess queue to sender
        :param dm: dict that returned from process_dm
        :param queue: the number of queue (len of self.dms)
        """
        try:
            x, y, z = queue, queue, 0
            # x is primary time (36 sec); y is queue; z is addition time for media
            time = datetime.now(timezone.utc) + timedelta(hours=self.credential.Timezone)

            y += 1
            x += (len(dm['message']) // 272) + 1
            if dm['media_url'] != None:
                z += 3
                
            if self.credential.Private_mediaTweet:
                z += len(dm['attachment_urls']['media']) * 3

            sent_time = time + timedelta(seconds= x * (37 + self.credential.Delay_time) + z)
            sent_time = datetime.strftime(sent_time, '%H:%M')
            notif = self.credential.Notify_queueMessage.format(str(y), sent_time)
            self.send_dm(dm['sender_id'], notif)

        except:
            logger.error(traceback.format_exc())

    def transfer_dm(self, dm) -> NoReturn:
        '''
        Append dm dict to self.dms
        '''
        if self.credential.Notify_queue:
            # notify queue to sender
            self.notify_queue(dm, queue=len(self.dms))   
        self.dms.append(dm)
        if self.indicator['automenfess'] == 0:
            self.indicator['automenfess'] = 1
            Thread(target=self.start_automenfess).start()

    def webhook_connector(self, raw_data: dict) -> NoReturn:
        '''
        Method that will be called by webhook to sends data to Autobase, the process must be separated by Thread
        or Process(if there is a Database app i.e. Postgres)
        :param raw_data: dict from webhook 
        '''
        # https://developer.twitter.com/en/docs/twitter-api/enterprise/account-activity-api/guides/account-activity-data-objects
        if 'direct_message_events' in raw_data:
            dm = self.process_dm(raw_data) # Inherited from ProcessDM class
            if dm != None:
                if self.credential.Verify_beforeSent:
                    button = self.credential.Verify_beforeSentData
                    self.send_dm(dm['sender_id'], button['text'], quick_reply_type='options',
                                 quick_reply_data=button['options'])
                    self._tmp_dms.append(dm)
                else:
                    self.transfer_dm(dm)
        
        elif 'follow_events' in raw_data:
            self.notify_follow(raw_data)


    def start_automenfess(self) -> NoReturn:
        '''
        Process data from self.dms, the process must be separated by Thread or Process(if there is a Database app i.e. Postgres)
        '''
        while len(self.dms):
            self.dms[0]['posting'] = True
            dm = self.dms[0]
            try:
                message = dm['message']
                sender_id = dm['sender_id']
                media_url = dm['media_url']
                attachment_urls = dm['attachment_urls']['tweet']
                list_attchmentUrlsMedia = dm['attachment_urls']['media']

                if self.credential.Keyword_deleter:
                    message = delete_trigger_word(message, self.credential.Trigger_word)

                # Cleaning attachment_url
                if attachment_urls != (None, None):
                    message = message.split(" ")
                    for x in message.copy():
                        if attachment_urls[0] in x:
                            message.remove(x)
                            break
                    message = " ".join(message)
                                        
                # Cleaning hashtags and mentions
                message = message.replace("#", "#.")
                message = message.replace("@", "@.")

                # Private_mediaTweet
                media_idsAndTypes = list() # e.g [(media_id, media_type), (media_id, media_type), ]
                if self.credential.Private_mediaTweet:
                    for media_tweet_url in list_attchmentUrlsMedia:
                        list_mediaIdsAndTypes = self.upload_media_tweet(media_tweet_url[1])
                        if len(list_mediaIdsAndTypes):
                            media_idsAndTypes.extend(list_mediaIdsAndTypes)
                            message = message.split(" ")
                            message.remove(media_tweet_url[0])
                            message = " ".join(message)
                        
                # Menfess contains sensitive contents
                possibly_sensitive = False
                if self.credential.Sensitive_word.lower() in message.lower():
                    possibly_sensitive = True

                # POST TWEET
                print("Posting menfess...")
                response = self.post_tweet(message, sender_id, media_url=media_url, attachment_url=attachment_urls[1],
                        media_idsAndTypes=media_idsAndTypes, possibly_sensitive=possibly_sensitive)
                        
                # NOTIFY MENFESS SENT OR NOT
                # Ref: https://github.com/azukacchi/twitter_autobase/blob/master/main.py
                if response['postid'] != None:
                    if self.credential.Notify_sent:
                        notif = self.credential.Notify_sentMessage.format(self.bot_username)
                        text = notif + str(response['postid'])
                        self.send_dm(sender_id, text)
                    # ADD TO DB_SENT
                    self.db_sent_updater('add_sent', sender_id, response['postid'], response['list_postid_thread'])
                elif response['postid'] == None:
                    # Error happen on system                     
                    self.send_dm(sender_id, self.credential.Notify_sentFail1)
                else:
                    # credential.Notify_sent is False
                    pass

            except:
                self.send_dm(sender_id, self.credential.Notify_sentFail1)
                logger.critical(traceback.format_exc())

            finally:
                # self.notify_queue is using len of dms to count queue, it's why the dms[0] deleted here
                del self.dms[0]
        
        self.indicator['automenfess'] = 0
