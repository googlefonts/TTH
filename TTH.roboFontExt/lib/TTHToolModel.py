from robofab.world import *
from mojo.extensions import *

import tempfile
import TextRenderer as TR

defaultKeyStub = "com.sansplomb.TTH."
defaultKeyPreviewWindowVisibility = defaultKeyStub + "previewWindowVisibility"
defaultKeyProgramWindowVisibility = defaultKeyStub + "programWindowVisibility"
defaultKeyAssemblyWindowVisibility = defaultKeyStub + "assemblyWindowVisibility"

defaultKeyCurrentPPMSize = defaultKeyStub + "currentPPMSize"
defaultKeySelectedAxis = defaultKeyStub + "selectedAxis"
defaultKeyPreviewFrom = defaultKeyStub + "previewFrom"
defaultKeyPreviewTo = defaultKeyStub + "previewTo"

# ======================================================================

FL_tth_key = "com.fontlab.v2.tth"

# ======================================================================

class fontModel():
	def __init__(self, font):
		self.f = font
		self.UPM = font.info.unitsPerEm

		self.bitmapPreviewSelection = 'Monochrome'

		tth_lib = self.getOrPutDefault(self.f.lib, FL_tth_key, {})
		self.zones = self.getOrPutDefault(tth_lib, "zones", {})
		self.stems = self.getOrPutDefault(tth_lib, "stems", {})
		self.codeppm	= self.getOrPutDefault(tth_lib, "codeppm", 72)
		self.alignppm	= self.getOrPutDefault(tth_lib, "alignppm", 64)
		self.stemsnap	= self.getOrPutDefault(tth_lib, "stemsnap", 17)
		self.stems = self.getOrPutDefault(tth_lib, "stems", {})

		self.textRenderer = None

		temp = tempfile.NamedTemporaryFile(suffix='.ttf', delete=False)
		self.partialtempfontpath = temp.name
		#print "Temporary file is", self.partialtempfontpath
		temp.close()
		self.doneGeneratingPartialFont = False

	def setFont(self, font):
		self.f = font

	def setUPM(self, UPM):
		self.UPM = int(UPM)

	def resetFontUPM(self, font):
		if font != None:
			self.UPM = font.info.unitsPerEm
			return self.UPM
		return None

	def setBitmapPreview(self, preview):
		if preview in ['Monochrome', 'Grayscale', 'Subpixel']:
			self.bitmapPreviewSelection = preview

	def setControlValues(self):
		try:
			tth_lib = self.getOrPutDefault(self.f.lib, FL_tth_key, {})
			self.zones = self.getOrPutDefault(tth_lib, "zones", {})
			self.stems = self.getOrPutDefault(tth_lib, "stems", {})
			self.codeppm	= self.getOrPutDefault(tth_lib, "codeppm", 72)
			self.alignppm	= self.getOrPutDefault(tth_lib, "alignppm", 64)
			self.stemsnap	= self.getOrPutDefault(tth_lib, "stemsnap", 17)
			self.stems = self.getOrPutDefault(tth_lib, "stems", {})
		except:
			print "ERROR: can't set font's control values"

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
		c_zoneDict['Position'] = zone['position']
		c_zoneDict['Width'] = zone['width']
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
		c_stemDict['Width'] = stem['width']
		invDico = self.invertedDictionary(stem['round'])
		for i in range(1,7):
			c_stemDict[str(i)+' px'] = self.getOrDefault(invDico, i, '0')
		return c_stemDict

	def buildStemsUIList(self, horizontal=True):
		return [self.buildStemUIDict(stem, name) for name, stem in self.stems.iteritems() if stem['horizontal'] == horizontal]


class TTHToolModel():
	def __init__(self):

		self.PPM_Size = getExtensionDefault(defaultKeyCurrentPPMSize, fallback=9)
		self.pitch = 1000/self.PPM_Size
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

		self.previewWindowOpened = 0
		self.previewWindowVisible = getExtensionDefault(defaultKeyPreviewWindowVisibility, fallback=0)

		self.programWindowOpened = 0
		self.programWindowVisible = getExtensionDefault(defaultKeyProgramWindowVisibility, fallback=0)

		self.assemblyWindowOpened = 0
		self.assemblyWindowVisible = getExtensionDefault(defaultKeyAssemblyWindowVisibility, fallback=0)


		self.previewWindowPosSize = (-510, 30, 500, 600)
		#self.previewWindowViewSize = (self.previewWindowPosSize[2]-35, self.previewWindowPosSize[3]-105)
		self.previewWindowViewSize = (465, 495)
		self.toolsWindowPosSize = (170, 30, 265, 95)
		self.centralWindowPosSize = (10, 30, 150, 135)
		self.programWindowPosSize = (10, -300, -10, 300)
		self.assemblyWindowPosSize = (10, 150, 150, -400)
		self.previewString = 'HH/?HH'
		self.previewFrom = getExtensionDefault(defaultKeyPreviewFrom, fallback=9)
		self.previewTo = getExtensionDefault(defaultKeyPreviewTo, fallback=72)
		self.requiredGlyphsForPartialTempFont = set()
		self.requiredGlyphsForPartialTempFont.add('space')
		self.alwaysRefresh = 1
		self.showOutline = 0
		self.showBitmap = 0
		self.showGrid = 0
		self.showCenterPixel = 0
		self.showPreviewInGlyphWindow = 1

		self.roundFactor_Stems = 40
		self.roundFactor_Jumps = 20

		self.minStemX = 20
		self.minStemY = 20
		self.maxStemX = 1000
		self.maxStemY = 1000

		self.angleTolerance = 10.0

	def setPreviewWindowVisible(self, valueBool):
		self.previewWindowVisible = 1
		setExtensionDefault(defaultKeyPreviewWindowVisibility, self.previewWindowVisible)

	def setProgramWindowVisible(self, valueBool):
		self.programWindowVisible = 1
		setExtensionDefault(defaultKeyProgramWindowVisibility, self.programWindowVisible)

	def setAssemblyWindowVisible(self, valueBool):
		self.assemblyWindowVisible = 1
		setExtensionDefault(defaultKeyAssemblyWindowVisibility, self.assemblyWindowVisible)

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

	def setAxis(self, axis):
		if axis in ['X', 'Y']:
			self.selectedAxis = axis
			setExtensionDefault(defaultKeySelectedAxis, axis)

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
