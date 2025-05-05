import asyncio
import websockets
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
import hashlib
from json import dumps, loads
import re
import aiohttp
import time
from datetime import datetime

class Group:
    allgroups = {}
    def __init__(self, name):
        self.name = name
        self.typing = set()
        self.users = {} # user.ws: user
        self.userids = {}
        Group.allgroups[name] = self
    
    async def rawpost(self, msg):
        await asyncio.gather(*(c.send(msg) for c in self.users.keys()))
    
    async def post(self, user, data):
        if user in self.typing: self.typing.remove(user)
        data["typing"] = [t.uid for t in self.typing]
        await self.rawpost(dumps(data))
    
    async def join(self, user):
        self.users[user.ws] = user
        self.userids[user.uid] = user
        await self.rawpost(dumps({"type": "join", "uid": user.uid}))
        
    async def postusercount(self):
        await self.rawpost(dumps({"type": "user_count", "count": len(self.users)}))
    
    async def pop(self, user):
        self.users.pop(user.ws)
        self.userids.pop(user.uid)
        await self.postusercount()
        
class User:
    def __init__(self, ws):
        self.uid = hashlib.md5(ws.remote_address[0].encode()).hexdigest()
        self.ws = ws
        self.messagecount = 0
        self.typingtimestamp = None
        self.group = None

    def updatetyping(self, group):
        removes = set()
        for t in group.typing:
            if t == self or (t.typingtimestamp and time.time() - t.typingtimestamp > 6):
                removes.add(t)
        group.typing -= removes
        self.typingtimestamp = None

    def loadmsg(self, msg, group):
        data = loads(msg)
        ty = data["type"]
        if ty == 'typing':
            group.typing.add(self)
            self.typingtimestamp = time.time()
            return
        elif ty == 'chat':
            self.messagecount += 1
        data["uid"] = self.uid
        data["messagecount"] = self.messagecount
        return data
    
    async def connect(self, group):
        await group.join(self)
        self.group = group

Group("/")
async def ws_handler(ws, path):
    u = User(ws)
    g = None
    path = ws.path
    if path not in Group.allgroups: g = Group(path)
    else: g = Group.allgroups[path]
    await asyncio.gather(ws.send(dumps({"type": "uid", "uid": u.uid})))
    await u.connect(g)
    try:
        await g.postusercount()
        async for msg in ws:
            data = u.loadmsg(msg, g)
            if not data: continue
            u.updatetyping(g)
            await g.post(u, data)
    finally:
        print("WebSocket connection closed.")
        await g.pop(u)


class SinglePageHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.path = '/index.html'
        return super().do_GET()

def start_http():
    port = 4242
    httpd = HTTPServer(('0.0.0.0', port), SinglePageHandler)
    print("Running on port", port)
    httpd.serve_forever()
    
async def start_websocket():
    try:
        async with websockets.serve(ws_handler, "0.0.0.0", 8765):
            print("WebSocket server running on ws://0.0.0.0:8765")
            await asyncio.Future()  # run forever
    except Exception as e:
        print(f"Error in WebSocket server: {e}")
        await asyncio.sleep(5)
        await start_websocket()

if __name__ == "__main__":
    threading.Thread(target=start_http, daemon=True).start()
    asyncio.run(start_websocket())
