import xml.etree.ElementTree as ET
from robofab.plistlib import Data
from robofab.objects.objectsRF import RPoint

from models.TTHTool import uniqueInstance as tthTool
from commons import helperFunctions
from drawing import geom
import tt
from tt import asm
reload(tt)
reload(asm)

silent = False

def makeRPoint(pos, name):
	return RPoint(pos.x, pos.y, None, name)

class CommandRemover(object):
	def __init__(self, gm, cmd):
		self.gm = gm
		self.cmd = cmd
	def __call__(self, menuIdx = 0):
		self.gm.removeHintingCommand(self.cmd)

class CommandConverter(object):
	def __init__(self, gm, cmd):
		self.gm = gm
		self.cmd = cmd
	def __call__(self, menuIdx = 0):
		g = self.gm.RFGlyph
		g.prepareUndo('Convert Command')
		code = self.cmd['code']
		if 'double' in code:
			code = 'single' + code[-1]
		elif 'single' in code:
			code = 'double' + code[-1]
		self.cmd['code'] = code
		g.performUndo()
		self.gm.dirtyHinting()
		self.gm.updateGlyphProgram(tthTool.getFontModel())

class CommandReverser(object):
	def __init__(self, gm, cmd):
		self.gm = gm
		self.cmd = cmd
	def __call__(self, menuIdx = 0):
		g = self.gm.RFGlyph
		g.prepareUndo('Reverse Link')
		p1 = self.cmd['point1']
		p2 = self.cmd['point2']
		self.cmd['point1'] = p2
		self.cmd['point2'] = p1
		g.performUndo()
		self.gm.dirtyHinting()
		self.gm.updateGlyphProgram(tthTool.getFontModel())

