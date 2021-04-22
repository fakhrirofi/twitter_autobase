from time import sleep
from datetime import datetime, timezone, timedelta


def dm_command(selfAlias: object, sender_id: str, message: str, message_data: dict) -> bool:
    '''
    Process command (DMCmd) that sent from dm
    :param selfAlias: an alias of self from Autobase class
    :param sender_id: id of account who sends the message
    :param message: message text
    :param message_data: dict of message data
    :return: bool, True: There is a command, False: There is no command
    '''
    list_command = list(selfAlias.credential.Admin_cmd) + list(selfAlias.credential.User_cmd)
    command = message.split(" ")[0].lower()

    if command not in list_command:
        return False

    else:
        DMCmd = selfAlias.DMCmd #pylint: disable=unused-variable
        contents = message.split(" ")[1:]
        notif = str()
                    
        if command in selfAlias.credential.Admin_cmd:
            # Manage admin access
            if sender_id not in selfAlias.credential.Admin_id:
                return False

        print(f"command {command} {str(contents)} in progress...")

        dict_command = selfAlias.credential.Admin_cmd.copy()
        dict_command.update(selfAlias.credential.User_cmd)

        if len(contents):
            urls = message_data["entities"]["urls"] #pylint: disable=unused-variable
            for arg in contents:
                try:
                    notif += f"\nprocessed: {command} {arg}"
                    fix_command = dict_command[command.lower()]
                    exec(fix_command)
                    if "urls" in fix_command:
                        break

                except Exception as ex:
                    pass
                    print(ex)
                    notif += f"\nException: {ex}"

        else:
            try:
                notif += f"\nprocessed: {command}"
                exec(dict_command[command.lower()])
            except Exception as ex:
                pass
                print(ex)
                notif += f"\nException: {ex}"
                    
        # Skip notif if '#no_notif' in command's comment
        if "#no_notif" in dict_command[command.lower()]:
            if "Exception" not in notif:
                return True
                    
        # Manage notification for user
        if sender_id not in selfAlias.credential.Admin_id:
            if "Exception" not in notif:
                notif = selfAlias.credential.Notify_DMCmdDelete
            else:
                notif = selfAlias.credential.Notify_DMCmdDeleteFail
                    
        selfAlias.send_dm(sender_id, notif)
        return True


