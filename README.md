# Kronos-Mobilizon Integration

Integration between Kronos bot (Discord events scraper) and the Mobilizon platform.

## Description

This project extends the functionality of the Kronos bot, which was originally responsible only for fetching events from Discord servers and saving them in Markdown format. Now the bot additionally sends these events to the Mobilizon platform using the GraphQL API.

## Requirements

- Python 3.8 or newer
- Discord access token
- Mobilizon API access token
- Account on a Mobilizon instance with permissions to create events

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/hs3city/kronos.git
   cd kronos
   ```

2. Add new files with Mobilizon integration:
   - `mobilizon_integration.py`
   - Updated `bot.py`

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Set the following environment variables:

```bash
# Required for Kronos
export DISCORD_TOKEN=your_discord_token

# For Mobilizon integration
export MOBILIZON_ENABLED=true
export MOBILIZON_API_URL=https://your-mobilizon-instance.org/api
export MOBILIZON_TOKEN=your_mobilizon_api_token
```

## Usage

Run the bot:

```bash
python bot.py
```

The bot will perform the following operations:
1. Connect to Discord and fetch all scheduled events from servers it has access to
2. Save these events as Markdown files in the `events/` folder
3. If Mobilizon integration is enabled (`MOBILIZON_ENABLED=true`), create or update these events on the Mobilizon platform

## File Structure

- `bot.py` - Main Discord bot script
- `sanitize.py` - Helper functions for filename sanitization
- `mobilizon_integration.py` - Class responsible for Mobilizon integration
- `synced_events.json` - File storing information about synchronized events (created automatically)

## How Mobilizon Integration Works

1. Bot fetches events from Discord
2. For each event, it checks if it has already been synchronized with Mobilizon (based on Discord event ID)
3. If the event doesn't exist in Mobilizon, it creates it using the GraphQL API
4. If the event already exists in Mobilizon, it updates it
5. Information about synchronized events is stored in the `synced_events.json` file

## Running in Docker

You can also run the project in a Docker container:

```bash
# Build the image
docker build -t kronos-mobilizon .

# Run the container
docker run -e DISCORD_TOKEN=your_discord_token \
           -e MOBILIZON_ENABLED=true \
           -e MOBILIZON_API_URL=https://your-mobilizon-instance.org/api \
           -e MOBILIZON_TOKEN=your_mobilizon_api_token \
           -v ./events:/app/events \
           kronos-mobilizon
```

## Troubleshooting

If you encounter integration issues, check the bot logs. All errors related to Mobilizon integration will be logged with the `ERROR` prefix and will contain detailed information about the problem.

Common issues:
- Invalid Mobilizon token
- Lack of permissions to create events
- Errors in event data (e.g., invalid dates)

## Limitations and Extensions

Current implementation has several limitations:
- Does not handle event deletion (if an event is deleted from Discord, it will remain in Mobilizon)
- Does not synchronize participant lists
- Handles only basic event fields

Possible extensions:
- Two-way synchronization (events from Mobilizon -> Discord)
- Handling of recurring events
- Participant list synchronization