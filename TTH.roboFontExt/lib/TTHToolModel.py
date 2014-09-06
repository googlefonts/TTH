from robofab.world import *

# ======================================================================

FL_tth_key = "com.fontlab.v2.tth"

# ======================================================================

class TTHToolModel():
	def __init__(self):
		self.f = CurrentFont()
		self.g = CurrentGlyph()
		self.UPM = 1000
		self.PPM_Size = 9
		self.pitch = self.UPM/self.PPM_Size
		self.selectedAxis = 'X'
		self.bitmapPreviewSelection = 'Monochrome'

		self.selectedHintingTool = 'Align'
		self.selectedAlignmentTypeAlign = 'round'
		self.selectedAlignmentTypeLink = 'None'
		self.selectedStemX = 'None'
		self.selectedStemY = 'None'
		self.stemsListX = []
		self.stemsListY = []
		self.roundBool = 0
		self.deltaOffset = 0
		self.deltaRange1 = 9
		self.deltaRange2 = 9

		self.textRenderer = None

		self.previewWindowVisible = 0
		self.programWindowVisible = 0


		self.previewWindowPosSize = (-510, 30, 500, -10)
		self.toolsWindowPosSize = (170, 30, 215, 65)
		self.centralWindowPosSize = (10, 30, 150, 115)
		self.programWindowPosSize = (395, 30, 600, 150)
		self.previewString = ''
		self.previewFrom = 9
		self.previewTo = 72
		self.requiredGlyphsForPartialTempFont = set()
		self.requiredGlyphsForPartialTempFont.add('space')
		self.alwaysRefresh = 1
		self.showOutline = 1
		self.showBitmap = 1
		self.showGrid = 1
		self.showCenterPixel = 0

	def setControlValues(self):
		try:
			tth_lib = self.getOrPutDefault(self.f.lib, FL_tth_key, {})
			self.zones	= self.getOrPutDefault(tth_lib, "zones", {})
			self.UITopZones = self.buildUIZonesList(buildTop=True)
			self.UIBottomZones = self.buildUIZonesList(buildTop=False)
			self.stems	= self.getOrPutDefault(tth_lib, "stems", {})
			self.codeppm	= self.getOrPutDefault(tth_lib, "codeppm", 48)
			self.alignppm	= self.getOrPutDefault(tth_lib, "alignppm", 48)
			self.stemsnap	= self.getOrPutDefault(tth_lib, "stemsnap", 17)
			self.stems = self.getOrPutDefault(tth_lib, "stems", {})
		except:
			print "ERROR: can't set font's control values"
			pass


	def invertedDictionary(self, dico):
		return dict([(v,k) for (k,v) in dico.iteritems()])

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

	def setFont(self, font):
		self.f = font

	def setGlyph(self, glyph):
		self.g = glyph

	def setUPM(self, UPM):
		self.UPM = int(UPM)

	def setSize(self, size):
		self.PPM_Size = int(size)

	def resetFontUPM(self, font):
		if font != None:
			self.UPM = font.info.unitsPerEm
			return self.UPM
		return None

	def resetPitch(self):
		self.resetFontUPM(self.f)
		self.pitch = self.UPM/self.PPM_Size

	def setAxis(self, axis):
		if axis in ['X', 'Y']:
			self.selectedAxis = axis

	def setBitmapPreview(self, preview):
		if preview in ['Monochrome', 'Grayscale', 'Subpixel']:
			self.bitmapPreviewSelection = preview

	def setHintingTool(self, hintingTool):
		if hintingTool in ['Align', 'Single Link', 'Double Link', 'Interpolation', 'Middle Delta', 'Final Delta']:
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


	def showPreviewWindow(self, ShowHide):
		if ShowHide == 0:
			self.previewWindowVisible = 0
		elif ShowHide == 1:
			self.previewWindowVisible = 1

	def setPreviewString(self, previewString):
		self.previewString = previewString

	def setAlwaysRefresh(self, valueBool):
		if valueBool in (0, 1):
			self.alwaysRefresh = valueBool

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
		c_zoneDict['Position'] = zone['position']
		c_zoneDict['Width'] = zone['width']
		deltaString = ''
		if 'delta' in zone:
			count = 0
			for ppEmSize in zone['delta']:
				delta= str(zone['delta'][str(ppEmSize)]) + '@' + str(ppEmSize)
				deltaString += delta
				if count > 0:
					deltaString += ','
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
		c_stemDict['Width'] = stem['width']
		invDico = self.invertedDictionary(stem['round'])
		for i in range(1,7):
			c_stemDict[str(i)+' px'] = self.getOrDefault(invDico, i, '0')
		return c_stemDict

	def buildStemsUIList(self, horizontal=True):
		return [self.buildStemUIDict(stem, name) for name, stem in self.stems.iteritems() if stem['horizontal'] == horizontal]

