#!/usr/bin/env python3

'''
AI classes for Python Ultima Online text client
'''

import threading
import time
import collections


class Brain(threading.Thread):
	''' This is the Brain for the client, the code who takes decisions '''

	def __init__(self):
		''' Initialize the object, internal '''
		self.started = False
		self.events = collections.deque()
		self.eventsLock = threading.Lock()
		## Client reference
		self.client = None
		## Default timeout while waiting for events
		self.timeout = 5
		super().__init__()

	def start(self, client):
		''' Prepare the script for startup, internal '''
		self.client = client
		self.started = True
		super().start()

	def run(self):
		''' This is the main Brain thread entry point, contains the main loop, internal '''

		self.init()

		main = threading.main_thread()

		while True:
			if not main.is_alive():
				print('Oops! Client crashed.')
				break

			if self.loop():
				print('Main loop terminated.')
				break

			# Wait for events
			self.processEvents()
			if not len(self.events) and self.timeout:
				start = time.time()
				timeout = start + self.timeout
				while time.time() < timeout:
					self.processEvents()
					time.sleep(0.01)

	def processEvents(self):
		''' Process event queue, internal '''
		while True:
			self.eventsLock.acquire()
			if not len(self.events):
				self.eventsLock.release()
				return
			ev = self.events.popleft()
			self.eventsLock.release()

			if ev.type == Event.EVT_HP_CHANGED:
				self.onHpChange(ev.old, ev.new)
			else:
				raise NotImplementedError("Unknown event {}",format(ev.type))

	def event(self, ev):
		''' Internal function, injects a single event '''
		if not isinstance(ev, Event):
			raise RuntimeError("Unknown event, expecting an Event instance, got {}".format(type(ev)))

		self.eventsLock.acquire()
		self.events.append(ev)
		self.eventsLock.release()

	def setTimeout(self, timeout):
		''' Sets the new timeout in seconds for the main loop '''
		self.timeout = timeout


	###################################
	# Methods intended to be overridden
	###################################

	def init(self):
		''' Called just once before first loop '''
		print('Brain inited')

	def loop(self):
		''' This is called once every main loop iteration, the main brain's loop
		@return Return true to terminate the program
		'''
		print('Brain running, nothing to do...')

	def onHpChange(self, old, new):
		''' Called when HP amount changes '''
		print('HP changed from {} to {}'.format(old, new))

	def onManaChange(self, old, new):
		''' Called when HP amount changes '''
		print('MANA changed from {} to {}'.format(old, new))

	def onStamChange(self, old, new):
		''' Called when HP amount changes '''
		print('STAM changed from {} to {}'.format(old, new))


class Event:
	''' An event sent from the client '''

	EVT_HP_CHANGED = 1
	EVT_MANA_CHANGED = 2
	EVT_STAM_CHANGED = 3

	def __init__(self, type, **kwargs):
		self.type = type
		for k, v in kwargs.items():
			setattr(self, k, v)
