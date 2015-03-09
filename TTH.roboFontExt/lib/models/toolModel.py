from mojo.extensions import *

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
		self.deltaMonoBool = 1
		self.deltaGrayBool = 1

		self.toolsWindowPosSize = (170, 30, 265, 95)
		self.previewString = '/?'
		self.previewFrom = getExtensionDefault(defaultKeyPreviewFrom, fallback=9)
		self.previewTo = getExtensionDefault(defaultKeyPreviewTo, fallback=72)
		self.alwaysRefresh = getExtensionDefault(defaultKeyAlwaysRefresh, fallback=1)
		self.showOutline = getExtensionDefault(defaultKeyShowOutline, fallback=0)
		self.showBitmap = getExtensionDefault(defaultKeyShowBitmap, fallback=0)
		self.showGrid = getExtensionDefault(defaultKeyShowGrid, fallback=0)
		self.showCenterPixel = getExtensionDefault(defaultKeyShowCenterPixels, fallback=0)
		self.showPreviewInGlyphWindow = getExtensionDefault(defaultKeyShowPreviewInGlyphWindow, fallback=1)

		self.requiredGlyphsForPartialTempFont = set()
		self.requiredGlyphsForPartialTempFont.add('space')

		self.roundFactor_Stems = 15
		self.roundFactor_Jumps = 20

		self.minStemX = 20
		self.minStemY = 20
		self.maxStemX = 1000
		self.maxStemY = 1000

		self.angleTolerance = 10.0

	def setSize(self, size):
		self.PPM_Size = int(size)
		setExtensionDefault(defaultKeyCurrentPPMSize, self.PPM_Size)

	def resetPitch(self, UPM):
		self.pitch = UPM/self.PPM_Size
		self.fPitch = float(UPM)/self.PPM_Size

	def setDeltaRange1(self, value):
		self.deltaRange1 = int(value)

	def setDeltaRange2(self, value):
		self.deltaRange2 = int(value)

	def setPreviewString(self, previewString):
		self.previewString = previewString