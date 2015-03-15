import tempfile
from lib.fontObjects.doodleFontCompiler.ttfCompiler import TTFCompilerSettings

from commons import helperFunctions, textRenderer

reload(helperFunctions)
reload(textRenderer)

FL_tth_key = "com.fontlab.v2.tth"
SP_tth_key = "com.sansplomb.tth"
gasp_key = TTFCompilerSettings.roboHintGaspLibKey
hdmx_key = TTFCompilerSettings.roboHintHdmxLibKey


class FontModel():
	def __init__(self, font):
		# the corresponding Robofont font
		self.f = font
		# Font-wise units per Em, typically 1000 for TrueType fonts
		self.UPM = font.info.unitsPerEm
		# FIXME: describe this
		self.OS2WinAscent = font.info.openTypeOS2WinAscent
		# FIXME: describe this
		self.OS2WinDescent = font.info.openTypeOS2WinDescent

		# A plist with custom 'SansPlomb' data
		self.SP_tth_lib = helperFunctions.getOrPutDefault(self.f.lib, SP_tth_key, {})
		# The rasterizer mode: Monochrome, Grayscale, or Subpixel
		self.bitmapPreviewSelection = helperFunctions.getOrPutDefault(self.SP_tth_lib, "bitmapPreviewSelection", 'Monochrome')

		# Defaults sizes at which to store cached advance widths.
		# PPEM = Pixel Per Em ? OR Point Per Em ?
		self.hdmx_ppem_sizes = [8, 9, 10, 11, 12, 13, 14, 15, 16]
		self.setControlValues()

		# The TextRenderer caches glyphs' bitmap, so that is must be stored
		# in the Font Model.
		self.textRenderer = None
		# What is this used for?
		self.textRendererFullFont = None

		tempPartial = tempfile.NamedTemporaryFile(suffix='.ttf', delete=False)
		# Path to temporary file for the partial font
		self.partialtempfontpath = tempPartial.name

		tempFull = tempfile.NamedTemporaryFile(suffix='.ttf', delete=False)
		# Path to temporary file for the full font (generated TTF)
		self.fulltempfontpath = tempFull.name
		
		tempPartial.close()
		tempFull.close()

		# Option for the generated TTH assembly
		self.deactivateStemWhenGrayScale = helperFunctions.getOrPutDefault(self.SP_tth_lib, "deactivateStemWhenGrayScale", False)


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

	def setUPM(self, UPM):
		self.UPM = int(UPM)

	def resetAscent(self):
		self.OS2WinAscent = self.f.info.openTypeOS2WinAscent

	def resetDescent(self):
		self.OS2WinDescent = self.f.info.openTypeOS2WinDescent

	def regenTextRenderer(self):
		self.textRenderer = textRenderer.TextRenderer(self.partialtempfontpath, self.bitmapPreviewSelection)

	def regenTextRendererFullFont(self):
		self.textRendererFullFont = textRenderer.TextRenderer(self.fulltempfontpath, self.bitmapPreviewSelection)

	def setBitmapPreview(self, preview):
		if preview in ['Monochrome', 'Grayscale', 'Subpixel']:
			self.bitmapPreviewSelection = self.SP_tth_lib["bitmapPreviewSelection"] = preview

	def setHdmxPpemSizes(self, ppems):
		self.hdmx_ppem_sizes = ppems
