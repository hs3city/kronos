import json
import logging
import os

import discord
from pytz import timezone

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
            directory = start_time.strftime("%Y/%m/%d")
            start_time = start_time.strftime("%H:%M")
            end_time = end_time.strftime("%H:%M")
            filename = f"{date}-{event.name.replace('/', '').replace(':', '')}.md"
            fields = f"""---
title: {json.dumps(event.name)}
tags: ["hs3"]
outputs:
- html
- calendar
discord_event:
  id: {event.id}
  link: {event.url}
  interested: {event.user_count}
  organizer: {event.creator}
  location: {event.location}
featureImage: {event.cover_image}
eventInfo:
  dates:
    extra:
      {date} {start_time}-{end_time}: null
---
{event.description}
"""
            print(fields)
            try:
                os.makedirs(directory)
            except FileExistsError:
                pass
            with open(f"{directory}/{filename}", "w") as f:
                f.write(fields)
        logging.info(
            f"Guilds processed: {guilds_processed}, guilds total: {guilds_total}"
        )
        if guilds_processed == guilds_total:
            await client.close()


client.run(discord_token)
