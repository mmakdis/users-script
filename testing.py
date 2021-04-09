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
import json
import socks
import socket
import sys
import csv
import traceback
from application import Automate
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

def get_client(api_id, api_hash, proxy=None):
    return TelegramClient("+79612865421", api_id, api_hash, connection_retries=5)

async def add_to_group(client, group_data, user_data, tries=0):
    if tries > 2:
        print('Unabled to add user... skipping')
        return False
    try:
        target = InputPeerChannel(group_data['id'], group_data['access_hash'])
        user = InputPeerUser(user_data['id'], user_data['access_hash'])
        await client(InviteToChannelRequest(target, [user]))
        return True
    except (errors.rpcerrorlist.ChannelInvalidError):
        seconds = randrange(*config.wait_before_adding)
        print(f"Retrying to add user in {seconds}")
        time.sleep(seconds)
        await add_to_group(client, group_data, user_data, tries+1)
    except (errors.rpcerrorlist.UserIdInvalidError,
            errors.rpcerrorlist.UserKickedError,
            errors.rpcerrorlist.UserPrivacyRestrictedError,
            errors.rpcerrorlist.UserBannedInChannelError,
            errors.rpcerrorlist.UsersTooMuchError,
            errors.rpcerrorlist.UserBlockedError):
        print("Unable to add user (possibly banned)... skipping")
        return False

async def start_adding(client, users, group):
    for x in range(5):
        user = next(users)
        try:
            print(f"Adding {user['name']} ({user['id']})")
            # if user['username'] == "":
            #     continue
            # user_to_add = client.get_input_entity(user['username'])
            await add_to_group(client, group, user)
            print(f"Waiting for {config.wait_before_adding[0]}-{config.wait_before_adding[1]} Seconds...")
            time.sleep(randrange(*config.wait_before_adding))
        except PeerFloodError:
            print("Peer flood error")
        except:
            traceback.print_exc()
            print("Unexpected Error")
            continue

group = get_group()
users = cycle(get_users_to_add())

async def get_code(client):
    messages = await client.get_messages(777000, limit=1)
    for message in messages:
        text = message.message
        if "Web login code" not in text:
            time.sleep(1)
            await get_code(client)
        matches = re.findall(r'(?<=This is your login code:\n)[^\n\s]*', text)
        if matches:
            return matches[0].strip()
        else:
            time.sleep(1)
            await get_code(client)

async def main():
    client = get_client(3106162, "0efcea8127045069c5163a7fc1341e48")
    await client.connect()
    await client.start()
    w = Automate()
    w.enter_number("+79612865421")
    code = await get_code(client)
    w.enter_code(code)
    # w.make_application()
    print(w.get_api())

loop = asyncio.get_event_loop()
loop.run_until_complete(main())