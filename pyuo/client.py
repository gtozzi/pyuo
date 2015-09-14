#!/usr/bin/env python3

'''
Ultima online text client (experiment)
'''

import struct
import logging
import ipaddress
import net
import time


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
			self.color = pkt.color if pkt.color else 0
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
		##TODO: handle equip if DrawObjectPacket

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

	## Minimum interval between two pings
	PING_INTERVAL = 30

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
	def play(self):
		''' Starts the endless game loop '''
		self.ping = time.time() + self.PING_INTERVAL

		while True:
			pkt = self.receive()

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
				if pkt.serial in self.objects.keys():
					self.objects[pkt.serial].update(pkt)
					self.log.info("Refreshed mobile: %s", self.objects[pkt.serial])
				else:
					mob = Mobile(pkt)
					self.objects[mob.serial] = mob
					self.log.info("New mobile: %s", mob)

			elif isinstance(pkt, net.ObjectInfoPacket):
				assert self.lc
				item = Item(pkt)
				assert item.serial not in self.objects.keys()
				self.log.info("New item: %s", item)
				self.objects[item.serial] = item

			elif isinstance(pkt, net.UpdatePlayerPacket):
				assert self.lc
				self.objects[pkt.serial].update(pkt)
				self.log.info("Updated mobile: %s", self.objects[pkt.serial])

			elif isinstance(pkt, net.DeleteObjectPacket):
				assert self.lc
				del self.objects[pkt.serial]
				self.log.info("Object 0x%X went out of sight", pkt.serial)

			elif isinstance(pkt, net.AddItemToContainerPacket):
				assert self.lc
				print(self.objects[pkt.serial])
				print(self.objects[pkt.container])
				raise NotImplementedError()

			elif isinstance(pkt, net.WarModePacket):
				assert self.player.war is None
				self.player.war = pkt.war

			elif isinstance(pkt, net.AllowAtackPacket):
				assert self.lc
				self.player.target = pkt.serial
				self.log.info("Target set to 0x%X", self.player.target)

			elif isinstance(pkt, net.UpdateHealthPacket):
				assert self.lc
				if self.player.serial == pkt.serial:
					self.player.maxhp = pkt.max
					self.player.hp = pkt.cur
					self.log.info("My HP: %d/%d", pkt.cur, pkt.max)
				else:
					mob = self.objects[pkt.serial]
					mob.maxhp = pkt.max
					mob.hp = pkt.cur
					self.log.info("0x%X's HP: %d/%d", pkt.serial, pkt.cur, pkt.max)

			elif isinstance(pkt, net.UpdateManaPacket):
				assert self.lc
				if self.player.serial == pkt.serial:
					self.player.maxmana = pkt.max
					self.player.mana = pkt.cur
					self.log.info("My MANA: %d/%d", pkt.cur, pkt.max)
				else:
					mob = self.objects[pkt.serial]
					mob.maxmana = pkt.max
					mob.mana = pkt.cur
					self.log.info("0x%X's MANA: %d/%d", pkt.serial, pkt.cur, pkt.max)

			elif isinstance(pkt, net.UpdateStaminaPacket):
				assert self.lc
				if self.player.serial == pkt.serial:
					self.player.maxstam = pkt.max
					self.player.stam = pkt.cur
					self.log.info("My STAM: %d/%d", pkt.cur, pkt.max)
				else:
					mob = self.objects[pkt.serial]
					mob.maxstam = pkt.max
					mob.stam = pkt.cur
					self.log.info("0x%X's STAM: %d/%d", pkt.serial, pkt.cur, pkt.max)

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

			elif isinstance(pkt, net.SendSpeechPacket) or isinstance(pkt, net.UnicodeSpeech):
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

				p = "u" if isinstance(pkt, net.UnicodeSpeech) else ""
				self.log.info('%s from 0x%X (%s): %s"%s"', what, pkt.serial, pkt.name, p, pkt.msg)

			elif isinstance(pkt, net.CharacterAnimationPacket):
				assert self.lc
				# Just check that the object exists
				self.objects[pkt.serial]

			elif isinstance(pkt, net.LoginCompletePacket):
				assert not self.lc
				self.lc = True

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
		@throws UnexpectedPacketError
		'''
		pkt = self.net.recv()

		if expect and pkt.cmd != expect:
			raise UnexpectedPacketError("Expecting 0x%0.2X packet, got 0x%0.2X intead" % expect, self.cmd)

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
	parser.add_argument('charidx', type=int, help="Character's Index")
	parser.add_argument('charname', help="Character's Name")
	parser.add_argument('-v', '--verbose', action='store_true', help='Show debug output')
	args = parser.parse_args()

	logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

	c = Client()
	servers = c.connect(args.ip, args.port, args.user, args.pwd)
	chars = c.selectServer(3)
	c.selectCharacter(args.charname, args.charidx)
	c.play()
	print('done')
