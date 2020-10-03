import tweepy
import constants
import time
import _json
from requests_oauthlib import OAuth1
import os
import requests
from async_upload import VideoTweet
import moviepy.editor as mp
from moviepy.video.fx.all import crop
from PIL import Image
import datetime

class Twitter:
    def __init__(self):
        print("Initializing twitter...")
        self.auth = tweepy.OAuthHandler(constants.CONSUMER_KEY, constants.CONSUMER_SECRET)
        self.auth.set_access_token(constants.ACCESS_KEY, constants.ACCESS_SECRET)
        self.api = tweepy.API(self.auth)

    def read_dm(self):
        print("Get direct messages...")
        dms = list()
        try:
            api = self.api
            dm = api.list_direct_messages()
            p = 0
            for x in range(len(dm)):
                sender_id = dm[x].message_create['sender_id']
                message = dm[x].message_create['message_data']['text']
                message_data = str(dm[x].message_create['message_data'])
                json_data = _json.encode_basestring(message_data)
                if constants.First_Keyword in message.lower() or constants.Second_Keyword in message.lower() or constants.Third_keyword in message.lower():
                    print("Getting message -> by sender id " + str(sender_id))
                    if 'attachment' not in json_data:
                        print("DM does not have any media..")
                        d = dict(message = message, sender_id = sender_id, id = dm[x].id, media = None)
                        dms.append(d)

                    else:
                        print("DM have an attachment")
                        media_type = dm[x].message_create['message_data']['attachment']['media']['type']
                        if media_type == 'photo':
                            attachment = dm[x].message_create['message_data']['attachment']
                            photo_url = attachment['media']['media_url']
                            d = dict(message = message, sender_id = sender_id, id = dm[x].id, media = photo_url, type = media_type)
                            dms.append(d)

                        elif media_type == 'video':
                            media = dm[x].message_create['message_data']['attachment']['media']
                            media_url = media['video_info']['variants'][0]
                            video_url = media_url['url']
                            d = dict(message = message, sender_id = sender_id, id = dm[x].id, media = video_url, type = media_type)
                            dms.append(d)

                        elif media_type == 'animated_gif':
                            media = dm[x].message_create['message_data']['attachment']['media']
                            media_url = media['video_info']['variants'][0]
                            video_url = media_url['url']
                            d = dict(message = message, sender_id = sender_id, id = dm[x].id, media = video_url, type = media_type)
                            dms.append(d)

            print(str(len(dms)) + " collected")
            if len(dms) > 1 :
                dms.reverse()
            for i in range(len(dms)):
                message = dms[i]['message']
                sender_id = dms[i]['sender_id']
                if constants.First_Keyword in message.lower() or constants.Second_Keyword in message.lower():
                    try:
                        y = p+1
                        waktu = datetime.datetime.now() + datetime.timedelta(hours= 7, seconds = p*50+70)
                        p += 1
                        hour = waktu.hour
                        minute = waktu.minute
                        if hour < 10:
                               hour = "0" + str(waktu.hour)
                        elif minute < 10:
                               minute = "0" + str(waktu.minute)
                        notif = f"[BOT]\n\nMenfess kamu berada pada urutan ke-{str(y)}, akan terkirim sekitar pukul {hour}:{minute}"
                        api.send_direct_message(recipient_id = sender_id, text = notif)
                    except Exception as ex:
                        time.sleep(60)
                        print(ex)
                        pass

                elif constants.Third_keyword in message.lower():
                    try:
                        p += 1
                        message1 = message.replace(constants.Third_keyword, "")
                        notif = f"[BOT]\n\"{message1}\"\nPesan kamu akan dikirimkan ke admin, silakan tunggu balasan.."
                        api.send_direct_message(recipient_id = sender_id, text = notif)
                    except Exception as ex:
                        print(ex)
                        time.sleep(60)
                        pass

            time.sleep(60)
            return dms

        except Exception as ex:
            print(ex)
            time.sleep(60)
            return dms
            pass

    def delete_dm(self, id):
        print("Deleting dm with id = " + str(id))
        try:
            self.api.destroy_direct_message(id)
            time.sleep(40)
        except Exception as ex:
            print(ex)
            time.sleep(60)
            pass


    def Thread(self, name, type, tweet):
        try:
            left = 0
            right = 272
            leftcheck = 260
            check = tweet[leftcheck:right].split(' ')
            separator = len(check[-1])
            tweet1 = tweet[left:right-separator] + '(cont..)'
            if type == 'photo' or type == 'animated_gif':
                complete = self.api.update_with_media(filename = name, status = tweet1).id
            elif type == 'video':
                videoTweet = VideoTweet(name)
                videoTweet.upload_init()
                videoTweet.upload_append()
                videoTweet.upload_finalize()
                complete = videoTweet.Tweet(tweet1)
            elif type == 'normal':
                complete = self.api.update_status(tweet1).id
            time.sleep(10)
            tweet2 = tweet[right-separator:len(tweet)]
            while len(tweet2) > 280:
                leftcheck += 272
                left += 272
                right +=272
                check = tweet[leftcheck:right]
                separator = len(check[-1])
                tweet2 = tweet[left:right-separator] + '(cont..)'
                complete = self.api.update_status(tweet2, in_reply_to_status_id = complete, auto_populate_reply_metadata = True).id
                time.sleep(10)
                tweet2 = tweet[right-separator:len(tweet)]
            self.api.update_status(tweet2, in_reply_to_status_id = complete, auto_populate_reply_metadata = True)
            time.sleep(10)
        except Exception as ex:
            print(ex)
            time.sleep(30)
            pass

    def post_tweet(self, tweet):
        try:
            if len(tweet) <= 280:
                self.api.update_status(tweet)
            if len(tweet) > 280:
                type = "normal"
                self.Thread(None, type, tweet)
        except Exception as ex:
            time.sleep(60)
            print(ex)
            pass

    def post_tweet_with_media(self, tweet, media_url, type):
        try:
            print("Downloading media...")
            #arr = str(media_url).split('/')
            oauth = OAuth1(client_key = constants.CONSUMER_KEY,
                          client_secret = constants.CONSUMER_SECRET,
                          resource_owner_key = constants.ACCESS_KEY,
                          resource_owner_secret = constants.ACCESS_SECRET)
            r = requests.get(media_url, auth = oauth)
            if type == 'photo':
                with open('photo.jpg', 'wb') as f:
                    f.write(r.content)

            elif type == 'video':
                with open('video.mp4', 'wb') as f:
                    f.write(r.content)

            elif type == 'animated_gif':
                with open('animated_gif.mp4', 'wb') as f:
                    f.write(r.content)
            time.sleep(5)
            print("Media download successfully!")
            tweet = tweet.split()
            tweet.pop()
            tweet = " ".join(tweet)
            if type == 'photo':
                size = os.path.getsize('photo.jpg')
                print("Photo size: " + str(size))
                while size > 3000000:
                    foo = Image.open('photo.jpg')
                    dimension = "{} {}".format(*foo).split(' ')
                    first = str(round(int(dimension[0])*0.8))
                    second = str(round(int(dimension[1])*0.8))
                    foo = foo.resize((first,second), Image.ANTIALIAS)
                    foo.save('photo.jpg', optimize=True, quality=95)
                    time.sleep(5)
                    size = os.path.getsize('photo.jpg')
                if len(tweet) <= 280:
                    self.api.update_with_media(filename = 'photo.jpg', status = tweet)
                elif len(tweet) > 280:
                    name = "photo.jpg"
                    self.Thread(name, type, tweet)
                os.remove('photo.jpg')
            elif type == 'animated_gif':
                clip = mp.VideoFileClip('animated_gif.mp4')
                clip.subclip((0), (0,2)).resize(0.2).without_audio()
                clip.write_gif('animated.gif', fps=12, program='ffmpeg')
                time.sleep(5)
                print("gif size: " + str(os.path.getsize('animated.gif')))
                if len(tweet) <= 280:
                    self.api.update_with_media(filename = 'animated.gif', status = tweet)
                elif len(tweet) > 280:
                    name = "animated.gif"
                    self.Thread(name, type, tweet)
                os.remove('animated_gif.mp4')
                os.remove('animated.gif')
            elif type == 'video':
                try:
                    clip = mp.VideoFileClip("video.mp4")
                    width = clip.w
                    height = clip.h
                    if height > width:
                        clip_resized = clip.resize(width=720)
                        cropped = crop(clip_resized, width=720, height=1280, x_center=width/2, y_center=height/2)
                        cropped.write_videofile("output.mp4", fps=20)
                    elif height < width:
                        clip_resized = clip.resize(height=720)
                        cropped = crop(clip_resized, width=1280, height=720, x_center=width/2, y_center=height/2)
                        cropped.write_videofile("output.mp4", fps=20)
                    elif height == width:
                        clip_resized = clip.resize(height=720, width=720)
                        clip_resized.write_videofile("output.mp4", fps=20)
                    time.sleep(5)
                    if len(tweet) <= 280:
                        time.sleep(5)
                        videoTweet = VideoTweet('output.mp4')
                        videoTweet.upload_init()
                        videoTweet.upload_append()
                        videoTweet.upload_finalize()
                        videoTweet.Tweet(tweet)
                    elif len(tweet) > 280:
                        time.sleep(5)
                        name = 'output.mp4'
                        self.Thread(name, type, tweet)
                    os.remove('video.mp4')
                    os.remove('output.mp4')
                except ValueError as va:
                    print(va)
                    print("Exception Happen")
                    pass
            print("Upload with media success!")
        except Exception as ex:
            time.sleep(60)
            print(ex)
            pass
