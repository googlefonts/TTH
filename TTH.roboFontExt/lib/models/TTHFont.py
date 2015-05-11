from mojo.roboFont import CurrentFont, RFont
from mojo.events import getActiveEventTool

import tempfile

from commons import helperFunctions
from drawing import textRenderer, geom

from models.TTHTool import uniqueInstance as tthTool
from models import TTHGlyph

from views import previewInGlyphWindow as PIGW

import tt_tables

reload(helperFunctions)
reload(textRenderer)
reload(TTHGlyph)
reload(tt_tables)

FL_tth_key = "com.fontlab.v2.tth"
SP_tth_key = "com.sansplomb.tth"

class TTHFont():
	def __init__(self, font):
		# the corresponding Robofont font
		self.f = font

		# A plist with custom 'SansPlomb' data
		SPLib = self.getSPLib()
		# The rasterizer mode: Monochrome, Grayscale, or Subpixel
		self.bitmapPreviewSelection = helperFunctions.getOrPutDefault(SPLib, "bitmapPreviewSelection", 'Monochrome')

		# Defaults sizes at which to store cached advance widths.
		# PPEM = Pixel Per Em ? OR Point Per Em ?
		self.hdmx_ppem_sizes = [8, 9, 10, 11, 12, 13, 14, 15, 16]

		self._readControlValuesFromUFO()

		# For storing the position and size of the zone labels
		self.zoneLabels = {}

		# Option for the generated TTH assembly
		self.deactivateStemWhenGrayScale = helperFunctions.getOrPutDefault(SPLib, "deactivateStemWhenGrayScale", False)

		self._pigw = None # internal preview in glyph-window

		# TTHGlyph instances
		self._glyphModels = {}

		# TrueType tables
		self.stem_to_cvt = None
		self.zone_to_cvt = None
		self.writeCVTandPREP()
		tt_tables.writeFPGM(self)
		tt_tables.writegasp(self)

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

	def __del__(self):
		self.f = None
		if self._pigw != None:
			self._pigw.removeFromSuperview()
			self._pigw = None

# - - - - - - - - - - - - - - - - - - - - - - - - - - TTHGlyph

	def glyphModelForGlyph(self, g):
		key = g.name
		if key not in self._glyphModels:
			model = TTHGlyph.TTHGlyph(g)
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

	def getSPLib(self):
		return helperFunctions.getOrPutDefault(self.f.lib, SP_tth_key, {})

# - - - - - - - - - - - - - - - - PREVIEW IN GLYPH-WINDOW

	def createPreviewInGlyphWindowIfNeeded(self):
		badFont = not helperFunctions.fontIsQuadratic(self.f)
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
		# useless because they ARE the same dictionary
		self.f.lib[FL_tth_key]["zones"] = self.zones

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

	def zoneClicked(self, clickPos):
		for zoneName, (lPos, lSize) in self.zoneLabels.iteritems():
			if lPos == None: continue
			lo = lPos - 0.5 * lSize
			hi = lPos + 0.5 * lSize
			if lo.x <= clickPos.x <= hi.x and lo.y <= clickPos.y <= hi.y:
				return (zoneName, self.zones[zoneName])
		return None, None

# - - - - - - - - - - - - - - - -

	def changeBitmapPreviewMode(self, mode):
		old = self.bitmapPreviewSelection
		if mode not in ['Monochrome', 'Grayscale', 'Subpixel']: return
		if old == mode: return False
		self.bitmapPreviewSelection = mode
		self.getSPLib()["bitmapPreviewSelection"] = mode
		self.regenTextRenderer()
		return True

# - - - - - - - - - - - - - - - -

	def writeCVTandPREP(self):
		stem_to_cvt, zone_to_cvt = tt_tables.writeCVTandPREP(self)
		self.stem_to_cvt = stem_to_cvt
		self.zone_to_cvt = zone_to_cvt

# - - - - - - - - - - - - - - - -

	def _readControlValuesFromUFO(self):
		try:
			tth_lib = helperFunctions.getOrPutDefault(self.f.lib, FL_tth_key, {})

			# From the plist written by FontLab when exporting a font to
			# UFO, we recover some useful data for hinting

			# Descriptions of zones
			self.zones = helperFunctions.getOrPutDefault(tth_lib, "zones", {})
			# Descriptions of typical stem widths
			stems = helperFunctions.getOrPutDefault(tth_lib, "stems", {})
			self.horizontalStems = dict((n,s) for (n,s) in stems.iteritems() if s['horizontal'])
			self.verticalStems   = dict((n,s) for (n,s) in stems.iteritems() if not s['horizontal'])
			# FIXME: describe this
			self.codeppm	= helperFunctions.getOrPutDefault(tth_lib, "codeppm", 72)
			# FIXME: describe this
			self.alignppm	= helperFunctions.getOrPutDefault(tth_lib, "alignppm", 64)
			# FIXME: describe this
			self.stemsnap	= helperFunctions.getOrPutDefault(tth_lib, "stemsnap", 17)

			# FIXME: describe this
			self.gasp_ranges  = helperFunctions.getOrPutDefault(self.f.lib, tt_tables.k_gasp_key, {})
			# FIXME: describe this
			self.hdmx_ppems   = helperFunctions.getOrPutDefault(self.f.lib, tt_tables.k_hdmx_key, {})
		except:
			print "[TTH ERROR]: Can't read font's control values"

	@property
	def UPM(self):
		return self.f.info.unitsPerEm

	def getPitch(self):
		return float(self.UPM) / tthTool.PPM_Size

	@property
	def ascent(self):
		return self.f.info.openTypeOS2WinAscent

	@property
	def descent(self):
		return self.f.info.openTypeOS2WinDescent

	def regenTextRenderer(self):
		self.textRenderer = textRenderer.TextRenderer(self.tempPartialFontPath, self.bitmapPreviewSelection)

	def setHdmxPpemSizes(self, ppems):
		self.hdmx_ppem_sizes = ppems

# - - - - - - - - - - - - - - - - - - - - - - - - - - - STEMS

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

# - - - - - - - - - - - - - - - - - - - - - - - - - - - FONT GENERATION

	_helpOnFontGeneration = '''
What tables are needed?
CVT , PREP
	The CVT and PREP table should be re-generated when the 'Control
	Value Panel' is closed.
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

	def generateFullTempFont(self):
		try:
			if tt_tables.k_hdmx_key in self.c_fontModel.f.lib:
				del self.c_fontModel.f.lib[tt_tables.k_hdmx_key]
			self.f.generate(self.tempFullFontPath, 'ttf',\
					decompose     = False,\
					checkOutlines = False,\
					autohint      = False,\
					releaseMode   = False,\
					glyphOrder    = None,\
					progressBar   = None)
			self.editComponentsFlags(self.f, self.tempFullFontPath)
		except:
			print 'ERROR: Unable to generate full font'

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
			for key in ['com.robofont.robohint.cvt ',
					'com.robofont.robohint.prep',
					'com.robofont.robohint.fpgm',
					'com.robofont.robohint.gasp',
					'com.robofont.robohint.hdmx',
					'com.robofont.robohint.maxp.maxStorage']:
				if key in lib:
					tempFont.lib[key] = lib[key]
			for name in glyphSet:
				#print '>'+name+'<'
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
