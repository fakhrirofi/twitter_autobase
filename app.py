from twitter import Twitter
from time import sleep
from threading import Thread
from datetime import datetime, timezone, timedelta
import constants
from os.path import exists
from os import remove
from html import unescape
from random import randrange

if constants.database == True:
    from github import Github
    github = Github(constants.Github_token)


def start():
    print("Starting program...")
    dms = list()
    tw = Twitter()
    api = tw.api
    constants.api = api
    me = api.me()
    tw.bot_id = me.id
    open('follower_data.txt', 'w').truncate()
    first = open('follower_data.txt').read()
    # sent = api.send_direct_message(recipient_id=constants.Admin_id, text="Twitter autobase is starting...!").id
    # tw.delete_dm(sent)

    while True:
        print("Updating followers...")
        # Auto accept message requests
        # Comment these if you want close your DM
        follower = api.followers_ids(user_id=me.id)
        if len(follower) != 0:
            try:
                if len(first) <= 3:
                    str_follower = [str(i) for i in follower]
                    data = " ".join(str_follower)
                    open("follower_data.txt", "w").write(data)
                    first = "checked"
                    del str_follower

                data = open('follower_data.txt').read()
                data = data.split()
                data1 = str()
                data2 = data.copy()

                for i in follower:
                    if str(i) not in data:
                        data1 += " " + str(i)
                        notif = "YEAY! Sekarang kamu bisa mengirim menfess, jangan lupa baca peraturan base yaa!"
                        # I don't know, sometimes error happen here, so, I update tw.follower after this loop
                        sent = api.send_direct_message(
                            recipient_id=i, text=notif).id
                        tw.delete_dm(sent)
                        
                tw.follower = follower
                for i in data2:
                    if int(i) not in follower:
                        data.remove(i)

                if data != data2:
                    data = " ".join(data)
                    data = data + data1
                    new = open("follower_data.txt", "w")
                    new.write(data)
                    new.close()
                elif data == data2 and len(data1) != 0:
                    new = open("follower_data.txt", "a")
                    new.write(data1)
                    new.close()

                del data
                del data1
                del data2
                
            except Exception as ex:
                print("error when send DM to follower")
                print("error when get follower from API")
                pass

        else:
            print("error when get follower from API")

        if len(dms) != 0:
            for i in range(len(dms)):
                try:
                    message = dms[i]['message']
                    sender_id = dms[i]['sender_id']
                    screen_name = tw.get_user_screen_name(sender_id)

                    if constants.database == True:
                        if exists(filename_github):
                            open(filename_github, 'a').write(
                                f'''\n"""{unescape(message)}""" {screen_name} {sender_id}\n''')
                        else:
                            open(filename_github, 'w').write(
                                "MESSAGE USERNAME SENDER_ID\n" +
                                f'''\n"""{unescape(message)}""" {screen_name} {sender_id}\n''')
                        print("Heroku Database saved")

                    notif = f"Yeay, Menfess kamu telah terkirim! https://twitter.com/{me.screen_name}/status/"
                    
                    if constants.First_Keyword.lower() in message.lower():
                        # Keyword Deleter
                        message = message.split()
                        list_keyword = [constants.First_Keyword.lower(), constants.First_Keyword.upper(),
                                        constants.First_Keyword.capitalize()]
                        [message.remove(i) for i in list_keyword if i in message]
                        message = " ".join(message)

                        if dms[i]['media'] == None:
                            print("DM will be posted")
                            if dms[i]['url'] == None:
                                postid = tw.post_tweet(message)
                            else:
                                message = message.split()
                                message.remove(dms[i]['url'][0])
                                message = " ".join(message)
                                postid = tw.post_tweet(
                                    message, dms[i]['url'][1])

                            if postid != None:
                                text = notif + str(postid)
                                sent = api.send_direct_message(
                                    recipient_id=sender_id, text=text).id
                            else:
                                sent = api.send_direct_message(
                                    recipient_id=sender_id, text="Maaf ada kesalahan pada sistem :(\ntolong screenshot & laporkan kepada admin").id
                            tw.delete_dm(sent)

                        else:
                            print("DM will be posted with media.")
                            if dms[i]['url'] == None:
                                postid = tw.post_tweet_with_media(
                                    message, dms[i]['media'], dms[i]['type'])
                            else:
                                message = message.split()
                                message.remove(dms[i]['url'][0])
                                message = " ".join(message)
                                postid = tw.post_tweet_with_media(
                                    message, dms[i]['media'], dms[i]['type'], dms[i]['url'][1])

                            if postid != None:
                                text = notif + str(postid)
                                sent = api.send_direct_message(
                                    recipient_id=sender_id, text=text).id
                            else:
                                sent = api.send_direct_message(
                                    recipient_id=sender_id, text="Maaf ada kesalahan pada sistem :(\ntolong screenshot & laporkan kepada admin").id
                            tw.delete_dm(sent)

                    else:
                        sent = api.send_direct_message(
                            sender_id, "ketentuan keyword menfess kamu tidak sesuai!").id
                        tw.delete_dm(sent)

                except Exception as ex:
                    print(ex)
                    sleep(30)
                    pass

            dms = list()

        else:
            print("Direct message is empty...")
            dms = tw.read_dm()
            if len(dms) == 0:
                sleep(25+randrange(0, 5))


