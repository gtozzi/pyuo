#!/usr/bin/env python3

'''
Python Ultima Online text client (experiment)
Copyright (C) 2015-2016 Gabriele Tozzi

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
'''

import struct
import logging
try:
    import ipaddress
except:
	class ipaddress:
		def __init__(self,ip):
			self._ip=list(map(int,ip.split('.')))
		@property
		def packed(self):
			return struct.pack(b'!I', int.from_bytes(self._ip,'big'))
		@classmethod
		def ip_address(cls,ip):
			return cls(ip)
import time
import traceback

from . import net
from . import brain


class status:
	''' Decorator, checks that status is valid '''

	def __init__(self, status):
		self.status = status

	def __call__(self, f):
		def wrapper(*args):
			if args[0].status != self.status:
				raise StatusError("Status {} not valid, need {}".format(args[0].status, self.status))
			return f(*args)
		return wrapper


def logincomplete(f):
	''' Decorator, check that login procedure is complete '''
	def wrapper(client, *args, **kwargs):
		if not client.lc or client.status != 'game':
			raise StatusError("Must complete login procedure before calling this")
		return f(client, *args, **kwargs)
	return wrapper


class UOBject:
	''' Base class for an UO Object '''

	def __init__(self, client):
		## Logging instance
		self.log = logging.getLogger(self.__class__.__name__)
		## Client reference
		self.client = client
		
		## Unique serial number
		self.serial = None
		## Graphic ID
		self.graphic = None
		## Color ID
		self.color = None
		## X coordinate
		self.x = None
		## Y coordinate
		self.y = None
		## z coordinate
		self.z = None
		## Facing
		self.facing = None


class Item(UOBject):
	''' Represents an item in the world '''

	def __init__(self, client, pkt=None):
		super().__init__(client)

		## Number of items in the stack
		self.amount = 1
		## Status flags
		self.status = None

		if pkt is not None:
			self.update(pkt)

	def update(self, pkt):
		''' Update from packet '''
		if not isinstance(pkt, net.ObjectInfoPacket):
			raise ValueError("Expecting a DrawObjectPacket")
		self.serial = pkt.serial
		self.graphic = pkt.graphic
		self.amount = pkt.count
		self.x = pkt.x
		self.y = pkt.y
		self.z = pkt.z
		self.facing = pkt.facing
		self.color = pkt.color if pkt.color else 0
		self.status = pkt.flag

	def upgradeToContainer(self):
		''' Upgrade this item to a container '''
		self.__class__ = Container
		self.upgrade()

	def use(self):
		''' Uses the given item '''
		self.client.doubleClick(self)

	def __repr__(self):
		serial = hex(self.serial)
		graphic = hex(self.graphic)
		color = hex(self.color)
		return "{} Item {} graphic {} color {} at {},{},{} facing {}".format(
				self.amount, serial, graphic, color, self.x, self.y, self.z, self.facing )


class Container(Item):
	''' A special representation of item '''

	def __init__(self, client):
		super().__init__(client)
		self.upgrade()

	def upgrade(self):
		''' Called when an Item's class has just been changed to container '''

		## The Content, none if still not received
		self.content = None

	def addItem(self, pkt):
		''' Adds an item to container, from packet or dictionary '''
		if type(pkt) == dict:
			it = pkt
		elif isinstance(pkt, net.AddItemToContainerPacket):
			it = pkt.__dict__
		else:
			raise ValueError("Expecting a AddItem(s)ToContainerPacket")

		if it['serial'] in self.client.objects.keys():
			item = self.client.objects[it['serial']]
		else:
			item = Item(self.client)
			item.serial = it['serial']
			self.client.objects[it['serial']] = item
		item.graphic = it['graphic']
		item.amount = it['amount']
		item.x = it['x']
		item.y = it['y']
		item.color = it['color']

		if self.content is None:
			self.content = []
		self.content.append(item)

	def __iter__(self):
		return self.content.__iter__()

	def __next__(self):
		return self.content.__next__()

	def __getitem__(self, key):
		return self.content[key]


