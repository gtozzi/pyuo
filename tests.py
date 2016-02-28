#!/usr/bin/env python3

'''
Do some consistency checks on the sources
'''

import unittest

import re
import inspect

# Even if it's bad pratice, import everything to check for syntax errors
from pyuo import *


class TestClient(unittest.TestCase):
	''' Client tests '''

	def test_instance(self):
		''' Chec that an instance can be created '''
		cli = client.Client()


class TestSource(unittest.TestCase):
	''' Source code tests '''

	def testPacketsOrder(self):
		''' Ensures packets are defined in the right order '''
		classInfo = {}
		for name, obj in inspect.getmembers(packets):
			if name.startswith('__'):
				continue
			if inspect.isclass(obj):
				classInfo[name] = obj

		classRe = re.compile(r'^\s*class\s+([a-zA-Z0-9_]+)')
		classNames = []
		for line in inspect.getsourcelines(packets)[0]:
			m = classRe.match(line)
			if m:
				classNames.append(m.group(1))

		diffs = list( set(classNames) ^ set(classInfo.keys()) )
		self.assertTrue(len(classInfo) == len(classNames) and len(diffs) == 0,
				'Bug in test script: "{}"'.format(diffs))

		base = True
		lastId = None
		for name in classNames:
			c = classInfo[name]

			if c not in packets.classes:
				self.assertTrue(base, 'Base class "{}" found after concrete class')
				continue

			base = False

			if lastId is not None:
				self.assertTrue(lastId < c.cmd,
					'Class "{}"(0x{:02X}) defined after 0x{:02X}'.format(name, c.cmd, lastId))

			self.assertTrue(name.endswith('Packet'),
					'Packet "{}" has invalid name: must end in "Packet"'.format(name))

			lastId = c.cmd



if __name__ == '__main__':
	unittest.main()
