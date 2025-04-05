# mobilizon_integration.py

import os
import logging
import json
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from datetime import datetime

class MobilizonIntegration:
    def __init__(self):
        # Mobilizon configuration
        self.mobilizon_url = os.getenv("MOBILIZON_API_URL", "https://mobilizacja.pl/api")
        self.mobilizon_token = os.getenv("MOBILIZON_TOKEN")
        
        # Initialize GraphQL transport
        self.transport = AIOHTTPTransport(
            url=self.mobilizon_url,
            headers={"Authorization": f"Bearer {self.mobilizon_token}"}
        )
        
        # Initialize GraphQL client
        self.client = Client(transport=self.transport, fetch_schema_from_transport=True)
        
        # Dictionary to track synchronized events
        self.synced_events = {}
        self.load_synced_events()
        
        # Logger configuration
        self.logger = logging.getLogger("mobilizon_integration")
    
    def load_synced_events(self):
        """Loads information about already synchronized events from JSON file"""
        try:
            with open("synced_events.json", "r") as f:
                self.synced_events = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.synced_events = {}
    
    def save_synced_events(self):
        """Saves information about synchronized events to JSON file"""
        with open("synced_events.json", "w") as f:
            json.dump(self.synced_events, f)
    
    async def create_or_update_event(self, discord_event, start_time, end_time):
        """Creates or updates an event in Mobilizon"""
        discord_id = str(discord_event.id)
        
        # Check if the event has already been synchronized
        if discord_id in self.synced_events:
            # Update existing event
            return await self.update_event(discord_event, start_time, end_time)
        else:
            # Create new event
            return await self.create_event(discord_event, start_time, end_time)
    
    async def create_event(self, discord_event, start_time, end_time):
        """Creates a new event in Mobilizon"""
        self.logger.info(f"Creating event in Mobilizon: {discord_event.name}")
        
        # Format dates in ISO format for Mobilizon
        begins_at = start_time.isoformat()
        ends_at = end_time.isoformat() if end_time else None
        
        # Prepare address/location
        address = {
            "description": discord_event.location or "Online"
        }
        
        # GraphQL mutation to create event
        create_event_mutation = gql("""
        mutation CreateEvent(
            $title: String!,
            $description: String!,
            $beginsAt: DateTime!,
            $endsAt: DateTime,
            $address: AddressInput,
            $visibility: EventVisibility!,
            $organizerActorId: ID!,
            $categoryId: ID,
            $tags: [String!]
        ) {
            createEvent(
                title: $title,
                description: $description,
                beginsAt: $beginsAt,
                endsAt: $endsAt,
                address: $address,
                visibility: $visibility,
                organizerActorId: $organizerActorId,
                categoryId: $categoryId,
                tags: $tags
            ) {
                id
                title
                url
            }
        }
        """)
        
        # Get actor ID (organizer)
        organizer_id = await self.get_default_actor_id()
        
        # Execute query
        try:
            variables = {
                "title": discord_event.name,
                "description": discord_event.description or "",
                "beginsAt": begins_at,
                "endsAt": ends_at,
                "address": address,
                "visibility": "PUBLIC",  # Public by default
                "organizerActorId": organizer_id,
                "tags": ["hs3", "hackerspace"]
            }
            
            result = await self.client.execute_async(
                create_event_mutation,
                variable_values=variables
            )
            
            # Save information about synchronized event
            if "createEvent" in result and result["createEvent"]:
                mobilizon_event = result["createEvent"]
                self.synced_events[discord_id] = {
                    "mobilizon_id": mobilizon_event["id"],
                    "mobilizon_url": mobilizon_event["url"],
                    "last_updated": datetime.now().isoformat()
                }
                self.save_synced_events()
                
                self.logger.info(f"Event created successfully: {mobilizon_event['url']}")
                return mobilizon_event
            
            self.logger.error(f"Failed to create event: {result}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error during event creation: {e}")
            return None
    
    async def update_event(self, discord_event, start_time, end_time):
        """Updates an existing event in Mobilizon"""
        discord_id = str(discord_event.id)
        
        if discord_id not in self.synced_events:
            self.logger.error(f"Attempt to update non-existent event: {discord_event.name}")
            return None
        
        mobilizon_id = self.synced_events[discord_id]["mobilizon_id"]
        self.logger.info(f"Updating event in Mobilizon: {discord_event.name}")
        
        # Format dates in ISO format for Mobilizon
        begins_at = start_time.isoformat()
        ends_at = end_time.isoformat() if end_time else None
        
        # Prepare address/location
        address = {
            "description": discord_event.location or "Online"
        }
        
        # GraphQL mutation to update event
        update_event_mutation = gql("""
        mutation UpdateEvent(
            $eventId: ID!,
            $title: String!,
            $description: String!,
            $beginsAt: DateTime!,
            $endsAt: DateTime,
            $address: AddressInput,
            $tags: [String!]
        ) {
            updateEvent(
                eventId: $eventId,
                title: $title,
                description: $description,
                beginsAt: $beginsAt,
                endsAt: $endsAt,
                address: $address,
                tags: $tags
            ) {
                id
                title
                url
            }
        }
        """)
        
        # Execute query
        try:
            variables = {
                "eventId": mobilizon_id,
                "title": discord_event.name,
                "description": discord_event.description or "",
                "beginsAt": begins_at,
                "endsAt": ends_at,
                "address": address,
                "tags": ["hs3", "hackerspace"]
            }
            
            result = await self.client.execute_async(
                update_event_mutation,
                variable_values=variables
            )
            
            # Update information about synchronized event
            if "updateEvent" in result and result["updateEvent"]:
                mobilizon_event = result["updateEvent"]
                self.synced_events[discord_id]["last_updated"] = datetime.now().isoformat()
                self.save_synced_events()
                
                self.logger.info(f"Event updated successfully: {mobilizon_event['url']}")
                return mobilizon_event
            
            self.logger.error(f"Failed to update event: {result}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error during event update: {e}")
            return None
    
    async def get_default_actor_id(self):
        """Gets the ID of the default actor (used as event organizer)"""
        get_actors_query = gql("""
        query {
            loggedUser {
                actors {
                    id
                    preferredUsername
                    name
                }
            }
        }
        """)
        
        try:
            result = await self.client.execute_async(get_actors_query)
            actors = result.get("loggedUser", {}).get("actors", [])
            
            if actors:
                # Use the first available actor
                return actors[0]["id"]
            
            self.logger.error("No actors found for the account")
            return None
            
        except Exception as e:
            self.logger.error(f"Error while fetching actors: {e}")
            return None