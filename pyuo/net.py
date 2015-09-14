#!/usr/bin/env python3

''' Network classes for Python Ultima Online text client '''

import time
import socket
import struct
import ipaddress
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
		self.log.debug('-> 0x%0.2X, %d bytes\n"%s"', data[0], len(data), data)
		self.sock.send(data)

	def recv(self, force=False):
		''' Reads next packet from the server, waits until a full packet is received '''

		# Wait for a full packet
		if len(self.buf) < 1 or force:
			data = self.sock.recv(4096)
			if not len(data):
				raise RuntimeError("Disconnected");
			self.buf += data

		if self.compress:
			try:
				raw, size = self.decompress(self.buf)
			except NoFullPacketError:
				# Not enough data to make a full packet. Sleep for a while and try again
				# TODO: definitely handle this better
				self.log.warn("No full packet. Waiting... (%d bytes in buffer)", len(self.buf))
				time.sleep(1)
				return self.recv(True)
		else:
			raw = self.buf
			size = len(self.buf)

		if not raw:
			raise NotImplementedError()

		cinfo = '{} compressed'.format(size) if self.compress else 'not compressed'
		self.log.debug('<- 0x%0.2X, %d bytes, %s\n"%s"', raw[0], len(raw), cinfo, raw)

		pkt = Ph.process(raw)
		pkt.validate()
		assert pkt.validated
		assert pkt.length == len(raw)

		# Remove the processed packet from the buffer the buffer
		self.buf = self.buf[size:]

		return pkt

	def decompress(self, buf):
		''' Internal usage, decompress a packet (thanks to UltimaXNA project
		@return tuple (decompressed, compressed_size)
		'''
		node = 0
		leaf = 0
		leafVal = 0
		bitNum = 8
		srcPos = 0
		dest = b''

		while srcPos < len(buf):
			# Gets next bit
			leaf = ( buf[srcPos] >> ( bitNum - 1 ) ) & 1
			# Look into decompression table
			leafVal = self.DECOMPRESSION_TREE[node][leaf]

			# all numbers below 1 (0..-256) are codewords
			# if the halt codeword has been found, skip this byte
			if leafVal == -256:
				return ( dest, srcPos + 1)
			elif leafVal < 1:
				dest += bytes([0 - leafVal])
				leafVal = 0

			# Go for next bit, if its the end of the byte, go to the next byte
			bitNum -= 1
			node = leafVal
			if bitNum < 1:
				bitNum = 8;
				srcPos += 1

		raise NoFullPacketError("No full packet could be read")


class Packet:
	''' Base class for packets '''

	def __init__(self, buf):
		self.log = logging.getLogger('packet')
		self.buf = buf
		self.readCount = 0
		self.validated = False
		cmd = self.uchar()
		if cmd != self.cmd:
			raise RuntimeError("Invalid data for this packet {} <> {}".format(cmd, self.cmd))

	def pb(self, num):
		''' Returns the given number of characters from the gibven buffer '''
		if num > len(self.buf):
			raise EOFError("Trying to read {} bytes, but only {} left in buffer".format(num, len(self.buf)))
		self.readCount += num
		ret = self.buf[:num]
		self.buf = self.buf[num:]
		return ret

	def uchar(self):
		''' Returns next unsngned byte from the buffer '''
		return struct.unpack('B', self.pb(1))[0]

	def schar(self):
		''' Returns next signed byte from the buffer '''
		return struct.unpack('b', self.pb(1))[0]

	def ushort(self):
		''' Returns next unsigned short from the buffer '''
		return struct.unpack('>H', self.pb(2))[0]

	def uint(self):
		''' Returns next unsigned int from the buffer '''
		return struct.unpack('>I', self.pb(4))[0]

	def string(self, length):
		''' Returns next string of the given length from the buffer '''
		return Util.varStr(self.pb(length))

	def ip(self):
		''' Returns next string ip address from the buffer '''
		return struct.unpack('BBBB', self.pb(4))

	def validate(self):
		''' Do validations things, but be called at end of init '''
		if( self.length != self.readCount ):
			self.log.debug(self.__dict__)
			raise RuntimeError("Len mismatch on packet 0x{:02x} ({} <> {})".format(self.cmd, self.length, self.readCount))
		self.validated = True


