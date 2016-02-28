#!/usr/bin/env python3

'''
This is just a rough example sparring script
'''

import configparser
import logging
import http.client
import json
import time

from pyuo import client
from pyuo import brain


class MyBrain(brain.Brain):
	''' This is the main script class '''

	CLEAN_BANDAGES = 0x0e21

	CHUCK_INTERVAL = 60

	def init(self):
		self.nextChuck = time.time() + self.CHUCK_INTERVAL
		self.nextHeal = 0
		self.client.say("Hello, world!")

	#def onHpChange(self, old, new):
		#if self.player.hp < self.player.maxhp - 10 and time.time() > self.nextHeal:
			## Heal myself
			#bp = self.player.openBackPack()
			#for item in bp:
				#if item.graphic == self.CLEAN_BANDAGES:
					#print("Using bandages")
					#item.use()
					#tgt = self.client.waitForTarget(timeout=10)
					#if tgt:
						#self.nextHeal = time.time() + 10
						#tgt.target(self.player)

	def loop(self):
		# Say a Chuck Norris Fact
		if time.time() > self.nextChuck:
			try:
				conn = http.client.HTTPConnection('api.icndb.com', timeout=5)
				conn.request("GET", "/jokes/random")
				res = json.loads(conn.getresponse().read().decode('utf8'))
				if res['type'] == 'success':
					self.client.say(res['value']['joke'])
			except Exception as e:
				self.log.error(str(e))
			self.nextChuck = time.time() + self.CHUCK_INTERVAL


if __name__ == '__main__':
	# Configure debug output
	logging.basicConfig(level=logging.DEBUG)

	# Read configuration
	conf = configparser.ConfigParser()
	conf.read('spar.cfg')
	lconf = conf['login']

	# Login to the server
	c = client.Client()
	servers = c.connect(lconf.get('ip'), lconf.getint('port'), lconf.get('user'), lconf.get('pass'))
	chars = c.selectServer(lconf.getint('serveridx'))
	c.selectCharacter(lconf.get('charname'), lconf.getint('charidx'))
	MyBrain(c)
