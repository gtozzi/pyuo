#!/usr/bin/env python3

'''
A curses-based UO client
'''

import os
import time
import logging
import collections
import curses
import curses.textpad
import curses.panel

from pyuo import client
from pyuo import brain


class UiBrain(brain.Brain):
	''' Handles client interaction '''

	def __init__(self, ui):
		self.ui = ui


class Ui:
	''' Handles the user interface '''

	def __init__(self, stdScreen, host, port, writeLog=False):
		# Main Screen and panel
		self.scr = stdScreen
		self.scr.clear()
		self.scr.border(0)
		self.panel = curses.panel.new_panel(self.scr)

		# World window
		self.wwin = curses.newwin(15, 15, 0, 0)
		self.wwin.border(0)
		#self.wwin.addch(7, 7, 'a')

		# Status window
		self.swin = StatusWindow(self.scr)
		self.swin.updLabel('status', 'initializing')

		# Log window
		self.lwin = LogWindow(self.scr)

		self.refreshAll()

		# Init logging
		rootLog = logging.getLogger()
		rootLog.setLevel(logging.DEBUG)
		compactFmt = logging.Formatter('%(name)s.%(levelname)s: %(message)s')
		uiHandler = UiLogHandler(self.lwin)
		uiHandler.setFormatter(compactFmt)
		rootLog.addHandler(uiHandler)
		if writeLog:
			verboseFmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
			logFile = os.path.join(
				os.path.dirname(os.path.abspath(__file__)),
				os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]+'.log'
			)
			fileHandler = logging.FileHandler(logFile, mode='w')
			fileHandler.setFormatter(verboseFmt)
			rootLog.addHandler(fileHandler)
		self.log = logging.getLogger('ui')

		# Login
		while True:
			# Ask for username and password
			user = InputDialog(self.scr, 'Username:', 25).edit()
			pwd = InputDialog(self.scr, 'Password:', 25).edit()

			# Connect to server
			self.updStatus('logging in {}:{}'.format(host,port))
			self.refreshAll()
			self.cli = client.Client()
			try:
				servers = self.cli.connect(host, port, user, pwd)
			except client.LoginDeniedError as e:
				self.swin.updLabel('status', 'login denied ({})'.format(e))
				self.swin.refresh()
			else:
				break

		self.updStatus('logged in as {}'.format(user))

		# Select server
		self.log.debug(servers)
		serverList = [ i['name'][:-1].strip().strip('\0') for i in servers ]
		idx = SelectDialog(self.scr, 'Select a server', serverList, 30, 5).select()
		server = servers[idx]

		self.updStatus('selecting server {}'.format(server['name']))
		self.refreshAll()

		# Select character
		chars = self.cli.selectServer(server['idx'])
		self.log.debug(chars)
		charList = [ i['name'] for i in chars ]
		idx = SelectDialog(self.scr, 'Select a character', charList, 30, 5).select()
		char = chars[idx]

		self.updStatus('selecting character {}'.format(char['name']))
		self.refreshAll()

		# Start brain
		self.cli.selectCharacter(char['name'], idx)
		brain = UiBrain(self)
		self.cli.play(brain)

	def refreshAll(self):
		self.scr.noutrefresh()
		self.wwin.noutrefresh()
		self.swin.noutrefresh()
		self.lwin.noutrefresh()
		curses.doupdate()

	def updStatus(self, text):
		self.log.info(text)
		self.swin.updLabel('status', text)
		self.swin.refresh()


class BaseWindow:
	''' Common utility class for a screen subwindow '''

	def __init__(self, parent, height, width, top, left):
		self.parent = parent
		self.height = height
		self.width = width
		self.top = top
		self.left = left
		self.win = self.parent.subwin(self.height, self.width, self.top, self.left)
		self.win.border(0)

	def refresh(self):
		self.win.refresh()

	def noutrefresh(self):
		self.win.noutrefresh()


class StatusWindow(BaseWindow):
	''' The status window: wraps a ncurses window '''

	# Sizes and position
	WIDTH = 50
	HEIGHT = 15
	TOP = 0
	LEFT = 15
	# Definition of updatable labels
	LABELS = {
		'status' : { 'x': 1, 'y': 1, 'l': 'status' },
	}

	def __init__(self, parent):
		super().__init__(parent, self.HEIGHT, self.WIDTH, self.TOP, self.LEFT)
		for k, label in self.LABELS.items():
			self.win.addstr(label['x'], label['y'], label['l'].upper()+':')

	def updLabel(self, name, text):
		''' Updates a label '''
		try:
			label = self.LABELS[name]
		except KeyError:
			raise ValueError('Invalid label "{}". Valid labels are: {}'.format(
					name, ','.join(self.LABELS.keys())))
		x = len(label['l']) + 2
		maxLen = self.WIDTH - x - 2
		if len(text) > maxLen:
			text = text[:maxLen-1] + '…'
		self.win.addnstr(label['y'], label['x'] + x, ' ' * maxLen, maxLen)
		self.win.addnstr(label['y'], label['x'] + x, text, maxLen)