def dm_user_filter(selfAlias: object, sender_id: str, message: str) -> bool:
    '''
    Filter user requirements and rules which has been set on config.py
    :param selfAlias: an alias of self from Autobase class
    :return: bool, True: dm shouldn't be processed, False: dm should be processed
    '''

    username = 0 # Used on requirements or blacklist_words, to use get_user effectively

    if sender_id in selfAlias.credential.Admin_id:
        return False
    
    # Ignore message when Account_status is False
    if not selfAlias.credential.Account_status:
        print("Account_status: False")
        selfAlias.send_dm(sender_id, selfAlias.credential.Notify_accountStatus)
        return True   

    # Interval time per sender
    if selfAlias.credential.Interval_perSender:
        date_now = datetime.now(timezone.utc) + timedelta(hours=selfAlias.credential.Timezone)
        for i in list(selfAlias.db_intervalTime):
            # cleaning selfAlias.db_intervalTime
            if selfAlias.db_intervalTime[i] < date_now:
                del selfAlias.db_intervalTime[i]

        if sender_id in selfAlias.db_intervalTime:
            free_time = datetime.strftime(selfAlias.db_intervalTime[sender_id], '%H:%M')
            notif = selfAlias.credential.Notify_intervalPerSender.format(free_time)
            selfAlias.send_dm(recipient_id=sender_id, text=notif)
            return True
        else:
            selfAlias.db_intervalTime[sender_id] = date_now + timedelta(minutes=selfAlias.credential.Interval_time)

    # Minimum/Maximum lenMenfess
    if len(message) < selfAlias.credential.Minimum_lenMenfess or len(message) > selfAlias.credential.Maximum_lenMenfess:
        selfAlias.send_dm(sender_id, selfAlias.credential.Notify_lenMenfess)
        return True

    # SENDER REQUIREMENTS
    if selfAlias.credential.Sender_requirements:
        user = (selfAlias.api.get_user(sender_id))._json
        username = user['screen_name']

        # only followed
        if selfAlias.credential.Only_followed:
            if user['following'] is False:
                selfAlias.send_dm(sender_id, selfAlias.credential.Notif_notFollowed)
                return True

        # minimum followers
        if user['followers_count'] < selfAlias.credential.Minimum_followers:
            selfAlias.send_dm(sender_id, selfAlias.credential.Notify_senderRequirements)
            return True

        # minimum age
        created_at = datetime.strptime(user['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
        date_now = (datetime.now(timezone.utc)
                 + timedelta(hours=selfAlias.credential.Timezone)).replace(tzinfo=None)

        if (date_now-created_at).days < selfAlias.credential.Minimum_day:
            selfAlias.send_dm(sender_id, selfAlias.credential.Notify_senderRequirements)
            return True

    # BLACKLIST WORDS
    list_blacklist = [i.lower() for i in selfAlias.credential.Blacklist_words]
    if any(i in message.lower() for i in list_blacklist):
        notif = selfAlias.credential.Notify_blacklistWords
        selfAlias.send_dm(recipient_id=sender_id, text=notif)

        if selfAlias.credential.Notify_blacklistWordsAdmin:
            if username == 0:
                username = selfAlias.get_user_screen_name(sender_id)
            for id in selfAlias.credential.Admin_id:
                selfAlias.send_dm(
                    recipient_id=id,
                    text=f"{message}\nstatus: blacklistWords\nfrom: @{username}\nid: {sender_id}"
                )

        return True

    # All filters were processed
    return False


def dm_menfess_trigger(selfAlias: object, sender_id: str, message: str, message_data: dict) -> list:
    '''
    Clean data from raw message_data
    :param selfAlias: an alias of self from Autobase class
    :return: list of dict filtered dm that contains menfess trigger
    '''
    filtered_dm = list()

    if any(j.lower() in message.lower() for j in selfAlias.credential.Trigger_word):

        dict_dms = dict(message=message, sender_id=sender_id,
            media_url=None, attachment_urls={'tweet':(None, None),
                                             'media':list()})
        # tweet and media: (url in message, the real url)

        # attachment url
        urls = message_data['entities']['urls']
        for i in urls:
            if "twitter.com/" in i['expanded_url'] and "/status/" in i['expanded_url']:
                # i['url]: url in text message                          
                # Media
                if any(j in i['expanded_url'] for j in ['/video/', '/photo/', '/media/']):
                    dict_dms['attachment_urls']['media'].append((i['url'], i['expanded_url']))
                    #i['expanded_url'] e.g https://twitter.com/username/status/123/photo/1
                        
                # Tweet
                else:
                    dict_dms['attachment_urls']['tweet'] = (i['url'], i['expanded_url'])
                    #i['expanded_url'] e.g https://twitter.com/username/status/123?s=19

        # attachment media
        if 'attachment' in message_data:
            media = message_data['attachment']['media']
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
                        
            dict_dms['media_url'] = media_url

        filtered_dm.append(dict_dms)

    # WRONG TRIGGER
    else:
        if selfAlias.credential.Notify_wrongTriggerUser:
            # Send notif to user
            notif = selfAlias.credential.Notify_wrongTriggerMsg
            selfAlias.send_dm(recipient_id=sender_id, text=notif)

        if selfAlias.credential.Notify_wrongTriggerAdmin:
            # Send wrong menfess to admin
            username = selfAlias.get_user_screen_name(sender_id)
            notif = message + f"\nstatus: wrong trigger\nfrom: @{username}\nid: {sender_id}"

            for admin in selfAlias.credential.Admin_id:
                selfAlias.send_dm(recipient_id=admin, text=notif)
            
    return filtered_dm

    
def process_dm(selfAlias: object, raw_dm: dict) -> list:
    '''
    :param selfAlias: an alias of self from Autobase class
    :param raw_dm: raw data from webhook
    :return: list of dict filtered dm
    This method contains DMCmd that can do exec and selfAlias.db_sent_updater
    Filters:
        - account status
        - admin & user command
        - user filter
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
    selfAlias.db_sent_updater('update')

    try:
        message_create = raw_dm['direct_message_events'][0]['message_create']
        sender_id = message_create['sender_id'] #str
        message_data = message_create['message_data']
        message = message_data['text']

        # Avoid keyword error & loop messages by skipping bot messages
        if sender_id in selfAlias.prevent_loop:
            return list()     
        print(f"Processing direct message, sender_id: {sender_id}")

        # ADMIN & USER COMMAND
        if dm_command(selfAlias, sender_id, message, message_data):
            return list()
        
        # FILTER FOR USER
        if dm_user_filter(selfAlias, sender_id, message):
            return list()
        
        return dm_menfess_trigger(selfAlias, sender_id, message, message_data)
        
    except Exception as ex:
        pass
        print(ex)
        selfAlias.send_dm(
            sender_id,
            selfAlias.credential.Notify_sentFail1 + f"\nerror_code: process_dm, {str(ex)}")
        return list()