class ServerListPacket(Packet):
	''' Receive server list '''

	cmd = 0xa8

	def __init__(self, buf):
		super().__init__(buf)
		self.length = self.ushort()
		self.flag = self.uchar()
		self.numServers = self.ushort()
		self.servers = []
		for i in range(0, self.numServers):
			self.servers.append({
				'idx': self.ushort(),
				'name': self.string(32),
				'full': self.uchar(),
				'tz': self.uchar(),
				'ip': self.ip(),
			})


class EnableFeaturesPacket(Packet):
	''' Used to enable client features '''

	cmd = 0xb9
	length = 3

	def __init__(self, buf):
		super().__init__(buf)
		self.features = self.ushort()


class ConnectToGameServerPacket(Packet):
	''' Login server is requesting to connect to the game server '''

	cmd = 0x8c
	length = 11

	def __init__(self, buf):
		super().__init__(buf)
		self.ip = self.ip()
		self.port = self.ushort()
		self.key = self.uint()


class PingPacket(Packet):
	''' Ping request/reply '''

	cmd = 0x73
	length = 2

	def __init__(self, buf):
		super().__init__(buf)
		self.seq = self.uchar()


class CharactersPacket(Packet):
	''' Gets lists of characters and starting locations from server '''

	cmd = 0xa9

	def __init__(self, buf):
		super().__init__(buf)
		self.length = self.ushort()
		self.numChars = self.uchar()
		self.chars = []
		for i in range(0, self.numChars):
			self.chars.append({
				'name': self.string(30),
				'pass': self.string(30),
			})
		self.numLocs = self.uchar()
		self.locs = []
		for i in range(0, self.numLocs):
			self.locs.append({
				'idx': self.uchar(),
				'name': self.string(31),
				'area': self.string(31),
			})
		self.flags = self.uint()


class CharLocaleBodyPacket(Packet):
	''' Server giving info about Char, Locale, and Body '''

	cmd = 0x1b
	length = 37

	def __init__(self, buf):
		super().__init__(buf)
		self.serial = self.uint()
		unk = self.uint() # Uknown
		self.bodyType = self.ushort()
		self.x = self.ushort()
		self.y = self.ushort()
		unk = self.uchar() # Unknown
		self.z = self.schar()
		self.facing = self.schar()
		unk = self.uint() # Unknown
		unk = self.uint() # Unknown
		unk = self.schar() # Unknown
		self.widthM8 = self.ushort()
		self.height = self.ushort()
		unk = self.ushort() # Unknown
		unk = self.uint() # Unknown


