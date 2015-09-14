#!/usr/bin/env python3

import configparser
import logging

from pyuo import client
from pyuo import brain


class MyBrain(brain.Brain):
	''' This is the main script class '''

	def init(self):
		self.client.say("Hello, world!")

	def onHpChange(self, old, new):
		self.client.say("I had {} HP but now i have {}.".format(old,new))


if __name__ == '__main__':
	# Configure debug output
	logging.basicConfig(level=logging.INFO)

	# Read configuration
	conf = configparser.ConfigParser()
	conf.read('spar.cfg')
	lconf = conf['login']

	# Login to the server
	c = client.Client()
	servers = c.connect(lconf.get('ip'), lconf.getint('port'), lconf.get('user'), lconf.get('pass'))
	chars = c.selectServer(lconf.getint('serveridx'))
	c.selectCharacter(lconf.get('charname'), lconf.getint('charidx'))
	c.play(MyBrain())
