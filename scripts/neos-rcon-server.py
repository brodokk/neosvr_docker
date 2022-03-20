#!/bin/python3

import signal
import asyncio
import websockets
import ssl
import datetime
import sys
import pexpect
import re
import argparse
import functools
import logging

logging.basicConfig(level=logging.INFO)

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
        logging.info("incoming: ", message)
    except:
        logging.error("malformed message from websocket")

    if incoming_access_code == access_code:
        logging.info("authenticated")

        child.sendline()
        i = child.expect_exact([">\x1b[37m\x1b[6n"])
        if i == 0:
            logging.info("running command: " + incoming_command)
            child.sendline(incoming_command)
        else:
            logging.error("Cant run command")

        i = child.expect_exact([">\x1b[37m\x1b[6n"])
        if i == 0:
            reply = cleanReply(child.before)
        else:
           logging.error("Cant get reply")

        child.sendline()
        i = child.expect_exact([">\x1b[37m\x1b[6n"])
        if i == 0:
            focused_world = cleanWorldReply(child.before)
            await websocket.send(focused_world + "," + reply)
        else:
            logging.error("Cant get a world reply")

    elif incoming_access_code != access_code:
        logging.error("invalid access code: " + incoming_access_code)
        await websocket.send("Websocket: Invalid access code")
    else:
        logging.error("error parsing incoming message")
        await websocket.send("Websocket: Server error. Malformed command sent?")

async def consumer_handler(websocket, child, access_code):
    while True:
        async for message in websocket:
            await consumer(websocket, message, child, access_code)

async def handler(websocket, path, args):
    logging.info("docker attach {}".format(args.container_id))
    child = pexpect.spawnu("docker attach {}".format(args.container_id))
    child.sendline()
    try:
        i = child.expect_exact([">\x1b[37m\x1b[6n"])
    except Exception as e:
        if 'No such container' in str(e):
            logging.error('Container not found')
        elif 'dial unix /var/run/docker.sock: connect: permission denied' in str(e):
            logging.error('Docker permission denied')
        else:
            logging.error(e)
        sys.exit(1)

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

async def rcon_server(stop, args):
    if args.nosecure:
        ssl_context = None
    else:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_cert = "cert.pem"
        ssl_key = "privkey.pem"
        ssl_context.load_cert_chain(ssl_cert, keyfile=ssl_key)

    bound_handler = functools.partial(handler, args=args)
    #async with websockets.serve(handler, "0.0.0.0", 8765):
    async with websockets.serve(bound_handler, "0.0.0.0", 8765, ssl=ssl_context):
        await stop



parser = argparse.ArgumentParser(description='RCon server arguments')
parser.add_argument('--nosecure', action='store_true',
                    help='disabled secure websocket (only use if you know)')
parser.add_argument('container_id', nargs=1)

args = parser.parse_args()

loop = asyncio.get_event_loop()

# The stop condition is set when receiving SIGTERM.
stop = loop.create_future()
loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

loop.run_until_complete(rcon_server(stop, args))