class GeneralInfoPacket(Packet):
	''' This packet does a lot of different things, based on subcommand '''

	## Initialize fastwalk prevention
	SUB_FASTWALK = 0x01
	## Add a key to fastwalk stack
	SUB_ADDFWKEY = 0x02
	## Close generic gump
	SUB_CLOSEGUMP = 0x04
	## Screen size
	SUB_SCREENSIZE = 0x05
	## Party system
	SUB_PARTY = 0x06
	## Set cursor hue / set map
	SUB_CURSORMAP = 0x08
	## Wrestling stun
	SUB_STUN = 0x0a
	## CLient language
	SUB_LANG = 0x0b
	## Closed status gump
	SUB_CLOSESTATUS = 0x0c
	## 3D Action
	SUB_3DACT = 0x0e
	## Enable map-diff files
	SUB_MAPDIFF = 0x18

	cmd = 0xbf

	def __init__(self, buf):
		super().__init__(buf)
		self.length = self.ushort()
		self.sub = self.ushort()

		if self.sub == self.SUB_FASTWALK:
			self.keys = []
			for i in range(0, 6):
				self.keys.append(self.uint())

		elif self.sub == self.SUB_ADDFWKEY:
			self.key = self.uint()

		elif self.sub == self.SUB_CLOSEGUMP:
			self.gumpid = self.uint()
			self.buttonid = self.uint()

		elif self.sub == self.SUB_SCREENSIZE:
			unk = self.ushort()
			self.x = self.ushort()
			self.y = self.ushort()
			unk = self.ushort()

		elif self.sub == self.SUB_PARTY:
			self.data = self.pb(len(self.buf))

		elif self.sub == self.SUB_CURSORMAP:
			self.cursor = self.uchar()

		elif self.sub == self.SUB_STUN:
			raise NotImplementedError("This should no longer be used")

		elif self.sub == self.SUB_LANG:
			self.lang = self.string(3)

		elif self.sub == self.SUB_CLOSESTATUS:
			self.serial = self.uint()

		elif self.sub == self.SUB_3DACT:
			self.animation = self.uint()

		elif self.sub == self.SUB_MAPDIFF:
			mapNum = self.uint()
			self.maps = []
			for i in range(0, mapNum):
				self.maps.append({
					'mpatches': self.uint(),
					'spatches': self.uint(),
				})

		else:
			raise NotImplementedError("Subcommand 0x%0.2X not implemented yet." % self.sub)


class Unk32Packet(Packet):
	''' Unknown packet '''

	cmd = 0x32
	length = 2

	def __init__(self, buf):
		super().__init__(buf)
		self.uchar()


class ControlAnimationPacket(Packet):
	''' Control Animation '''

	cmd = 0x1e
	length = 4

	def __init__(self, buf):
		super().__init__(buf)
		self.uchar() # Unknown
		self.uchar() # Unknown
		self.uchar() # Unknown


class CharacterAnimationPacket(Packet):
	''' Play an animation for a character '''

	cmd = 0x6e
	length = 14

	def __init__(self, buf):
		super().__init__(buf)
		self.serial = self.uint()
		self.action = self.ushort()
		self.uchar() # unknown
		self.frames = self.uchar()
		self.repeat = self.ushort()
		self.backwards = self.uchar()
		self.repeat = self.uchar()
		self.delay = self.uchar()


class GraphicalEffectPacket(Packet):
	''' Play a generic graphical effect '''

	cmd = 0x70
	length = 28

	def __init__(self, buf):
		super().__init__(buf)
		self.direction = self.uchar()
		self.serial = self.uint()
		self.target = self.uint()
		self.graphic = self.ushort()
		self.x = self.ushort()
		self.y = self.ushort()
		self.z = self.schar()
		self.tx = self.ushort()
		self.ty = self.ushort()
		self.tz = self.schar()
		self.speed = self.uchar()
		self.duration = self.uchar()
		self.ushort() # Unknown
		self.adjust = self.uchar()
		self.explode = self.uchar()


class DrawGamePlayerPacket(Packet):
	''' Draw game player '''

	cmd = 0x20
	length = 19

	def __init__(self, buf):
		super().__init__(buf)
		self.serial = self.uint()
		self.graphic = self.ushort()
		self.uchar() # unknown
		self.hue = self.ushort()
		self.flag = self.uchar()
		self.x = self.ushort()
		self.y = self.ushort()
		self.ushort() # unknown
		self.direction = self.schar()
		self.z = self.schar()


class OverallLightLevelPacket(Packet):
	''' Overall Light Level '''

	cmd = 0x4f
	length = 2

	def __init__(self, buf):
		super().__init__(buf)
		self.level = self.uchar()


class SendSpeechPacket(Packet):
	''' Send(Receive) Speech '''

	cmd = 0x1c

	def __init__(self, buf):
		super().__init__(buf)
		self.length = self.ushort()
		self.serial = self.uint()
		self.model = self.ushort()
		self.type = self.uchar()
		self.color = self.ushort()
		self.font = self.ushort()
		self.name = self.string(30)
		self.msg = self.string(self.length-44)


