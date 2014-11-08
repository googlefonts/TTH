from robofab.world import *
from mojo.extensions import *
import HelperFunc as HF

import tempfile
import TextRenderer as TR

from lib.fontObjects.doodleFontCompiler.ttfCompiler import TTFCompilerSettings

DefaultKeyStub = "com.sansplomb.TTH."

defaultKeyCurrentPPMSize = DefaultKeyStub + "currentPPMSize"
defaultKeySelectedAxis = DefaultKeyStub + "selectedAxis"
defaultKeyPreviewFrom = DefaultKeyStub + "previewFrom"
defaultKeyPreviewTo = DefaultKeyStub + "previewTo"

defaultKeyAlwaysRefresh = DefaultKeyStub + "alwaysRefresh"
defaultKeyShowOutline = DefaultKeyStub + "showOutline"
defaultKeyShowBitmap = DefaultKeyStub + "showBitmap"
defaultKeyShowGrid = DefaultKeyStub + "showGrid"
defaultKeyShowCenterPixels = DefaultKeyStub + "showCenterPixels"
defaultKeyShowPreviewInGlyphWindow = DefaultKeyStub + "showPreviewInGlyphWindow"

# ======================================================================

FL_tth_key = "com.fontlab.v2.tth"
SP_tth_key = "com.sansplomb.tth"
gasp_key = TTFCompilerSettings.roboHintGaspLibKey

# ======================================================================

class fontModel():
	def __init__(self, font):
		self.f = font
		self.UPM = font.info.unitsPerEm

		self.SP_tth_lib = HF.getOrPutDefault(self.f.lib, SP_tth_key, {})
		self.bitmapPreviewSelection = HF.getOrPutDefault(self.SP_tth_lib, "bitmapPreviewSelection", 'Monochrome')

		self.setControlValues()

		self.textRenderer = None

		temp = tempfile.NamedTemporaryFile(suffix='.ttf', delete=False)
		self.partialtempfontpath = temp.name
		#print "Temporary file is", self.partialtempfontpath
		temp.close()
		self.doneGeneratingPartialFont = False

		self.deactivateStemWhenGrayScale = HF.getOrPutDefault(self.SP_tth_lib, "deactivateStemWhenGrayScale", False)

	def setFont(self, font):
		self.f = font

	def setUPM(self, UPM):
		self.UPM = int(UPM)

	def resetFontUPM(self, font):
		if font != None:
			self.UPM = font.info.unitsPerEm
			return self.UPM
		return None

	def setDeactivateStemWhenGrayScale(self, valueBool):
		self.deactivateStemWhenGrayScale = self.SP_tth_lib["deactivateStemWhenGrayScale"] = valueBool

	def setBitmapPreview(self, preview):
		if preview in ['Monochrome', 'Grayscale', 'Subpixel']:
			self.bitmapPreviewSelection = self.SP_tth_lib["bitmapPreviewSelection"] = preview

	def setControlValues(self):
		try:
			tth_lib = HF.getOrPutDefault(self.f.lib, FL_tth_key, {})

			self.zones = HF.getOrPutDefault(tth_lib, "zones", {})
			self.stems = HF.getOrPutDefault(tth_lib, "stems", {})
			self.codeppm	= HF.getOrPutDefault(tth_lib, "codeppm", 72)
			self.alignppm	= HF.getOrPutDefault(tth_lib, "alignppm", 64)
			self.stemsnap	= HF.getOrPutDefault(tth_lib, "stemsnap", 17)
			self.stems = HF.getOrPutDefault(tth_lib, "stems", {})

			self.gasp_ranges = HF.getOrPutDefault(self.f.lib, gasp_key, {})
		except:
			print "ERROR: can't set font's control values"
			pass

	def regenTextRenderer(self):
		self.textRenderer = TR.TextRenderer(self.partialtempfontpath, self.bitmapPreviewSelection)

	def getOrDefault(self, dico, key, default):
		try:
			return dico[key]
		except:
			return default

	def getOrPutDefault(self, dico, key, default):
		try:
			return dico[key]
		except:
			dico[key] = default
			return default

	def invertedDictionary(self, dico):
		return dict([(v,k) for (k,v) in dico.iteritems()])

	def setStemsnap(self, value):
		self.stemsnap = int(value)

	def setAlignppm(self, value):
		self.alignppm = int(value)

	def setCodeppm(self, value):
		self.codeppm = int(value)

# ==================================== Functions for Zones

	def buildUIZoneDict(self, zone, name):
		c_zoneDict = {}
		c_zoneDict['Name'] = name
		c_zoneDict['Position'] = int(zone['position'])
		c_zoneDict['Width'] = int(zone['width'])
		deltaString = ''
		if 'delta' in zone:
			count = 0
			for ppEmSize in zone['delta']:
				delta= str(zone['delta'][str(ppEmSize)]) + '@' + str(ppEmSize)
				deltaString += delta
				if count < len(zone['delta'])-1:
					deltaString += ', '
				count += 1
			c_zoneDict['Delta'] = deltaString
		else:
			c_zoneDict['Delta'] = '0@0'
		return c_zoneDict

	def buildUIZonesList(self, buildTop):
		return [self.buildUIZoneDict(zone, name) for name, zone in self.zones.iteritems() if zone['top'] == buildTop]

