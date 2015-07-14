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

kTTProgramKey = 'com.fontlab.ttprogram'

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
		self.gm.prepareUndo('Convert Command')
		code = self.cmd.get('code')
		if 'double' in code:
			code = 'single' + code[-1]
		elif 'single' in code:
			code = 'double' + code[-1]
		self.cmd.set('code', code)
		self.gm.updateGlyphProgram(tthTool.getFontModel())
		self.gm.performUndo()

class CommandReverser(object):
	def __init__(self, gm, cmd):
		self.gm = gm
		self.cmd = cmd
	def __call__(self, menuIdx = 0):
		self.gm.prepareUndo('Reverse Link')
		p1 = self.cmd.get('point1')
		p2 = self.cmd.get('point2')
		self.cmd.set('point1', p2)
		self.cmd.set('point2', p1)
		self.gm.updateGlyphProgram(tthTool.getFontModel())
		self.gm.performUndo()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class TTHGlyph(object):

	def __init__(self, rfGlyph, fm, compile=True):
		# private variables: freely accessible, but the underscore, by
		# python-convention, indicates `please don't use me outside of the
		# class methods'.
		self._g = rfGlyph
		self._contours = None
		self._h_stems  = None # a list of pairs of CSIs
		self._v_stems  = None
		self._sortedHintingCommands = None
		self._nameToCSI = None
		# public variables
		self.hintingCommands = None
		# load stuff from the UFO Lib
		self.loadFromUFO()
		if compile:
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
			return list(self.hintingCommands)

	def pointOfCSI(self, csi):
		return self._g[csi[0]][csi[1]].points[csi[2]]

	def positionForPointName(self, name):
		'''Returns the position of a ON control point with the given name.
		Coordinates in Font Units.'''
		if name == 'lsb':
			return geom.Point(0,0)
		elif name == 'rsb':
			return geom.Point(self.RFGlyph.width, 0)
		else:
			csi = self.csiOfPointName(name)
			return geom.makePoint(self.pointOfCSI(csi))

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

	def csiOfPointName(self, name):
		if None == self._nameToCSI:
			self.buildNameToCSIDict()
		try:
			return self._nameToCSI[name]
		except:
			return None

	def decreaseCSI(self, csi, alsoOff):
		"""Given a contour index and a segment index, finds the contour
		index and segment index of the previous segment"""
		c, s, i = csi
		if alsoOff:
			i = i - 1
			if i == -1:
				s = s - 1
		else:
			s = s - 1
		if s == -1:
			c = c - 1
			if c == -1:
				c = len(self._g)-1
			s = len(self._g[c])-1
		if (not alsoOff) or (i == -1):
			i = len(self._g[c][s].points)-1
		return (c, s, i)

	def increaseCSI(self, csi, alsoOff):
		"""Given a contour index and a segment index, finds the contour
		index and segment index of the next segment"""
		c, s, i = csi
		contourLen = len(self._g[c])
		segLen = len(self._g[c][s])
		if alsoOff:
			i = i + 1
			if i == segLen:
				s = s + 1
				i = 0
		else:
			s = s + 1
		if s == contourLen:
			s = 0
			c = c + 1
			if c == len(self._g):
				c = 0
		if (not alsoOff):
			i = len(self._g[c][s].points)-1
		return (c, s, i)

	def hintingNameForPoint(self, p):
		uid  = p.naked().uniqueID # !! Call this first because it will possibly modify p.name
		name = p.name
		if name is None or name == '':
			p.name = uid
			return uid
		if name == 'inserted':
			p.name += ','+uid
			return p.name
		return name

	def buildNameToCSIDict(self):
		'''A `CSI` is a triple (cidx,sidx,idx) where cidx is the index of a
		contour in the glyph _g and sidx is the index of a segment in that
		contour. idx is the index of a point in that segment.
		A segment has exactly one ON-point and zero or more OFF-points.
		The segment, 'seg' is self._g[cidx][sidx]
		The ON-point is seg.onCurve OR seg.points[idx] OR seg.points[-1]
		A CSI therefore identifies a point in a glyph, as well as
		its contour index and its position in that contour.'''
		self._nameToCSI = {}
		for cidx, contour in enumerate(self._g):
			for sidx, seg in enumerate(contour):
				for idx, p in enumerate(seg.points):
					name = self.hintingNameForPoint(p)
					csi = (cidx, sidx, idx)
					self._nameToCSI[name] = csi
					# This is to find the point using the original name that may
					# still be in the hinting commands (from FontLab). For
					# example, point.name = 'sh03, *123456799' and we find 'sh03'
					# in the commands (the command point name will be rewritten
					# after)
					names = name.split(',')
					if len(names) > 1 and names[0] != 'inserted':
						self._nameToCSI[names[0]] = csi

	def pointClicked(self, clickPos, alsoOff = False):
		if len(self._g) == 0: return (None, False, -1.0)
		# 'best', 'dist' and 'on' are lists of length one: This is a
		# workaround in python2 to access the variables in the outer scope
		# (in function 'update' below). python3 would use the 'nonlocal'
		# keyword.
		seg  = self._g[0][0]
		best = [(seg.onCurve, 0, 0, len(seg.points)-1)]
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
				update(segment.onCurve, cont, seg, len(segment.points)-1, True)
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

	def getLabelPosSize(self, cmd):
		s = cmd.get('labelPosSize', None)
		if s is None: return (None, None)
		return tuple(geom.pointOfString(p) for p in s.split('#'))

	def commandClicked(self, clickPos):
		if tthTool.selectedAxis == 'X':
			skipper = ['v','t','b']
		else:
			skipper = ['h']
		for cmd in self.hintingCommands:
			code = cmd.get('code')
			if code[-1] in skipper: continue
			lPos, lSize = self.getLabelPosSize(cmd)
			if lPos == None: continue
			lo = lPos - 0.5 * lSize
			hi = lPos + 0.5 * lSize
			if lo.x <= clickPos.x <= hi.x and lo.y <= clickPos.y <= hi.y:
				if 'delta' in code:
					if int(cmd.get('ppm1')) <= tthTool.PPM_Size <= int(cmd.get('ppm2')):
						return cmd
				else:
					return cmd
		return None

	def getAssembly(self):
		return self.RFGlyph.lib.get(tt.tables.k_glyph_assembly_key, [])

	def prepareUndo(self, label):
		self.saveCommandsToUFO()
		self._g.prepareUndo(label)

	def performUndo(self):
		self._g.performUndo()

	def compileToUFO(self, fm):
		# compile to TT assembly language and write it in UFO lib.
		if fm.stem_to_cvt is None: fm.writeCVTandPREP()
		tt.asm.writeAssembly(self, fm.stem_to_cvt, fm.zone_to_cvt)

	def commandIsOK(self, cmd, verbose = False, absent = []):
		for key in ['point', 'point1', 'point2']:
			if not helperFunctions.commandHasAttrib(cmd, key): continue
			ptName = cmd.get(key)
			if ptName in ['lsb', 'rsb']: continue
			csi = self.csiOfPointName(ptName)
			if csi is None:
				if verbose: absent.append((cmd.get('code'), key, ptName))
				return False
			# Rename the command's point using the RF name
			cmd.set(key, self.pointOfCSI(csi).name)
		return True

	def addCommand(self, cmd, update=True):
		if not self.commandIsOK(cmd): return
		self.prepareUndo("Add '{}' Command".format(cmd.get('code')))
		self.hintingCommands.append(cmd)
		self.dirtyHinting()
		if update:
			self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def removeHintingCommand(self, cmd):
		self.prepareUndo("Remove '{}' Command".format(cmd.get('code')))
		self.hintingCommands.remove(cmd)
		self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def deactivateAllCommands(self, item=0):
		self.prepareUndo("Deactivate All Commands")
		for c in self.hintingCommands:
			c.set('active', 'false')
		# fixme: TTHGlyph should store 'fm' in a weakref
		self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def activateAllCommands(self, item=0):
		self.prepareUndo("Activate All Commands")
		for c in self.hintingCommands:
			c.set('active', 'true')
		self.dirtyHinting()
		self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def deleteAllCommands(self, item=0):
		self.prepareUndo("Clear All Program")
		self.clearCommands(True, True)
		self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def clearCommands(self, x, y):
		if x and y:
			cmds = []
		elif x:
			cmds = [c for c in self.hintingCommands if c.get('code')[-1] != 'h']
		else:
			cmds = [c for c in self.hintingCommands if c.get('code')[-1] == 'h']

		if self.hintingCommands is None:
			self.hintingCommands = ET.Element('ttProgram')
		else:
			self.hintingCommands.clear()
		self.hintingCommands.extend(cmds)
		self.dirtyHinting()

	def deleteXCommands(self, item=0):
		self.prepareUndo("Clear X Commands")
		self.clearCommands(True, False)
		self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def deleteYCommands(self, item=0):
		self.prepareUndo("Clear Y Commands")
		self.clearCommands(False, True)
		self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def deleteAllDeltas(self, item=0):
		self.prepareUndo("Clear All Deltas")
		cmds = [cmd for cmd in self.hintingCommands if 'delta' not in cmd.get('code')]
		self.hintingCommands.clear()
		self.hintingCommands.extend(cmds)
		self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def deleteXDeltas(self, item=0):
		self.prepareUndo("Clear X Deltas")
		cmds = [cmd for cmd in self.hintingCommands if 'deltah' not in cmd.get('code')]
		self.hintingCommands.clear()
		self.hintingCommands.extend(cmds)
		self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def deleteYDeltas(self, item=0):
		self.prepareUndo("Clear Y Deltas")
		cmds = [cmd for cmd in self.hintingCommands if 'deltav' not in cmd.get('code')]
		self.hintingCommands.clear()
		self.hintingCommands.extend(cmds)
		self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def deleteXDeltas(self, item=0):
		self.prepareUndo("Clear X Deltas")
		cmds = [cmd for cmd in self.hintingCommands if 'deltah' not in cmd.get('code')]
		self.hintingCommands.clear()
		self.hintingCommands.extend(cmds)
		self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def deleteYDeltas(self, item=0):
		self.prepareUndo("Clear X Deltas")
		cmds = [cmd for cmd in self.hintingCommands if 'deltav' not in cmd.get('code')]
		self.hintingCommands.clear()
		self.hintingCommands.extend(cmds)
		self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def cleanCommands(self):
		cmds = [c for c in self.hintingCommands if self.commandIsOK(c)]
		self.hintingCommands.clear()
		self.hintingCommands.extend(cmds)
		self.dirtyHinting()

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

	def saveCommandsToUFO(self):
		"""Save what can be saved in the UFO Lib."""
		# write self.hintingCommands to UFO lib.
		self._g.lib[kTTProgramKey] = Data(ET.tostring(self.hintingCommands))

	def loadFromUFO(self):
		"""Load what can be loaded from the UFO Lib."""
		self.dirtyHinting()
		self.clearCommands(True, True)
		if kTTProgramKey not in self._g.lib: return
		#ttprogram = self._g.lib['com.fontlab.ttprogram']
		#strTTProgram = str(ttprogram)
		#if strTTProgram[:4] == 'Data' and strTTProgram[-3:] == "n')":
		#	ttprogram = strTTProgram[6:-4]
		#else:
		#	ttprogram = strTTProgram[6:-2]
		ttprogram = self._g.lib[kTTProgramKey].data
		root = ET.fromstring(ttprogram)
		absent = []
		for cmd in root:
			cmd.set('active', cmd.get('active', 'true'))
			if 'delta' in cmd.get('code'):
				cmd.set('gray', cmd.get('gray', 'true'))
				cmd.set('mono', cmd.get('mono', 'true'))
			if self.commandIsOK(cmd, verbose = True, absent = absent):
				self.hintingCommands.append(cmd)
		if silent: return
		message = "[TTH WARNING] In glyph "+self._g.name+":"
		if absent:
			message += "The following points do not exist. "
			message += "Commands acting on these points have been erased:\n\t"
			message += '\n\t'.join([repr(e) for e in absent])
		if absent: print message

	def renameStem(self, nameChanger):
		'''Use newName = '' to transform the stem into a simple round'''
		modified = False
		for command in self.hintingCommands:
			if not (helperFunctions.commandHasAttrib(command, 'stem')): continue
			oldName = command.get('stem')
			if oldName not in nameChanger: continue
			newName = nameChanger[oldName]
			modified = True
			if newName != None: # change name
				command.set('stem', newName)
			else: # delete stem, replace with rounding
				helperFunctions.delCommandAttrib(command, 'stem')
		if modified:
			self.saveCommandsToUFO()
		return modified

	def renameZone(self, nameChanger):
		'''Use newName = '' to transform the align-to-zone into a simple alignv'''
		modified = False
		for command in self.hintingCommands:
			if not (command.get('code') in ['alignt', 'alignb']): continue
			oldName = command.get('zone')
			if oldName not in nameChanger: continue
			newName = nameChanger[oldName]
			modified = True
			if newName != None: # change name
				command.set('zone', newName)
			else: # delete zone
				helperFunctions.delCommandAttrib(command, 'zone')
				command.set('code', 'alignv')
				command.set('align', 'round')
		if modified:
			self.saveCommandsToUFO()
		return modified

if tthTool._printLoadings: print "TTHGlyph, ",