class Mobile(UOBject):
	''' Represents a mobile in the world '''

	# Constants for equipment layers
	LAYER_NONE        = 0x00 #  0. Not used?
	LAYER_HAND1       = 0x01 #  1. One handed weapon.
	LAYER_HAND2       = 0x02 #  2. Two handed weapon, shield or misc.
	LAYER_SHOES       = 0x03 #  3. Shoes.
	LAYER_PANTS       = 0x04 #  4. Pants.
	LAYER_SHIRT       = 0x05 #  5. Shirt.
	LAYER_HELM        = 0x06 #  6. Helm or Hat.
	LAYER_GLOVES      = 0x07 #  7. Gloves.
	LAYER_RING        = 0x08 #  8. Ring.
	LAYER_TALISMAN    = 0x09 #  9. Talisman. (since POL097, Mondain's Legacy)
	LAYER_NECK        = 0x0a # 10. Neck.
	LAYER_HAIR        = 0x0b # 11. Hair
	LAYER_WAIST       = 0x0c # 12. Waist (half apron).
	LAYER_CHEST       = 0x0d # 13. Torso (inner) (chest armor).
	LAYER_WRIST       = 0x0e # 14. Bracelet.
	LAYER_PACK2       = 0x0f # 15. Unused (backpack, but ord. bp is 0x15).
	LAYER_BEARD       = 0x10 # 16. Facial hair.
	LAYER_TUNIC       = 0x11 # 17. Torso (middle) (tunic, sash etc.).
	LAYER_EARS        = 0x12 # 18. Earrings.
	LAYER_ARMS        = 0x13 # 19. Arms.
	LAYER_CAPE        = 0x14 # 20. Back (cloak). (Also Quivers in Mondain's Legacy)
	LAYER_PACK        = 0x15 # 21. Backpack
	LAYER_ROBE        = 0x16 # 22. Torso (outer) (robe)
	LAYER_SKIRT       = 0x17 # 23. Legs (outer) (skirt/robe).
	LAYER_LEGS        = 0x18 # 24. Legs (inner) (leg armor).
	LAYER_MOUNT       = 0x19 # 25. Mount (horse, ostard etc.).
	LAYER_VENDORSTOCK = 0x1a # 26. This vendor will sell and restock.
	LAYER_VENDOREXTRA = 0x1b # 27. This vendor will resell to players but not restock.
	LAYER_VENDORBUY   = 0x1c # 28. This vendor can buy from players but does not stock.
	LAYER_BANKBOX     = 0x1d # 29. Contents of bankbox
	LAYER_TRADE       = 0x1e # 30. Can be multiple of these, do not use directly.

	def __init__(self, client, pkt=None):
		super().__init__(client)

		## Status flags
		## 0x00: Normal
		## 0x01: Unknown
		## 0x02: Can Alter Paperdoll
		## 0x04: Poisoned
		## 0x08: Golden Health
		## 0x10: Unknown
		## 0x20: Unknown
		## 0x40: War Mode
		self.status = None
		## War mode flag
		self.war = None
		## Notoriety
		## 0x1: Innocent (Blue)
		## 0x2: Friend (Green)
		## 0x3: Grey (Grey - Animal)
		## 0x4: Criminal (Grey)
		## 0x5: Enemy (Orange)
		## 0x6: Murderer (Red)
		## 0x7: Invulnerable (Yellow)
		self.notoriety = None
		## Hit Points
		self.hp = None
		## Max Hit Points
		self.maxhp = None
		## Mana
		self.mana = None
		## Max Mana
		self.maxmana = None
		## Stamina
		self.stam = None
		## Max Stamina
		self.maxstam = None
		## Equip serials list, by layer (None = unknown)
		self.equip = None

		if pkt is not None:
			self.update(pkt)

	def update(self, pkt):
		''' Update from packet '''
		if not isinstance(pkt, net.UpdatePlayerPacket) and not isinstance(pkt, net.DrawObjectPacket):
			raise ValueError("Expecting an UpdatePlayerPacket or DrawObjectPacket")
		self.serial = pkt.serial
		self.graphic = pkt.graphic
		self.x = pkt.x
		self.y = pkt.y
		self.z = pkt.z
		self.facing = pkt.facing
		self.color = pkt.color
		self.status = pkt.flag
		self.notoriety = pkt.notoriety

		# Handle equip
		if isinstance(pkt, net.DrawObjectPacket):
			self.equip = {}
			for eq in pkt.equip:
				serial = eq['serial']
				if serial in self.client.objects.keys():
					item = self.client.objects[serial]
				else:
					item = Item(self.client)
					item.serial = eq['serial']
					self.client.objects[item.serial] = item
				item.graphic = eq['graphic']
				item.color = eq['color']

				self.equip[eq['layer']] = item

	def getEquipByLayer(self, layer):
		''' Returns item equipped in the given layer '''
		self.client.waitFor(lambda: self.equip is not None)
		return self.equip[layer]

	def __repr__(self):
		return "Mobile 0x{serial:02X} graphic 0x{graphic:02X} color 0x{color:02X} at {x},{y},{z} facing {facing}".format(**self.__dict__)


