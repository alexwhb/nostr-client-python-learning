import asyncio
import json
import ssl
import certifi
import websockets
from dotenv import load_dotenv
from nostr.event import Event, EventKind
from nostr.filter import Filters, Filter
from nostr.key import PrivateKey
from nostr.message_type import ClientMessageType
import os

async def send_event(relay: str, event_content: str, private_key: PrivateKey) -> None:
    """
    Sends a Kind 1 (text note) event to a specified Nostr relay.

    Parameters:
        relay (str): The WebSocket URL of the Nostr relay (e.g., "wss://relay.example.com").
        event_content (str): The content of the event, such as a message or note.
        private_key (PrivateKey): The private key used to sign the event. The corresponding
                                  public key will be included in the event.

    Notes:
        - Kind 1 events are used for broadcasting text notes or general messages.
        - The private key must be an instance of `PrivateKey` from the `nostr` library.
    """
    event = Event(private_key.public_key.hex(), event_content)
    private_key.sign_event(event)

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    async with websockets.connect(relay, ssl=ssl_context) as websocket:
        await websocket.send(event.to_message())
        print(f"Sent event: {event}")

        response = await websocket.recv()
        print(f"Received response: {response}")


async def request_event_deletion(relay: str, private_key: PrivateKey, event_id: str) -> None:
    """
    Sends a Kind 5 (deletion) event to request the deletion of a specific event.

    Parameters:
        relay (str): The WebSocket URL of the Nostr relay (e.g., "wss://relay.example.com").
        private_key (PrivateKey): The private key used to sign the deletion request.
        event_id (str): The hex ID of the event to be deleted.

    Notes:
        - Kind 5 events are used to notify relays and clients to delete or ignore the specified event.
        - Only the original author (using their private key) can issue a valid deletion request.
        - Relays and clients are not guaranteed to honor deletion requests.
    """
    event = Event(private_key.public_key.hex(), "", kind=5, tags=[["e", event_id]])
    private_key.sign_event(event)

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    async with websockets.connect(relay, ssl=ssl_context) as websocket:
        await websocket.send(event.to_message())
        print(f"Sent event: {event}")

        response = await websocket.recv()
        print(f"Received response: {response}")


async def query_all_events(relay: str) -> None:
    """
    Subscribes to all events from a specified Nostr relay.

    WARNING!!! THIS SHOULD ONLY BE USED ON RELAYS THAT YOU OWN !!! THIS WILL FETCH EVERYTHING ON A RELAY

    Parameters:
        relay (str): The WebSocket URL of the Nostr relay (e.g., "wss://relay.example.com").

    Notes:
        - This function sends a subscription request for all events with no filters applied.
        - It prints received events to the console and terminates upon receiving the first matching event.
    """
    subscription_id = "test-subscription-id"
    request = ["REQ", "all_events", {}]

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    async with websockets.connect(relay, ssl=ssl_context) as websocket:
        await websocket.send(json.dumps(request))
        print(f"Sent subscription request: {request}")

        while True:
            response = await websocket.recv()
            event = json.loads(response)
            print(f"Received event: {event}")
            if event[0] == "EVENT" and event[1] == subscription_id:
                print(f"Received event: {event[2]}")
                break


async def query_kind_0(relay: str, pub_key: str) -> None:
    """
    Queries Kind 0 (set metadata) events for a specific public key.

    Parameters:
        relay (str): The WebSocket URL of the Nostr relay (e.g., "wss://relay.example.com").
        pub_key (str): The hex-encoded public key (not npub format) to filter events by.

    Notes:
        - Kind 0 events are used to update user metadata, such as profile information.
        - The public key must be in its hex-encoded form.
        - Clients typically use these events to display user profiles or other metadata.
    """
    filters = Filters([Filter(authors=[pub_key], kinds=[EventKind.SET_METADATA])])
    subscription_id = "test-subscription-id"

    request = [ClientMessageType.REQUEST, subscription_id]
    request.extend(filters.to_json_array())

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    async with websockets.connect(relay, ssl=ssl_context) as websocket:
        await websocket.send(json.dumps(request))
        print(f"Sent subscription request: {request}")
        while True:
            response = await websocket.recv()
            event = json.loads(response)
            if event[0] == "EVENT" and event[1] == subscription_id:
                print(f"Received event: {event[2]}")
                break


async def query_kind_1(relay: str, pub_key: str) -> None:
    """
    Queries Kind 1 (text note) events for a specific public key.

    Parameters:
        relay (str): The WebSocket URL of the Nostr relay (e.g., "wss://relay.example.com").
        pub_key (str): The hex-encoded public key (not npub format) to filter events by.

    Notes:
        - Kind 1 events are used for general messages or text notes.
        - The public key must be in its hex-encoded form.
        - Clients typically use these events to display user messages or notes.
    """
    filters = Filters([Filter(authors=[pub_key], kinds=[EventKind.TEXT_NOTE])])
    subscription_id = "test-subscription-id"
    request = [ClientMessageType.REQUEST, subscription_id]
    request.extend(filters.to_json_array())

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    async with websockets.connect(relay, ssl=ssl_context) as websocket:
        await websocket.send(json.dumps(request))
        while True:
            response = await websocket.recv()
            event = json.loads(response)
            if event[0] == "EVENT" and event[1] == subscription_id:
                print(f"Received event: {event[2]}")
                break


if __name__ == "__main__":
    load_dotenv()
    private_key = PrivateKey.from_nsec(os.getenv('NOSTR_PRIVATE_KEY'))
    relay_url = os.getenv('NOSTR_RELAY_URL')

    # asyncio.run(send_event(relay_url, "Hello this is a big test", private_key))

    asyncio.run(query_all_events(relay_url))
    # asyncio.run(query_event(relay_url, "06c66b81c82d96a7b73b396fd7364884630f147ba853fe3a208a61a608d9ac59"))

    # asyncio.run(query_kind_0(relay_url,"06c66b81c82d96a7b73b396fd7364884630f147ba853fe3a208a61a608d9ac59"))
    # asyncio.run(query_kind_1(relay_url,"32c391f28e4caff0031c1983e7ee48bdffd29d585b947b980c5de79593d83ce7" ))

    # asyncio.run(request_event_deletion(relay_url, private_key, "488b724d49af9d48f66f1a000e1535a7d23748b0a1de9be19bb13bbc86ae8c20"))
