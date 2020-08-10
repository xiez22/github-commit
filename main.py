# A github commit email sender.

import requests
import time
import json
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import logging

# Config logging module.
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
handler = logging.FileHandler("log.txt")
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

 
# SMTP Setup
mail_host="smtp.sjtu.edu.cn"
mail_user="userid"
mail_pass="pwd"

sender = 'userid@sjtu.edu.cn'
receivers = ['userid@sjtu.edu.cn']

# Hyper params
SLEEP_TIME = 30
MAX_GET_TIMES = 30


class Commit():
    def __init__(self, repo, sha, author, time, message):
        self.repo = repo
        self.sha = sha
        self.author = author
        self.time = time
        self.message = message

def get_latest_commit(repo: str):
    '''
    repo: string. e.g. https://github.com/{user}/{repo}.git
    '''

    # Get user name and repo name.
    if not repo.endswith('.git') or not repo.startswith('https://github.com/'):
        print('Illegal git repo address.')
        logger.info('Illegal repo.')
        raise RuntimeError()

    get_url = 'https://api.github.com/repos/' + repo[19: -4] + '/commits'
    logger.info(get_url)

    # Get commit list.
    get_times = 0
    while True:
        try:
            response = requests.get(get_url)
            break
        except Exception:
            get_times += 1
            if get_times > MAX_GET_TIMES:
                print('Get times exceeds limit.')
                logger.info('Get times exceeds limit.')
                raise RuntimeError()

            print('Connect failed, retrying...')
            logger.info('Connect failed, retrying...')
            time.sleep(3)

    # print(response.content)
    commit_list = json.loads(response.content)[0]
    print('Commit:', commit_list['sha'])
    logger.info('Commit: ' + commit_list['sha'])

    return Commit(repo, commit_list['sha'], commit_list['commit']['committer']['name'], 
                    commit_list['commit']['committer']['date'], 
                    commit_list['commit']['message'])


def send_email_messages(new_commits):
    msg_to_send = f'共有{len(new_commits)}个新的提交。\n\n'

    for commit in new_commits:
        msg_to_send += f'仓库:{commit.repo}\n提交者:{commit.author}\n提交信息:{commit.message}\n提交时间:{commit.time}\n\n'

    message = MIMEText(msg_to_send, 'plain', 'utf-8')
    message['From'] = Header("GitHub推送", 'utf-8')
    message['To'] =  Header("订阅收件人", 'utf-8')
    
    subject = '新的Github提交'
    message['Subject'] = Header(subject, 'utf-8')
    
    try:
        smtpObj = smtplib.SMTP() 
        smtpObj.connect(mail_host, 587)
        smtpObj.login(mail_user,mail_pass)  
        smtpObj.sendmail(sender, receivers, message.as_string())
        print('Email send succesfully.')
        logger.info('Email send.')
    except smtplib.SMTPException:
        print('Error.')
        logger.info('Error when sending email.')

def main_loop():
    commit_dict = {}

    # Scan the git.txt.
    print('Start checking...')
    logger.info('Start checking...')

    while True:
        new_commit_list = []
        with open('git.txt') as f:
            for line in f.readlines():
                line = line.strip()
                if commit_dict.get(line) is None:
                    commit_dict[line] = ''
                
                # Check the git.
                try:
                    latest_commit = get_latest_commit(line)
                    if latest_commit.sha != commit_dict[line]:
                        # Found new commit!
                        commit_dict[line] = latest_commit.sha
                        new_commit_list.append(latest_commit)

                except Exception as err:
                    print(err)
                    logger.info(err)
                    continue

        print(f'Finished. {len(new_commit_list)} found.')
        logger.info(f'Finished. {len(new_commit_list)} found.')

        if len(new_commit_list) > 0:
            print('Sending emails...')

            try:
                send_email_messages(new_commit_list)
                print('Finished!')
            except Exception as err:
                print(err)
                logger.info('Error when sending email.')

        time.sleep(SLEEP_TIME)
    

if __name__ == '__main__':
    main_loop()