class Player(Mobile):
	''' Represents the current player '''

	def __init__(self, client):
		super().__init__(client)

		## Current target serial
		self.target = None

	def openBackPack(self):
		''' Opens player's backpack, waits for it to be loaded '''
		bp = self.getEquipByLayer(self.LAYER_PACK)
		if not isinstance(bp, Container):
			self.client.doubleClick(bp)
			self.client.waitFor(lambda: isinstance(bp, Container))
			self.client.waitFor(lambda: bp.content is not None)
		return bp


class Target:
	''' Represents an active target '''

	# Constants for what
	OBJECT = 0
	LOCATION = 1

	# Constants for type
	NEUTRAL = 0
	HARMFUL = 1
	HELPFUL = 2

	def __init__(self, client, pkt):
		assert isinstance(pkt, net.TargetCursorPacket)

		self.client = client

		self.what = pkt.what
		self.id = pkt.id
		self.type = pkt.type

	def target(self, obj):
		''' Sends a target for the given object '''
		assert self.what == self.OBJECT
		po = net.PacketOut(net.Ph.TARGET_CURSOR)
		po.uchar(self.what)
		po.uint(self.id)
		po.uchar(self.type)
		po.uint(obj.serial) # Object
		po.ushort(0) # X
		po.ushort(0) # Y
		po.uchar(0) # unknown
		po.schar(0) # Z
		po.ushort(0) # graphic
		self.client.target = None
		self.client.send(po)


