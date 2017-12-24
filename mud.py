#Additional ideas:
#   * More rooms to explore
#   * Monsters to fight
#   * Loot to collect
#   * Saving players accounts between sessions
#   * A password login
#   * A money system
#   * A shop from which to buy items
#   * A bank to store items and money
import socket, select, time, sys
class MudServer(object):
    class _Client(object):
        socket = None
        address = ""
        buffer = ""
        lastcheck = 0
        def __init__(self, socket, address, buffer, lastcheck):
            self.socket = socket
            self.address = address
            self.buffer = buffer
            self.lastcheck = lastcheck
    _EVENT_NEW_PLAYER = 1
    _EVENT_PLAYER_LEFT = 2
    _EVENT_COMMAND = 3
    _READ_STATE_NORMAL = 1
    _READ_STATE_COMMAND = 2
    _READ_STATE_SUBNEG = 3
    _TN_INTERPRET_AS_COMMAND = 255
    _TN_ARE_YOU_THERE = 246
    _TN_WILL = 251
    _TN_WONT = 252
    _TN_DO = 253
    _TN_DONT = 254
    _TN_SUBNEGOTIATION_START = 250
    _TN_SUBNEGOTIATION_END = 240
    _listen_socket = None
    _clients = {}
    _nextid = 0
    _events = []
    _new_events = []
    def __init__(self):
        self._clients = {}
        self._nextid = 0
        self._events = []
        self._new_events = []
        self._listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        socketOpen = self._listen_socket.connect_ex(('127.0.0.1',80))
        if socketOpen == 0:
            self._listen_socket.bind(("0.0.0.0", 8000))
            self._listen_socket.setblocking(False)
            self._listen_socket.listen(1)
        else:
            print("Port 8000 not open. Shutting down.")
    def update(self):
        self._check_for_new_connections()
        self._check_for_disconnected()
        self._check_for_messages()
        self._events = list(self._new_events)
        self._new_events = []
    def get_new_players(self):
        retval = []
        for ev in self._events:
            if ev[0] == self._EVENT_NEW_PLAYER:
                retval.append(ev[1])
        return retval
    def get_disconnected_players(self):
        retval = []
        for ev in self._events:
            if ev[0] == self._EVENT_PLAYER_LEFT:
                retval.append(ev[1])
        return retval
    def get_commands(self):
        retval = []
        for ev in self._events:
            if ev[0] == self._EVENT_COMMAND:
                retval.append((ev[1], ev[2], ev[3]))
        return retval
    def send_message(self, to, message):
        self._attempt_send(to, message+"\n\r")
    def shutdown(self):
        for cl in self._clients.values():
            cl.socket.shutdown()
            cl.socket.close()
        self._listen_socket.close()
    def _attempt_send(self, clid, data):
        data = unicode(data, "latin1")
        try:
            self._clients[clid].socket.sendall(bytearray(data, "latin1"))
        except KeyError:
            pass
        except socket.error:
            self._handle_disconnect(clid)
    def _check_for_new_connections(self):
        rlist, wlist, xlist = select.select([self._listen_socket], [], [], 0)
        if self._listen_socket not in rlist:
            return
        joined_socket, addr = self._listen_socket.accept()
        joined_socket.setblocking(False)
        self._clients[self._nextid] = MudServer._Client(joined_socket, addr[0],"", time.time())
        self._new_events.append((self._EVENT_NEW_PLAYER, self._nextid))
        self._nextid += 1
    def _check_for_disconnected(self):
        for id, cl in list(self._clients.items()):
            if time.time() - cl.lastcheck < 5.0:
                continue
            self._attempt_send(id, "\x00")
            cl.lastcheck = time.time()
    def _check_for_messages(self):
        for id, cl in list(self._clients.items()):
            rlist, wlist, xlist = select.select([cl.socket], [], [], 0)
            if cl.socket not in rlist:
                continue
            try:
                data = cl.socket.recv(4096).decode("latin1")
                message = self._process_sent_data(cl, data)
                if message:
                    message = message.strip()
                    command, params = (message.split(" ", 1) + ["", ""])[:2]
                    self._new_events.append((self._EVENT_COMMAND, id,command, params))
            except socket.error:
                self._handle_disconnect(id)
    def _handle_disconnect(self, clid):
        del(self._clients[clid])
        self._new_events.append((self._EVENT_PLAYER_LEFT, clid))
    def _process_sent_data(self, client, data):
        message = None
        state = self._READ_STATE_NORMAL
        for c in data:
            if state == self._READ_STATE_NORMAL:
                if ord(c) == self._TN_INTERPRET_AS_COMMAND:
                    state = self._READ_STATE_COMMAND
                elif c == "\n":
                    message = client.buffer
                    client.buffer = ""
                elif c == "\x08":
                    client.buffer = client.buffer[:-1]
                else:
                    client.buffer += c
            elif state == self._READ_STATE_COMMAND:
                if ord(c) == self._TN_SUBNEGOTIATION_START:
                    state = self._READ_STATE_SUBNEG
                elif ord(c) in (self._TN_WILL, self._TN_WONT, self._TN_DO,
                                self._TN_DONT):
                    state = self._READ_STATE_COMMAND
                else:
                    state = self._READ_STATE_NORMAL
            elif state == self._READ_STATE_SUBNEG:
                if ord(c) == self._TN_SUBNEGOTIATION_END:
                    state = self._READ_STATE_NORMAL
        return message
