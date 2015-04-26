import xml.etree.ElementTree as ET
from robofab.plistlib import Data

from models.TTHTool import uniqueInstance as tthTool

class TTHGlyph(object):

	def __init__(self, rfGlyph):
		# private variables: freely accessible, but the underscore, by
		# python-convention, indicates `please don't use me outside of the
		# class methods'.
		self._g = rfGlyph
		self._contours = None
		self._h_stems  = None # a list of pairs of ContSegs
		self._v_stems  = None
		self._sortedHintingCommands = None
		self._nameToContSeg = None
		# public variables
		self.hintingCommands = []
		# load stuff from the UFO Lib
		self.loadFromUFO()
	
	def __del__(self):
		self._g = None
		self.dirtyGeometry()
		self.dirtyHinting()

	@property
	def contours(self):
		if None == self._contours:
			self.computeContours() # or maybe, self._contours = Automation.prepareContours(_g)
		return self._contours

	@property
	def horizontalStems(self):
		if None == self._h_stems:
			self.computeStems() # or maybe, self._v_stems, self._h_tems = Automation.computeStems(_g)
		return self._h_stems

	@property
	def verticalStems(self):
		if None == self._v_stems:
			self.computeStems() # see comment above
		return self._v_stems

	@property
	def sortedHintingCommands(self):
		if None == self._sortedHintingCommands:
			# FIXME: TOPOLOGICAL SORT
			self._sortedHintingCommands = self.hintingCommands
		return self._sortedHintingCommands

	def dirtyGeometry(self):
		'''This should be called whenever the geometry of the associated
		glyph (_g) is modified: a point is moved, added, deleted, etc...'''
		self._contours = None
		self._h_stems  = None
		self._v_stems  = None

	def dirtyHinting(self):
		'''Should be called if the list of hinting commands changes, or if
		a command is modified. So this may be called by the
		command-popovers for example.'''
		self._sortedHintingCommands = None
	
	def contSegOfPointName(self, name):
		if None == self._nameToContSeg:
			self.buildNameToContSegDict()
		try:
			return self._nameToContSeg[name]
		except:
			return None

	def buildNameToContSegDict(self):
		'''A `ContSeg` is a pair (cidx,sidx) where cidx is the index of a
		contour in the glyph _g and sidx is the index of a segment in that
		contour. A segment has exactly one ON-point and zero or more
		OFF-points.
		The ON-point is self._g[cidx][sidx].onCurve
		A ContSeg therefore identifies an ON-point in a glyph, as well as
		its contour index and its position in that contour.'''
		self._nameToContSeg = {}
		for cidx, contour in enumerate(self._g):
			for sidx, seg in enumerate(contour):
				self._nameToContSeg[seg.onCurve.name] = (cidx, sidx)

	def saveToUFO(self):
		"""Save what can be saved in the UFO Lib."""
		# write self.hintingCommands to UFO lib.
		root = ET.Element('ttProgram')
		listOfCommands = self.sortedHintingCommands
		for command in listOfCommands:
			com = ET.SubElement(root, 'ttc')
			if 'active' not in command:
				command['active'] = 'true'
			if command['code'] in ['mdeltav', 'mdeltah', 'fdeltav', 'fdeltah']:
				if 'gray' not in command:
					command['gray'] = 'true'
				if 'mono' not in command:
					command['mono'] = 'true'
			com.attrib = command
		text = ET.tostring(root)
		self._g.lib['com.fontlab.ttprogram'] = Data(text)

	def loadFromUFO(self):
		"""Load what can be loaded from the UFO Lib."""
		# read self.hintingCommands from UFO lib.
		self.hintingCommands = []
		if 'com.fontlab.ttprogram' not in self._g.lib:
			return
		ttprogram = self._g.lib['com.fontlab.ttprogram']
		strTTProgram = str(ttprogram)
		if strTTProgram[:4] == 'Data' and strTTProgram[-3:] == "n')":
			ttprogram = strTTProgram[6:-4]
		else:
			ttprogram = strTTProgram[6:-2]
		root = ET.fromstring(ttprogram)
		for child in root:
			cmd = child.attrib
			if 'active' not in cmd:
				cmd['active'] = 'true'
			if cmd['code'] in ['mdeltav', 'mdeltah', 'fdeltav', 'fdeltah']:
				if 'gray' not in cmd:
					cmd['gray'] = 'true'
				if 'mono' not in cmd:
					cmd['mono'] = 'true'
			goodCmd = True
			for key in ['point', 'point1', 'point2']:
				if key not in cmd: continue
				ptName = cmd[key]
				if ptName in ['lsb', 'rsb']: continue
				if self.contSegOfPointName(ptName) is None:
					print "WARNING:", key,'"'+ptName+\
						'" in hinting command for glyph',self._g.name,\
						"was not found. Killing the command."
					goodCmd = False
				if 'inserted' in ptName:
					print "WARNING:", key,'"'+ptName+\
						'" in hinting command for glyph',self._g.name,\
						"contains the word 'inserted'. Killing the command."
					goodCmd = False
			if goodCmd:
				self.hintingCommands.append(cmd)

if tthTool._printLoadings: print "TTHGlyph, ",
