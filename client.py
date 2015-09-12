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


class Client:

	def __init__(self):
		## Dict info about last server connected to {ip, port, user, pass}
		self.server = None
		## Current client status, one of:
		## - disconnected: The client is not connected
		## - connected: Connected and logged in, server not selected
		## - loggedin: Connected to game server, character not selected
		self.status = 'disconnected'
		## Logger, for internal usage
		self.log = logging.getLogger('client')
		## Features sent with 0xb9 packet
		self.features = None
		## Flags sent with 0xa9 packet
		self.flags = None
		## Locations sent with 0xa9 packets
		self.locs = None

		## Current player's serial
		self.serial = None
		## Current player's graphic
		self.graphic = None
		## Current player's X coordinate
		self.x = None
		## Current player's X coordinate
		self.y = None
		## Current player's X coordinate
		self.z = None
		## Current player's facing
		self.facing = None

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
		po.byte(0x00)
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
				assert self.serial is None
				self.serial = pkt.serial
				assert self.graphic is None
				self.graphic = pkt.bodyType
				assert self.x is None
				self.x = pkt.x
				assert self.y is None
				self.y = pkt.y
				assert self.z is None
				self.z = pkt.z
				assert self.facing is None
				self.facing = pkt.facing
				assert self.width is None
				self.width = pkt.widthM8 + 8
				assert self.height is None
				self.height = pkt.height

				self.log.info("Realm size: %d,%d", self.width, self.height)
				self.log.info("You are 0x%X and your graphic is 0x%X", self.serial, self.graphic)
				self.log.info("Position: %d,%d,%d facing %d", self.x, self.y, self.z, self.facing)

			elif isinstance(pkt, net.GeneralInfoPacket):
				if pkt.sub == net.GeneralInfoPacket.SUB_CURSORMAP:
					self.cursor = pkt.cursor
				else:
					raise RuntimeError("Unhandled subpacket {}".format(pkt.sub))

			elif isinstance(pkt, net.Unk32Packet):
				self.log.warn("Unknown 32 packet received")

			elif isinstance(pkt, net.ControlAnimationPacket):
				pass

			else:
				raise RuntimeError("Unhandled packet {}".format(pkt.__class__))

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
	args = parser.parse_args()

	logging.basicConfig(level=logging.INFO)

	c = Client()
	servers = c.connect(args.ip, args.port, args.user, args.pwd)
	chars = c.selectServer(3)
	c.selectCharacter('Developer Bodom', 1)
	c.play()
	print('done')
