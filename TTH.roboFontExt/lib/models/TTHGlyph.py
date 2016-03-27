import xml.etree.ElementTree as ET
from robofab.plistlib import Data
from robofab.objects.objectsRF import RPoint

from models.TTHTool import uniqueInstance as tthTool
from commons import helperFunctions
from drawing import geom
import tt
from tt import asm
from ps import parametric
reload(tt)
reload(asm)
reload(parametric)

kTTProgramKey = 'com.fontlab.ttprogram'

silent = False

def makeRPoint(pos, name):
	return RPoint(pos.x, pos.y, None, name)

class PointLocation(object):
	def __init__(self, rfPoint, cont, seg, idx, compIdx, compOffset):
		p = geom.makePoint(rfPoint)
		if compIdx != None:
			p = p + compOffset
		self.pos = p
		self.rfPoint = rfPoint
		self.cont = cont
		self.seg = seg
		self.idx = idx
		self.component = compIdx

class ApplyParametric(object):
	def __init__(self, gm, fm):
		self.gm = gm
		self.fm = fm
	def __call__(self, menuIdx = 0):
		self.gm.prepareUndo('Apply Parametric')
		parametric.processParametric(self.fm, self.gm, actual=True)
		self.gm.updateGlyphProgram(tthTool.getFontModel())
		self.gm.RFGlyph.update()
		self.gm.performUndo()

