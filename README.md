# twitter_autobase
**postgres***<br>
A Twitter bot that can read your DMs, then tweets like Twitter autobase. Inspired by
https://github.com/ydhnwb/autodm_base and using https://github.com/twitivity/twitivity You can try on my autobase account
[@autobase_reborn](https://twitter.com/autobase_reborn).

- **Read Twitter rules[[1]](https://help.twitter.com/en/rules-and-policies/twitter-search-policies)[[2]](https://developer.twitter.com/en/developer-terms/more-on-restricted-use-cases)[[3]](https://help.twitter.com/en/rules-and-policies/twitter-automation)** <br>
- **USING THIS BOT FOR 'ADULT' BASE IS STRICTLY PROHIBITED** <br>

## Features
- Real-time account activity
- User (account) requirements
- Tweet photo, GIF, and video
- Post a Thread when characters > 280
- Make quick reply button
- Send command from admin account (via DM)
- Run multiple autobase accounts (see on app.py)
- etc. see on config.py


## Requirements
- Python 3.8.x
- Twitter Developer Account
- Ngrok Account
- Heroku Account (optional)
 

## Getting Started
- Install [pip](https://pypi.org/project/pip/), [virtualenv](https://pypi.org/project/virtualenv/),
  [git](https://github.com/git-guides/install-git), and [heroku](https://devcenter.heroku.com/articles/heroku-cli)(optional)
- [Do Installation](#installation)
- Edit contents on config.py
- [Deploy to Heroku](#deploy-to-heroku)


## Installation
Open your terminal on the specified folder <br>
```bash
# download on https://github.com/fakhrirofi/twitter_autobase/releases for stable version
git clone https://github.com/fakhrirofi/twitter_autobase.git
cd twitter_autobase
```
Linux
```
virtualenv venv
source venv/bin/activate
pip3 install -r requirements.txt
```
Windows
```
virtualenv venv
venv\Scripts\activate
pip3 install -r requirements.txt
```
Make .gitignore file <br>
```
venv/
**/__pycache__
# add another, up to you
```
After modifying contents on config, run app by using syntax: `python3 app.py`


## Deploy to Heroku

### Deploy using Heroku CLI
```bash
git add .
git commit -m "initial commit"
heroku git:remote -a your_heroku_app_name
git push -f heroku master
```

### Heroku limitations
- 550 free dyno hours, you can upgrade to 1000 hours by adding credit card to your account.
- Dyno cycling (restart), so `add_admin`, `rm_admin`, `add_blacklist`, `rm_blacklist`,
`switch on/off`, and all temporary db won't work perfectly. It would be better if you use Heroku database services e.g. Postgres. Please setting `Blacklist_words`, `Admin_id`, and etc. before
deploying to Heroku. Database will be changed to Postgres in future updates.


## DMs examples (based on config)
You can tweet more than one media with media link on tweet. Open your twitter app then tap (hold) the tweet.
Media link automatically will be copied, then send the link to this bot from DM.

### Quote-retweet
`fess! your message https://twitter.com/username/1234567890?s=19` (by attaching media, url, or not)

### Make a thread
`fess! Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.` (by attaching media, url, or not)

### Normal tweet
`fess! your message` (by attaching media, url, or not)

### Admin command
Note: Due to Heroku dyno cycling, some commands that use temporary data won't work perfectly. <br>
Only admin can access these commands. <br>
`/add_blacklist word1 word2 word-n` <br>
`/rm_blacklist word1 word2 word-n` <br>
`/display_blacklist` <br>
`/add_admin username1 username2 username-n` <br>
`/rm_admin username1 username2 username-n` <br>
`/who https://twitter.com/username/status/1234567890?s=19` check who was sent the menfess <br>
`/switch off` turn off the automenfess <br>
`/switch on` turn on the automenfess <br>
`/block https://twitter.com/username/status/1234567890?s=19` delete menfess & block user by attaching his menfess url <br>
`/unfoll https://twitter.com/username/status/1234567890?s=19` delete menfess & unfoll user by attaching his menfess url <br><br>
For add_blacklist and rm_blacklist, you can add space into your words by giving underscore "_". Example: <br>
`/add_blacklist _word1_ word2_word3 word-n` <br>
This command will append " word1 ", "word2 word3", and "word-n" to Blacklist words list.

### User command
`/delete https://twitter.com/username/status/1234567890?s=19` delete menfess by attaching tweet url <br>
`/unsend` delete the last menfess <br>
`/menu` send config.DMCmdMenu to sender <br>
`/cancel` cancel the last menfess when it's still on the queue


## Quick Reply Documentation

### Quick Reply Json
Reference: https://developer.twitter.com/en/docs/twitter-api/v1/direct-messages/quick-replies/api-reference/options
```python
{
    "text"      : "Text that will be sent from DM",
    "options"   : [
        {
            "label"         : "button's name",
            "description"   : "button's description",
            "metadata"      : "metadata",
        }
    ]
}
```
The maximum of options is 20 and the maximum characters of description is 72

### Raw Send DM
```python
self.send_dm(sender_id, data['text'], quick_reply_type='options', quick_reply_data=data['options'])
```
- `data` : [Quick Reply Json](#quick-reply-json)

### Metadata
You can see the code of metadata processing on _quick_reply_manager method at quick_reply.py. The abstract value of metadata is: `action|data`

### Execute method call `exec|method_call`
The method can be normal method or protected method. Method call must have only one undefined sender_id argument. Example: <br>
Method:
```python
# something.py (inside class that inherited to Autobase class)
def _do_something(self, sender_id, defined_argument) -> NoReturn:
    pass
```
Metadata: `exec|self._do_something(sender_id, "defined argument")` # sender_id is only one undefined argument here

### Send text message `send_text|attribute_string`
Send Autobase's attribute (string) to user. Example: <br>
Attribute:
```python
# config.py (credential)
Notif_something = "This message will be sent to sender"
```
Metadata: `send_text|self.credential.Notif_something`

### Send quick reply button `send_button|attribute_quick_reply_json`
attribute_quick_reply_json template is [Quick Reply Json](#quick-reply-json). Example: <br>
Attribute:
```python
# config.py (credential)
Button_something = {
    'text'      : 'Message that will be sent to sender',
    'options'   : [
        {
            'label'         : 'something',
            'description'   : 'something description',
            'metadata'      : 'exec|self._do_something(sender_id, "defined argument")',
        }
    ]
}
```
Metadata: `send_button|self.credential.Button_something`


## Notes
- Admin passes all filters
- Only admin that can set account using admin command
- All temporary data only available for one day (reset at midnight or heroku dyno cycling)
- If you use github repository to deploy to heroku, make sure to set the repository to private.
- Keywords are not case-sensitive
- See changelogs on [releases's notes](https://github.com/fakhrirofi/twitter_autobase/releases)
- I have written documentation in config


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to
change. To make a pull request, see the GitHub documentation on [creating a pull request](https://help.githubcom/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request).


## MIT License

Copyright (c) 2020- Fakhri Catur Rofi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