class Client:
	''' The main client instance '''

	## Minimum interval between two pings
	PING_INTERVAL = 30
	## Version sent to server
	VERSION = '5.0.9.1'
	## Language sent to server
	LANG = 'ENU'

	def __init__(self):
		## Dict info about last server connected to {ip, port, user, pass}
		self.server = None
		## Current client status, one of:
		## - disconnected: The client is not connected
		## - connected: Connected and logged in, server not selected
		## - loggedin: Connected to game server, character not selected
		self.status = 'disconnected'
		## Login complete, will be false during the initial fase of the game
		self.lc = False
		## When to send next ping
		self.ping = 0
		## Logger, for internal usage
		self.log = logging.getLogger('client')
		## Features sent with 0xb9 packet
		self.features = None
		## Flags sent with 0xa9 packet
		self.flags = None
		## Locations sent with 0xa9 packets
		self.locs = None

		## Reference to player, character instance
		self.player = None
		## Dictionary of Objects (Mobiles and Items) around, by serial
		self.objects = {}
		## Reference to current active target, if any
		self.target = None

		## Current Realm's width
		self.width = None
		## Current Realm's height
		self.height = None

		## Current cursor (0 = Felucca, unhued / BRITANNIA map. 1 = Trammel, hued gold / BRITANNIA map, 2 = (switch to) ILSHENAR map)
		self.cursor = None

	@status('disconnected')
	def connect(self, ip, port, user, pwd):
		''' Conmnects to the server, returns a list of gameservers
			@param ip string: Server IP
			@param port string: Server IP
			@param user string: Username
			@param pwd string: Password
			@return list of dicts{name, tz, full, idx, ip}
		'''
		self.server = {
			'ip': ip,
			'port': port,
			'user': user,
			'pass': pwd,
		}
		self.log.info('connecting')
		self.net = net.Network(self.server['ip'], self.server['port'])

		# Send IP as key (will not use encryption)
		self.send(ipaddress.ip_address(self.server['ip']).packed)

		# Send account login request
		self.log.info('logging in')
		po = net.PacketOut(net.Ph.LOGIN_REQUEST)
		po.string(self.server['user'], 30)
		po.string(self.server['pass'], 30)
		po.uchar(0x00)
		self.send(po)

		# Get servers list
		pkt = self.receive(net.Ph.SERVER_LIST)
		self.log.debug("Received serverlist: %s", str(pkt.servers))

		self.status = 'connected'
		return pkt.servers

	@status('connected')
	def selectServer(self, idx):
		''' Selects the game server with the given idx '''
		self.log.info('selecting server %d', idx)
		self.send(struct.pack('>BH', 0xa0, idx))

		pkt = self.receive(net.Ph.CONNECT_TO_GAME_SERVER)
		ip = '.'.join(map(str, pkt.ip))
		self.log.info("Connecting to gameserver ip %s, port %s (key %s)", ip, pkt.port, pkt.key)

		# Connect
		self.net.close()
		self.net = net.Network(ip, pkt.port)

		# Send key
		bkey = struct.pack('>I', pkt.key)
		self.send(bkey)

		# Send login
		self.log.info('logging in')
		po = net.PacketOut(net.Ph.GAME_SERVER_LOGIN)
		po.uint(pkt.key)
		po.string(self.server['user'], 30)
		po.string(self.server['pass'], 30)
		self.send(po)

		# From now on, server will use compression
		self.net.compress = True

		# Get features packet
		pkt = self.receive(net.Ph.ENABLE_FEATURES)
		self.features = pkt.features

		# Get character selection
		pkt = self.receive(net.Ph.CHARACTERS)
		self.flags = pkt.flags
		self.locs = pkt.locs

		self.status = 'loggedin'
		return pkt.chars

	@status('loggedin')
	def selectCharacter(self, name, idx):
		''' Login the character with the given name '''
		self.log.info('selecting character #%d %s', idx, name)
		po = net.PacketOut(net.Ph.LOGIN_CHARACTER)
		po.uint(0xedededed) #Pattern1
		po.string(name, 30) #Char name
		po.ushort(0x0000)   #unknown0
		po.uint(0x00000000) #clientflag
		po.uint(0x00000000) #unknown1
		po.uint(0x0000001d) #login count
		po.uint(0x00000000) # unknown2
		po.uint(0x00000000) # unknown2
		po.uint(0x00000000) # unknown2
		po.uint(0x00000000) # unknown2
		po.uint(idx) # slot chosen
		po.ip('127.0.0.1')
		self.send(po)

		self.status = 'game'

	@status('game')
	def play(self, script):
		''' Starts the endless game loop
		@script Thread: The brain thread will be started once login is completed
		'''
		self.ping = time.time() + self.PING_INTERVAL

		if not isinstance(script, brain.Brain):
			raise RuntimeError("Unknown brain, expecting a Brain instance, got {}".format(type(brain)))

		while True:
			pkt = self.receive()

			# Check if brain is alive
			if script.started and not script.is_alive():
				self.log.info("Brain died, terminating")
				break

			# Send ping if needed
			if self.lc and self.ping < time.time():
				po = net.PacketOut(net.Ph.PING)
				po.uchar(0x00)
				self.send(po)
				self.ping = time.time() + self.PING_INTERVAL

			# Process packet
			if isinstance(pkt, net.LoginDeniedPacket):
				raise LoginDeniedError(pkt.reason)

			elif isinstance(pkt, net.PingPacket):
				self.log.debug("Server sent a ping back")

			elif isinstance(pkt, net.CharLocaleBodyPacket):
				assert not self.lc

				assert self.player is None
				self.player = Player(self)

				assert self.player.serial is None
				self.player.serial = pkt.serial
				assert self.player.graphic is None
				self.player.graphic = pkt.bodyType
				assert self.player.x is None
				self.player.x = pkt.x
				assert self.player.y is None
				self.player.y = pkt.y
				assert self.player.z is None
				self.player.z = pkt.z
				assert self.player.facing is None
				self.player.facing = pkt.facing
				assert self.width is None
				self.width = pkt.widthM8 + 8
				assert self.height is None
				self.height = pkt.height

				assert self.player.serial not in self.objects.keys()
				self.objects[self.player.serial] = self.player

				self.log.info("Realm size: %d,%d", self.width, self.height)
				self.log.info("You are 0x%X and your graphic is 0x%X", self.player.serial, self.player.graphic)
				self.log.info("Position: %d,%d,%d facing %d", self.player.x, self.player.y, self.player.z, self.player.facing)

			elif isinstance(pkt, net.DrawGamePlayerPacket):
				assert self.player.serial == pkt.serial
				assert self.player.graphic == pkt.graphic
				assert self.player.x == pkt.x
				assert self.player.y == pkt.y
				assert self.player.z == pkt.z
				#assert self.player.facing == pkt.direction

				self.player.color = pkt.hue
				self.player.status = pkt.flag

				self.log.info("Your color is %d and your status is 0x%X", self.player.color, self.player.status)

			elif isinstance(pkt, net.DrawObjectPacket):
				assert self.lc
				if pkt.serial in self.objects.keys():
					self.objects[pkt.serial].update(pkt)
					self.log.info("Refreshed mobile: %s", self.objects[pkt.serial])
				else:
					mob = Mobile(self, pkt)
					self.objects[mob.serial] = mob
					self.log.info("New mobile: %s", mob)
					# Auto single click for new mobiles
					self.singleClick(mob)

			elif isinstance(pkt, net.ObjectInfoPacket):
				assert self.lc
				if pkt.serial in self.objects.keys():
					self.objects[pkt.serial].update(pkt)
					self.log.info("Refresh item: %s", self.objects[pkt.serial])
				else:
					item = Item(self, pkt)
					self.log.info("New item: %s", item)
					self.objects[item.serial] = item

			elif isinstance(pkt, net.UpdatePlayerPacket):
				assert self.lc
				self.objects[pkt.serial].update(pkt)
				self.log.info("Updated mobile: %s", self.objects[pkt.serial])

			elif isinstance(pkt, net.DeleteObjectPacket):
				assert self.lc
				if pkt.serial in self.objects:
					del self.objects[pkt.serial]
					self.log.info("Object 0x%X went out of sight", pkt.serial)
				else:
					self.log.warn("Server requested to delete 0x%X but i don't know it", pkt.serial)

			elif isinstance(pkt, net.AddItemToContainerPacket):
				assert self.lc
				if isinstance(self.objects[pkt.container], Container):
					self.objects[pkt.container].addItem(pkt)
				else:
					self.log.warn("Ignoring add item 0x%X to non-container 0x%X", pkt.serial, pkt.container)

			elif isinstance(pkt, net.AddItemsToContainerPacket):
				assert self.lc
				for it in pkt.items:
					if isinstance(self.objects[it['container']], Container):
						self.objects[it['container']].addItem(it)
					else:
						self.log.warn("Ignoring add item 0x%X to non-container 0x%X", it['serial'], it['container'])

			elif isinstance(pkt, net.WarModePacket):
				assert self.player.war is None
				self.player.war = pkt.war

			elif isinstance(pkt, net.AllowAttackPacket):
				assert self.lc
				self.player.target = pkt.serial
				self.log.info("Target set to 0x%X", self.player.target)

			elif isinstance(pkt, net.UpdateHealthPacket):
				assert self.lc
				old = self.player.hp
				if self.player.serial == pkt.serial:
					self.player.maxhp = pkt.max
					self.player.hp = pkt.cur
					self.log.info("My HP: %d/%d", pkt.cur, pkt.max)
				else:
					mob = self.objects[pkt.serial]
					mob.maxhp = pkt.max
					mob.hp = pkt.cur
					self.log.info("0x%X's HP: %d/%d", pkt.serial, pkt.cur, pkt.max)
				script.event(brain.Event(brain.Event.EVT_HP_CHANGED, old=old, new=self.player.hp))

			elif isinstance(pkt, net.UpdateManaPacket):
				assert self.lc
				old = self.player.mana
				if self.player.serial == pkt.serial:
					self.player.maxmana = pkt.max
					self.player.mana = pkt.cur
					self.log.info("My MANA: %d/%d", pkt.cur, pkt.max)
				else:
					mob = self.objects[pkt.serial]
					mob.maxmana = pkt.max
					mob.mana = pkt.cur
					self.log.info("0x%X's MANA: %d/%d", pkt.serial, pkt.cur, pkt.max)
				script.event(brain.Event(brain.Event.EVT_MANA_CHANGED, old=old, new=self.player.mana))

			elif isinstance(pkt, net.UpdateStaminaPacket):
				assert self.lc
				old = self.player.stam
				if self.player.serial == pkt.serial:
					self.player.maxstam = pkt.max
					self.player.stam = pkt.cur
					self.log.info("My STAM: %d/%d", pkt.cur, pkt.max)
				else:
					mob = self.objects[pkt.serial]
					mob.maxstam = pkt.max
					mob.stam = pkt.cur
					self.log.info("0x%X's STAM: %d/%d", pkt.serial, pkt.cur, pkt.max)
				script.event(brain.Event(brain.Event.EVT_STAM_CHANGED, old=old, new=self.player.stam))

			elif isinstance(pkt, net.GeneralInfoPacket):
				if pkt.sub == net.GeneralInfoPacket.SUB_CURSORMAP:
					self.cursor = pkt.cursor
				elif pkt.sub == net.GeneralInfoPacket.SUB_MAPDIFF:
					pass
				elif pkt.sub == net.GeneralInfoPacket.SUB_PARTY:
					self.log.info("Ignoring party system data")
				else:
					self.log.warn("Unhandled GeneralInfo subpacket 0x%X", pkt.sub)

			elif isinstance(pkt, net.DrawContainerPacket):
				cont = self.objects[pkt.serial]
				assert isinstance(cont, Item)
				if not isinstance(cont, Container):
					# Upgrade the item to a Container
					cont.upgradeToContainer()

			elif isinstance(pkt, net.TipWindowPacket):
				assert self.lc
				self.log.info("Received tip: %s", pkt.msg.replace('\r','\n'))

			elif isinstance(pkt, net.SendSpeechPacket) or isinstance(pkt, net.UnicodeSpeech):
				if pkt.type == 0x00:
					what = "Say"
				elif pkt.type == 0x01:
					what = "Broadcast"
				elif pkt.type == 0x02:
					what = "Emote"
				elif pkt.type == 0x07:
					what = "Message"
				elif pkt.type == 0x08:
					what = "Whisper"
				elif pkt.type == 0x09:
					what = "Yell"
				elif pkt.type == 0x0a:
					what = "Spell"
				elif pkt.type == 0x0d:
					what = "Guild Chat"
				elif pkt.type == 0x0e:
					what = "Alliance Chat"
				elif pkt.type == 0x0f:
					what = "Command prompt"
				else:
					what = "Unknown message"

				p = "u" if isinstance(pkt, net.UnicodeSpeech) else ""
				if self.lc:
					self.log.info('%s from 0x%X (%s): %s"%s"', what, pkt.serial, pkt.name, p, pkt.msg)
				else:
					self.log.warn('EARLY %s from 0x%X (%s): %s"%s"', what, pkt.serial, pkt.name, p, pkt.msg)

			elif isinstance(pkt, net.TargetCursorPacket):
				assert self.target is None
				self.target = Target(self, pkt)

			elif isinstance(pkt, net.CharacterAnimationPacket):
				assert self.lc
				# Just check that the object exists
				self.objects[pkt.serial]

			elif isinstance(pkt, net.LoginCompletePacket):
				assert not self.lc
				assert self.player is not None
				self.lc = True
				# Send some initial info packets      ..
				self.requestSkills()
				self.sendVersion()
				# Original client also sends this now
				# bf 00 0d 00 05 00 00 03 20 01 00 00 a7 - General info 0x05
				self.sendClientType()
				# Original client also sends this now, seems to also send it again later
				# 34 ed ed ed ed 04 00 45 dd f5 - Get Player status something
				self.sendLanguage()
				self.singleClick(self.player)

				# Start the brain
				script.start(self)

			elif isinstance(pkt, net.Unk32Packet):
				self.log.warn("Unknown 0x32 packet received")

			elif isinstance(pkt, net.ControlAnimationPacket):
				assert self.lc
				self.log.info('Ignoring animation packet')

			elif isinstance(pkt, net.GraphicalEffectPacket):
				assert self.lc
				self.log.info('Graphical effect packet')

			elif isinstance(pkt, net.PlaySoundPacket):
				assert self.lc
				self.log.info('Ignoring sound packet')

			elif isinstance(pkt, net.SetWeatherPacket):
				assert self.lc
				self.log.info('Ignoring weather packet')

			elif isinstance(pkt, net.OverallLightLevelPacket):
				self.log.info('Ignoring light level packet')

			elif isinstance(pkt, net.SeasonInfoPacket):
				self.log.info('Ignoring season packet')

			else:
				self.log.warn("Unhandled packet {}".format(pkt.__class__))

	@logincomplete
	def sendVersion(self):
		''' Sends client version to server, should not send it twice '''
		po = net.PacketOut(net.Ph.CLIENT_VERSION)
		po.ulen()
		po.string(self.VERSION, len(self.VERSION)+1)
		self.send(po)

	@logincomplete
	def sendLanguage(self):
		''' Sends client lamguage to server, should not send it twice '''
		po = net.PacketOut(net.Ph.GENERAL_INFO)
		po.ulen()
		po.ushort(0x0b) # subcommad
		po.string(self.LANG, len(self.LANG)+1)
		self.send(po)

	@logincomplete
	def sendClientType(self):
		''' Sends client type flag, should be sent only once at login '''
		po = net.PacketOut(net.Ph.GENERAL_INFO)
		po.ulen()
		po.uint(0x1f) # 0x1f for login, something else for char create=
		self.send(po)

	@logincomplete
	def requestSkills(self):
		''' Requests skill info (0x3a packet) '''
		po = net.PacketOut(net.Ph.REQUEST_STATUS)
		po.uint(0xedededed) #Pattern (unknown)
		po.uchar(0x05) # Type
		po.uint(self.player.serial)
		self.send(po)

	@logincomplete
	def requestStatus(self):
		''' Requests basic statuc (0x11 packet) '''
		po = net.PacketOut(net.Ph.REQUEST_STATUS)
		po.uint(0xedededed) #Pattern (unknown)
		po.uchar(0x04) # Type
		po.uint(self.player.serial)
		self.send(po)

	@logincomplete
	def singleClick(self, obj):
		''' Sends a single click for the given object (Item/Mobile or serial) to server '''
		po = net.PacketOut(net.Ph.SINGLE_CLICK)
		po.uint(obj if type(obj) == int else obj.serial)
		self.send(po)

	@logincomplete
	def doubleClick(self, obj):
		''' Sends a single click for the given object (Item/Mobile or serial) to server '''
		po = net.PacketOut(net.Ph.DOUBLE_CLICK)
		po.uint(obj if type(obj) == int else obj.serial)
		self.send(po)

	@logincomplete
	def say(self, text, font=3, color=0):
		''' Say something, in unicode
		@param text string: Any unicode string
		@param font int: Font code, usually 3
		@param colot int: Font color, usually 0
		'''
		po = net.PacketOut(net.Ph.UNICODE_SPEECH_REQUEST)
		po.ulen()
		po.uchar(0x00) # Type TODO: implement other types
		po.ushort(color)
		po.ushort(font)
		assert len(self.LANG) == 3
		po.string(self.LANG, 4)
		po.string(text, len(text)*2 + 1, True)
		self.send(po)

	@logincomplete
	def waitForTarget(self, timeout=None):
		''' Waits until a target cursor is requested and return it. If timeout is given, returns after timeout
		@param timeout float: Timeout, in seconds
		@return Target on success, None on timeout
		'''
		self.waitFor(lambda: self.target is not None, timeout)
		return self.target

	def waitFor(self, cond, timeout=None):
		''' Utility function, waits until a condition is satisfied or until timeout expires
		@return True when consition succeeds, False on timeout
		'''
		wait = 0.0
		nextWarn = 5.0
		while not cond():
			time.sleep(0.01)
			wait += 0.01
			if timeout:
				if wait >= timeout:
					return False
			elif wait >= nextWarn:
				self.log.warn("Waiting for {}...".format(traceback.extract_stack(limit=2)[0]))
				nextWarn = wait + 5.0
		return True

	def send(self, data):
		''' Sends a raw packet to the Server '''
		if isinstance(data, net.PacketOut):
			data = data.getBytes()
		self.net.send(data)

	def receive(self, expect=None):
		''' Receives next packet from the server
		@param expect If given, throws an exception if packet type is not the expected one
		@return Packet
		@throws UnexpectedPacketError
		'''
		pkt = self.net.recv()

		if expect and pkt.cmd != expect:
			print(expect,pkt.cmd)
			raise UnexpectedPacketError("Expecting 0x%0.2X packet, got 0x%0.2X intead" % (expect, pkt.cmd))

		return pkt



