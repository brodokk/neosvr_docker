#!/bin/python3

import asyncio
import websockets
import ssl
import datetime
import sys
import pexpect
import re

def cleanWorldReply(focused_world):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    focused_world = ansi_escape.sub('', focused_world)
    return focused_world

def cleanReply(reply):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    ansi_escape = ansi_escape.sub('', reply)
    reply = ansi_escape.split("\n",1)[1]
    reply = reply.replace('\t', ' ')
    reply = reply[:reply.rfind('\n')]
    return reply

async def consumer(websocket, message, child, access_code):
    try:
        message = message.split(",")
        incoming_access_code = message[0]
        incoming_command = message[1]
        print("incoming: ", message)
    except:
        print("malformed message from websocket")

    if incoming_access_code == access_code:
        print("authenticated")

        child.sendline()
        i = child.expect_exact([">\x1b[37m\x1b[6n"])
        if i == 0:
            print("running command: " + incoming_command)
            child.sendline(incoming_command)
        else:
            print("error")

        i = child.expect_exact([">\x1b[37m\x1b[6n"])
        if i == 0:
            reply = cleanReply(child.before)
        else:
           print("error")

        child.sendline()
        i = child.expect_exact([">\x1b[37m\x1b[6n"])
        if i == 0:
            focused_world = cleanWorldReply(child.before)
            await websocket.send(focused_world + "," + reply)
        else:
            print("error")

    elif incoming_access_code != access_code:
        print("invalid access code: " + incoming_access_code)
        await websocket.send("Websocket: Invalid access code")
    else:
        print("error parsing incoming message")
        await websocket.send("Websocket: Server error. Malformed command sent?")

async def consumer_handler(websocket, child, access_code):
    while True:
        async for message in websocket:
            await consumer(websocket, message, child, access_code)

async def handler(websocket, path):
    child = pexpect.spawnu("docker attach e8364dae7321")
    child.sendline()
    i = child.expect_exact([">\x1b[37m\x1b[6n"])
    with open("accesscode.txt") as f:
        access_code = f.read()
        access_code = access_code.split('\n', 1)[0]
    consumer_task = asyncio.ensure_future(consumer_handler(websocket, child, access_code))
    done, pending = await asyncio.wait(
        [consumer_task],
        return_when=asyncio.ALL_COMPLETED,
    )

    for task in pending:
        task.cancel()

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_cert = "cert.pem"
ssl_key = "privkey.pem"
ssl_context.load_cert_chain(ssl_cert, keyfile=ssl_key)

start_server = websockets.serve(handler, '0.0.0.0', 8765, ssl=ssl_context)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
