#!/usr/bin/env python

'''
Do some consistency checks on the sources
'''

import unittest

import re
import inspect

from pyuo import packets


class TestPacketsOrder(unittest.TestCase):
	''' Ensures packets are defined in the right order '''

	# List of base classes
	BASE = (
		'Packet',
		'UpdateVitalPacket',
	)

	def test(self):
		classInfo = {}
		for name, obj in inspect.getmembers(packets):
			if name.startswith('__'):
				continue
			classInfo[name] = obj

		classRe = re.compile(r'^\s*class\s+([a-zA-Z0-9_]+)')
		classNames = []
		for line in inspect.getsourcelines(packets)[0]:
			m = classRe.match(line)
			if m:
				classNames.append(m.group(1))

		self.assertTrue(len(classInfo) == len(classNames), "Bug in test script")

		base = list(self.BASE)
		lastId = None
		for name in classNames:
			c = classInfo[name]
			if len(base):
				self.assertTrue(name == base[0],
						"Base class {} in wrong order".format(base[0]))
				del base[0]
				continue

			if lastId is not None:
				self.assertTrue(lastId < c.cmd,
					"Class {}(0x{:02X}) defined after 0x{:02X}".format(name, c.cmd, lastId))

			lastId = c.cmd



if __name__ == '__main__':
	unittest.main()
