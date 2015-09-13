#!/usr/bin/env python3

'''
Ultima online text client (experiment)
'''

import struct
import logging
import ipaddress
import net


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


class UOBject:
	''' Base class for an UO Object '''

	def __init__(self):
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

	def __init__(self, pkt=None):
		super().__init__()

		## Number of items in the stack
		self.amount = None
		## Status flags
		self.status = None

		if pkt is not None:
			if not isinstance(pkt, net.ObjectInfoPacket):
				raise ValueError("Expecting a DrawObjectPacket")
			self.serial = pkt.serial
			self.graphic = pkt.graphic
			self.amount = pkt.count
			self.x = pkt.x
			self.y = pkt.y
			self.z = pkt.z
			self.facing = pkt.facing
			self.color = pkt.color
			self.status = pkt.flag

	def __repr__(self):
		return "{amount}x Item 0x{serial:02X} graphic 0x{graphic:02X} color 0x{color:02X} at {x},{y},{z} facing {facing}".format(**self.__dict__)


class Mobile(UOBject):
	''' Represents a mobile in the world '''

	def __init__(self, pkt=None):
		super().__init__()

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

		if pkt is not None:
			if not isinstance(pkt, net.DrawObjectPacket):
				raise ValueError("Expecting a DrawObjectPacket")
			self.serial = pkt.serial
			self.graphic = pkt.graphic
			self.x = pkt.x
			self.y = pkt.y
			self.z = pkt.z
			self.facing = pkt.facing
			self.color = pkt.color
			self.status = pkt.flag
			self.notoriety = pkt.notoriety
			##TODO: handle equip

	def __repr__(self):
		return "Mobile 0x{serial:02X} graphic 0x{graphic:02X} color 0x{color:02X} at {x},{y},{z} facing {facing}".format(**self.__dict__)


class Player(Mobile):
	''' Represents the current player '''

	def __init__(self):
		super().__init__()

		## Current target serial
		self.target = None


class Client:
	''' The main client instance '''

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
		## Dictionary of mobs around, by serial
		self.mobs = {}
		## Dictionary of items around, by serial
		self.items = {}

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
		self.log.info('selecting character %s', name)
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
	def play(self):
		''' Starts the endless game loop '''
		while True:
			pkt = self.receive()

			if isinstance(pkt, net.CharLocaleBodyPacket):
				if self.lc:
					raise NotImplementedError("Unexpected")

				assert self.player is None
				self.player = Player()

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
				mob = Mobile(pkt)
				assert mob.serial not in self.mobs.keys()
				self.log.info("New mobile: %s", mob)
				self.mobs[mob.serial] = mob

			elif isinstance(pkt, net.ObjectInfoPacket):
				assert self.lc
				item = Item(pkt)
				assert item.serial not in self.items.keys()
				self.log.info("New item: %s", item)
				self.items[item.serial] = item

			elif isinstance(pkt, net.WarModePacket):
				assert self.player.war is None
				self.player.war = pkt.war

			elif isinstance(pkt, net.AllowAtackPacket):
				assert self.lc
				self.player.target = pkt.serial
				self.log.info("Target set to 0x%X", self.player.target)

			elif isinstance(pkt, net.GeneralInfoPacket):
				if pkt.sub == net.GeneralInfoPacket.SUB_CURSORMAP:
					self.cursor = pkt.cursor
				elif pkt.sub == net.GeneralInfoPacket.SUB_MAPDIFF:
					pass
				elif pkt.sub == net.GeneralInfoPacket.SUB_PARTY:
					self.log.info("Ignoring party system data")
				else:
					self.log.warn("Unhandled GeneralInfo subpacket 0x%X", pkt.sub)

			elif isinstance(pkt, net.TipWindowPacket):
				assert self.lc
				self.log.info("Received tip: %s", pkt.msg.replace('\r','\n'))

			elif isinstance(pkt, net.SendSpeechPacket):
				assert self.lc
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
				self.log.info('%s from 0x%X (%s): "%s"', what, pkt.serial, pkt.name, pkt.msg)

			elif isinstance(pkt, net.LoginCompletePacket):
				assert not self.lc
				self.lc = True

			elif isinstance(pkt, net.Unk32Packet):
				self.log.warn("Unknown 0x32 packet received")

			elif isinstance(pkt, net.ControlAnimationPacket):
				self.log.info('Ignoring animation packet')

			elif isinstance(pkt, net.PlaySoundPacket):
				self.log.info('Ignoring sound packet')

			elif isinstance(pkt, net.SetWeatherPacket):
				assert self.lc
				self.log.info('Ignoring weather packet')

			else:
				self.log.warn("Unhandled packet {}".format(pkt.__class__))

	def send(self, data):
		''' Sends a raw packet to the Server '''
		if isinstance(data, net.PacketOut):
			data = data.getBytes()
		self.net.send(data)

	def receive(self, expect=None):
		''' Receives next packet from the server
		@param expect If given, throws an exception if packet type is not the expected one
		@return Packet
		@throws UnexpectedPacket
		'''
		pkt = self.net.recv()

		if expect and pkt.cmd != expect:
			raise UnexpectedPacket("Expecting 0x%0.2X packet, got 0x%0.2X intead" % expect, self.cmd)

		return pkt


class StatusError(Exception):
	pass

class UnexpectedPacket(Exception):
	pass


if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument('ip', help='Server ip')
	parser.add_argument('port', type=int, help='Server port')
	parser.add_argument('user', help='Username')
	parser.add_argument('pwd', help='Password')
	parser.add_argument('-v', '--verbose', action='store_true', help='Show debug output')
	args = parser.parse_args()

	logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

	c = Client()
	servers = c.connect(args.ip, args.port, args.user, args.pwd)
	chars = c.selectServer(3)
	c.selectCharacter('Developer Bodom', 1)
	c.play()
	print('done')
