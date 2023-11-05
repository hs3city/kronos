import json
import logging
import os

import discord
from pytz import timezone

from sanitize import sanitize

discord_token = os.getenv("DISCORD_TOKEN")

# Logging configuration
logging.basicConfig(level=logging.INFO)

# Discord configuration
intents = discord.Intents.default()
client = discord.Client(intents=intents)

local_timezone = timezone("Europe/Warsaw")


@client.event
async def on_ready():
    guilds_total = len(client.guilds)
    guilds_processed = 0
    for guild in client.guilds:
        guilds_processed += 1
        logging.info(f"Scraping {guild}")
        logging.info(f"{client.user} has connected to Discord server {guild}!")
        for event in guild.scheduled_events:
            full_event = await guild.fetch_scheduled_event(event.id)
            event = full_event
            start_time = event.start_time.astimezone(local_timezone)
            end_time = event.end_time.astimezone(local_timezone)
            logging.info(event)
            logging.info(event.creator)
            logging.info(event.creator_id)
            logging.info(event.description)
            logging.info(start_time)
            date = start_time.strftime("%Y-%m-%d")
            directory = f'events/{start_time.strftime("%Y/%m/%d")}'
            start_time = start_time.strftime("%H:%M")
            end_time = end_time.strftime("%H:%M")
            filename = f"{date}-{sanitize(event.name)}.md"
            if event.cover_image is not None:
                feature_image = f"featureImage: {event.cover_image.url}"
            else:
                feature_image = ""
            fields = f"""---
title: {json.dumps(event.name)}
tags: ["hs3"]
outputs:
- html
- calendar
discord_event:
  id: {json.dumps(event.id)}
  link: {json.dumps(event.url)}
  interested: {json.dumps(event.user_count)}
  organizer: {json.dumps(event.creator.name)}
  location: {json.dumps(event.location)}
{feature_image}
eventInfo:
  dates:
    extra:
      {date} {start_time}-{end_time}: null
---
{event.description}
"""
            print(fields)
            try:
                os.makedirs(directory, mode=0o777, exist_ok=True)
            except FileExistsError:
                logging.exception("We can't create a tree. Why, oh why?")
            try:
                with open(f"{directory}/{filename}", "w") as f:
                    f.write(fields)
            except PermissionError:
                logging.exception("Oops, we can't write here!")
        logging.info(
            f"Guilds processed: {guilds_processed}, guilds total: {guilds_total}"
        )
        if guilds_processed == guilds_total:
            await client.close()


client.run(discord_token)
