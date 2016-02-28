#!/usr/bin/env python3

'''
Network packets classes for Python Ultima Online text client
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
import zlib


################################################################################
# Please keep the base classes first then packet classes sorted by packet ID/cmd
################################################################################


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
		return self.varStr(self.pb(length))

	def ucstring(self, length):
		''' Returns next unicode string of the given length from the buffer '''
		if length % 2:
			raise ValueError('Length must be a multiple of 2')
		return self.varUStr(self.pb(length))

	def ip(self):
		''' Returns next string ip address from the buffer '''
		return struct.unpack('BBBB', self.pb(4))

	def validate(self):
		''' Do validations things, but be called at end of init '''
		if( self.length != self.readCount ):
			self.log.debug(self.__dict__)
			raise RuntimeError("Len mismatch on packet 0x{:02x} ({} <> {})".format(self.cmd, self.length, self.readCount))
		self.validated = True

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
		return Packet.nullTrunc(dec)

	@staticmethod
	def varUStr(byt):
		''' Convert unicode bytes into a variable-length string '''
		dec = byt.decode('utf_16_be')
		return Packet.nullTrunc(dec)

	@staticmethod
	def nullTrunc(dec):
		''' Truncates the given string before first null char
		(just like the original client '''
		zero = dec.find('\x00')
		if zero >= 0:
			for char in dec[zero:]:
				if char != '\x00':
					logging.warning('Truncating string "%s"', dec)
					break
			dec = dec[:zero]
		return dec


class UpdateVitalPacket(Packet):
	''' Just an utility base class '''

	length = 9

	def __init__(self, buf):
		super().__init__(buf)
		self.serial = self.uint()
		self.max = self.ushort()
		self.cur = self.ushort()


################################################################################
# Packets for here on, sorted by ID/cmd
################################################################################

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
		if flag == 0:
			return
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


class DeleteObjectPacket(Packet):
	''' Object went out of sight '''

	cmd = 0x1d
	length = 5

	def __init__(self, buf):
		super().__init__(buf)
		self.serial = self.uint()


class ControlAnimationPacket(Packet):
	''' Control Animation '''

	cmd = 0x1e
	length = 4

	def __init__(self, buf):
		super().__init__(buf)
		self.uchar() # Unknown
		self.uchar() # Unknown
		self.uchar() # Unknown


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


class DrawContainerPacket(Packet):
	''' Draws a container's gump '''

	cmd = 0x24
	length = 7

	def __init__(self, buf):
		super().__init__(buf)
		self.serial = self.uint()
		self.gump = self.ushort()


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


class MobAttributesPacket(Packet):
	''' Informs about a Mobile's attributes '''

	cmd = 0x2d
	length = 17

	def __init__(self, buf):
		super().__init__(buf)
		self.serial = self.uint()
		self.hits_max = self.ushort()
		self.hits_current = self.ushort()
		self.mana_max = self.ushort()
		self.mana_current = self.ushort()
		self.stam_max = self.ushort()
		self.stam_current = self.ushort()


class Unk32Packet(Packet):
	''' Unknown packet '''

	cmd = 0x32
	length = 2

	def __init__(self, buf):
		super().__init__(buf)
		self.uchar()


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
			try:
				id = self.ushort()
			except EOFError:
				break
			else:
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


class OverallLightLevelPacket(Packet):
	''' Overall Light Level '''

	cmd = 0x4f
	length = 2

	def __init__(self, buf):
		super().__init__(buf)
		self.level = self.uchar()


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


class TargetCursorPacket(Packet):
	''' Requesting/Answering a target '''

	cmd = 0x6c
	length = 19

	def __init__(self, buf):
		super().__init__(buf)
		## 0 = object, 1 = location
		self.what = self.uchar()
		self.id = self.uint()
		## 0 = Neutral, 1 = Harmful, 2 = Helpful, 3 = Cancel (server sent)
		self.type = self.uchar()

		# Following data ignored when sent my server
		self.uint() # Clicked on
		self.ushort() # x
		self.ushort() # y
		self.uchar() # unknown
		self.schar() # z
		self.ushort() # graphic (if static tile)


class PlayMidiPacket(Packet):
	''' Play Midi Music '''

	cmd = 0x6d
	length = 3

	def __init__(self, buf):
		super().__init__(buf)
		self.music = self.ushort()


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


class PingPacket(Packet):
	''' Ping request/reply '''

	cmd = 0x73
	length = 2

	def __init__(self, buf):
		super().__init__(buf)
		self.seq = self.uchar()


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
#		if not len(self.equip):
#			self.uchar() # unused/closing


class LoginDeniedPacket(Packet):
	''' Login Denied '''

	cmd = 0x82
	length = 2

	def __init__(self, buf):
		super().__init__(buf)
		self.reason = self.uchar()


class ConnectToGameServerPacket(Packet):
	''' Login server is requesting to connect to the game server '''

	cmd = 0x8c
	length = 11

	def __init__(self, buf):
		super().__init__(buf)
		self.ip = self.ip()
		self.port = self.ushort()
		self.key = self.uint()


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


class AllowAttackPacket(Packet):
	''' Allow/Refuse attack '''

	cmd = 0xaa
	length = 5

	def __init__(self, buf):
		super().__init__(buf)
		self.serial = self.uint()


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
		self.lang = self.string(4)
		self.name = self.string(30)
		self.msg = self.ucstring(self.length-48)


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
			self.texts.append(self.ucstring(tlen*2))
		self.uchar() # Trailing byte? TODO: check this


class EnableFeaturesPacket(Packet):
	''' Used to enable client features '''

	cmd = 0xb9
	length = 3

	def __init__(self, buf):
		super().__init__(buf)
		self.features = self.ushort()


class SeasonInfoPacket(Packet):
	''' Seasonal Information Packet '''

	cmd = 0xbc
	length = 3

	def __init__(self, buf):
		super().__init__(buf)
		self.flag = self.uchar()
		self.sound = self.uchar()


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
	## MegaCliLoc
	SUB_MEGACLILOC = 0x10
	## Send House Revision State
	SUB_HOUSE_REV = 0x1d
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

		elif self.sub == self.SUB_MEGACLILOC:
			self.serial = self.uint()
			self.revision = self.uint()

		elif self.sub == self.SUB_HOUSE_REV:
			self.serial = self.uint()
			self.rev = self.uint()

		else:
			raise NotImplementedError("Subcommand 0x%0.2X not implemented yet." % self.sub)


class ClilocMsgPacket(Packet):
	''' A CliLoc message (predefined messages with an unique ID) '''

	cmd = 0xc1

	def __init__(self, buf):
		super().__init__(buf)
		self.length = self.ushort()
		self.id = self.uint()
		self.body = self.ushort()
		self.type = self.uchar()
		self.hue = self.ushort()
		self.font = self.ushort()
		self.msg = self.uint()
		self.speaker_name = self.string(30)
		self.unicode_string = self.pb(self.length-48)


class MegaClilocRevPacket(Packet):
	''' SE Introduced Revision '''

	cmd = 0xdc
	length = 9

	def __init__(self, buf):
		super().__init__(buf)
		self.serial = self.uint()
		self.revision = self.uint()


class CompressedGumpPacket(Packet):
	''' Receiving a compressed gump from the server '''

	cmd = 0xdd

	def __init__(self, buf):
		super().__init__(buf)
		self.length = self.ushort()
		self.serial = self.uint()
		self.gumpid = self.uint()
		self.x = self.uint()
		self.y = self.uint()
		cLen = self.uint()
		dLen = self.uint()
		self.commands = zlib.decompress(self.pb(cLen-4))
		assert len(self.commands) == dLen
		textLines = self.uint()
		ctxtLen = self.uint()
		dtxtLen = self.uint()
		self.texts = zlib.decompress(self.pb(ctxtLen-4))
		assert len(self.texts) == dtxtLen
		#self.uchar() # Trailing byte?

