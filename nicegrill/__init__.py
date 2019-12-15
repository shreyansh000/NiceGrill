from telethon.sync import TelegramClient, events
import functools
import asyncio
from nicegrill.main import main
from nicegrill.modules import _init
from nicegrill import loader
from config import API_HASH, API_ID
from database.allinone import get_storage
from nicegrill import dbsets
import pandas as pd
import sqlite3
import time
import os

if not API_ID or not API_HASH:
    API_ID = int(input("Enter your API ID:"))
    API_HASH = input("Enter your API HASH:")
    file = open("config.py", "w")
    file.write(f"API_ID={API_ID}\nAPI_HASH=\"{API_HASH}\"")
    file.close()

async def restore(client):
    async for msg in client.iter_messages((await client.get_me()).id, limit=5):
        if msg.document and msg.document.attributes[0].file_name == "database.db":
            await client.download_media(msg)
    qtables = "SELECT * FROM sqlite_master WHERE type='table'"
    os.remove("database/database.db")
    olddb = sqlite3.connect("database.db")
    tables = pd.read_sql(qtables, olddb)
    newdb = sqlite3.connect("database/database.db")
    newcur = newdb.cursor()
    for table in tables.index:
        try:
            newcur.execute(tables.sql[table])
        except ValueError:
            pass
        qcols = pd.read_sql(f"SELECT * from {tables.name[table]}", olddb)
        qcols.to_sql(tables.name[table], newdb, index=False, if_exists="append")
    os.remove("database.db")
    olddb.close()
    newdb.close()


with TelegramClient('NiceGrill', API_ID, API_HASH) as client:
    asyncio.get_event_loop().create_task(restore(client))
    client.parse_mode = 'html'
    _init.loads()
    loop = asyncio.get_event_loop()
    task = loop.create_task(main.storage(client))
    loop.run_until_complete(task)
    main.read(client)
    client.add_event_handler(
       functools.partial(main.outgoing),
       events.NewMessage(outgoing=True, forwards=False))
    client.add_event_handler(
       functools.partial(main.outgoing),
       events.MessageEdited(outgoing=True, forwards=False))
    print(f"Logged in as {(client.get_me()).first_name}")
    client.run_until_disconnected()