class StatusError(Exception):
	pass


class UnexpectedPacketError(Exception):
	pass


class LoginDeniedError(Exception):

	def __init__(self, code):
		self.code = code
		if code == 0x00:
			mex = "Uncorrect name or password"
		elif code == 0x01:
			mex = "Someone is already using this account"
		elif code == 0x02:
			mex = "Your account has been blocked"
		elif code == 0x03:
			mex = "Your account credentials are invalid"
		elif code == 0x04:
			mex = "Communication problem"
		elif code == 0x05:
			mex = "The IGR concurrency limit has been met"
		elif code == 0x06:
			mex = "The IGR time limit has been met"
		elif code == 0x07:
			mex = "General IGR authentication failure"
		else:
			mex = "Unknown reason {:02X}".format(code)
		super().__init__(mex)


if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument('ip', help='Server ip')
	parser.add_argument('port', type=int, help='Server port')
	parser.add_argument('user', help='Username')
	parser.add_argument('pwd', help='Password')
	parser.add_argument('srvidx', type=int, help="Gameserver's Index")
	parser.add_argument('charidx', type=int, help="Character's Index")
	parser.add_argument('charname', help="Character's Name")
	parser.add_argument('-v', '--verbose', action='store_true', help='Show debug output')
	args = parser.parse_args()

	logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

	c = Client()
	servers = c.connect(args.ip, args.port, args.user, args.pwd)
	chars = c.selectServer(args.srvidx)
	c.selectCharacter(args.charname, args.charidx)
	c.play()
	print('done')
