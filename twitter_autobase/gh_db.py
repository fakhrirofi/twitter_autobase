from json import dump, load
from html import unescape
from os.path import exists
from datetime import datetime, timedelta, timezone
from time import sleep
from os import remove
from typing import NoReturn


def update_local_file(selfAlias: object, sender_id: str, message: str, postid: str) -> NoReturn:
    '''
    update database file (json) on local
    :param selfAlias: an alias of self from Autobase class
    '''
    screen_name = selfAlias.get_user_screen_name(sender_id)
    if exists(selfAlias.DMCmd.filename_github):
        with open(selfAlias.DMCmd.filename_github, 'r+') as f:
            data = load(f)
            for x in range(len(data)):
                if int(data[x]['id']) == int(sender_id):
                    data[x]['username'] = screen_name
                    data[x]['menfess'].append({'postid': postid, 'text': unescape(message)})
                    break
            else:
                data.append({'username': screen_name, 'id': int(sender_id),
                            'menfess': [{'postid': postid, 'text': unescape(message)}]})
            f.seek(0)
            dump(data, f, indent=4)
            f.truncate()
            f.close()
    else:
        with open(selfAlias.DMCmd.filename_github, 'w+') as f:
            data = [{'username': screen_name, 'id': int(sender_id),
                    'menfess': [{'postid': postid, 'text': unescape(message)}]}]
            f.seek(0)
            dump(data, f, indent=4)
            f.truncate()
            f.close()


def check_file_github(selfAlias: object, new: bool=True) -> NoReturn:
    '''
    :param new: True when bot was just started, download & save file from github when bot was just started
    False when bot is running. If file exists, It doesn't save the file from github.
    'new' parameter used if you update database not every midnight on Database method
    '''
    print("checking github file...")
    try:
        datee = datetime.now(timezone.utc) + \
            timedelta(hours=selfAlias.credential.Timezone)
        selfAlias.DMCmd.filename_github = "{} {}-{}-{}.json".format(
            selfAlias.bot_username, datee.year, datee.month, datee.day)
        contents = selfAlias.DMCmd.repo.get_contents("")

        if any(selfAlias.DMCmd.filename_github == content.name for content in contents):
            # If filename exists in github. But, when midnight,
            # filename automatically changed.
            print(f"filename_github detected, new: {str(new)}")
            if new == False:
                return
            for content in contents:
                if selfAlias.DMCmd.filename_github == content.name:
                    contents = content.decoded_content.decode()
                    break
        else:
            print("filename_github not detected")
            contents = "[]"
            selfAlias.DMCmd.repo.create_file(selfAlias.DMCmd.filename_github, "first commit",
                            contents)

        if exists(selfAlias.DMCmd.filename_github) == False:
            with open(selfAlias.DMCmd.filename_github, 'w') as f:
                f.write(contents)
                f.close()
        else:
            pass

        old_filename = "{} {}-{}-{}.json".format(
                selfAlias.bot_username, datee.year, datee.month, datee.day - 1)

        if exists(old_filename):
            remove(old_filename)
            print("Heroku yesterday's Database has been deleted")
        else:
            print("Heroku yesterday's Database doesn't exist")

    except Exception as ex:
        pass
        print(ex)


def gh_database(selfAlias: object, Github_database: bool=True):
    '''
    :param Github_database: sync local database to github repo
    Sync will only happen on midnight or when admin sends command from DM
    '''
    while True:
        try:
            # update every midnight, you can update directly from DM with 'db_update'
            # check on config.py
            datee = datetime.now(timezone.utc) + timedelta(hours=selfAlias.credential.Timezone)
            if selfAlias.DMCmd.filename_github != f"{selfAlias.bot_username} {datee.year}-{datee.month}-{datee.day}.json":
                if Github_database is True:
                    print("Github threading active...")
                    contents = selfAlias.DMCmd.repo.get_contents(selfAlias.DMCmd.filename_github)
                    with open(selfAlias.DMCmd.filename_github) as f:
                        selfAlias.DMCmd.repo.update_file(contents.path, "updating Database", f.read(), contents.sha)
                        f.close()
                    check_file_github(selfAlias, new=False)
                    print("Github Database updated")
                
                else:
                    selfAlias.DMCmd.filename_github = f"{selfAlias.bot_username} {datee.year}-{datee.month}-{datee.day}.json"

            else:
                sleep(60)

        except Exception as ex:
            print(ex)
            print("Github threading failed..")
            sleep(720)
            pass