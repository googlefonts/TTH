from mojo.roboFont import CurrentFont, RFont
from mojo.events import getActiveEventTool
from fontTools import ttLib

import os, tempfile

from commons import helperFunctions as HF
from drawing import textRenderer, geom

from models.TTHTool import uniqueInstance as tthTool
from models import TTHGlyph

from views import previewInGlyphWindow as PIGW

import tt
from tt import tables

reload(HF)
reload(textRenderer)
reload(TTHGlyph)
reload(tables)

class TTHFont(object):
	def __init__(self, font):
		# the corresponding Robofont font
		self.f = font

		# Defaults sizes at which to store cached advance widths.
		# PPEM = Pixel Per Em ? OR Point Per Em ?
		self.hdmx_ppem_sizes = [8, 9, 10, 11, 12, 13, 14, 15, 16]

		self._readControlValuesFromUFO()

		# For storing the position and size of the zone labels
		self.zoneLabels = {}

		self._pigw = None # internal preview in glyph-window

		# TTHGlyph instances
		self._glyphModels = {}

		# TrueType tables
		self.dirtyCVT()
		self.writeCVTandPREP()
		tables.write_FPGM(self)
		tables.write_gasp(self)

		# The TextRenderer caches glyphs' bitmap, so that is must be stored
		# in the Font Model.
		self.textRenderer = None
		# Path to temporary file for the partial font
		tempPartial = tempfile.NamedTemporaryFile(suffix='.ttf', delete=False)
		self.tempPartialFontPath = tempPartial.name
		tempPartial.close()
		# Path to temporary file for the full font (generated TTF)
		tempFull = tempfile.NamedTemporaryFile(suffix='.ttf', delete=False)
		self.tempFullFontPath = tempFull.name
		tempFull.close()

		self.updatePartialFont(tthTool.requiredGlyphsForPartialTempFont)

	def __del__(self):
		self.f = None
		if self._pigw != None:
			self._pigw.removeFromSuperview()
			self._pigw = None

	# getter / setter for 'sansplomb' lib PLIST

	def getSPVal(self, name, default):
		return HF.getOrPutDefault(self.getSPLib(), name, default)

	@property # The rasterizer mode: Monochrome, Grayscale, or Subpixel
	def bitmapPreviewMode(self):
		return self.getSPVal('bitmapPreviewMode', 'Monochrome')
	@bitmapPreviewMode.setter
	def bitmapPreviewMode(self, mode):
		if mode not in ['Monochrome', 'Grayscale', 'Subpixel']: return
		old = self.bitmapPreviewMode
		if old == mode: return
		self.getSPLib()["bitmapPreviewMode"] = mode
		self.regenTextRenderer()

	@property # Option for the generated TTH assembly (in the PREP table)
	def deactivateStemWhenGrayScale(self):
		return self.getSPVal('deactivateStemWhenGrayScale', 0)
	@deactivateStemWhenGrayScale.setter
	def deactivateStemWhenGrayScale(self, dgs):
		self.getSPLib()['deactivateStemWhenGrayScale'] = dgs

	@property
	def angleTolerance(self):
		return self.getSPVal('angleTolerance', 10)
	@angleTolerance.setter
	def angleTolerance(self, at):
		self.getSPLib()['angleTolerance'] = at

	@property # the minimum and maximum width of horizontal/vertical stems
	def stemSizeBounds(self):
		return self.getSPVal('stemSizeBounds', ((20, 200), (20,200)))
	@stemSizeBounds.setter
	def stemSizeBounds(self, b):
		self.getSPLib()['stemSizeBounds'] = b

	# getter / setter for 'FontLab' lib PLIST

	@property # FIXME: describe this. written in the FPGM table
	def stemsnap(self):
		return HF.getOrPutDefault(self.getFLLib(), "stemsnap", 17)
	@stemsnap.setter
	def stemsnap(self, ss):
		self.getFLLib()['stemsnap'] = ss

	@property # FIXME: describe this. used in generationg the (GASP ? and) PREP tables
	def codeppm(self):
		return HF.getOrPutDefault(self.getFLLib(), "codeppm", 72)
	@codeppm.setter
	def codeppm(self, cp):
		self.getFLLib()['codeppm'] = cp

	@property # FIXME: describe this. used in first element of the CVT
	def alignppm(self):
		return HF.getOrPutDefault(self.getFLLib(), "alignppm", 64)
	@alignppm.setter
	def alignppm(self, ap):
		self.getFLLib()['alignppm'] = ap

	def dirtyCVT(self):
		self.stem_to_cvt = None
		self.zone_to_cvt = None

	def setOptions(self, stemsnap, alignppm, codeppm, dswgs):
		self.stemsnap = stemsnap
		self.alignppm = alignppm
		self.codeppm  = codeppm
		self.deactivateStemWhenGrayScale = dswgs
		self.dirtyCVT()