class TTHGlyph(object):

	def __init__(self, rfGlyph, fm):
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
		self.compile(fm)

	def __del__(self):
		self._g = None
		self.dirtyGeometry()
		self.dirtyHinting()

	@property
	def RFGlyph(self):
		return self._g

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
		try:
			if None == self._sortedHintingCommands:
				self._sortedHintingCommands = tt.sort(self.hintingCommands)
			return self._sortedHintingCommands
		except:
			print "ERROR: probable loop in hinting commands for glyph", self._g.name
			self._sortedHintingCommands = None
			return self.hintingCommands

	def positionForPointName(self, name):
		'''Returns the position of a ON control point with the given name.
		Coordinates in Font Units.'''
		if name == 'lsb':
			return geom.Point(0,0)
		elif name == 'rsb':
			return geom.Point(self.RFGlyph.width, 0)
		else:
			cont, seg = self.contSegOfPointName(name)
			return geom.makePoint(self._g[cont][seg].onCurve)

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

	def decreaseContSeg(self, contour, segment):
		"""Given a contour index and a segment index, finds the contour
		index and segment index of the previous segment"""
		s = segment - 1
		c = contour
		if s == -1:
			c = contour-1
			if c == -1:
				c = len(self._g)-1
			s = len(self._g[c])-1
		return c, s

	def increaseContSeg(self, contour, segment):
		"""Given a contour index and a segment index, finds the contour
		index and segment index of the next segment"""
		contourLen = len(self._g[contour])
		s = segment + 1
		c = contour
		if s == contourLen:
			s = 0
			c = contour + 1
			if c == len(self._g):
				c = 0
		return c, s

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

	def pointClicked(self, clickPos, alsoOff = False):
		if len(self._g) == 0: return (None, False, -1.0)
		# 'best', 'dist' and 'on' are lists of length one: This is a
		# workaround in python2 to access the variables in the outer scope
		# (in function 'update' below). python3 would use the 'nonlocal'
		# keyword.
		best = [(self._g[0][0].onCurve, 0, 0, 0)]
		dist = [(clickPos - geom.makePoint(best[0][0])).squaredLength()]
		on   = [True]
		def update(p, cont, seg, idx, isOn):
			d = (clickPos - geom.makePoint(p)).squaredLength()
			if d < dist[0]:
				dist[0] = d
				best[0] = (p, cont, seg, idx)
				on[0] = isOn
		for cont, contour in enumerate(self._g):
			for seg, segment in enumerate(contour):
				update(segment.onCurve, cont, seg, 0, True)
				if not alsoOff: continue
				for idx, p in enumerate(segment.offCurve):
					update(p, cont, seg, idx, False)
		fakeLSB = makeRPoint(self.positionForPointName('lsb'), 'lsb')
		fakeRSB = makeRPoint(self.positionForPointName('rsb'), 'rsb')
		update(fakeLSB, 0, 0, 0, True)
		update(fakeRSB, 0, 0, 0, True)
		if dist[0] <= 10.0 * 10.0:
			return (best[0], on[0], dist[0])
		else:
			return (None, False, -1.0)

	def commandClicked(self, clickPos):
		if tthTool.selectedAxis == 'X':
			skipper = ['v','t','b']
		else:
			skipper = ['h']
		for cmd in self.hintingCommands:
			if cmd['code'][-1] in skipper: continue
			lPos, lSize = helperFunctions.getOrDefault(cmd, 'labelPosSize', (None, None))
			if lPos == None: continue
			lo = lPos - 0.5 * lSize
			hi = lPos + 0.5 * lSize
			if lo.x <= clickPos.x <= hi.x and lo.y <= clickPos.y <= hi.y:
				return cmd
		return None

	def getAssembly(self):
		key = 'com.robofont.robohint.assembly'
		g = self.RFGlyph
		return helperFunctions.getOrDefault(g.lib, key, [])

	def saveCommandsToUFO(self):
		"""Save what can be saved in the UFO Lib."""
		# write self.hintingCommands to UFO lib.
		root = ET.Element('ttProgram')
		listOfCommands = self.sortedHintingCommands
		for c in listOfCommands:
			com = ET.SubElement(root, 'ttc')
			command = c.copy()
			for key in ['labelPosSize']: # cleanup
				if key in command:
					del command[key]
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

	def compileToUFO(self, fm):
		# compile to TT assembly language and write it in UFO lib.
		if fm.stem_to_cvt is None: fm.writeCVTandPREP()
		tt.asm.writeAssembly(self, fm.stem_to_cvt, fm.zone_to_cvt)

	def commandIsOK(self, cmd, verbose = False, absent = [], badName = []):
		for key in ['point', 'point1', 'point2']:
			if key not in cmd: continue
			ptName = cmd[key]
			if ptName in ['lsb', 'rsb']: continue
			if self.contSegOfPointName(ptName) is None:
				if verbose: absent.append((cmd['code'], key, ptName))
				return False
			if 'inserted' in ptName:
				if verbose: badName.append((cmd['code'], key, ptName))
				return False
		if 'active' not in cmd:
			cmd['active'] = 'true'
		return True

	def addCommand(self, cmd, update=True):
		if not self.commandIsOK(cmd): return
		self.hintingCommands.append(cmd)
		self.dirtyHinting()
		if update:
			self.updateGlyphProgram(tthTool.getFontModel())

	def removeHintingCommand(self, cmd):
		try:
			i = self.hintingCommands.index(cmd)
		except:
			return
		if i >= 0:
			self.hintingCommands.pop(i)
			self.dirtyHinting()
			self.updateGlyphProgram(tthTool.getFontModel())

	def deactivateAllCommands(self, item=0):
		for c in self.hintingCommands:
			c['active'] = 'false'
		self.dirtyHinting()
		# fixme: TTHGlyph should store 'fm' in a weakref
		self.updateGlyphProgram(tthTool.getFontModel())

	def activateAllCommands(self, item=0):
		for c in self.hintingCommands:
			c['active'] = 'true'
		self.dirtyHinting()
		self.updateGlyphProgram(tthTool.getFontModel())

	def deleteAllCommands(self, item=0):
		self.hintingCommands = []
		self.dirtyHinting()
		self.updateGlyphProgram(tthTool.getFontModel())

	def clearCommands(self, x, y):
		if x and y:
			self.hintingCommands = []
		elif x:
			self.hintingCommands = [c for c in self.hintingCommands if c['code'][-1] != 'h']
		else:
			self.hintingCommands = [c for c in self.hintingCommands if c['code'][-1] == 'h']
		self.dirtyHinting()

	def deleteXYCommands(self, hv):
		commandsToDelete = [i for (i,cmd) in enumerate(self.hintingCommands) if cmd['code'][-1:] in hv]
		commandsToDelete.sort()
		for offset,i in enumerate(commandsToDelete):
			self.hintingCommands.pop(i-offset)
		self.dirtyHinting()
		self.updateGlyphProgram(tthTool.getFontModel())

	def deleteXCommands(self, item=0):
		self.deleteXYCommands(['h'])

	def deleteYCommands(self, item=0):
		self.deleteXYCommands(['v', 't', 'b'])

	def deleteAllDeltas(self, item=0):
		commandsToDelete = [i for (i,cmd) in enumerate(self.hintingCommands) if 'delta' in cmd['code']]
		commandsToDelete.sort()
		for offset,i in enumerate(commandsToDelete):
			self.hintingCommands.pop(i-offset)
		self.dirtyHinting()
		self.updateGlyphProgram(tthTool.getFontModel())

	def cleanCommands(self):
		self.dirtyHinting()
		self.hintingCommands = [c for c in self.hintingCommands if self.commandIsOK(c)]

	def glyphProgramDoesNotTouchLSBOrRSB(self):
		if len(self._g.components) > 0:
			# FIXME: this is temporary, ideally, we should look
			#at the component that the USE_MY_METRICS flag
			return False
		for cmd in self.hintingCommands:
			if tt.commandModifiesLSBOrRSB(cmd):
				return False
		return True

	def compile(self, fm):
		self.cleanCommands()
		self.saveCommandsToUFO()
		self.compileToUFO(fm)

	def updateGlyphProgram(self, fm):
		self.compile(fm)
		tthTool.hintingProgramHasChanged(fm)

	def loadFromUFO(self):
		"""Load what can be loaded from the UFO Lib."""
		# read self.hintingCommands from UFO lib.
		self.hintingCommands = []
		self.dirtyHinting()
		if 'com.fontlab.ttprogram' not in self._g.lib:
			return
		ttprogram = self._g.lib['com.fontlab.ttprogram']
		strTTProgram = str(ttprogram)
		if strTTProgram[:4] == 'Data' and strTTProgram[-3:] == "n')":
			ttprogram = strTTProgram[6:-4]
		else:
			ttprogram = strTTProgram[6:-2]
		root = ET.fromstring(ttprogram)
		absent = []
		badName = []
		for child in root:
			cmd = child.attrib
			if 'active' not in cmd:
				cmd['active'] = 'true'
			if cmd['code'] in ['mdeltav', 'mdeltah', 'fdeltav', 'fdeltah']:
				if 'gray' not in cmd:
					cmd['gray'] = 'true'
				if 'mono' not in cmd:
					cmd['mono'] = 'true'
			if self.commandIsOK(cmd, verbose = True, absent = absent, badName = badName):
				self.hintingCommands.append(cmd)
		if silent: return
		message = "[TTH WARNING] In glyph "+self._g.name+":"
		if absent:
			message += "The following points do not exist. "
			message += "Commands acting on these points have been erased:\n\t"
			message += '\n\t'.join([repr(e) for e in absent])
		if badName:
			message += "The following points have a name containing the word 'inserted'. "
			message += "Commands acting on these points have been erased:\n\t"
			message += '\n\t'.join([repr(e) for e in badName])
		if absent or badName: print message

	def renameStem(self, nameChanger):
		'''Use newName = '' to transform the stem into a simple round'''
		modified = False
		for command in self.hintingCommands:
			if not ('stem' in command): continue
			oldName = command['stem']
			if oldName not in nameChanger: continue
			newName = nameChanger[oldName]
			modified = True
			if newName != None: # change name
				command['stem'] = newName
			else: # delete stem, replace with rounding
				del command['stem']
		if modified:
			#self.dirtyHinting()
			self.saveCommandsToUFO()
		return modified

	def renameZone(self, nameChanger):
		'''Use newName = '' to transform the align-to-zone into a simple alignv'''
		modified = False
		for command in self.hintingCommands:
			if not (command['code'] in ['alignt', 'alignb']): continue
			oldName = command['zone']
			if oldName not in nameChanger: continue
			newName = nameChanger[oldName]
			modified = True
			if newName != None: # change name
				command['zone'] = newName
			else: # delete zone
				del command['zone']
				command['code'] = 'alignv'
				command['align'] = 'round'
		if modified:
			#self.dirtyHinting()
			self.saveCommandsToUFO()
		return modified

if tthTool._printLoadings: print "TTHGlyph, ",