def giveDungeon(id):
    mud.send_message(id, "Great; thanks! Nice to have you on board! I'm just gonna go ahead and put the dungeon in your warps.")
    players[id]['warps']['dungeon'] = 'Dungeon'
def refQuest(id): mud.send_message(id, "Got it. Well, if you ever change your mind, you know where I am.")
def buySword(id):
    if players[id]["money"] >= 50:
        players[id]["weapon"] = weapons["Wooden"]
        players[id]["money"] -= 50
        mud.send_message(id, "You bought a wooden sword for 50 gold!")
    else: mud.send_message(id, "You can't afford that item! You need 50 gold!")
rooms = {
    "Tavern": {
        "description": "You're in a cozy tavern warmed by an open fire.",
        "exits": {"outside": "Village"},
        "npcs": {"Adventurer": {"text": "Hey! If you're not busy, I have a quest for you! Do you want to take it? It's really simple. You just need to go to a dungeon and beat the boss.", "replies": {"yes": giveDungeon, "no": refQuest}}},
        "objects": {"fireplace": "You see a roaring, burning fire in the fireplace."},
        "items": {},
        "enemies": [],
    },
    "Village": {
        "description": "You're standing in a small village. It's raining.",
        "exits": {"inside": "Tavern", "shop": "Shop"},
        "npcs": {"Phil": {"text": "Hello! Nice to meet you!"}},
        "objects": {"well": "You see a full well that goes very deep in the ground."},
        "items": {},
        "enemies": [],
    },
    "Shop": {
        "description": "You're in a somewhat small shop with varied items on display.",
        "exits": {"outside": "Village"},
        "npcs": {"Shopkeeper": {"text": "Do you want to buy this sword for sale?", "replies": {"yes": buySword}}},
        "objects": {"sword": "You see a wooden sword on display in a frame for sale."},
        "items": {},
        "enemies": [],
    },
    "Dungeon": {
        "description": "You're in a large, stone building with a few cracks in the wall.",
        "exits": {"door": "Boss Room"},
        "npcs": {},
        "objects": {"sword": "You see a large, rusty sword broken in half."},
        "items": {"gold": 50},
        "enemies": [],
    },
    "Boss Room": {
        "description": "You're in a small room with cobwebs all over.",
        "exits": {"door": "Dungeon"},
        "npcs": {},
        "objects": {"rat corpse": "You see the body of a dead rat with bite marks."},
        "items": {},
        "enemies": [{"name": "rat", "health": 3, "armor": 0, "attack": 1, "xp": 1}],
    }
}
armors = {"Cloth": 0,"Leather": 1,"Chain": 2,"Iron": 3,"Steel": 5}
shields = {"None": 0,"Wooden": 1,"Reinforced": 2,"Iron": 3,"Steel": 5}
weapons = {"None": 0,"Wooden": 1,"Stone": 2,"Iron": 3,"Steel": 5}
helmets = {"None": 0,"Leather": 1,"Chain": 2,"Iron": 3,"Steel": 5}
items = {"warpCrystal": 0}
players = {}
mud = MudServer()
while True:
    mud.update()
    for id in mud.get_new_players():
        players[id] = {
            "health": 5,
            "armor": 0,
            "attack": 0,
            "xp": 0,
            "lv": 0,
            "name": None,
            "room": None,
            "weapon": weapons["None"],
            "shield": shields["None"],
            "helmet": helmets["None"],
            "armor": armors["Cloth"],
            "items": {},
            "money": 0,
            "lastNpcTalked": None,
            "warps": {},
        }
        mud.send_message(id, "What is your name?")
    for id in mud.get_disconnected_players():
        if id not in players:
            continue
        for pid, pl in players.items():
            mud.send_message(pid, "{} quit the game".format(players[id]["name"]))
        del(players[id])
    for id, command, params in mud.get_commands():
        if id not in players:
            continue
        if players[id]["name"] is None:
            players[id]["name"] = command
            players[id]["room"] = "Tavern"
            players[id]["items"]["warpCrystal"] = items["warpCrystal"]
            mud.send_message(id, "You found a Warp Crystal in the Tavern!")
            players[id]["warps"]["tavern"] = "Tavern"
            for pid, pl in players.items():
                mud.send_message(pid, "{} entered the game".format(players[id]["name"]))
            mud.send_message(id, "Welcome to the game, {}. ".format(players[id]["name"]) + "Type 'help' for a list of commands. Have fun!")
            mud.send_message(id, rooms[players[id]["room"]]["description"])
        elif command.lower() == "help":
            mud.send_message(id, "Commands:")
            mud.send_message(id, "  say <message>              - Says something out loud to everyone in your room, e.g. 'say Hello'")
            mud.send_message(id, "  look [object]              - Examines the surroundings or specified object, e.g. 'look' or 'look fireplace'")
            mud.send_message(id, "  go <exit>                  - Moves through the exit specified, e.g. 'go outside'")
            mud.send_message(id, "  me <message>               - Says text as if you performed an action, e.g. 'me laughs'")
            mud.send_message(id, "  interact [npc]             - Interacts with an NPC or lists all NPCs present, e.g. 'interact Bob'")
            mud.send_message(id, "  shout <message>            - Says something out loud to everyone, not just people in your room, e.g. 'shout Hello'")
            mud.send_message(id, "  whisper <player> <message> - Says something to only the specified player, e.g. 'whisper Bob What's up?'")
            mud.send_message(id, "  reply <message>            - Replies to the last NPC you talked to, e.g. 'reply Yes'")
            mud.send_message(id, "  warp [location]            - Warps you to a location or lists possible warps, e.g. 'warp home'")
        elif command == "say":
            for pid, pl in players.items():
                if players[pid]["room"] == players[id]["room"]:
                    mud.send_message(pid, "{} says: {}".format(players[id]["name"], params))
        elif command.lower() == "look" and params == "":
            mud.send_message(id, rooms[players[id]["room"]]["description"])
            playershere = []
            for pid, pl in players.items():
                if players[pid]["room"] == players[id]["room"]:
                    if players[pid]["name"] is not None:
                        playershere.append(players[pid]["name"])
            mud.send_message(id, "Players here: {}".format(", ".join(playershere)))
            mud.send_message(id, "Exits are: {}".format(", ".join(rooms[players[id]["room"]]["exits"])))
            mud.send_message(id, "Objects are: {}".format(", ".join(rooms[players[id]["room"]]["objects"])))
        elif command.lower() == "look" and params:
            if params in rooms[players[id]["room"]]["objects"]:
                mud.send_message(id, rooms[players[id]["room"]]["objects"][params])
            else:
                mud.send_message(id, "{} is not an object in the room.".format(params))
        elif command.lower() == "go":
            if params.lower() in rooms[players[id]["room"]]["exits"].keys():
                for pid, pl in players.items():
                    if players[pid]["room"] == players[id]["room"] and pid != id:
                        mud.send_message(pid, "{} left via exit '{}'".format(players[id]["name"], params.lower()))
                players[id]["room"] = rooms[players[id]["room"]]["exits"][params.lower()]
                for pid, pl in players.items():
                    if players[pid]["room"] == players[id]["room"] and pid != id:
                        mud.send_message(pid,"{} arrived via exit '{}'".format(players[id]["name"], params.lower()))
                mud.send_message(id, "You arrive at '{}'".format(players[id]["room"]))
            else:
                mud.send_message(id, "Unknown exit '{}'".format(params.lower()))
        elif command.lower() == "me":
            for pid, pl in players.items():
                mud.send_message(pid,"{} {}".format(players[id]["name"],params))
        elif command.lower() == "interact":
            if len(rooms[players[id]["room"]]["npcs"]) > 0:
                if params in rooms[players[id]["room"]]["npcs"]:
                    mud.send_message(id, "{} talks to you, saying, '{}'".format(params, rooms[players[id]["room"]]["npcs"][params]["text"]))
                    players[id]["lastNpcTalked"] = params
                elif params:
                    mud.send_message(id,"{} is not here! The NPCs here are {}.".format(params,", ".join(rooms[players[id]["room"]]["npcs"])))
                else:
                    mud.send_message(id,"The NPCs here are {}.".format(", ".join(rooms[players[id]["room"]]["npcs"])))
            else:
                mud.send_message(id,"There are no NPCs in your room!")
        elif command.lower() == "shout":
            for pid, pl in players.items():
                mud.send_message(pid, "{} shouts: {}".format(players[id]["name"], params))
        elif command.lower() == "whisper":
             target = params.split(" ", 1)[0]
             for pid, pl in players.items():
                 if players[pid]["name"] == target:
                     mud.send_message(pid, "{} whispers to you: {}".format(players[id]["name"], params.partition(' ')[2]))
        elif command.lower() == "leave":
            pass
        elif command.lower() == "reply":
            if players[id]["lastNpcTalked"] in rooms[players[id]["room"]]["npcs"]:
                print(rooms[players[id]["room"]]["npcs"])
                if params.lower() in rooms[players[id]["room"]]["npcs"]["replies"]:
                    rooms[players[id]["room"]]["npcs"]["replies"][params.lower()](id)
                else:
                    mud.send_message(id, "Potential replies are: {}".format(", ".join(rooms[players[id]["room"]]["npcs"]["replies"])))
            else:
                mud.send_message(id, "You haven't talked to anyone here recently!")
        elif command.lower() == "warp":
            if players[id]["items"]["warpCrystal"] == items["warpCrystal"]:
                if params != "":
                    if params.lower() in players[id]["warps"]:
                        players[id]["room"] = players[id]["warps"][params.lower()]
                        mud.send_message(id, "You warped to {}".format(params))
                    else:
                        mud.send_message(id, "That is not a warp! Use 'warp' to view all warps.")
                else:
                    mud.send_message(id, "Warps: {}".format(", ".join(players[id]["warps"])))
            else:
                mud.send_message(id, "You don't have a warp crystal!")
        elif command.lower() == "pickup":
            if params.lower() in rooms[players[id]["room"]]["items"].keys():
                if params.lower() == "gold":
                    players[id]["money"] += rooms[players[id]["room"]]["items"]["gold"]
                    mud.send_message(id, "You found gold! You now have {} gold!".format(players[id]["money"]))
                else:
                    players[id]["items"][params] = rooms[players[id]["room"]]["items"][params]
        else:
            mud.send_message(id, "Unknown command: '{}'".format(command))
