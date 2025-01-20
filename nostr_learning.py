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

async def send_event(relay, event_content, private_key):
    event = Event(private_key.public_key.hex(), event_content)
    private_key.sign_event(event)

    # Use certifi's certificate bundle to handle SSL verification
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # Connect to the relay and send the event
    async with websockets.connect(relay, ssl=ssl_context) as websocket:
        await websocket.send(event.to_message())
        print(f"Sent event: {event}")

        # Await for acknowledgment or response (optional)
        response = await websocket.recv()
        print(f"Received response: {response}")


async def request_event_deletion(relay, private_key, event_id):
    event = Event(private_key.public_key.hex(), "", kind=5, tags=[["e", event_id]])
    private_key.sign_event(event)

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # Connect to the relay and send the event
    async with websockets.connect(relay, ssl=ssl_context) as websocket:
        await websocket.send(event.to_message())
        print(f"Sent event: {event}")

        # Await for acknowledgment or response (optional)
        response = await websocket.recv()
        print(f"Received response: {response}")


async def query_all_events(relay):
    subscription_id = "test-subscription-id"
    request = ["REQ", "all_events", {}]

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # Connect to the relay and send the subscription request
    async with websockets.connect(relay, ssl=ssl_context) as websocket:
        await websocket.send(json.dumps(request))
        print(f"Sent subscription request: {request}")

        while True:
            # Wait for events matching the query
            response = await websocket.recv()
            event = json.loads(response)
            print(f"Received event: {event}")
            if event[0] == "EVENT" and event[1] == subscription_id:
                print(f"Received event: {event[2]}")
                break

async def query_kind_0(relay, pub_key):
    filters = Filters([Filter(authors=[pub_key], kinds=[EventKind.SET_METADATA])])
    subscription_id = "test-subscription-id"

    request = [ClientMessageType.REQUEST, subscription_id]
    request.extend(filters.to_json_array())

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # Connect to the relay and send the subscription request
    async with websockets.connect(relay, ssl=ssl_context) as websocket:
        await websocket.send(json.dumps(request))
        print(f"Sent subscription request: {request}")
        while True:
            # Wait for events matching the query
            response = await websocket.recv()
            event = json.loads(response)
            if event[0] == "EVENT" and event[1] == subscription_id:
                print(f"Received event: {event[2]}")
                break

async def query_kind_1(relay, pub_key):
    filters = Filters([Filter(authors=[pub_key], kinds=[EventKind.TEXT_NOTE])])
    subscription_id = "test-subscription-id"
    request = [ClientMessageType.REQUEST, subscription_id]
    request.extend(filters.to_json_array())

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # Connect to the relay and send the subscription request
    async with websockets.connect(relay, ssl=ssl_context) as websocket:
        await websocket.send(json.dumps(request))
        while True:
            # Wait for events matching the query
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
