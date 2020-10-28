import discord
from random import shuffle
import re
import emoji
import sys
import json
import string
from copy import deepcopy
from datetime import datetime

token = ""
client = discord.Client()

@client.event
async def on_message(message):
    if message.content != "hi": return
    await message.channel.send(file=discord.File('PNG/2C.png'))


client.run(token)