# - - - - - - - - - - - - - - - - - - - - - - - - - - TTHGlyph

	def hasGlyphModelForGlyph(self, g):
		key = g.name
		return (key in self._glyphModels)

	def glyphModelForGlyph(self, g, compile=True):
		key = g.name
		if not self.hasGlyphModelForGlyph(g):
			model = TTHGlyph.TTHGlyph(g, self, compile)
			self._glyphModels[key] = model
			return model
		return self._glyphModels[key]

	def delGlyphModelForGlyph(self, glyph):
		key = glyph.name
		if key in self._glyphModels:
			model = self._glyphModels[key]
			del model
			del self._glyphModels[key]

# - - - - - - - - - - - - - - - - - - - - - - - - - - LIB

	def getFLLib(self):
		'''A plist with custom 'FontLab' data'''
		return HF.getOrPutDefault(self.f.lib, tt.FL_tth_key, {})

	def getSPLib(self):
		'''A plist with custom 'SansPlomb' data'''
		return HF.getOrPutDefault(self.f.lib, tt.SP_tth_key, {})

# - - - - - - - - - - - - - - - - PREVIEW IN GLYPH-WINDOW

	def createPreviewInGlyphWindowIfNeeded(self):
		badFont = not HF.fontIsQuadratic(self.f)
		if (not badFont) and self._pigw == None:
			self._pigw = self.createPreviewInGlyphWindow()
			return True
		return False

	@property
	def previewInGlyphWindow(self):
		return self._pigw

	def killPreviewInGlyphWindow(self):
		if self._pigw == None: return
		self._pigw.setHidden_(True)
		self._pigw.die()
		self._pigw.removeFromSuperview()
		self._pigw = None

	def setPreviewInGlyphWindowVisibility(self, visible):
		if self._pigw == None: return
		self._pigw.setHidden_(visible == 0)

	def createPreviewInGlyphWindow(self):
		eventController = getActiveEventTool()
		if eventController is None: return
		superview = eventController.getNSView().enclosingScrollView().superview()
		if superview == None: return
		newView = PIGW.PreviewInGlyphWindow.alloc().initWithFontAndTool(self, tthTool)
		superview.addSubview_(newView)
		newView.recomputeFrame()
		if tthTool.showPreviewInGlyphWindow == 0:
			newView.setHidden_(True)
		return newView

