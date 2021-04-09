import smsactivate
import config
from telethon import TelegramClient
import time
import requests
import asyncio
from faker import Faker
import os
from random import choice as rand_choice
from random import randrange
from telethon.tl.functions.photos import UploadProfilePhotoRequest
from telethon import errors
from telethon.sessions import StringSession
from prettyprinter import pprint as pp
from itertools import cycle
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.account import UpdateUsernameRequest
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.messages import GetDialogsRequest, GetHistoryRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import InviteToChannelRequest
from autoapi import Automate
import json
import socks
import socket
import sys
import csv
import traceback
import re

def get_users_to_add():
    users = []
    with open("data/users.csv", encoding='UTF-8') as f:
        rows = csv.reader(f, delimiter=",", lineterminator="\n")
        next(rows, None)
        for row in rows:
            user = {}
            user['username'] = row[0]
            user['id'] = int(row[1])
            user['access_hash'] = int(row[2])
            user['name'] = row[3]
            users.append(user)
    return users

def get_group():
    username = config.group_username
    group = {}
    with open("data/chats.json") as chatsfile:
        chats = json.load(chatsfile)
        for chat in chats:
            if chat['username'] == config.group_username:
                group['id'] = chat['id']
                group['access_hash'] = chat['access_hash']
                return group
        return None

def get_proxies():
    proxies = []
    with open('data/proxies/russian.txt', 'r') as f:
        data = f.readlines()
        for proxy in data:
            if proxy.startswith("#"):
                continue
            ip, port, username, password = proxy.split(':')
            proxies.append(
                {
                    'addr': ip.rstrip(),
                    'port': int(port.rstrip()),
                    'username': username.rstrip(),
                    'password': password.rstrip(),
                    'proxy_type': socks.SOCKS5
                })
    return proxies

def get_picture():
    pics = os.listdir('data/pics')
    ch = rand_choice(pics)
    return f'./data/pics/{ch}'

def get_api_creds():
    creds = []
    with open('data/creds.txt', 'r') as f:
        data = f.readlines()
        for cred in data:
            if cred.startswith("#"):
                continue
            api_id, api_hash, phone = cred.split(':')
            creds.append(
                {
                    'api_id': int(api_id.rstrip()),
                    'api_hash': api_hash.rstrip()
                }
            )
    return creds

def get_client(api_id, api_hash, proxy):
    return TelegramClient(StringSession(), api_id, api_hash, proxy=proxy, connection_retries=5)

async def sign_up(client, phone, code, hash_):
    fake = Faker()
    await client.sign_up(
        code=code,
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        phone=phone,
        phone_code_hash=hash_
    )

async def set_picture(client):
    profile_picture = get_picture()
    await client(UploadProfilePhotoRequest(
        await client.upload_file(profile_picture)
    ))


async def join_group(client, group, tries=0):
    if tries > 10:
        print('Unabled to join group... restarting cycle')
        raise Exception('restart_work_cycle') 
    try:
        group = await client.get_entity(group)
        await client(JoinChannelRequest(group))
    except Exception as ex:
        print(ex)
        print("Couldn't join group... retrying after 30 seconds")
        time.sleep(30)
        await join_group(client, group, tries+1)

async def invite_to_group(client, group):
    pass

async def set_username(client, tries=0):
    faker = Faker()
    if tries > 10:
        print('Unabled to find a suitable username... skipping')
        return False

    rand = randrange(1, 10000)
    username = f'{faker.first_name()}{rand}'
    try:
        await client(UpdateUsernameRequest(username))
    except (errors.rpcerrorlist.UsernameInvalidError, errors.rpcerrorlist.UsernameOccupiedError):
        print(f'Retrying to set username in 5 seconds, {username} failed/occupied')
        time.sleep(5)
        await set_username(client, tries+1)


async def set_bio(client):
    await client(UpdateProfileRequest(
        about='This is a testing update'
    ))

async def add_to_group(client, group_data, user_data, tries=0):
    if tries > 0:
        print('Unabled to add user... skipping')
        return False
    try:
        target = InputPeerChannel(group_data['id'], group_data['access_hash'])
        user = InputPeerUser(user_data['id'], user_data['access_hash'])
        await client(InviteToChannelRequest(target, [user]))
        return True
    except (errors.rpcerrorlist.ChannelInvalidError):
        print("Channel invalid error...")
        return False
    except (errors.rpcerrorlist.UserIdInvalidError,
            errors.rpcerrorlist.UserKickedError,
            errors.rpcerrorlist.UserPrivacyRestrictedError,
            errors.rpcerrorlist.UserBannedInChannelError,
            errors.rpcerrorlist.UsersTooMuchError,
            errors.rpcerrorlist.UserBlockedError):
        print("Unable to add user (possibly banned)... skipping")
        return False