class UnicodeSpeech(Packet):
	''' Receive an unicode speech '''

	cmd = 0xae

	def __init__(self, buf):
		super().__init__(buf)
		self.length = self.ushort()
		self.serial = self.uint()
		self.model = self.ushort()
		self.type = self.uchar()
		self.color = self.ushort()
		self.font = self.ushort()
		self.lang = self.ushort()
		self.name = self.string(30)
		self.msg = self.string(self.length-48+2)


class PlayMidiPacket(Packet):
	''' Play Midi Music '''

	cmd = 0x6d
	length = 3

	def __init__(self, buf):
		super().__init__(buf)
		self.music = self.ushort()


class WarModePacket(Packet):
	''' Request/Set war mode '''

	cmd = 0x72
	length = 5

	def __init__(self, buf):
		super().__init__(buf)
		self.war = self.uchar()
		self.uchar() # unknown
		self.uchar() # unknown
		self.uchar() # unknown


class LoginCompletePacket(Packet):
	''' Login Complete '''

	cmd = 0x55
	length = 1

	def __init__(self, buf):
		super().__init__(buf)


class SetWeatherPacket(Packet):
	''' Sets Weather '''

	cmd = 0x65
	length = 4

	def __init__(self, buf):
		super().__init__(buf)
		self.type = self.uchar()
		self.num = self.uchar()
		self.temp = self.uchar()


class DrawObjectPacket(Packet):
	''' Draws a mobile '''

	cmd = 0x78

	def __init__(self, buf):
		super().__init__(buf)
		self.length = self.ushort()
		self.serial = self.uint()
		self.graphic = self.ushort()
		self.x = self.ushort()
		self.y = self.ushort()
		self.z = self.schar()
		self.facing = self.schar()
		self.color = self.ushort()
		self.flag = self.uchar()
		self.notoriety = self.uchar()
		self.equip = []
		while True:
			serial = self.uint()
			if not serial:
				break
			graphic = self.ushort()
			layer = self.uchar()
			if graphic & 0x8000:
				color = self.ushort()
			else:
				color = 0
			self.equip.append({
				'serial': serial,
				'graphic': graphic,
				'layer': layer,
				'color': color,
			})
		if not len(self.equip):
			self.uchar() # unused/closing


class UpdatePlayerPacket(Packet):
	''' Updates a mobile '''

	cmd = 0x77
	length = 17

	def __init__(self, buf):
		super().__init__(buf)
		self.serial = self.uint()
		self.graphic = self.ushort()
		self.x = self.ushort()
		self.y = self.ushort()
		self.z = self.schar()
		self.facing = self.schar()
		self.color = self.ushort()
		self.flag = self.uchar()
		self.notoriety = self.uchar()


class ObjectInfoPacket(Packet):
	''' Braws an item '''

	cmd = 0x1a

	def __init__(self, buf):
		super().__init__(buf)
		self.length = self.ushort()
		self.serial = self.uint()
		self.graphic = self.ushort()
		if self.serial & 0x80000000:
			self.count = self.ushort()
		else:
			self.count = None
		if self.graphic & 0x8000:
			self.graphic += self.uchar()
		x = self.ushort()
		y = self.ushort()
		if x & 0x8000:
			self.facing = self.schar()
		else:
			self.facing = None
		self.z = self.schar()
		if y & 0x8000:
			self.color = self.ushort()
		else:
			self.color = None
		if y & 0x4000:
			self.flag = self.uchar()
		else:
			self.flag = None
		self.x = x & 0x7fff
		self.y = y & 0x3fff


class AddItemToContainerPacket(Packet):
	''' Adds a single item to a container '''

	cmd = 0x25
	length = 20

	def __init__(self, buf):
		super().__init__(buf)
		self.serial = self.uint()
		self.graphic = self.ushort()
		self.offset = self.uchar()
		self.amount = self.ushort()
		self.x = self.ushort()
		self.y = self.ushort()
		self.container = self.uint()
		self.color = self.ushort()