# - - - - - - - - - - - - - - - - ZONES & ZONE LABELS

	def saveZonesToUFO(self):
		self.f.lib[tt.FL_tth_key]["zones"] = self.zones

	def setZoneDelta(self, (zoneName, zone), PPMSize, deltaValue):
		assert(zoneName in self.zones)
		if 'delta' not in zone:
			if deltaValue != 0: zone['delta'] = {}
			else: return
		deltas = zone['delta']
		key    = str(PPMSize)
		if deltaValue == 0:
			if key in deltas:
				del deltas[key]
				if len(deltas) == 0:
					del zone['delta']
		else:
			deltas[key] = deltaValue
		self.saveZonesToUFO()

	def zoneAtPoint(self, point):
		for name, zone in self.zones.iteritems():
			if zone['top']:
				y_min = int(zone['position'])
				y_max = int(zone['position']) + int(zone['width'])
			else:
				y_max = int(zone['position'])
				y_min = int(zone['position']) - int(zone['width'])
			if y_min <= point.y <= y_max:
				return name, zone
		return None, None

	def zoneClicked(self, clickPos):
		for zoneName, (lPos, lSize) in self.zoneLabels.iteritems():
			if lPos == None: continue
			lo = lPos - 0.5 * lSize
			hi = lPos + 0.5 * lSize
			if lo.x <= clickPos.x <= hi.x and lo.y <= clickPos.y <= hi.y:
				return (zoneName, self.zones[zoneName])
		return None, None

	def addZone(self, name, newZone):
		self.zones[name] = newZone
		self.saveZonesToUFO()
		self.dirtyCVT()

	def applyChangesFromUIZones(self, topUIZones, bottomUIZones):
		self.zones = {}
		for top, uiZones in [(True, topUIZones), (False, bottomUIZones)]:
			for uiZone in uiZones:
				# fill missing data
				if not ('Position' in uiZone): uiZone['Position'] = 0
				if not ('Width' in uiZone):    uiZone['Width'] = 0
				if not ('Delta' in uiZone):    uiZone['Delta'] = '0@0'
				self.addZone(uiZone['Name'], self.zoneOfUIZone(uiZone, top))
		self.saveZonesToUFO()
		self.dirtyCVT()

	def renameZonesInGlyphs(self, nameChanger, progress):
		TTHGlyph.silent = True
		counter = 0
		maxCount = len(self.f)
		for g in self.f:
			hasG = self.hasGlyphModelForGlyph(g)
			gm = self.glyphModelForGlyph(g, compile=False)
			gm.renameZone(nameChanger)
			if not hasG: self.delGlyphModelForGlyph(g)
			counter += 1
			if counter == 30:
				progress.increment(30)
				counter = 0
		progress.increment(counter)
		TTHGlyph.silent = False

	def zoneOfUIZone(self, uiZone, top):
		return {
				'position': uiZone['Position'],
				'width': uiZone['Width'],
				'delta': HF.deltaDictFromString(uiZone['Delta']),
				'top': top,
			}

# - - - - - - - - - - - - - - - -

	def writeCVTandPREP(self):
		stem_to_cvt, zone_to_cvt, CVT = tables.write_CVT_PREP(self)
		self.stem_to_cvt = stem_to_cvt
		self.zone_to_cvt = zone_to_cvt
		return (stem_to_cvt, zone_to_cvt, CVT)

# - - - - - - - - - - - - - - - -

	def _readControlValuesFromUFO(self):
		try:
			tth_lib = self.getFLLib()
			# From the plist written by FontLab when exporting a font to
			# UFO, we recover some useful data for hinting:

			# Descriptions of zones
			self.zones = HF.getOrPutDefault(tth_lib, "zones", {})
			# Descriptions of typical stem widths
			stems = HF.getOrPutDefault(tth_lib, "stems", {})
			self.horizontalStems = dict((n,s) for (n,s) in stems.iteritems() if s['horizontal'])
			self.verticalStems   = dict((n,s) for (n,s) in stems.iteritems() if not s['horizontal'])
			# FIXME: describe this
			self.gasp_ranges  = HF.getOrPutDefault(self.f.lib, tables.k_gasp_key, {})
		except:
			print "[TTH ERROR]: Can't read font's control values"

	@property
	def UPM(self):
		return self.f.info.unitsPerEm

	def getPitch(self):
		return float(self.UPM) / tthTool.PPM_Size

	@property
	def ascent(self): # FIXME: obtain this value from VDMX
		return self.f.info.openTypeOS2WinAscent

	@property
	def descent(self): # FIXME: obtain this value from VDMX
		return -self.f.info.openTypeOS2WinDescent

	def regenTextRenderer(self):
		self.textRenderer = textRenderer.TextRenderer(self.tempPartialFontPath, self.bitmapPreviewMode)

	def setHdmxPpemSizes(self, ppems):
		self.hdmx_ppem_sizes = ppems

