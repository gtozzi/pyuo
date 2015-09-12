#!/usr/bin/env python3

''' Network classes for python UO client '''

import socket
import struct
import logging


class Network:
	''' Network handler '''

	def __init__(self, ip, port):
		''' Connects to the socket '''
		## Logger, for internal usage
		self.log = logging.getLogger('net')
		## Socket connection, for internal usage
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((ip, port))
		## Buffer, for internal usage
		self.buf = b''

	def close(self):
		''' Disconnects, makes this object unusable '''
		self.sock.close()

	def send(self, data):
		''' Sends a packet, expects raw binary data '''
		self.log.debug('-> "%s"', data)
		self.sock.send(data)

	def recv(self):
		''' Reads next packet from the server, waits until a full packet is received '''

		# Wait for a full packet
		wait = None
		while len(self.buf) < 1:
			if wait:
				self.log.info("Waiting for a packet...")
				wait = False
			self.buf += self.sock.recv(4096)
			if wait is None:
				wait = True

		# Process it
		cmd = self.buf[0]
		c = 1
		if cmd in (Packet.CONNECT_TO_GAME_SERVER, ):
			length = 11
		elif cmd in (Packet.SERVER_LIST, ):
			length = struct.unpack('>H',self.buf[c : c+2])[0]
			c += 2
		else:
			raise NotImplementedError("Unknown cmd 0x%0.2X" % cmd)
		data = self.buf[c : c+length]
		c += length

		self.log.debug('<- 0x%0.2X "%s"', cmd, data)
		pkt = Packet(cmd, length, data)

		# Remove the processed packet from the buffer the buffer
		self.buf = self.buf[c:]

		return pkt


class Packet:
	''' An UO packet '''

	SERVER_LIST = 0xa8
	LOGIN_REQUEST = 0x80
	CONNECT_TO_GAME_SERVER = 0x8c
	GAME_SERVER_LOGIN = 0x91

	def __init__(self, cmd, length, data):
		self.cmd = cmd
		self.length = length
		self.data = data

		if( self.cmd == Packet.SERVER_LIST ):
			self.descr = 'Receive Server List'
			self.flag = self.data[0]
			self.numServers = struct.unpack('>H',self.data[1:3])[0]
			self.servers = []
			for i in range(0, self.numServers):
				o = i * 40
				self.servers.append({
					'idx': struct.unpack('>H',self.data[3+o:5+o])[0],
					'name': Util.varStr(self.data[5+o:36+o]),
					'full': self.data[36+o],
					'tz': self.data[37+o],
					'ip': struct.unpack('BBBB',self.data[39+o:43+o]),
				})

		elif( self.cmd == Packet.CONNECT_TO_GAME_SERVER ):
			self.descr = 'Connect to Game Server'
			self.ip = struct.unpack('BBBB',self.data[0:4])
			self.port = struct.unpack('>H',self.data[4:6])[0]
			self.key = struct.unpack('>I',self.data[6:12])[0]


class Util:
	''' Utility class for conversions and so on '''

	@staticmethod
	def fixStr(string, length):
		''' Convert a str to fixed length, return bytes '''
		enc = string.encode('ascii')
		ret = b''
		for i in range(0,length):
			try:
				ret += bytes([enc[i]])
			except IndexError:
				ret += b'\x00'
		return ret

	@staticmethod
	def varStr(byt):
		''' Convert bytes into a variable-length string '''
		return byt.decode('ascii').rstrip('\x00')