class AddItemsToContainerPacket(Packet):
	''' Adds multiple items to a container '''

	cmd = 0x3c

	def __init__(self, buf):
		super().__init__(buf)
		self.length = self.ushort()
		itemNum = self.ushort()
		self.items = []
		for i in range(0, itemNum):
			self.items.append({
				'serial': self.uint(),
				'graphic': self.ushort(),
				'unknown': self.uchar(),
				'amount': self.ushort(),
				'x': self.ushort(),
				'y': self.ushort(),
				'container': self.uint(),
				'color': self.ushort(),
			})


class DeleteObjectPacket(Packet):
	''' Object went out of sight '''

	cmd = 0x1d
	length = 5

	def __init__(self, buf):
		super().__init__(buf)
		self.serial = self.uint()


class DrawContainerPacket(Packet):
	''' Draws a container's gump '''

	cmd = 0x24
	length = 7

	def __init__(self, buf):
		super().__init__(buf)
		self.serial = self.uint()
		self.gump = self.ushort()


class AllowAtackPacket(Packet):
	''' Allow/Refuse attack '''

	cmd = 0xaa
	length = 5

	def __init__(self, buf):
		super().__init__(buf)
		self.serial = self.uint()


class TipWindowPacket(Packet):
	''' Tip/Notice Window '''

	cmd = 0xa6

	def __init__(self, buf):
		super().__init__(buf)
		self.length = self.ushort()
		self.flag = self.uchar()
		self.tipid = self.uint()
		msgSize = self.ushort()
		self.msg = self.string(msgSize)


class PlaySoundPacket(Packet):
	''' Play Sound Effect '''

	cmd = 0x54
	length = 12

	def __init__(self, buf):
		super().__init__(buf)
		self.mode = self.uchar()
		self.model = self.ushort()
		self.ushort() # unknown
		self.x = self.ushort()
		self.y = self.ushort()
		self.z = self.ushort()


class LoginDeniedPacket(Packet):
	''' Login Denied '''

	cmd = 0x82
	length = 2

	def __init__(self, buf):
		super().__init__(buf)
		self.reason = self.uchar()


class UpdateVitalPacket(Packet):
	''' Just an utility base class '''

	length = 9

	def __init__(self, buf):
		super().__init__(buf)
		self.serial = self.uint()
		self.max = self.ushort()
		self.cur = self.ushort()


class UpdateHealthPacket(UpdateVitalPacket):
	''' Updates current health '''

	cmd = 0xa1

	def __init__(self, buf):
		super().__init__(buf)


class UpdateManaPacket(UpdateVitalPacket):
	''' Updates current mana '''

	cmd = 0xa2

	def __init__(self, buf):
		super().__init__(buf)


class UpdateStaminaPacket(UpdateVitalPacket):
	''' Updates current stamina '''

	cmd = 0xa3

	def __init__(self, buf):
		super().__init__(buf)


