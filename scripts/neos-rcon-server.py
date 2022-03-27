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

import threading, queue

cmd_q = queue.Queue()
resp_q = queue.Queue()

logging.basicConfig(level=logging.INFO)

def cleanWorldReply(focused_world):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    focused_world = ansi_escape.sub('', focused_world)
    return focused_world

def cleanReply(reply):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    ansi_escape = ansi_escape.sub('', reply)
    reply = ansi_escape.split("\n",1)
    reply = reply[1]
    reply = reply.replace('\t', ' ')
    reply = reply[:reply.rfind('\n')]
    return reply

from time import sleep

def neosvr_worker(args):
    container_id = args.container_id[0]
    starting = True
    while True:
        if starting:
            try:
                logging.info("Trying attaching to docker {}...".format(container_id))
                child = pexpect.spawnu("docker attach {}".format(container_id))
                child.sendline()
                i = child.expect_exact([">\x1b[37m\x1b[6n"])
                starting = False
            except Exception as e:
                if 'No such container' in str(e):
                    logging.error('Container not found')
                    sleep(1)
                    continue
                elif 'dial unix /var/run/docker.sock: connect: permission denied' in str(e):
                    logging.error('Docker permission denied')
                elif "buffer (last 100 chars): ''" in str(e):
                    sleep(1)
                    continue
                elif 'Timeout exceeded' in str(e):
                    sleep(1)
                    continue
                else:
                    logging.error(e)
                    sys.exit(1)
            logging.info('Attached to docker {}'.format(container_id))

        logging.info('waiting for command now')

        cmd = cmd_q.get()
        logging.info(cmd)
        logging.debug('oiki')
        child.sendline()
        date = datetime.datetime.now().isoformat()
        focused_world = ''
        try:
            i = child.expect_exact([">\x1b[37m\x1b[6n"])
            if i == 0:
                logging.info("running command: " + cmd)
                child.sendline(cmd)
                if cmd == 'shutdown':
                    starting = True
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
                resp = focused_world + "," + date + " - " + focused_world + " > " + cmd + "\n"  + reply
                resp_q.put(resp)
            else:
                logging.error("Cant get a world reply")
        except pexpect.exceptions.EOF:
            starting = True
            resp = focused_world + "," + date + " - " + focused_world + " > " + cmd + "\nSomething goes wrong, try again"
            resp_q.put(resp)
            continue
        cmd_q.task_done()

async def websocket_consumer(websocket, message, access_code):
    try:
        message = message.split(",")
        incoming_access_code = message[0]
        incoming_command = message[1]
        logging.info("incoming: {}".format(message))
    except:
        logging.error("malformed message from websocket")

    if incoming_access_code == access_code:
        logging.info("authenticated")

        cmd_q.put(incoming_command)
        resp = resp_q.get()
        await websocket.send(resp)

    elif incoming_access_code != access_code:
        logging.error("invalid access code: " + incoming_access_code)
        await websocket.send("Websocket: Invalid access code")
    else:
        logging.error("error parsing incoming message")
        await websocket.send("Websocket: Server error. Malformed command sent?")

async def websocket_consumer_handler(websocket, access_code):
    while True:
        async for message in websocket:
            await websocket_consumer(websocket, message,access_code)

async def websocket_handler(websocket, path, args):
    try:
        with open(args.secret_file) as f:
            access_code = f.read()
            access_code = access_code.split('\n', 1)[0]
    except:
        logging.error(str(e))
    websocket_consumer_task = asyncio.ensure_future(websocket_consumer_handler(websocket, access_code))
    done, pending = await asyncio.wait(
        [websocket_consumer_task],
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

    cmd_q.join()
    resp_q.join()
    bound_handler = functools.partial(websocket_handler, args=args)
    async with websockets.serve(bound_handler, "0.0.0.0", 8765, ssl=ssl_context):
        await stop



parser = argparse.ArgumentParser(
    description='RCon server arguments',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument(
    '--nosecure', action='store_true',
    help='disabled secure websocket (only use if you know)'
)
parser.add_argument(
    '--secret_file', default='accesscode.txt',
    help='path of the file where the access code is, search by default next ' \
        'to the script'
)
parser.add_argument(
    'container_id', nargs=1, help='neosvr docker container id'
)

args = parser.parse_args()

# Turn-on the worker thread.
threading.Thread(target=worker, args=(args,), daemon=True).start()

loop = asyncio.get_event_loop()

# The stop condition is set when receiving SIGTERM.
stop = loop.create_future()
loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

loop.run_until_complete(rcon_server(stop, args))
