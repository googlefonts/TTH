import tempfile
from lib.fontObjects.doodleFontCompiler.ttfCompiler import TTFCompilerSettings

from generals import helperFunctions

FL_tth_key = "com.fontlab.v2.tth"
SP_tth_key = "com.sansplomb.tth"
gasp_key = TTFCompilerSettings.roboHintGaspLibKey


class FontModel():
	def __init__(self, font):
		self.f = font
		self.UPM = font.info.unitsPerEm

		self.SP_tth_lib = helperFunctions.getOrPutDefault(self.f.lib, SP_tth_key, {})
		self.bitmapPreviewSelection = helperFunctions.getOrPutDefault(self.SP_tth_lib, "bitmapPreviewSelection", 'Monochrome')

		self.setControlValues()

		self.textRenderer = None

		temp = tempfile.NamedTemporaryFile(suffix='.ttf', delete=False)
		self.partialtempfontpath = temp.name

		temp.close()
		self.doneGeneratingPartialFont = False

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
		except:
			print "ERROR: can't set font's control values"