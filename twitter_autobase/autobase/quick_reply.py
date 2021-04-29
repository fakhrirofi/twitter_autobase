from abc import abstractmethod, ABC
from typing import NoReturn

class ProcessQReply(ABC):
    '''
    Ref: https://developer.twitter.com/en/docs/twitter-api/v1/direct-messages/quick-replies/api-reference/options
    '''
    _tmp_dms: list = None
    dms: list = None
    credential: object = None

    @abstractmethod
    def transfer_dm(self, dm) -> NoReturn:
        pass

    @abstractmethod
    def send_dm(self, recipient_id, text, quick_reply_type=None, quick_reply_data=None,
                attachment_type=None, attachment_media_id=None) -> NoReturn:
        pass

    @abstractmethod
    def _command(self, sender_id: str, message: str, message_data: dict) -> bool:
        pass
    
    def _verif_menfess(self, action, sender_id) -> NoReturn:
        '''
        Move dm dict from self._tmp_dms to self.dms
        '''
        for x in self._tmp_dms.copy()[::-1]:
            if x['sender_id'] == sender_id:
                if action == "accept":
                    self.transfer_dm(x)
                self._tmp_dms.remove(x)
                break
    
    def _button_command(self, sender_id, message) -> NoReturn:
        '''
        Process dm command using button
        '''
        message_data = {
            'entities'  : {
                'urls'  : []
            }
        }
        self._command(sender_id, message, message_data)

    def _quick_reply_manager(self, sender_id: str, metadata: str) -> NoReturn:
        '''
        Manage dm buttons
        '''
        metadata = metadata.split("|")
        action = metadata[0]
        data = metadata[1]

        if action == "send_text":
            data = eval(data)
            self.send_dm(sender_id, data)
        elif action == "send_button":
            data = eval(data)
            self.send_dm(sender_id, data['text'], quick_reply_type='options',
                         quick_reply_data=data['options'])
        elif action == "exec":
            exec(data)
        else:
            raise Exception("action is not valid")
    