# ======================================= Functions for Stems


	def buildStemUIDict(self, stem, name):
		c_stemDict = {}
		c_stemDict['Name'] = name
		c_stemDict['Width'] = int(stem['width'])
		invDico = self.invertedDictionary(stem['round'])
		for i in range(1,7):
			c_stemDict[str(i)+' px'] = HF.getOrDefault(invDico, i, '0')
		return c_stemDict

	def buildStemsUIList(self, horizontal=True):
		return [self.buildStemUIDict(stem, name) for name, stem in self.stems.iteritems() if stem['horizontal'] == horizontal]


class TTHToolModel():
	def __init__(self):

		self.PPM_Size = getExtensionDefault(defaultKeyCurrentPPMSize, fallback=9)
		self.pitch = 1000/self.PPM_Size
		self.fPitch = 1000.0/self.PPM_Size
		self.selectedAxis = getExtensionDefault(defaultKeySelectedAxis, fallback='X')

		self.selectedHintingTool = 'Align'
		self.selectedAlignmentTypeAlign = 'round'
		self.selectedAlignmentTypeLink = 'None'
		self.selectedStemX = 'Guess'
		self.selectedStemY = 'Guess'
		self.stemsListX = []
		self.stemsListY = []
		self.roundBool = 0
		self.deltaOffset = 0
		self.deltaRange1 = 9
		self.deltaRange2 = 9

		self.toolsWindowPosSize = (170, 30, 265, 95)
		self.previewString = '/?'
		self.previewFrom = getExtensionDefault(defaultKeyPreviewFrom, fallback=9)
		self.previewTo = getExtensionDefault(defaultKeyPreviewTo, fallback=72)
		self.requiredGlyphsForPartialTempFont = set()
		self.requiredGlyphsForPartialTempFont.add('space')
		self.alwaysRefresh = getExtensionDefault(defaultKeyAlwaysRefresh, fallback=1)
		self.showOutline = getExtensionDefault(defaultKeyShowOutline, fallback=0)
		self.showBitmap = getExtensionDefault(defaultKeyShowBitmap, fallback=0)
		self.showGrid = getExtensionDefault(defaultKeyShowGrid, fallback=0)
		self.showCenterPixel = getExtensionDefault(defaultKeyShowCenterPixels, fallback=0)
		self.showPreviewInGlyphWindow = getExtensionDefault(defaultKeyShowPreviewInGlyphWindow, fallback=1)

		self.roundFactor_Stems = 15
		self.roundFactor_Jumps = 20

		self.minStemX = 20
		self.minStemY = 20
		self.maxStemX = 1000
		self.maxStemY = 1000

		self.angleTolerance = 10.0

	def setAlwaysRefresh(self, valueBool):
		self.alwaysRefresh = valueBool
		setExtensionDefault(defaultKeyAlwaysRefresh, valueBool)

	def setShowOutline(self, valueBool):
		self.showOutline = valueBool
		setExtensionDefault(defaultKeyShowOutline, valueBool)

	def setShowBitmap(self, valueBool):
		self.showBitmap = valueBool
		setExtensionDefault(defaultKeyShowBitmap, valueBool)

	def setShowGrid(self, valueBool):
		self.showGrid = valueBool
		setExtensionDefault(defaultKeyShowGrid, valueBool)

	def setShowCenterPixels(self, valueBool):
		self.showCenterPixel = valueBool
		setExtensionDefault(defaultKeyShowCenterPixels, 0)

	def setShowPreviewInGlyphWindow(self, valueBool):
		self.showPreviewInGlyphWindow = valueBool
		setExtensionDefault(defaultKeyShowPreviewInGlyphWindow, valueBool)

	def setSize(self, size):
		self.PPM_Size = int(size)
		setExtensionDefault(defaultKeyCurrentPPMSize, self.PPM_Size)

	def setPreviewFrom(self, value):
		self.previewFrom = value
		setExtensionDefault(defaultKeyPreviewFrom, value)

	def setPreviewTo(self, value):
		self.previewTo = value
		setExtensionDefault(defaultKeyPreviewTo, value)

	def resetPitch(self, UPM):
		self.pitch = UPM/self.PPM_Size
		self.fPitch = float(UPM)/self.PPM_Size

	def setAxis(self, axis):
		if axis in ['X', 'Y']:
			self.selectedAxis = axis
			setExtensionDefault(defaultKeySelectedAxis, axis)

	def setHintingTool(self, hintingTool):
		if hintingTool in ['Align', 'Single Link', 'Double Link', 'Interpolation', 'Middle Delta', 'Final Delta', 'Selection']:
			self.selectedHintingTool = hintingTool

	def setAlignmentTypeAlign(self, alignmentType):
		if alignmentType in ['round', 'left', 'right', 'center', 'double']:
			self.selectedAlignmentTypeAlign = alignmentType

	def setAlignmentTypeLink(self, alignmentType):
		if alignmentType in ['None', 'round', 'left', 'right', 'center', 'double']:
			self.selectedAlignmentTypeLink = alignmentType

	def setStemX(self, stem):
		self.selectedStemX = str(stem)

	def setStemY(self, stem):
		self.selectedStemY = str(stem)

	def setRoundBool(self, roundBool):
		if roundBool in [0, 1]:
			self.roundBool = roundBool

	def setDeltaOffset(self, offset):
		if offset >= -8 and offset <= 8:
			self.deltaOffset = int(offset)

	def setDeltaRange1(self, value):
		self.deltaRange1 = int(value)

	def setDeltaRange2(self, value):
		self.deltaRange2 = int(value)

	def setPreviewString(self, previewString):
		self.previewString = previewString

	def setAlwaysRefresh(self, valueBool):
		if valueBool in (0, 1):
			self.alwaysRefresh = valueBool