class StatusBarInfoPacket(Packet):
	''' Sends status bar info '''

	cmd = 0x11

	def __init__(self, buf):
		super().__init__(buf)
		self.length = self.ushort()
		self.serial = self.uint()
		self.name = self.string(30)
		self.hp = self.ushort()
		self.maxhp = self.ushort()
		self.canrename = self.uchar()
		flag = self.uchar()
		## Sex and race: 0 = Human Male, 1 = Human female, 2 = Elf Male, 3 = Elf Female
		self.gener = self.uchar()
		self.str = self.ushort()
		self.dex = self.ushort()
		self.int = self.ushort()
		self.stam = self.ushort()
		self.maxstam = self.ushort()
		self.mana = self.ushort()
		self.maxmana = self.ushort()
		self.gold = self.uint()
		self.ar = self.ushort()
		self.weight = self.ushort()
		if flag >= 5:
			self.maxweight = self.ushort()
			## Race: 1 = Human, 2 = Elf, 3 = Gargoyle
			self.race = self.uchar()
		if flag >= 3:
			self.statcap = self.ushort()
			self.followers = self.uchar()
			self.maxfollowers = self.uchar()
		if flag >= 4:
			self.rfire = self.ushort()
			self.rcold = self.ushort()
			self.rpoison = self.ushort()
			self.renergy = self.ushort()
			self.luck = self.ushort()
			self.mindmg = self.ushort()
			self.maxdmg = self.ushort()
			self.tithing = self.uint()
		if flag >= 6:
			self.hitinc = self.ushort()
			self.swinginc = self.ushort()
			self.dmginc = self.ushort()
			self.lrc = self.ushort()
			self.hpregen = self.ushort()
			self.stamregen = self.ushort()
			self.manaregen = self.ushort()
			self.reflectphysical = self.ushort()
			self.enhancepot = self.ushort()
			self.definc = self.ushort()
			self.spellinc = self.ushort()
			self.fcr = self.ushort()
			self.fc = self.ushort()
			self.lmc = self.ushort()
			self.strinc = self.ushort()
			self.dexinc = self.ushort()
			self.intinc = self.ushort()
			self.hpinc = self.ushort()
			self.staminc = self.ushort()
			self.manainc = self.ushort()
			self.maxhpinc = self.ushort()
			self.maxstaminc = self.ushort()
			self.maxmanainc = self.ushort()


class SendSkillsPacket(Packet):
	''' When received contains a single skill or full list of skills
	When sent by client, sets skill lock for a single skill '''

	cmd = 0x3a

	def __init__(self, buf):
		super().__init__(buf)
		self.length = self.ushort()
		typ = self.uchar() # 0x00 full list, 0xff single skill, 0x02 full with caps, 0xdf single with caps
		self.skills = {}
		while True:
			id = self.ushort()
			if not id:
				break
			assert id not in self.skills
			self.skills[id] = {
				'id': id,
				'val': self.ushort(), # Current value, in tenths
				'base': self.ushort(), # Base value, in tenths
				'lock': self.uchar(), # Lock status 0 = up, 1 = down, 2 =locked
				'cap': self.ushort() if typ == 0x02 or typ == 0xdf else None
			}


class SeasonInfoPacket(Packet):
	''' Seasonal Information Packet '''

	cmd = 0xbc
	length = 3

	def __init__(self, buf):
		super().__init__(buf)
		self.flag = self.uchar()
		self.sound = self.uchar()


class SendGumpDialogPacket(Packet):
	''' Receiving a gump from the server '''

	cmd = 0xb0

	def __init__(self, buf):
		super().__init__(buf)
		self.length = self.ushort()
		self.serial = self.uint()
		self.gumpid = self.uint()
		self.x = self.uint()
		self.y = self.uint()
		cmdLen = self.ushort()
		self.commands = self.string(cmdLen)
		textLines = self.ushort()
		self.texts = []
		for i in range(0, textLines):
			tlen = self.ushort() # In unicode 2-bytes chars
			self.texts.append(self.string(tlen*2))