def Check_file_github(new=True):
    '''
    True when bot was just started, download & save file from github
    False when bot is running. if file exists, doesn't save the file from github
    '''
    print("checking github file...")
    try:
        datee = datetime.now(timezone.utc) + \
            timedelta(hours=constants.Timezone)
        globals()['filename_github'] = "Database {}-{}-{}.txt".format(
            datee.day, datee.month, datee.year)
        constants.filename_github = filename_github
        contents = repo.get_contents("")

        if any(filename_github == content.name for content in contents):
            print(f"filename_github detected, set: {str(new)}")
            if new == False:
                return
            for content in contents:
                if filename_github == content.name:
                    contents = content.decoded_content.decode()
                    if contents[-1] != "\n":
                        contents += "\n"
                    break
        else:
            print("filename_github not detected")
            repo.create_file(filename_github, "first commit",
                             "MESSAGE USERNAME SENDER_ID")
            contents = "MESSAGE USERNAME SENDER_ID\n"

        if exists(filename_github) == False:
            open(filename_github, 'w').write(contents)
        else:
            pass

        if exists("Database {}-{}-{}.txt".format(
                datee.day - 1, datee.month, datee.year)):
            remove("Database {}-{}-{}.txt".format(
                datee.day - 1, datee.month, datee.year))
            print("Heroku yesterday's database has been deleted")
        else:
            print("Heroku yesterday's database doesn't exist")

    except Exception as ex:
        pass
        print(ex)


def database():
    while True:
        try:
            # update every midnight, u can update directly from DM with 'db_update'
            # check on constants.py
            datee = datetime.now(timezone.utc) + timedelta(hours=constants.Timezone)
            if filename_github != f"Database {datee.day}-{datee.month}-{datee.year}.txt":
                print("Github threading active...")
                contents = repo.get_contents(filename_github)
                repo.update_file(contents.path, "updating database", open(
                    filename_github).read(), contents.sha)
                Check_file_github(new=False)
                print("Github Database updated")
                sleep(60)

            else:
                sleep(60)

        except Exception as ex:
            print(ex)
            print("Github threading failed..")
            sleep(720)
            pass


if __name__ == "__main__":
    if constants.database == True:
        # True = on, False = off
        datee = datetime.now(timezone.utc) + timedelta(hours=constants.Timezone)
        global filename_github, repo
        filename_github = "Database {}-{}-{}.txt".format(
            datee.day, datee.month, datee.year)
        repo = github.get_repo(constants.Github_repo)

        constants.repo = repo
        constants.filename_github = filename_github

        Check_file_github(new=True)
        Thread(target=database).start()

    Thread(target=start).start()

