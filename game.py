import argparse
import asyncio
import json
import os

from aiohttp import web

from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.rtcrtpsender import RTCRtpSender

import numpy
from av import VideoFrame

from screen import get_screen

import subprocess
import time
import xlib_helper

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WebRTC demo with eggnoggplus")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port for HTTP server (default: 8080)"
    )
    parser.add_argument(
        "--resolution", 
        default='normal',
        const='normal',
        nargs='?',
        choices=['normal', 'half', 'quarter', 'one-eighth'],
        help="Choose the resolution of the game"
    )

    args = parser.parse_args()


class GameTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        npa = numpy.array(get_screen())
        npa = npa[::quality, ::quality, ::]
        frame = VideoFrame.from_ndarray(npa)
        frame.pts = pts
        frame.time_base = time_base
        return frame

game_track = GameTrack()

def create_local_tracks():
    global game_track
    return game_track

def force_codec(pc, sender, forced_codec):
    kind = forced_codec.split("/")[0]
    codecs = RTCRtpSender.getCapabilities(kind).codecs
    transceiver = next(t for t in pc.getTransceivers() if t.sender == sender)
    transceiver.setCodecPreferences(
        [codec for codec in codecs if codec.mimeType == forced_codec]
    )


async def index(request):
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    content = open(os.path.join(ROOT, "client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("keydown"):
                xlib_helper.keyboard_down(message[7:])
            elif isinstance(message, str) and message.startswith("keyup"):
                xlib_helper.keyboard_up(message[5:])

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    # open media source
    video = create_local_tracks()

    if video:
        video_sender = pc.addTrack(video)

    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


pcs = set()

async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


if __name__ == "__main__":
    if args.resolution == 'one-eighth':
        quality = 8
    elif args.resolution == 'quarter':
        quality = 4
    elif args.resolution == 'half':
        quality = 2
    else:
        quality = 1

    ROOT = os.path.dirname(__file__)

    game = subprocess.Popen('./eggnoggplus')
    time.sleep(1)
    xlib_helper.init()
    time.sleep(1)

    quality = 1
    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)
    app.router.add_post("/offer", offer)
    web.run_app(app, host=args.host, port=args.port)