class Ph:
	''' Packet Handler '''

	SERVER_LIST              = ServerListPacket.cmd
	LOGIN_CHARACTER          = 0x5d
	LOGIN_REQUEST            = 0x80
	CHARACTERS               = CharactersPacket.cmd
	CONNECT_TO_GAME_SERVER   = ConnectToGameServerPacket.cmd
	GAME_SERVER_LOGIN        = 0x91
	REQUEST_STATUS           = 0x34
	CLIENT_VERSION           = 0xbd
	SINGLE_CLICK             = 0x09
	DOUBLE_CLICK             = 0x06
	UNICODE_SPEECH_REQUEST   = 0xad
	PING                     = PingPacket.cmd
	ENABLE_FEATURES          = EnableFeaturesPacket.cmd
	CHAR_LOCALE_BODY         = CharLocaleBodyPacket.cmd
	GENERAL_INFO             = GeneralInfoPacket.cmd
	UNKNOWN_32               = Unk32Packet.cmd
	CONTROL_ANIMATION        = ControlAnimationPacket.cmd
	CHARACTER_ANIMATION      = CharacterAnimationPacket.cmd
	GRAPHICAL_EFFECT         = GraphicalEffectPacket.cmd
	DRAW_GAME_PLAYER         = DrawGamePlayerPacket.cmd
	OVERALL_LIGHT_LEVEL      = OverallLightLevelPacket.cmd
	SEND_SPEECH              = SendSpeechPacket.cmd
	UNICODE_SPEECH           = UnicodeSpeech.cmd
	PLAY_MIDI                = PlayMidiPacket.cmd
	WAR_MODE                 = WarModePacket.cmd
	LOGIN_COMPLETE           = LoginCompletePacket.cmd
	SET_WEATHER              = SetWeatherPacket.cmd
	SEASON_INFO              = SeasonInfoPacket.cmd
	DRAW_OBJECT              = DrawObjectPacket.cmd
	UPDATE_PLAYER            = UpdatePlayerPacket.cmd
	OBJECT_INFO              = ObjectInfoPacket.cmd
	DELETE_OBJECT            = DeleteObjectPacket.cmd
	DRAW_CONTAINER           = DrawContainerPacket.cmd
	ADD_ITEM_TO_CONTAINER    = AddItemToContainerPacket.cmd
	ADD_ITEMS_TO_CONTAINER   = AddItemsToContainerPacket.cmd
	ALLOW_ATTACK             = AllowAtackPacket.cmd
	TIP_WINDOW               = TipWindowPacket.cmd
	PLAY_SOUND               = PlaySoundPacket.cmd
	LOGIN_DENIED             = LoginDeniedPacket.cmd
	UPDATE_HEALTH            = UpdateHealthPacket.cmd
	UPDATE_MANA              = UpdateManaPacket.cmd
	UPDATE_STAMINA           = UpdateStaminaPacket.cmd
	STATUS_BAR_INFO          = StatusBarInfoPacket.cmd
	SEND_SKILL               = SendSkillsPacket.cmd
	SEND_GUMP                = SendGumpDialogPacket.cmd

	HANDLERS = {
		SERVER_LIST:              ServerListPacket,
		CONNECT_TO_GAME_SERVER:   ConnectToGameServerPacket,
		PING:                     PingPacket,
		ENABLE_FEATURES:          EnableFeaturesPacket,
		CHARACTERS:               CharactersPacket,
		CHAR_LOCALE_BODY:         CharLocaleBodyPacket,
		GENERAL_INFO:             GeneralInfoPacket,
		UNKNOWN_32:               Unk32Packet,
		CONTROL_ANIMATION:        ControlAnimationPacket,
		CHARACTER_ANIMATION:      CharacterAnimationPacket,
		GRAPHICAL_EFFECT:         GraphicalEffectPacket,
		DRAW_GAME_PLAYER:         DrawGamePlayerPacket,
		OVERALL_LIGHT_LEVEL:      OverallLightLevelPacket,
		SEND_SPEECH:              SendSpeechPacket,
		UNICODE_SPEECH:           UnicodeSpeech,
		PLAY_MIDI:                PlayMidiPacket,
		WAR_MODE:                 WarModePacket,
		LOGIN_COMPLETE:           LoginCompletePacket,
		SET_WEATHER:              SetWeatherPacket,
		SEASON_INFO:              SeasonInfoPacket,
		DRAW_OBJECT:              DrawObjectPacket,
		UPDATE_PLAYER:            UpdatePlayerPacket,
		OBJECT_INFO:              ObjectInfoPacket,
		DELETE_OBJECT:            DeleteObjectPacket,
		DRAW_CONTAINER:           DrawContainerPacket,
		ADD_ITEM_TO_CONTAINER:    AddItemToContainerPacket,
		ADD_ITEMS_TO_CONTAINER:   AddItemsToContainerPacket,
		ALLOW_ATTACK:             AllowAtackPacket,
		TIP_WINDOW:               TipWindowPacket,
		PLAY_SOUND:               PlaySoundPacket,
		LOGIN_DENIED:             LoginDeniedPacket,
		UPDATE_HEALTH:            UpdateHealthPacket,
		UPDATE_MANA:              UpdateManaPacket,
		UPDATE_STAMINA:           UpdateStaminaPacket,
		STATUS_BAR_INFO:          StatusBarInfoPacket,
		SEND_SKILL:               SendSkillsPacket,
		SEND_GUMP:                SendGumpDialogPacket,
	}

	@staticmethod
	def process(buf):
		''' Init next packet from buffer, returns a packet instance '''
		cmd = buf[0]
		try:
			return Ph.HANDLERS[cmd](buf)
		except KeyError:
			raise NotImplementedError("Unknown packet 0x%0.2X, %d bytes\n%s" % (cmd, len(buf), buf))