class ApplyParametricForMultipleGlyphs(object):
	def __init__(self, gmList, fm):
		self.gmList = gmList
		self.fm = fm
	def __call__(self, menuIdx = 0):
		for gm in self.gmList:
			gm.prepareUndo('Apply Parametric')
			parametric.processParametric(self.fm, gm, actual=True)
			gm.updateGlyphProgram(tthTool.getFontModel())
			gm.RFGlyph.update()
			gm.performUndo()

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
		self._pg = None
		self._contours = None # FIXME: remove this member variable which is useless
		self._h_stems  = None # a list of pairs of CSIs
		self._v_stems  = None
		self._sortedHintingCommands = None
		self._nameToCSI = None
		self._nameToCSILayer = None
		self._posToName = None
		# public variables
		self.hintingCommands = None
		# load stuff from the UFO Lib
		self.loadFromUFO(fm)
		if compile:
			self.compile(fm)

	def __del__(self):
		self._g = None
		self.dirtyGeometry()
		self.dirtyHinting()

	@property
	def RFGlyph(self):
		return self._g

	# @property
	# def pGlyph(self):
	# 	return self._pg

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

	def pPointOfCSI(self, csi):
		return self._pg[csi[0]][csi[1]].points[csi[2]]

	def pointOfCSIForLayer(self, csi, layerName):
		return self._g.getLayer(layerName, clear=False)[csi[0]][csi[1]].points[csi[2]]

	def positionForPointName(self, name, fm=None, comp=None):
		'''Returns the position of a ON control point with the given name.
		Coordinates in Font Units.'''
		if name == None:
			print "\npositionForPointName(",name,',',fm,',',comp,")\n"
		if name == 'lsb':
			return geom.Point(0,0)
		elif name == 'rsb':
			return geom.Point(self.RFGlyph.width, 0)
		else:
			if comp:
				compo = self._g.components[int(comp)]
				offset = geom.makePointForPair(compo.offset)
				gm = fm.glyphModelForGlyph(fm.f[compo.baseGlyph])
				return gm.positionForPointName(name) + offset
			else:
				csi = self.csiOfPointName(name)
				return geom.makePoint(self.pointOfCSI(csi))

	def positionForPointNameForLayer(self, name, layerName, fm=None, comp=None):
		'''Returns the position of a ON control point with the given name.
		Coordinates in Font Units.'''
		if name == None:
			print "\npositionForPointName(",name,',',fm,',',comp,")\n"
		if name == 'lsb':
			return geom.Point(0,0)
		elif name == 'rsb':
			return geom.Point(self.RFGlyph.width, 0)
		else:
			if comp:
				compo = self._g.getLayer(layerName, clear=False).components[int(comp)]
				offset = geom.makePointForPair(compo.offset)
				gm = fm.glyphModelForGlyph(fm.f[compo.baseGlyph])
				return gm.positionForPointNameForLayer(name, layerName) + offset
			else:
				csi = self.csiOfPointNameForLayer(name, layerName)
				return geom.makePoint(self.pointOfCSIForLayer(csi, layerName))

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

	def csiOfPointName(self, name, fm=None, comp=None):
		if None == self._nameToCSI:
			self.buildNameToCSIDict()
		try:
			if comp:
				compo = self._g.components[int(comp)]
				gm = fm.glyphModelForGlyph(fm.f[compo.baseGlyph])
				return gm.csiOfPointName(name)
			return self._nameToCSI[name]
		except:
			return None

	def positionOfPointName(self, name):
		if None == self._posToName:
			self.buildPositionToNameDict()
		try:
			return self._posToName[name]
		except:
			return None


	def csiOfPointNameForLayer(self, name, layerName, fm=None, comp=None):
		if None == self._nameToCSILayer:
			self.buildNameToCSIDictForLayer(layerName)
		try:
			# if comp:
			# 	compo = self._g.components[int(comp)]
			# 	gm = fm.glyphModelForGlyph(fm.f[compo.baseGlyph])
			# 	return gm.csiOfPointName(name)
			return self._nameToCSILayer[name]
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

	def increaseSI(self, csi, alsoOff):
		"""Given a contour index and a segment index, finds the segment
		index of the next segment IN THE SAME CONTOUR"""
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

	def buildNameToCSIDictForLayer(self, layerName):
		self._nameToCSILayer = {}
		for cidx, contour in enumerate(self._g.getLayer(layerName, clear=False)):
			for sidx, seg in enumerate(contour):
				for idx, p in enumerate(seg.points):
					name = self.hintingNameForPoint(p)
					csi = (cidx, sidx, idx)
					self._nameToCSILayer[name] = csi
					# This is to find the point using the original name that may
					# still be in the hinting commands (from FontLab). For
					# example, point.name = 'sh03, *123456799' and we find 'sh03'
					# in the commands (the command point name will be rewritten
					# after)
					names = name.split(',')
					if len(names) > 1 and names[0] != 'inserted':
						self._nameToCSILayer[names[0]] = csi


	def pointClickedOnGlyph(self, clickPos, glyph, best, dist, compIdx, compOffset, on, alsoOff = False):
		if len(glyph) == 0: return
		def update(p, cont, seg, idx, isOn):
			d = (clickPos - geom.makePoint(p)).squaredLength()
			if d < dist[0]:
				dist[0] = d
				best[0] = PointLocation(p, cont, seg, idx, compIdx, compOffset)
				on[0] = isOn
		for cont, contour in enumerate(glyph):
			for seg, segment in enumerate(contour):
				update(segment.onCurve, cont, seg, len(segment.points)-1, True)
				if not alsoOff: continue
				for idx, p in enumerate(segment.offCurve):
					update(p, cont, seg, idx, False)

	def pointClicked(self, clickPos, fontModel, scale, alsoOff = False):
		# 'best', 'dist' and 'on' are lists of length one: This is a
		# workaround in python2 to access the variables in the outer scope
		# (in function 'update' below). python3 would use the 'nonlocal'
		# keyword.
		thresh = 10.0 * 10.0 * scale * scale
		best = [None]
		dist = [999999999.0]
		on   = [True]
		def update(p, cont, seg, idx, isOn):
			d = (clickPos - geom.makePoint(p)).squaredLength()
			if d < dist[0]:
				dist[0] = d
				best[0] = PointLocation(p, cont, seg, idx, None, None)
				on[0] = isOn
		self.pointClickedOnGlyph(clickPos, self._g, best, dist, None, None, on, alsoOff)

		for i,compo in enumerate(self._g.components):
			offset = geom.makePointForPair(compo.offset)
			self.pointClickedOnGlyph(clickPos-offset, fontModel.f[compo.baseGlyph], best, dist, i, offset, on, alsoOff) 

		fakeLSB = makeRPoint(self.positionForPointName('lsb'), 'lsb')
		fakeRSB = makeRPoint(self.positionForPointName('rsb'), 'rsb')
		update(fakeLSB, 0, 0, 0, True)
		update(fakeRSB, 0, 0, 0, True)
		if dist[0] <= thresh:
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
		tt.asm.writeAssembly(fm, self, fm.stem_to_cvt, fm.zone_to_cvt)

	def commandIsOK(self, cmd, fm, verbose = False, absent = []):
		for base, key in [('base', 'point'), ('base1', 'point1'), ('base2', 'point2')]:
			if not helperFunctions.commandHasAttrib(cmd, key): continue
			ptName = cmd.get(key)
			if ptName in ['lsb', 'rsb']: continue
			baseGm = self
			if helperFunctions.commandHasAttrib(cmd, base):
				try:
					compo = self._g.components[int(cmd.get(base))]
					baseGm = fm.glyphModelForGlyph(fm.f[compo.baseGlyph])
				except:
					return False
			csi = baseGm.csiOfPointName(ptName)
			if csi is None:
				if verbose: absent.append((cmd.get('code'), key, ptName))
				return False
			# Rename the command's point using the RF name
			cmd.set(key, baseGm.pointOfCSI(csi).name)
		return True

	def convertCmdPoints(self, cmd, cubicLayerName):
		cubicLayer = self._g.getLayer(cubicLayerName, clear=False)
		for base, key in [('base', 'point'), ('base1', 'point1'), ('base2', 'point2')]:
			if not helperFunctions.commandHasAttrib(cmd, key): continue
			c_ptName = cmd.get(key)
			c_ptPosition = self.positionForPointNameForLayer(c_ptName, cubicLayerName)
			for cidx, contour in enumerate(self._g):
				for sidx, seg in enumerate(contour):
					for idx, p in enumerate(seg.points):
						q_name = self.hintingNameForPoint(p)
						q_pos = geom.makePoint(p)
						if c_ptPosition.x == q_pos.x and c_ptPosition.y == q_pos.y:
							cmd.set(key, q_name)


	def buildPositionToNameDict(self):
			self._posToName = {}
			for cidx, contour in enumerate(self._g):
				for sidx, seg in enumerate(contour):
					for idx, p in enumerate(seg.points):
						name = self.hintingNameForPoint(p)
						pos = geom.makePoint(p)
						self._posToName[pos] = name


	def addCommand(self, fm, cmd, update=True):
		if not self.commandIsOK(cmd, fm): return
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

	def setCommands(self, cmds):
		if self.hintingCommands is None:
			self.hintingCommands = ET.Element('ttProgram')
		else:
			self.hintingCommands.clear()
		self.hintingCommands.extend(cmds)
		self.dirtyHinting()

	def clearCommands(self, x, y):
		if x and y:
			cmds = []
		elif x:
			cmds = [c for c in self.hintingCommands if c.get('code')[-1] != 'h']
		else:
			cmds = [c for c in self.hintingCommands if c.get('code')[-1] == 'h']
		self.setCommands(cmds)

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
		self.setCommands(cmds)
		self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def deleteXDeltas(self, item=0):
		self.prepareUndo("Clear X Deltas")
		cmds = [cmd for cmd in self.hintingCommands if 'deltah' not in cmd.get('code')]
		self.setCommands(cmds)
		self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def deleteYDeltas(self, item=0):
		self.prepareUndo("Clear Y Deltas")
		cmds = [cmd for cmd in self.hintingCommands if 'deltav' not in cmd.get('code')]
		self.setCommands(cmds)
		self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def deleteXDeltas(self, item=0):
		self.prepareUndo("Clear X Deltas")
		cmds = [cmd for cmd in self.hintingCommands if 'deltah' not in cmd.get('code')]
		self.setCommands(cmds)
		self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def deleteYDeltas(self, item=0):
		self.prepareUndo("Clear X Deltas")
		cmds = [cmd for cmd in self.hintingCommands if 'deltav' not in cmd.get('code')]
		self.setCommands(cmds)
		self.updateGlyphProgram(tthTool.getFontModel())
		self.performUndo()

	def cleanCommands(self, fm):
		cmds = [c for c in self.hintingCommands if self.commandIsOK(c, fm)]
		self.setCommands(cmds)

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
		self.cleanCommands(fm)
		self.saveCommandsToUFO()
		self.compileToUFO(fm)

	def updateGlyphProgram(self, fm):
		self.compile(fm)
		parametric.processParametric(fm, self)
		tthTool.parametricPreviewPanel.updateDisplay()
		tthTool.hintingProgramHasChanged(fm)

	def saveCommandsToUFO(self):
		"""Save what can be saved in the UFO Lib."""
		# write self.hintingCommands to UFO lib.
		self._g.lib[kTTProgramKey] = Data(ET.tostring(self.hintingCommands))

	def loadFromUFO(self, fm):
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

		layerName = "Cubic contour"

		ttprogram = self._g.lib[kTTProgramKey].data
		root = ET.fromstring(ttprogram)
		absent = []
		stillMissing = []
		for cmd in root:
			cmd.set('active', cmd.get('active', 'true'))
			if 'delta' in cmd.get('code'):
				cmd.set('gray', cmd.get('gray', 'true'))
				cmd.set('mono', cmd.get('mono', 'true'))
			if self.commandIsOK(cmd, fm, verbose = True, absent = absent):
				self.hintingCommands.append(cmd)
			else:
				self.convertCmdPoints(cmd, layerName)
				if self.commandIsOK(cmd, fm, verbose = True, absent = stillMissing):
					self.hintingCommands.append(cmd)
					if silent: return
					message = "[TTH WARNING] In glyph "+self._g.name+":"
					if stillMissing:
						message += "The following points do not exist. "
						message += "Commands acting on these points have been erased:\n\t"
						message += '\n\t'.join([repr(e) for e in stillMissing])
					if stillMissing: print message


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
