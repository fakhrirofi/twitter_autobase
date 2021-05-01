from abc import abstractmethod, ABC
from typing import NoReturn
import re


class DMCommand(ABC):
    '''
    Command that can be accessed from direct message, you can manage command on config.py
    '''
    api: object = None
    credential: object = None
    db_deleted: dict = None
    db_sent: dict = None
    dms: list = None
    
    @abstractmethod
    def get_user_screen_name(self, id):
        pass

    @abstractmethod
    def send_dm(self, recipient_id, text, quick_reply_type=None, quick_reply_data=None,
                attachment_type=None, attachment_media_id=None) -> NoReturn:
        pass

    @abstractmethod
    def db_sent_updater(self, action, sender_id, postid, list_postid_thread=list()) -> NoReturn:
        pass

    def _add_blacklist(self, word: str) -> NoReturn:
        '''
        :param word: word that will be added to Blacklist_words
        '''
        word = word.replace("_", " ")
        self.credential.Blacklist_words.append(word)

    def _rm_blacklist(self, word: str) -> NoReturn:
        '''
        :param word: word that will be deleted from Blacklist_words
        '''
        word = word.replace("_", " ")
        self.credential.Blacklist_words.remove(word)

    def _display_blacklist(self, sender_id: str) -> NoReturn:
        '''
        Send list of blacklist words to sender
        '''
        self.send_dm(sender_id, str(self.credential.Blacklist_words))

    def _who_sender(self, sender_id: str, urls: list) -> NoReturn:
        '''Check who was sent the menfess
        :param urls: list of urls from dm
        '''
        if len(urls) == 0:
            raise Exception("Tweet link is not mentioned")
        
        for i in urls:
            url = i["expanded_url"]
            postid = str()

            if "?" in url:
                postid = re.sub("[/?]", " ", url).split()[-2]
            else:
                postid = url.split("/")[-1]

            for req_senderId in self.db_sent.keys():
                if postid in self.db_sent[req_senderId].keys():
                    username = self.get_user_screen_name(req_senderId)
                    text = f"username: @{username}\nid: {req_senderId}\nstatus: exists {url}"
                    self.send_dm(sender_id, text)
                    return
            
            for req_senderId in self.db_deleted.keys():
                if postid in self.db_deleted[req_senderId]:
                    username = self.get_user_screen_name(req_senderId)
                    text = f"username @{username}\nid: {req_senderId}\nstatus: deleted\nurl: {url}"
                    self.send_dm(sender_id, text)
                    return

            raise Exception("menfess is not found in db_sent or db_deleted")

    def _add_admin(self, username: str) -> NoReturn:
        '''
        Add (append) user to credential.Admin_id
        :param username: username without '@'
        '''
        user = (self.api.get_user(screen_name=username))._json
        self.credential.Admin_id.append(str(user['id']))

    def _rm_admin(self, username: str) -> NoReturn:
        '''
        :param username: username without '@'
        '''
        user = (self.api.get_user(screen_name=username))._json
        self.credential.Admin_id.remove(str(user['id']))

    def _switch_status(self, arg: str) -> NoReturn:
        '''
        :param arg: 'on' or 'off'
        '''
        if arg.lower() == "on":
            self.credential.Account_status = True
        elif arg.lower() == "off":
            self.credential.Account_status = False
        else:
            raise Exception("available parameters are on or off")

    def __delete_tweet(self, postid: str, list_postid_thread: list) -> NoReturn:
        try:
            for postidx in [postid] + list_postid_thread:
                self.api.destroy_status(postidx) # It doesn't matter when error happen here
        except Exception as ex:
            raise Exception(f"You can't delete this tweet. Error: {ex}")

    def __delete_menfess(self, sender_id: str, urls: list) -> str:
        '''Delete tweet
        :param urls: list of urls from dm
        '''
        if sender_id not in self.db_sent and sender_id not in self.credential.Admin_id:
            raise Exception("sender_id not in db_sent")
        if len(urls) == 0:
            raise Exception("Tweet link is not mentioned")
        
        for i in urls:
            if "?" in i["expanded_url"]:
                postid = re.sub("[/?]", " ", i["expanded_url"]).split()[-2]
            else:
                postid = i["expanded_url"].split("/")[-1]

            if sender_id in self.db_sent: # user has sent menfess
                if postid in self.db_sent[sender_id]: # normal succes
                    list_postid_thread = self.db_sent[sender_id][postid]
                    self.db_sent_updater('add_deleted', sender_id, postid)
                    self.db_sent_updater('delete_sent', sender_id, postid)
                    self.__delete_tweet(postid, list_postid_thread)
                    return sender_id

                elif sender_id not in self.credential.Admin_id: # normal trying other menfess
                    raise Exception("sender doesn't have access to delete postid")
            
            elif sender_id not in self.credential.Admin_id: # user hasn't sent menfess
                raise Exception("sender doesn't have access to delete postid")
            
            # administrator mode
            found = 0 # sender_id that will be searched
            for req_senderId in self.db_sent.keys():
                if postid in self.db_sent[req_senderId].keys():
                    found = req_senderId
                    break

            if found != 0:
                list_postid_thread = self.db_sent[found][postid]
                self.db_sent_updater('add_deleted', found, postid)
                self.db_sent_updater('delete_sent', found, postid)
            else:
                list_postid_thread = list()
                print("admin mode: directly destroy_status")
            
            self.__delete_tweet(postid, list_postid_thread)
            if found != 0: return found
    
    def _delete_menfess(self, sender_id: str, urls: list) -> NoReturn:
        try:
            self.__delete_menfess(sender_id, urls)
        except Exception as e:
            self.send_dm(sender_id, self.credential.Notif_DMCmdDelete['failed'])
            raise e
        else:
            self.send_dm(sender_id, self.credential.Notif_DMCmdDelete['succeed'])
    
    def _unsend_menfess(self, sender_id: str) -> NoReturn:
        '''
        Delete the last tweet that sent by sender
        '''
        try:
            last_postid = list(self.db_sent[sender_id])[-1]
            list_postid_thread = self.db_sent[sender_id][last_postid]
            self.db_sent_updater('add_deleted', sender_id, last_postid)
            self.db_sent_updater('delete_sent', sender_id, last_postid)
            self.__delete_tweet(last_postid, list_postid_thread)
        except Exception as e:
            self.send_dm(sender_id, self.credential.Notif_DMCmdDelete['failed'])
            raise e
        else:
            self.send_dm(sender_id, self.credential.Notif_DMCmdDelete['succeed'])

    def _menu_dm(self, sender_id) -> NoReturn:
        '''
        Send command's menu to sender
        '''
        self.send_dm(sender_id, self.credential.DMCmdMenu['text'], quick_reply_type='options',
                     quick_reply_data=self.credential.DMCmdMenu['options'])

    def _block_user(self, sender_id, urls) -> NoReturn:
        '''
        Delete menfess and block the sender
        '''
        sender_idx = self.__delete_menfess(sender_id, urls)
        if sender_idx is None:
            raise Exception("sender_id not found")
        elif sender_idx in self.credential.Admin_id:
            raise Exception("You can't block Admin")
        else:
            username = self.get_user_screen_name(sender_idx)     
        
        try:
            self.api.create_block(user_id=sender_idx)
        except:
            raise Exception("You can't block the sender")
        else:
            self.send_dm(sender_id, f'username: @{username}\nid: {sender_idx}\nstatus: blocked')
    
    def _unfoll_user(self, sender_id, urls) -> NoReturn:
        '''
        Delete menfess and unfoll the sender
        '''
        sender_idx = self.__delete_menfess(sender_id, urls)
        if sender_idx is None:
            raise Exception("sender_id not found")
        else:
            username = self.get_user_screen_name(sender_idx)     
        
        try:
            self.api.destroy_friendship(user_id=sender_idx)
        except:
            raise Exception("You can't unfollow the sender")
        else:
            self.send_dm(sender_id, f'username: @{username}\nid: {sender_idx}\nstatus: unfollowed')
    
    def _cancel_menfess(self, sender_id) -> NoReturn:
        '''
        Cancel menfess when it's still on self.dms queue
        '''
        for x in self.dms.copy()[::-1]:
            if x['sender_id'] == sender_id:
                if x['posting']:
                    self.send_dm(sender_id, self.credential.Notif_DMCmdCancel['on_process'])
                    return
                self.dms.remove(x)
                self.send_dm(sender_id, self.credential.Notif_DMCmdCancel['succeed'])
                break
        else:
            self.send_dm(sender_id, self.credential.Notif_DMCmdCancel['failed'])