class PacketOut:
	''' Helper class for outputting a packet '''
	def __init__(self, cmd):
		self.buf = b''
		self.uchar(cmd)
		self.lenIdx = None

	def ulen(self):
		''' Special value: will place there an ushort containing packet length '''
		assert self.lenIdx is None
		self.lenIdx = len(self.buf)
		self.ushort(0)

	def uchar(self, val):
		''' Add an unsigned char (byte) to the packet '''
		if not isinstance(val, int):
			raise TypeError("Expected int, got {}".format(type(val)))
		if val < 0 or val > 255:
			raise ValueError("Byte {} out of range".format(val))
		self.buf += bytes((val, ))

	def ushort(self, val):
		''' Adds an unsigned short to the packet '''
		if not isinstance(val, int):
			raise TypeError("Expected int, got {}".format(type(val)))
		if val < 0 or val > 0xffff:
			raise ValueError("UShort {} out of range".format(val))
		self.buf += struct.pack('>H', val)

	def uint(self, val):
		''' Adds and unsigned int to the packet '''
		if not isinstance(val, int):
			raise TypeError("Expected int, got {}".format(type(val)))
		if val < 0 or val > 0xffffffff:
			raise ValueError("UInt {} out of range".format(val))
		self.buf += struct.pack('>I', val)

	def string(self, val, length, unicode=False):
		''' Adds a string to the packet '''
		if not isinstance(val, str):
			raise TypeError("Expected str, got {}".format(type(val)))
		if len(val) > length:
			raise ValueError('String "{}" too long'.format(val))
		self.buf += Util.fixStr(val, length, unicode)

	def ip(self, val):
		''' Adds an ip to the packet '''
		if not isinstance(val, str):
			raise TypeError("Expected str, got {}".format(type(val)))
		self.buf += ipaddress.ip_address(val).packed

	def getBytes(self):
		''' Returns the packet as bytes '''
		# Replace length if needed
		if self.lenIdx is not None:
			self.buf = self.buf[:self.lenIdx] + struct.pack('>H', len(self.buf)) + self.buf[self.lenIdx+2:]
		return self.buf


class Util:
	''' Utility class for conversions and so on '''

	@staticmethod
	def fixStr(string, length, unicode=False):
		''' Convert a str to fixed length, return bytes '''
		##TODO: Better handling on unicode
		enc = string.encode('ascii')
		ret = b''
		for i in range(0,length):
			if unicode:
				ret += b'\x00'
			try:
				ret += bytes([enc[i]])
			except IndexError:
				ret += b'\x00'
		return ret

	@staticmethod
	def varStr(byt):
		''' Convert bytes into a variable-length string '''
		try:
			dec = byt.decode('utf8')
		except UnicodeDecodeError:
			dec = byt.decode('iso8859-15')
		return dec.rstrip('\x00')


class NoFullPacketError(Exception):
	''' Exception thrown when no full packet is available '''
	pass