async def start_adding(client, users, group):
    for x in range(config.members_per_account):
        user = next(users)
        try:
            print (f"Adding {user['name']} ({user['id']})")
            # if user['username'] == "":
            #     continue
            # user_to_add = client.get_input_entity(user['username'])
            await add_to_group(client, group, user)
            seconds = randrange(*config.wait_before_adding)
            print(f"Waiting for {seconds} seconds ({config.wait_before_adding[0]}-{config.wait_before_adding[1]})...")
            time.sleep(seconds)
        except PeerFloodError:
            print("Peer flood error")
        except Exception:
            traceback.print_exc()
            print("Unexpected Error")
            continue

async def get_web_code(client):
    messages = await client.get_messages(777000, limit=1)
    for message in messages:
        text = message.message
        if "Web login code" not in text:
            time.sleep(1)
            await get_web_code(client)
        matches = re.findall(r'(?<=This is your login code:\n)[^\n\s]*', text)
        if matches:
            return matches[0].strip()
        else:
            time.sleep(1)
            await get_web_code(client)

async def get_login_code(client):
    messages = await client.get_messages(777000, limit=1)
    for message in messages:
        text = message.message
        if "Login code" not in text:
            time.sleep(1)
            await get_login_code(client)
        matches = re.findall(r'(?<=Login code: )[^.\s]*', t)
        if matches:
            return int(matches[0].strip())
        else:
            time.sleep(1)
            await get_login_code(client)

async def work(proxy, cred, sms, users, group):
    timing_actions = [10, 20, 30]
    timing_messages = [30, 60, 120]
    # Lets create a client
    api_id = cred['api_id']
    api_hash = cred['api_hash']

    print(f"Setting proxy ({proxy['addr']}) and getting client...")
    client = get_client(api_id, api_hash, proxy)
    print("Connecting...")
    await client.connect()
    if not sms.order_number():
        print('No balance in smsru, exiting.')
        return -1

    smsid, phone = sms.access_number
    print(f"Phone: {phone} | ID: {smsid}")
    await client.connect()
    sent = await client.send_code_request(int(phone))

    if sms.change_status():
        sms.get_activation_status()
        await client.connect()
        await sign_up(client, phone, sms.activation_code, sent.phone_code_hash)
        sms.complete_activation()
        await client.start()

        print("Waiting 5 seconds to set picture")
        time.sleep(5)
        await set_picture(client)
        
        print("Waiting 5 seconds to set bio")
        time.sleep(5)
        await set_bio(client)
        
        print("Waiting 8 seconds to set username")
        time.sleep(8)
        await set_username(client)
        
        print("Waiting 15 seconds to join group")
        time.sleep(15)
        await join_group(client, 'bottestinggrou')

        print("Automatically getting API id/hash...")
        w = Automate(False, proxy)
        print("Entering number...")
        w.enter_number(phone)
        print("Getting code...")
        code = await get_web_code(client)
        print("Entering code...")
        w.enter_code(code)
        print("Making an application...")
        w.make_application()
        print("Done")
        api = w.get_api()
        client = TelegramClient("+{phone}", api_id, api_hash, proxy=proxy, connection_retries=5)
        print("Signing in...")
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            login_code = await get_login_code(client)
            await client.sign_in(phone, login_code)
        print("Signed in...")
        print("Waiting 2 seconds to start adding members...")
        time.sleep(2)
        await start_adding(client, users, group)
        raise Exception('restart_work_cycle')


async def main(creds, proxies, smsru_key, users, group, accounts=0, current_proxy=None):
    print('Starting work cycle')
    sms = smsactivate.SMSActivate(smsru_key, country=0)
    if not current_proxy:
        current_proxy = next(proxies)
    if accounts == 10:
        current_proxy = next(proxies)
        print(f"Made 10 accounts, switching proxy to {current_proxy}")
        accounts = 0
    try:
        cred = next(creds)
        await work(current_proxy, cred, sms, users, group)
        # await main(creds, proxies, smsru_key, users, group, accounts+1, current_proxy=current_proxy)
    except Exception as e:
        # attempt to deactivate number
        print(str(e))
        sms.deactivate_number()
        await main(creds, proxies, smsru_key, users, group, accounts+1, current_proxy=current_proxy)

def is_good_proxy(proxy):
    try:
        proxies = {"http": f"http://{proxy['username']}:{proxy['password']}@{proxy['addr']}:{proxy['port']}"}
        requests.get("https://www.google.com", proxies=proxies)
        return True
    except Exception:
        return False

if __name__ == "__main__":
    # socks.set_default_proxy(socks.HTTP, "103.147.170.112", 59157, "XSCgKJCR", "h4zT6Jfi")
    # socket.socket = socks.socksocket
    # sys.exit(0)
    creds = cycle(get_api_creds())
    proxies = cycle(get_proxies())
    users = cycle(get_users_to_add())
    group = get_group()
    if not group:
        print(f"Couldn't find a group with the username: {config.group_username}. Did you run scraper.py?")
        sys.exit(0)
    smsru_key = config.key
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(creds, proxies, smsru_key, users, group))