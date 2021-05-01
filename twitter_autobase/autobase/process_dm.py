from .dm_command import DMCommand
from .quick_reply import ProcessQReply
from abc import abstractmethod, ABC
from datetime import datetime, timezone, timedelta
from time import sleep
import logging
import traceback

logger = logging.getLogger(__name__)

class ProcessDM(ProcessQReply, DMCommand, ABC):
    api: object = None
    bot_username: str = None
    credential: object = None
    db_intervalTime: dict = None
    prevent_loop: list = None
    _lock: object = None
    
    @abstractmethod
    def send_dm(self, recipient_id, text, quick_reply_type=None, quick_reply_data=None,
                attachment_type=None, attachment_media_id=None):
        pass

    @abstractmethod
    def get_user_screen_name(self, id):
        pass

    @abstractmethod
    def db_sent_updater(self, action=str(), sender_id=str(), postid=str(), list_postid_thread=list()):
        pass

    def _command(self, sender_id: str, message: str, message_data: dict) -> bool:
        '''
        Process command (DMCmd) that sent from dm
        :param sender_id: id of account who sends the message
        :param message: message text
        :param message_data: dict of message data
        :return: bool, True: There is a command, False: There is no command
        '''
        list_command = list(self.credential.Admin_cmd) + list(self.credential.User_cmd)
        command = message.split(" ")[0].lower()

        if command not in list_command:
            return False

        if command in self.credential.Admin_cmd:
            if sender_id not in self.credential.Admin_id:
                return False
            dict_command = self.credential.Admin_cmd
        else:
            dict_command = self.credential.User_cmd

        contents = message.split(" ")[1:]
        print(f"command {command} {str(contents)} in progress...")
        notif = str() # terminal message
        if len(contents):
            urls = message_data["entities"]["urls"] #pylint: disable=unused-variable
            for arg in contents:
                try:
                    notif += f"\nprocessed: {command} {arg}"
                    exec(dict_command[command])
                    if "urls" in dict_command[command]:
                        break
                except Exception as ex:
                    logger.warning(ex)
                    notif += f"\nException: {ex}"
        else:
            try:
                notif += f"\nprocessed: {command}"
                exec(dict_command[command])
            except Exception as ex:
                logger.warning(ex)
                notif += f"\nException: {ex}"

        if sender_id not in self.credential.Admin_id:
            return True
        if "#no_notif" in dict_command[command]:
            return True
        if "arg" not in dict_command[command]:
            if "Exception" not in notif:
                return True
           
        self.send_dm(sender_id, notif)
        return True


    def __check_off_schedule(self, sender_id: str, date_now: object) -> bool:
        off_data = self.credential.Off_scheduleData
        delta_start_day = 0 
        delta_end_day = 0
        if off_data['different_day']:
            if date_now.hour < int(off_data['end'][0]) and date_now.minute < int(off_data['end'][1]):
            # at the beginning of midnight until the end of schedule
                delta_start_day -= 1
            else:
                delta_end_day += 1
        
        off_start = date_now.replace(hour=int(off_data['start'][0]), minute=int(off_data['start'][1])) \
                + timedelta(days=delta_start_day)
                
        off_end = date_now.replace(hour=int(off_data['end'][0]), minute=int(off_data['end'][1])) \
                + timedelta(days=delta_end_day)
            
        if date_now > off_start and date_now < off_end:
            print("Off_schedule is active")
            self.send_dm(sender_id, self.credential.Off_scheduleMsg)
            return True
        else:
            return False


    def __user_filter(self, sender_id: str, message: str) -> bool:
        '''
        Filter user requirements and rules which has been set on config.py
        :return: bool, True: dm shouldn't be processed, False: dm should be processed
        '''

        if sender_id in self.credential.Admin_id:
            return False

        # Account_status
        if not self.credential.Account_status:
            print("Account_status: False")
            self.send_dm(sender_id, self.credential.Notify_accountStatus)
            return True

        # DATA
        username = 0 # Will be edited on requirements or used on blacklist words, to make get_user effectively
        date_now = datetime.now(timezone.utc) + timedelta(hours=self.credential.Timezone)
        # Used on Off schedule, interval per sender, and sender requirements (minimum age)

        # Off schedule
        if self.credential.Off_schedule:
            if self.__check_off_schedule(sender_id, date_now):
                return True

        # Interval time per sender
        if self.credential.Interval_perSender:
            with self._lock: # pylint: disable=not-context-manager
                for i in list(self.db_intervalTime):
                    # cleaning self.db_intervalTime
                    if self.db_intervalTime[i] < date_now:
                        del self.db_intervalTime[i]

            if sender_id in self.db_intervalTime:
                free_time = datetime.strftime(self.db_intervalTime[sender_id], '%H:%M')
                notif = self.credential.Notify_intervalPerSender.format(free_time)
                self.send_dm(sender_id, notif)
                return True
            else:
                self.db_intervalTime[sender_id] = date_now + timedelta(minutes=self.credential.Interval_time)

        # Minimum/Maximum lenMenfess
        if len(message) < self.credential.Minimum_lenMenfess or len(message) > self.credential.Maximum_lenMenfess:
            self.send_dm(sender_id, self.credential.Notify_lenMenfess)
            return True

        # SENDER REQUIREMENTS
        if self.credential.Sender_requirements:
            user = (self.api.get_user(sender_id))._json
            username = user['screen_name']

            # only followed
            if self.credential.Only_followed:
                if user['following'] is False:
                    self.send_dm(sender_id, self.credential.Notif_notFollowed)
                    return True

            # minimum followers
            if user['followers_count'] < self.credential.Minimum_followers:
                self.send_dm(sender_id, self.credential.Notify_senderRequirements)
                return True

            # minimum age
            created_at = datetime.strptime(user['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
            date_now_req = date_now.replace(tzinfo=None)

            if (date_now_req - created_at).days < self.credential.Minimum_day:
                self.send_dm(sender_id, self.credential.Notify_senderRequirements)
                return True

        # BLACKLIST WORDS
        list_blacklist = [i.lower() for i in self.credential.Blacklist_words]
        if any(i in message.lower() for i in list_blacklist):
            self.send_dm(sender_id, self.credential.Notify_blacklistWords)
            if self.credential.Notify_blacklistWordsAdmin:
                if username == 0:
                    username = self.get_user_screen_name(sender_id)
                for id in self.credential.Admin_id:
                    self.send_dm(id, f"{message}\nstatus: blacklistWords\nfrom: @{username}\nid: {sender_id}")

            return True

        # All filters were processed
        return False


    def __menfess_trigger(self, sender_id: str, message: str, message_data: dict) -> dict or None:
        '''
        Clean data from raw message_data, Contains __user_filter method call
        :return: dict dm that contains menfess trigger or None
        '''
        if any(j.lower() in message.lower() for j in self.credential.Trigger_word):
            # User Filter
            if self.__user_filter(sender_id, message):
                return None

            dict_dm = dict(message=message, sender_id=sender_id, posting=False,
                media_url=None, attachment_urls={'tweet':(None, None),
                                                'media':list()})
            # 'tweet' and 'media': (url in message, the real url)
            # attachment url
            urls = message_data['entities']['urls']
            for i in urls:
                if "twitter.com/" in i['expanded_url'] and "/status/" in i['expanded_url']:
                    # i['url]: url in text message                          
                    # Media tweet
                    if any(j in i['expanded_url'] for j in ['/video/', '/photo/', '/media/']):
                        dict_dm['attachment_urls']['media'].append((i['url'], i['expanded_url']))
                        #i['expanded_url'] e.g https://twitter.com/username/status/123/photo/1          
                    # Tweet
                    else:
                        # Only_QRTBaseTweet
                        if self.credential.Only_QRTBaseTweet and sender_id not in self.credential.Admin_id:
                            if self.bot_username not in i['expanded_url']:
                                self.send_dm(sender_id, self.credential.Notif_QRTBaseTweet)
                                return None
                        dict_dm['attachment_urls']['tweet'] = (i['url'], i['expanded_url'])
                        #i['expanded_url'] e.g https://twitter.com/username/status/123?s=19
                # Only_twitterUrl
                elif "twitter.com/" not in i['expanded_url']: 
                    if self.credential.Only_twitterUrl and sender_id not in self.credential.Admin_id:
                        self.send_dm(sender_id, self.credential.Notif_twitterUrl)
                        return None

            # attachment media
            if 'attachment' in message_data:
                media = message_data['attachment']['media']
                media_type = media['type']
                if media_type == 'photo':
                    dict_dm['media_url'] = media['media_url']
                elif media_type == 'video':
                    media_urls = media['video_info']['variants']
                    temp_bitrate = list()
                    for varian in media_urls:
                        if varian['content_type'] == "video/mp4":
                            temp_bitrate.append((varian['bitrate'], varian['url']))
                    # sort to choose the highest bitrate
                    temp_bitrate.sort()
                    dict_dm['media_url'] = temp_bitrate[-1][1]
                elif media_type == 'animated_gif':
                    dict_dm['media_url'] = media['video_info']['variants'][0]['url']                            
                
            return dict_dm

        # WRONG TRIGGER
        else:
            if self.credential.Notify_wrongTrigger['user']:
                self.send_dm(sender_id, self.credential.Notify_wrongTrigger['message'])

            if self.credential.Notify_wrongTrigger['admin']:
                # Send wrong menfess to admin
                username = self.get_user_screen_name(sender_id)
                notif = message + f"\nstatus: wrong trigger\nfrom: @{username}\nid: {sender_id}"
                for admin in self.credential.Admin_id:
                    self.send_dm(admin, notif)
            
            return None

        
    def process_dm(self, raw_dm: dict) -> dict or None:
        '''
        :param raw_dm: raw data from webhook
        :return: dict filtered dm or None
        This method contains DMCmd that can do exec and self.db_sent_updater
        Filters:
            - account status
            - admin & user command
            - user filter
                - account status
                - off schedule
                - interval per sender
                - minimum and maximum len menfess
                - sender requirements (only followed, minimum followers and age of account)
                - blacklist words
            - menfess trigger
                - attachment_url
                - photo
                - video
                - animated_gif
        '''

        # Update db_sent
        self.db_sent_updater('update')

        try:
            message_create = raw_dm['direct_message_events'][0]['message_create']
            sender_id = message_create['sender_id'] #str
            message_data = message_create['message_data']
            message = message_data['text']

            # Avoid keyword error & loop messages by skipping bot messages
            if sender_id in self.prevent_loop:
                return None
            print(f"Processing direct message, sender_id: {sender_id}")

            # button (quick reply response)
            if "quick_reply_response" in message_data:
                metadata = message_data['quick_reply_response']['metadata']
                self._quick_reply_manager(sender_id, metadata)
                return None
            
            # ADMIN & USER COMMAND
            if self._command(sender_id, message, message_data):
                return None       
            
            return self.__menfess_trigger(sender_id, message, message_data)
            
        except:
            logger.critical(traceback.format_exc())
            self.send_dm(sender_id, self.credential.Notify_sentFail1)
            return None