class LogWindow(BaseWindow):
	''' The log window '''

	TOP = 15
	LEFT = 0

	def __init__(self, parent):
		ph, pw = parent.getmaxyx()
		self.height = ph - self.TOP
		self.width = pw
		super().__init__(parent, self.height, self.width, self.TOP, self.LEFT)
		self.lines = collections.deque([], self.height-2)

	def append(self, text):
		''' Appends a log line '''
		self.lines.append(text)
		self.win.clear()
		self.win.border(0)
		for idx, l in enumerate(self.lines):
			self.win.addnstr(idx+1, 2, l, self.width-2)
		self.win.refresh()


class BaseDialog:
	''' Common utility class for a dialog '''

	def __init__(self, parent, title):
		self.parent = parent
		self.title = title

	def draw(self, width, height):
		''' Draw the base window centered '''
		ph, pw = self.parent.getmaxyx()
		self.top = int( (ph-height) / 2 )
		self.left = int( (pw-width) / 2 )
		self.width = width
		self.height = height

		self.win = curses.newwin(self.height, self.width, self.top, self.left)
		self.panel = curses.panel.new_panel(self.win)
		self.win.border(0)
		self.win.addnstr(0, 2, self.title, width - 4)

	def undraw(self):
		self.win.clear()
		self.panel.hide()
		self.win.refresh()


class InputDialog(BaseDialog):
	''' Shows an input dialog centered on the parent '''

	def __init__(self, parent, title, maxLen):
		super().__init__(parent, title)
		self.maxLen = maxLen

	def edit(self):
		width = self.maxLen + 2
		height = 3

		self.draw(width, height)
		self.win.refresh()

		ewin = curses.newwin(1, self.maxLen, self.top+1, self.left+1)
		ewin.refresh()

		box = curses.textpad.Textbox(ewin)

		# Let the user edit until Ctrl-G is struck.
		box.edit(lambda key: self.onKey(key))

		res = box.gather().strip()

		ewin.clear()
		self.undraw()

		return res

	def onKey(self, key):
		if key == ord('\n'):
			return 7 #Ctrl+G
		return key


class SelectDialog(BaseDialog):
	''' Allows the user to select an element from a list '''

	def __init__(self, parent, title, elems, minWidth=None, minHeight=None):
		super().__init__(parent, title)
		self.elems = elems
		self.minWidth = minWidth
		self.minHeight = minHeight

	def select(self):
		''' Make the user perform the selection, return selected index '''
		maxLen = max([len(i) for i in self.elems] + [self.minWidth])
		height = max(len(self.elems), self.minHeight)
		self.draw(maxLen+2, height+2)
		self.win.keypad(1)

		self.curidx = 0
		self.drawList()

		curses.flushinp()
		while True:
			key = self.win.getch()
			if key in (curses.KEY_ENTER, ord('\n')):
				break
			elif key == curses.KEY_UP:
				if self.curidx > 0:
					self.curidx -= 1
					self.drawList()
			elif key == curses.KEY_DOWN:
				if self.curidx < len(self.elems) - 1:
					self.curidx += 1
					self.drawList()

		self.undraw()
		return self.curidx

	def drawList(self):
		for idx, elem in enumerate(self.elems):
			attr = curses.A_REVERSE if idx == self.curidx else 0
			self.win.addnstr(idx+1, 1, elem, self.width-2, attr)
		self.win.refresh()


class UiLogHandler(logging.Handler):
	''' Custom logging handler '''

	def __init__(self, lwin):
		super().__init__()
		self.lwin = lwin

	def emit(self, record):
		if record.levelno == logging.DEBUG:
			return

		lines = self.format(record).splitlines()
		for line in lines:
			self.lwin.append(line)


if __name__ == '__main__':
	import argparse

	# Configure debug output
	#logging.basicConfig(level=logging.DEBUG)

	# Parse command line
	parser = argparse.ArgumentParser()
	parser.add_argument('host', help="Server's IP address or host name")
	parser.add_argument('port', type=int, help="Server's port")
	parser.add_argument('-l', '--log', action='store_true', help="Write a verbose log")
	args = parser.parse_args()

	curses.wrapper(Ui, args.host, args.port, args.log)
