# Copyright (c) 2016- @TwitterDev
# Distributed under the MIT software license
# Source: https://github.com/twitterdev/large-video-upload-python

# Re-code by Fakhri Catur Rofi
# Source: https://github.com/fakhrirofi/twitter_autobase

from os.path import getsize
from requests import get, post
from time import sleep
from typing import NoReturn
import json


MEDIA_ENDPOINT_URL = 'https://upload.twitter.com/1.1/media/upload.json'
POST_TWEET_URL = 'https://api.twitter.com/1.1/statuses/update.json'


class MediaUpload:
    '''
    Upload media using twitter api v.1.1

    Attributes:
        - filename
        - total_bytes
        - media_id
        - processing_info
        - file_format
        - media_type
        - media_category
    :param file_name: filename of the media
    :param media_category: 'tweet' or 'dm'
    '''

    def __init__(self, auth: object, file_name: str, media_category: str='tweet'):
        '''
        :param file_name: filename of the media
        :param media_category: 'tweet' or 'dm'
        '''
        self.oauth = auth
        self.filename = file_name
        self.total_bytes = getsize(self.filename)
        self.media_id = None
        self.processing_info = None
        data_media = {
            'gif'		: 'image/gif',
            'mp4'		: 'video/mp4',
            'jpg'		: 'image/jpeg',
            'webp'		: 'image/webp',
            'png'		: 'image/png',
            'jpeg'      : 'image/jpeg',
            'image/gif'	: 'tweet_gif',
            'video/mp4'	: 'tweet_video',
            'image/jpeg': 'tweet_image',
            'image/webp': 'tweet_image',
            'image/png'	: 'tweet_image'
        }
        self.file_format = file_name.split('.')[-1]
        if self.file_format in data_media.keys():
            self.media_type = data_media[file_name.split('.')[-1]]
            self.media_category = data_media[self.media_type]
        else:
            raise Exception(f"sorry, the .{self.file_format} format is not supported")
        if media_category == 'dm':
            self.media_category = None


    def upload_init(self) -> tuple:
        '''
        init section
        :return: media id, media_type
        '''
        # print('INIT')
        request_data = {
            'command': 'INIT',
            'media_type': self.media_type,
            'total_bytes': self.total_bytes,
            'media_category': self.media_category
        }
        if self.media_category == None:
            del request_data['media_category']

        req = post(url=MEDIA_ENDPOINT_URL,
                            data=request_data, auth=self.oauth)
        media_id = req.json()['media_id']

        self.media_id = media_id
        print('Media ID: %s' % str(media_id))

        dict_format = {
                'gif':'animated_gif',
                'mp4':'video',
                'png':'photo',
                'jpg':'photo',
                'webp':'photo',
                'jpeg':'photo',
            }
        media_type = dict_format[self.file_format]
        return str(media_id), media_type


    def upload_append(self) -> NoReturn:
        '''
        append section
        '''
        segment_id = 0
        bytes_sent = 0
        file = open(self.filename, 'rb')

        while bytes_sent < self.total_bytes:
            chunk = file.read(1024*1024)
            # print('APPEND')
            request_data = {
                'command': 'APPEND',
                'media_id': self.media_id,
                'segment_index': segment_id,

            }

            files = {
                'media': chunk
            }

            req = post(url=MEDIA_ENDPOINT_URL,
                                data=request_data, files=files, auth=self.oauth)

            if req.status_code < 200 or req.status_code > 299:
                print(req.status_code)
                print("Getting error status code")
                return False
            else:
                segment_id = segment_id + 1
                bytes_sent = file.tell()
                print('%s of %s bytes uploaded' %
                      (str(bytes_sent), str(self.total_bytes)))
        
        file.close()
        # print('Upload chunks complete.')


    def upload_finalize(self) -> NoReturn:
        '''
        Finalize upload and start media processing
        '''
        # print('FINALIZE')
        request_data = {
            'command': 'FINALIZE',
            'media_id': self.media_id
        }

        req = post(url=MEDIA_ENDPOINT_URL,
                            data=request_data, auth=self.oauth)

        self.processing_info = req.json().get('processing_info', None)
        self.check_status()


    def check_status(self) -> NoReturn:
        '''
        Check video processing status
        '''
        if self.processing_info is None:
            return

        state = self.processing_info['state']
        print('Media processing status is %s ' % state)

        if state == 'succeeded':
            return

        elif state == 'failed':
            raise ValueError("Upload failed")

        else:

            check_after_secs = self.processing_info['check_after_secs']

            # print('Checking after %s seconds' % str(check_after_secs))
            sleep(check_after_secs)
            # print('STATUS')
            request_params = {
                'command': 'STATUS',
                'media_id': self.media_id
            }

            req = get(url=MEDIA_ENDPOINT_URL,
                               params=request_params, auth=self.oauth)

            self.processing_info = req.json().get('processing_info', None)
            self.check_status()
