#!/usr/bin/env python3

''' Network classes for python UO client '''

import socket
import struct
import logging


class Network:
	''' Network handler '''

	## Decompression Tree, internal usage. Thanks to UOXNA project
	DECOMPRESSION_TREE = (
		# leaf0, leaf1, #node
		( 2, 1 ), #0
		( 4, 3 ), #1
		( 0, 5 ), #2
		( 7, 6 ), #3
		( 9, 8 ), #4
		( 11, 10 ), #5
		( 13, 12 ), #6
		( 14, -256 ), #7
		( 16, 15 ), #8
		( 18, 17 ), #9
		( 20, 19 ), #10
		( 22, 21 ), #11
		( 23, -1 ), #12
		( 25, 24 ), #13
		( 27, 26 ), #14
		( 29, 28 ), #15
		( 31, 30 ), #16
		( 33, 32 ), #17
		( 35, 34 ), #18
		( 37, 36 ), #19
		( 39, 38 ), #20
		( -64, 40 ), #21
		( 42, 41 ), #22
		( 44, 43 ), #23
		( 45, -6 ), #24
		( 47, 46 ), #25
		( 49, 48 ), #26
		( 51, 50 ), #27
		( 52, -119 ), #28
		( 53, -32 ), #29
		( -14, 54 ), #30
		( -5, 55 ), #31
		( 57, 56 ), #32
		( 59, 58 ), #33
		( -2, 60 ), #34
		( 62, 61 ), #35
		( 64, 63 ), #36
		( 66, 65 ), #37
		( 68, 67 ), #38
		( 70, 69 ), #39
		( 72, 71 ), #40
		( 73, -51 ), #41
		( 75, 74 ), #42
		( 77, 76 ), #43
		( -111, -101 ), #44
		( -97, -4 ), #45
		( 79, 78 ), #46
		( 80, -110 ), #47
		( -116, 81 ), #48
		( 83, 82 ), #49
		( -255, 84 ), #50
		( 86, 85 ), #51
		( 88, 87 ), #52
		( 90, 89 ), #53
		( -10, -15 ), #54
		( 92, 91 ), #55
		( 93, -21 ), #56
		( 94, -117 ), #57
		( 96, 95 ), #58
		( 98, 97 ), #59
		( 100, 99 ), #60
		( 101, -114 ), #61
		( 102, -105 ), #62
		( 103, -26 ), #63
		( 105, 104 ), #64
		( 107, 106 ), #65
		( 109, 108 ), #66
		( 111, 110 ), #67
		( -3, 112 ), #68
		( -7, 113 ), #69
		( -131, 114 ), #70
		( -144, 115 ), #71
		( 117, 116 ), #72
		( 118, -20 ), #73
		( 120, 119 ), #74
		( 122, 121 ), #75
		( 124, 123 ), #76
		( 126, 125 ), #77
		( 128, 127 ), #78
		( -100, 129 ), #79
		( -8, 130 ), #80
		( 132, 131 ), #81
		( 134, 133 ), #82
		( 135, -120 ), #83
		( -31, 136 ), #84
		( 138, 137 ), #85
		( -234, -109 ), #86
		( 140, 139 ), #87
		( 142, 141 ), #88
		( 144, 143 ), #89
		( 145, -112 ), #90
		( 146, -19 ), #91
		( 148, 147 ), #92
		( -66, 149 ), #93
		( -145, 150 ), #94
		( -65, -13 ), #95
		( 152, 151 ), #96
		( 154, 153 ), #97
		( 155, -30 ), #98
		( 157, 156 ), #99
		( 158, -99 ), #100
		( 160, 159 ), #101
		( 162, 161 ), #102
		( 163, -23 ), #103
		( 164, -29 ), #104
		( 165, -11 ), #105
		( -115, 166 ), #106
		( 168, 167 ), #107
		( 170, 169 ), #108
		( 171, -16 ), #109
		( 172, -34 ), #110
		( -132, 173 ), #111
		( -108, 174 ), #112
		( -22, 175 ), #113
		( -9, 176 ), #114
		( -84, 177 ), #115
		( -37, -17 ), #116
		( 178, -28 ), #117
		( 180, 179 ), #118
		( 182, 181 ), #119
		( 184, 183 ), #120
		( 186, 185 ), #121
		( -104, 187 ), #122
		( -78, 188 ), #123
		( -61, 189 ), #124
		( -178, -79 ), #125
		( -134, -59 ), #126
		( -25, 190 ), #127
		( -18, -83 ), #128
		( -57, 191 ), #129
		( 192, -67 ), #130
		( 193, -98 ), #131
		( -68, -12 ), #132
		( 195, 194 ), #133
		( -128, -55 ), #134
		( -50, -24 ), #135
		( 196, -70 ), #136
		( -33, -94 ), #137
		( -129, 197 ), #138
		( 198, -74 ), #139
		( 199, -82 ), #140
		( -87, -56 ), #141
		( 200, -44 ), #142
		( 201, -248 ), #143
		( -81, -163 ), #144
		( -123, -52 ), #145
		( -113, 202 ), #146
		( -41, -48 ), #147
		( -40, -122 ), #148
		( -90, 203 ), #149
		( 204, -54 ), #150
		( -192, -86 ), #151
		( 206, 205 ), #152
		( -130, 207 ), #153
		( 208, -53 ), #154
		( -45, -133 ), #155
		( 210, 209 ), #156
		( -91, 211 ), #157
		( 213, 212 ), #158
		( -88, -106 ), #159
		( 215, 214 ), #160
		( 217, 216 ), #161
		( -49, 218 ), #162
		( 220, 219 ), #163
		( 222, 221 ), #164
		( 224, 223 ), #165
		( 226, 225 ), #166
		( -102, 227 ), #167
		( 228, -160 ), #168
		( 229, -46 ), #169
		( 230, -127 ), #170
		( 231, -103 ), #171
		( 233, 232 ), #172
		( 234, -60 ), #173
		( -76, 235 ), #174
		( -121, 236 ), #175
		( -73, 237 ), #176
		( 238, -149 ), #177
		( -107, 239 ), #178
		( 240, -35 ), #179
		( -27, -71 ), #180
		( 241, -69 ), #181
		( -77, -89 ), #182
		( -118, -62 ), #183
		( -85, -75 ), #184
		( -58, -72 ), #185
		( -80, -63 ), #186
		( -42, 242 ), #187
		( -157, -150 ), #188
		( -236, -139 ), #189
		( -243, -126 ), #190
		( -214, -142 ), #191
		( -206, -138 ), #192
		( -146, -240 ), #193
		( -147, -204 ), #194
		( -201, -152 ), #195
		( -207, -227 ), #196
		( -209, -154 ), #197
		( -254, -153 ), #198
		( -156, -176 ), #199
		( -210, -165 ), #200
		( -185, -172 ), #201
		( -170, -195 ), #202
		( -211, -232 ), #203
		( -239, -219 ), #204
		( -177, -200 ), #205
		( -212, -175 ), #206
		( -143, -244 ), #207
		( -171, -246 ), #208
		( -221, -203 ), #209
		( -181, -202 ), #210
		( -250, -173 ), #211
		( -164, -184 ), #212
		( -218, -193 ), #213
		( -220, -199 ), #214
		( -249, -190 ), #215
		( -217, -230 ), #216
		( -216, -169 ), #217
		( -197, -191 ), #218
		( 243, -47 ), #219
		( 245, 244 ), #220
		( 247, 246 ), #221
		( -159, -148 ), #222
		( 249, 248 ), #223
		( -93, -92 ), #224
		( -225, -96 ), #225
		( -95, -151 ), #226
		( 251, 250 ), #227
		( 252, -241 ), #228
		( -36, -161 ), #229
		( 254, 253 ), #230
		( -39, -135 ), #231
		( -124, -187 ), #232
		( -251, 255 ), #233
		( -238, -162 ), #234
		( -38, -242 ), #235
		( -125, -43 ), #236
		( -253, -215 ), #237
		( -208, -140 ), #238
		( -235, -137 ), #239
		( -237, -158 ), #240
		( -205, -136 ), #241
		( -141, -155 ), #242
		( -229, -228 ), #243
		( -168, -213 ), #244
		( -194, -224 ), #245
		( -226, -196 ), #246
		( -233, -183 ), #247
		( -167, -231 ), #248
		( -189, -174 ), #249
		( -166, -252 ), #250
		( -222, -198 ), #251
		( -179, -188 ), #252
		( -182, -223 ), #253
		( -186, -180 ), #254
		( -247, -245 ), #255
	)

	def __init__(self, ip, port):
		''' Connects to the socket '''
		## Logger, for internal usage
		self.log = logging.getLogger('net')
		## Socket connection, for internal usage
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((ip, port))
		## Buffer, for internal usage
		self.buf = b''
		## Wether to use compression or not
		self.compress = False

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

		if self.compress:
			raw = self.decompress(self.buf)
		else:
			raw = self.buf

		# Process it
		cmd = raw[0]
		c = 1
		if cmd in (Packet.ENABLE_FEATURES, ):
			length = 3
		elif cmd in (Packet.CONNECT_TO_GAME_SERVER, ):
			length = 11
		elif cmd in (Packet.SERVER_LIST, ):
			length = struct.unpack('>H',raw[c : c+2])[0]
			c += 2
		else:
			raise NotImplementedError("Unknown cmd 0x%0.2X" % cmd)
		data = raw[c : c+length]
		c += length

		self.log.debug('<- 0x%0.2X %s"%s"', cmd, 'C' if self.compress else '', data)
		pkt = Packet(cmd, length, data)

		# Remove the processed packet from the buffer the buffer
		self.buf = self.buf[c:]

		return pkt

	def decompress(self, buf):
		node = 0
		leaf = 0
		leafVal = 0
		bitNum = 8
		srcPos = 0
		dest = b''

		while srcPos < len(buf):
			# Gets next bit
			leaf = ( buf[srcPos] >> ( bitNum - 1 ) ) & 1
			leafVal = self.DECOMPRESSION_TREE[node][leaf]

			# all numbers below 1 (0..-256) are codewords
			# if the halt codeword has been found, skip this byte
			if leafVal == -256:
				return dest
			elif leafVal < 1:
				dest += bytes([0 - leafVal])
				leafVal = 0

			# Go for next bit, if its the end of the byte, go to the next byte
			bitNum -= 1
			node = leafVal
			if bitNum < 1:
				bitNum = 8;
				srcPos += 1

			# check to see if the current codeword has no end
			# if not, make it an incomplete byte
			if srcPos == len(buf):
				if node != 0:
					return false;
				else:
					raise NotImplementedError("Incomplete packet")


class Packet:
	''' An UO packet '''

	SERVER_LIST = 0xa8
	LOGIN_REQUEST = 0x80
	CONNECT_TO_GAME_SERVER = 0x8c
	GAME_SERVER_LOGIN = 0x91
	ENABLE_FEATURES = 0xb9

	def __init__(self, cmd, length, data):
		self.cmd = cmd
		self.length = length
		self.data = data

		if self.cmd == Packet.SERVER_LIST:
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

		elif self.cmd == Packet.CONNECT_TO_GAME_SERVER:
			self.descr = 'Connect to Game Server'
			self.ip = struct.unpack('BBBB',self.data[0:4])
			self.port = struct.unpack('>H',self.data[4:6])[0]
			self.key = struct.unpack('>I',self.data[6:12])[0]

		elif self.cmd == Packet.ENABLE_FEATURES:
			self.features = struct.unpack('>H',self.data[0:3])[0]


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
