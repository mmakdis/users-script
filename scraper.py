from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.sessions import StringSession
from itertools import cycle
import csv
import sys
import json
import datetime


def date_format(message):
    """
    :param message:
    :return:
    """
    if type(message) is datetime:
        return message.strftime("%Y-%m-%d %H:%M:%S")

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
                    'api_hash': api_hash.rstrip(),
                    'phone': phone
                }
            )
    return creds

def get_client(phone, api_id, api_hash, proxy=None):
    return TelegramClient(phone, api_id, api_hash, proxy=proxy, connection_retries=5)

creds = get_api_creds()[0]
api_id = creds['api_id']
api_hash = creds['api_hash']
phone = creds['phone']
client = get_client(phone, api_id, api_hash)
client.connect()

if not client.is_user_authorized():
    client.send_code_request(phone)
    client.sign_in(phone, input('Enter the code: '))
 
chats = []
last_date = None
chunk_size = 200
groups = []

result = client(GetDialogsRequest(
             offset_date=last_date,
             offset_id=0,
             offset_peer=InputPeerEmpty(),
             limit=chunk_size,
             hash = 0
         ))
chats.extend(result.chats)
 
for chat in chats:
    try:
        if chat.megagroup == True:
            groups.append(chat)
    except:
        continue
 

print('Choose a group to scrape members from: ')
i = 0
group_data = []

for g in groups:
    group_data.append(g.to_dict())
    print(str(i) + ' - ' + g.title)
    i +=1

with open("data/chats.json", "w") as chats:
    json.dump(group_data, chats, indent=4, default=date_format)
    print("Dumped group data to chats.json")
 
g_index = input("Enter a number: ")
target_group = groups[int(g_index)]
 
print('Fetching members...')
all_participants = []
all_participants = client.get_participants(target_group, aggressive=True)
 
print('Appending to file...')
members = 0

with open("data/users.csv", "w", encoding='UTF-8') as f:
    writer = csv.writer(f, delimiter=",", lineterminator="\n")
    writer.writerow(['username', 'user id', 'access hash', 'name', 'group', 'group id'])
    for user in all_participants:
        if user.username:
            username = user.username
        else:
            username = ""
        if user.first_name:
            first_name = user.first_name
        else:
            first_name = ""
        if user.last_name:
            last_name = user.last_name
        else:
            last_name = ""
        name = (first_name + ' ' + last_name).strip()
        writer.writerow([username,user.id,user.access_hash,name,target_group.title, target_group.id])
        members += 1   
print(f'{members} members scraped successfully.')

