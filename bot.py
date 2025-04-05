import json
import logging
import os
import discord
from pytz import timezone
from sanitize import sanitize
from mobilizon_integration import MobilizonIntegration

# Environment configuration
discord_token = os.getenv("DISCORD_TOKEN")
mobilizon_enabled = os.getenv("MOBILIZON_ENABLED", "false").lower() == "true"

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kronos")

# Discord configuration
intents = discord.Intents.default()
client = discord.Client(intents=intents)
local_timezone = timezone("Europe/Warsaw")

# Initialize Mobilizon integration (if enabled)
mobilizon = MobilizonIntegration() if mobilizon_enabled else None

@client.event
async def on_ready():
    guilds_total = len(client.guilds)
    guilds_processed = 0
    
    for guild in client.guilds:
        guilds_processed += 1
        logger.info(f"Scraping {guild}")
        logger.info(f"{client.user} has connected to Discord server {guild}!")
        
        for event in guild.scheduled_events:
            full_event = await guild.fetch_scheduled_event(event.id)
            event = full_event
            
            # Time information processing
            start_time = event.start_time.astimezone(local_timezone)
            end_time = event.end_time.astimezone(local_timezone) if event.end_time else None
            
            # Logging event information
            logger.info(event)
            logger.info(event.creator)
            logger.info(event.creator_id)
            logger.info(event.description)
            logger.info(start_time)
            
            # Preparing paths and filenames
            date = start_time.strftime("%Y-%m-%d")
            directory = f'events/{start_time.strftime("%Y/%m/%d")}'
            start_time_str = start_time.strftime("%H:%M")
            end_time_str = end_time.strftime("%H:%M") if end_time else "?"
            filename = f"{date}-{sanitize(event.name)}.md"
            
            # Cover image handling
            if event.cover_image is not None:
                feature_image = f"featureImage: {event.cover_image.url}"
            else:
                feature_image = ""
            
            # Preparing Markdown file content
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
      {date} {start_time_str}-{end_time_str}: null
---
{event.description}
"""
            print(fields)
            
            # Creating directories (if they don't exist)
            try:
                os.makedirs(directory, mode=0o777, exist_ok=True)
            except FileExistsError:
                logger.exception("We can't create a tree. Why, oh why?")
            
            # Saving Markdown file
            try:
                with open(f"{directory}/{filename}", "w") as f:
                    f.write(fields)
            except PermissionError:
                logger.exception("Oops, we can't write here!")
            
            # Mobilizon integration (if enabled)
            if mobilizon_enabled and mobilizon:
                try:
                    mobilizon_event = await mobilizon.create_or_update_event(event, start_time, end_time)
                    if mobilizon_event:
                        logger.info(f"Event synchronized with Mobilizon: {mobilizon_event['url']}")
                    else:
                        logger.error(f"Failed to synchronize event with Mobilizon: {event.name}")
                except Exception as e:
                    logger.error(f"Error during Mobilizon synchronization: {e}")
        
        logger.info(
            f"Guilds processed: {guilds_processed}, guilds total: {guilds_total}"
        )
        
        if guilds_processed == guilds_total:
            await client.close()

client.run(discord_token)