# - - - - - - - - - - - - - - - - - - - - - - - - - - - STEMS

	def saveStemsToUFO(self):
		stems = self.horizontalStems.copy()
		stems.update(self.verticalStems)
		self.f.lib[tt.FL_tth_key]["stems"] = stems

	def guessStem(self, point1, point2):
		diff = geom.makePoint(point1) - geom.makePoint(point2)
		if tthTool.selectedAxis == 'X':
			dist = abs(diff.x)
		else:
			dist = abs(diff.y)
		if tthTool.selectedAxis == 'Y':
			candidates = self.horizontalStems
		else:
			candidates = self.verticalStems
		candidates = [(abs(int(stem['width'])-dist), stemName) for (stemName, stem) in candidates.iteritems()]
		if len(candidates) == 0:
			return None
		candidates.sort()
		if candidates[0][0] <= 0.3 * dist:
			return candidates[0][1]
		else:
			return None

	def applyChangesFromUIStems(self, horizontalUIStems, verticalUIStems):
		self.horizontalStems = {}
		self.verticalStems = {}
		for uiStem in horizontalUIStems:
			self.horizontalStems[uiStem['Name']] = self.stemOfUIStem(uiStem, True)
		for uiStem in verticalUIStems:
			self.verticalStems[uiStem['Name']] = self.stemOfUIStem(uiStem, False)
		self.saveStemsToUFO()
		self.dirtyCVT()

	def renameStemsInGlyphs(self, nameChanger, progress):
		TTHGlyph.silent = True
		counter = 0
		maxCount = len(self.f)
		for g in self.f:
			hasG = self.hasGlyphModelForGlyph(g)
			gm = self.glyphModelForGlyph(g, compile=False)
			glyphChanged = gm.renameStem(nameChanger)
			#if True:#hasG:# glyphChanged:
			#	gm.compileToUFO(self)
			if not hasG: self.delGlyphModelForGlyph(g)
			counter += 1
			if counter == 30:
				progress.increment(30)
				counter = 0
		progress.increment(counter)
		TTHGlyph.silent = False

	def stemOfUIStem(self, uiStem, isHorizontal):
		return {
				'horizontal': isHorizontal,
				'width': uiStem['Width'],
				'round': dict((str(uiStem[str(i)+' px']),i) for i in range(1,7)),
				}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - FONT GENERATION

	def compileAllGlyphs(self, progress=None):
		TTHGlyph.silent = True
		counter = 0
		maxCount = len(self.f)
		for g in self.f:
			hasG = self.hasGlyphModelForGlyph(g)
			self.glyphModelForGlyph(g, compile=False).compileToUFO(self)
			if not hasG: self.delGlyphModelForGlyph(g)
			counter += 1
			if (progress != None) and counter == 30:
				progress.increment(30)
				counter = 0
		if progress != None:
			progress.increment(counter)
		TTHGlyph.silent = False

	_helpOnFontGeneration = '''
What tables are needed?
CVT , PREP
	The CVT and PREP table should be re-generated
	- when the 'Control Value Panel' is closed?
	- when the zones change
FPGM
	Always regenerated. This is fast and safe.
	The table depends on 'stemsnap' which is modifiable in the
	'Control Value Panel'.
gasp
	The gasp table should be re-generated when the 'gasp sheet' of
	the preference panel is closed.
hdmx
VDMX
LTSH
	It is safe to generate these tables only just before the final
	complete font generation.

When do we regenerate a partial font?
	When one of the tables above is re-generated and when a
	hinting command is added/deleted/modified.
	(And of course when preview text uses a missing glyph.)'''

	def compileAllTTFData(self):
		print "Compiling CVT, PREP,",
		self.dirtyCVT()
		self.writeCVTandPREP()
		print "FPGM,",
		tables.write_FPGM(self)
		print "gasp,",
		tables.write_gasp(self)
		print "VDMX,",
		tables.write_VDMX(self)
		print "LTSH,",
		tables.write_LTSH(self)
		print "hdmx,",
		tables.write_hdmx(self)
		print "glyphs,",
		self.compileAllGlyphs()
		print "done."

	def generateFullTempFont(self):
		#try:
			if tables.k_hdmx_key in self.f.lib:
				del self.f.lib[tables.k_hdmx_key]
			self.f.generate(self.tempFullFontPath, 'ttf',\
					decompose     = False,\
					checkOutlines = False,\
					autohint      = False,\
					releaseMode   = False,\
					glyphOrder    = None,\
					progressBar   = None)
			self.editComponentsFlags(self.f, self.tempFullFontPath)
		#except:
		#	print 'ERROR: Unable to generate full font'

	def editComponentsFlags(self, workingUFO, destination):
		(head, tail) = os.path.split(destination)
		tail = tail[:-4]
		tail += '_glyf.' + 'ttf'
		fontpath_glyph = os.path.join(head, tail)
		tt = ttLib.TTFont(destination)
		glyfTable = tt['glyf']
		for glyphName in tt.glyphOrder:
			glyph = glyfTable[glyphName]
			if glyph.isComposite():
				for component in glyph.components:
					compoFlags = component.flags
					compoName = component.glyphName
					if workingUFO[glyphName].width == workingUFO[compoName].width:
						# turn the tenth bit on
						compoFlags = compoFlags | 0x200
					else:
						# turn the tenth bit off
						compoFlags = compoFlags & (~0x200)
					component.flags = compoFlags

		tt.save(fontpath_glyph)
		os.remove(destination)
		os.rename(fontpath_glyph, destination)

	def generatePartialTempFont(self, glyphSet):
		#try:
			tempFont = RFont(showUI=False)
			info = self.f.info
			tempFont.info.unitsPerEm = info.unitsPerEm
			tempFont.info.ascender   = info.ascender
			tempFont.info.descender  = info.descender
			tempFont.info.xHeight    = info.xHeight
			tempFont.info.capHeight  = info.capHeight
			tempFont.info.familyName = info.familyName
			tempFont.info.styleName  = info.styleName
			tempFont.glyphOrder = self.f.glyphOrder
			lib = self.f.lib
			for key in [tables.k_CVT_key,
					tables.k_prep_key,
					tables.k_fpgm_key,
					tables.k_gasp_key,
					tables.k_hdmx_key,
					'com.robofont.robohint.maxp.maxStorage']:
				if key in lib:
					tempFont.lib[key] = lib[key]
			for name in glyphSet:
				oldG = self.f[name]
				tempFont[name] = oldG
				newG = tempFont[name]
				newG.unicode = oldG.unicode # FIXME: why?
				key = 'com.robofont.robohint.assembly'
				if key in oldG.lib:
					newG.lib[key] = oldG.lib[key]
			tempFont.generate(self.tempPartialFontPath, 'ttf',
					decompose     = False,
					checkOutlines = False,
					autohint      = False,
					releaseMode   = False,
					glyphOrder    = None,
					progressBar   = None )
		#except:
		#	print 'ERROR: Unable to generate temporary font'

	def updatePartialFont(self, glyphSet):
		"""Typically called directly when the current glyph has been modifed."""
		self.generatePartialTempFont(glyphSet)
		self.regenTextRenderer()

	def updatePartialFontIfNeeded(self, g, curSet):
		"""Re-create the partial font if new glyphs are required."""
		(text, curGlyphString) = tthTool.prepareText(g, self.f)
		newSet = self.defineGlyphsForPartialTempFont(text, curGlyphString)
		regenerate = not newSet.issubset(curSet)
		n = len(curSet)
		if (n > 128) and (len(newSet) < n):
			regenerate = True
		if regenerate:
			self.updatePartialFont(newSet)
			return newSet
		return curSet

	def defineGlyphsForPartialTempFont(self, text, curGlyphName):
		def addGlyph(s, name):
			try:
				s.add(name)
				for component in self.f[name].components:
					s.add(component.baseGlyph)
			except:
				pass
		glyphSet = set()
		addGlyph(glyphSet, 'space')
		#for i in string.lowercase:
		#	addGlyph(glyphSet, i)
		#for i in string.uppercase:
		#	addGlyph(glyphSet, i)
		#for i in ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'zero']:
		#	addGlyph(glyphSet, i)
		addGlyph(glyphSet, curGlyphName)
		for name in text:
			addGlyph(glyphSet, name)
		return glyphSet

if tthTool._printLoadings: print "TTHFont, ",
