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
		self.f = font
		self.UPM = font.info.unitsPerEm
		self.OS2WinAscent = font.info.openTypeOS2WinAscent
		self.OS2WinDescent = font.info.openTypeOS2WinDescent

		self.SP_tth_lib = helperFunctions.getOrPutDefault(self.f.lib, SP_tth_key, {})
		self.bitmapPreviewSelection = helperFunctions.getOrPutDefault(self.SP_tth_lib, "bitmapPreviewSelection", 'Monochrome')

		self.hdmx_ppem_sizes = [8, 9, 10, 11, 12, 13, 14, 15, 16]
		self.setControlValues()

		self.textRenderer = None
		self.textRendererFullFont = None

		tempPartial = tempfile.NamedTemporaryFile(suffix='.ttf', delete=False)
		self.partialtempfontpath = tempPartial.name

		tempFull = tempfile.NamedTemporaryFile(suffix='.ttf', delete=False)
		self.fulltempfontpath = tempFull.name
		
		tempPartial.close()
		tempFull.close()

		self.deactivateStemWhenGrayScale = helperFunctions.getOrPutDefault(self.SP_tth_lib, "deactivateStemWhenGrayScale", False)


	def setControlValues(self):
		try:
			tth_lib = helperFunctions.getOrPutDefault(self.f.lib, FL_tth_key, {})

			self.zones 		= helperFunctions.getOrPutDefault(tth_lib, "zones", {})
			self.stems 		= helperFunctions.getOrPutDefault(tth_lib, "stems", {})
			self.codeppm	= helperFunctions.getOrPutDefault(tth_lib, "codeppm", 72)
			self.alignppm	= helperFunctions.getOrPutDefault(tth_lib, "alignppm", 64)
			self.stemsnap	= helperFunctions.getOrPutDefault(tth_lib, "stemsnap", 17)
			self.stems 		= helperFunctions.getOrPutDefault(tth_lib, "stems", {})

			self.gasp_ranges = helperFunctions.getOrPutDefault(self.f.lib, gasp_key, {})
			self.hdmx_ppems = helperFunctions.getOrPutDefault(self.f.lib, hdmx_key, {})
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
