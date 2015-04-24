from lib.fontObjects.doodleFontCompiler.ttfCompiler import TTFCompilerSettings
from mojo.roboFont import CurrentFont, RFont

import tempfile

from commons import helperFunctions, textRenderer

from models.TTHTool import uniqueInstance as tthTool

from views import previewInGlyphWindow as PIGW

reload(helperFunctions)
reload(textRenderer)

FL_tth_key = "com.fontlab.v2.tth"
SP_tth_key = "com.sansplomb.tth"
gasp_key = TTFCompilerSettings.roboHintGaspLibKey
hdmx_key = TTFCompilerSettings.roboHintHdmxLibKey

class TTHFont():
	def __init__(self, font):
		# the corresponding Robofont font
		self.f = font

		# A plist with custom 'SansPlomb' data
		self.SP_tth_lib = helperFunctions.getOrPutDefault(self.f.lib, SP_tth_key, {})
		# The rasterizer mode: Monochrome, Grayscale, or Subpixel
		self.bitmapPreviewSelection = helperFunctions.getOrPutDefault(self.SP_tth_lib, "bitmapPreviewSelection", 'Monochrome')

		# Defaults sizes at which to store cached advance widths.
		# PPEM = Pixel Per Em ? OR Point Per Em ?
		self.hdmx_ppem_sizes = [8, 9, 10, 11, 12, 13, 14, 15, 16]
		self.setControlValues()

		# Option for the generated TTH assembly
		self.deactivateStemWhenGrayScale = helperFunctions.getOrPutDefault(self.SP_tth_lib, "deactivateStemWhenGrayScale", False)

		self._pigw = None # internal preview in glyph-window

		# The TextRenderer caches glyphs' bitmap, so that is must be stored
		# in the Font Model.
		self.textRenderer = None
		# Path to temporary file for the partial font
		tempPartial = tempfile.NamedTemporaryFile(suffix='.ttf', delete=False)
		self.partialtempfontpath = tempPartial.name
		tempPartial.close()
		# Path to temporary file for the full font (generated TTF)
		tempFull = tempfile.NamedTemporaryFile(suffix='.ttf', delete=False)
		self.fulltempfontpath = tempFull.name
		tempFull.close()

	def __del__(self):
		self.f = None
		if self._pigw != None:
			self._pigw.removeFromSuperview()
			self._pigw = None

# - - - - - - - - - - - - - - - - PREVIEW IN GLYPH-WINDOW

	def createPreviewInGlyphWindowIfNeeded(self):
		if self._pigw == None:
			self._pigw = self.createPreviewInGlyphWindow()

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
		superview = tthTool.eventController.getNSView().enclosingScrollView().superview()
		if superview == None: return
		newView = PIGW.PreviewInGlyphWindow.alloc().initWithFontAndTool(self, tthTool)
		superview.addSubview_(newView)
		newView.recomputeFrame()
		if tthTool.showPreviewInGlyphWindow == 0:
			newView.setHidden_(True)
		return newView

# - - - - - - - - - - - - - - - -

	def setControlValues(self):
		try:
			tth_lib = helperFunctions.getOrPutDefault(self.f.lib, FL_tth_key, {})

			# From the plist written by FontLab when exporting a font to
			# UFO, we recover some useful data for hinting

			# Descriptions of zones
			self.zones 		= helperFunctions.getOrPutDefault(tth_lib, "zones", {})
			# Descriptions of typical stem widths
			self.stems 		= helperFunctions.getOrPutDefault(tth_lib, "stems", {})
			# FIXME: describe this
			self.codeppm	= helperFunctions.getOrPutDefault(tth_lib, "codeppm", 72)
			# FIXME: describe this
			self.alignppm	= helperFunctions.getOrPutDefault(tth_lib, "alignppm", 64)
			# FIXME: describe this
			self.stemsnap	= helperFunctions.getOrPutDefault(tth_lib, "stemsnap", 17)

			# FIXME: describe this
			self.gasp_ranges  = helperFunctions.getOrPutDefault(self.f.lib, gasp_key, {})
			# FIXME: describe this
			self.hdmx_ppems   = helperFunctions.getOrPutDefault(self.f.lib, hdmx_key, {})
		except:
			print "ERROR: can't set font's control values"

	def setFont(self, font):
		self.f = font

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
		self.textRenderer = textRenderer.TextRenderer(self.partialtempfontpath, self.bitmapPreviewSelection)

	def setBitmapPreview(self, preview):
		if preview in ['Monochrome', 'Grayscale', 'Subpixel']:
			old = self.bitmapPreviewSelection
			self.bitmapPreviewSelection = preview
			self.SP_tth_lib["bitmapPreviewSelection"] = preview
			if old != preview:
				self.regenTextRenderer()

	def setHdmxPpemSizes(self, ppems):
		self.hdmx_ppem_sizes = ppems

# - - - - - - - - - - - - - - - - - - - - - - - - - - - FONT GENERATION

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
			tempFont.generate(self.partialtempfontpath, 'ttf', decompose = False, checkOutlines = False, autohint = False, releaseMode = False, glyphOrder=None, progressBar = None )
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

