from lib.fontObjects.doodleFontCompiler.ttfCompiler import TTFCompilerSettings

import tempfile

from commons import helperFunctions, textRenderer
from models.TTHTool import uniqueInstance as tthTool

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
