#!/usr/bin/env python3

'''
Ultima online text client (experiment)
'''

import struct
import ipaddress
import logging

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
		self.send(bytes([net.Packet.LOGIN_REQUEST]) + net.Util.fixStr(self.server['user'],30) + net.Util.fixStr(self.server['pass'],30) + bytes([0x00]))

		# Get servers list
		pkt = self.receive(net.Packet.SERVER_LIST)
		self.log.info("Received serverlist: %s", str(pkt.servers))

		self.status = 'connected'
		return pkt.servers

	@status('connected')
	def selectServer(self, idx):
		''' Selects the game server with the given idx '''
		self.log.info('selecting server %d', idx)
		self.send(struct.pack('>BH', 0xa0, idx))

		pkt = self.receive(net.Packet.CONNECT_TO_GAME_SERVER)
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
		self.send(bytes([net.Packet.GAME_SERVER_LOGIN]) + bkey + net.Util.fixStr(self.server['user'],30) + net.Util.fixStr(self.server['pass'],30))

		# From now on, server will use compression
		self.net.compress = True

		# Get features packet
		pkt = self.receive(net.Packet.ENABLE_FEATURES)
		self.features = pkt.features

		# Get character selection
		pkt = self.receive()
		print(pkt)

	def send(self, data):
		''' Sends a raw packet to the Server '''
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

	logging.basicConfig(level=logging.DEBUG)

	c = Client()
	servers = c.connect(args.ip, args.port, args.user, args.pwd)
	c.selectServer(3)
	print('done')