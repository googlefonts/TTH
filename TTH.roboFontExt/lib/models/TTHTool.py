from mojo.extensions import *

from models import TTHFont

import string

reload(TTHFont)

DefaultKeyStub = "com.sansplomb.TTH."

defaultKeyCurrentPPMSize			= DefaultKeyStub + "currentPPMSize"
defaultKeySelectedAxis			= DefaultKeyStub + "selectedAxis"
defaultKeyPreviewSampleStrings	= DefaultKeyStub + "previewSampleStrings"
defaultKeyPreviewFrom			= DefaultKeyStub + "previewFrom"
defaultKeyPreviewTo				= DefaultKeyStub + "previewTo"
defaultKeyAlwaysRefresh			= DefaultKeyStub + "alwaysRefresh"
defaultKeyShowOutline			= DefaultKeyStub + "showOutline"
defaultKeyOutlineThickness		= DefaultKeyStub + "outlineThickness"
defaultKeyShowBitmap			= DefaultKeyStub + "showBitmap"
defaultKeyBitmapOpacity			= DefaultKeyStub + "bitmapOpacity"
defaultKeyShowGrid				= DefaultKeyStub + "showGrid"
defaultKeyGridOpacity			= DefaultKeyStub + "gridOpacity"
defaultKeyShowCenterPixels		= DefaultKeyStub + "showCenterPixels"
defaultKeyCenterPixelSize		= DefaultKeyStub + "centerPixelSize"
defaultKeyShowPreviewInGlyphWindow	= DefaultKeyStub + "showPreviewInGlyphWindow"

class TTHTool():
	def __init__(self):

		# The current Point/Pixel Per Em size for displaying the hinted preview
		self.PPM_Size = getExtensionDefault(defaultKeyCurrentPPMSize, fallback=9)
		# The current hinting axis: 'X' or 'Y'
		self.selectedAxis = getExtensionDefault(defaultKeySelectedAxis, fallback='X')

		# The CURRENT hinting tool
		self.selectedHintingTool = 'Align'
		# A parameter for the hinting tool
		self.selectedAlignmentTypeAlign = 'round'
		# A parameter for the hinting tool
		self.selectedAlignmentTypeLink = 'None'
		# A parameter for the hinting tool
		self.selectedStemX = 'Guess'
		# A parameter for the hinting tool
		self.selectedStemY = 'Guess'
		self.roundBool = 0
		self.deltaOffset = 0
		self.deltaRange1 = 9
		self.deltaRange2 = 9
		self.deltaMonoBool = 1
		self.deltaGrayBool = 1
		
		self.previewString = '/?'

		self.previewSampleStringsList = getExtensionDefault(defaultKeyPreviewSampleStrings, fallback=['/?', 'HH/?HH/?OO/?OO/?', 'nn/?nn/?oo/?oo/?', '0123456789', string.uppercase, string.lowercase])
		self.previewFrom		= getExtensionDefault(defaultKeyPreviewFrom,		fallback=9)
		self.previewTo		= getExtensionDefault(defaultKeyPreviewTo,		fallback=72)
		self.alwaysRefresh	= getExtensionDefault(defaultKeyAlwaysRefresh,		fallback=1)
		self.showOutline		= getExtensionDefault(defaultKeyShowOutline,		fallback=0)
		self.outlineThickness	= getExtensionDefault(defaultKeyOutlineThickness,	fallback=2)
		self.showBitmap		= getExtensionDefault(defaultKeyShowBitmap,		fallback=0)
		self.bitmapOpacity	= getExtensionDefault(defaultKeyBitmapOpacity,		fallback=0.4)
		self.showGrid		= getExtensionDefault(defaultKeyShowGrid,			fallback=0)
		self.gridOpacity		= getExtensionDefault(defaultKeyGridOpacity,		fallback=0.4)
		self.showCenterPixel	= getExtensionDefault(defaultKeyShowCenterPixels,	fallback=0)
		self.centerPixelSize	= getExtensionDefault(defaultKeyCenterPixelSize,	fallback=3)
		self.showPreviewInGlyphWindow = getExtensionDefault(defaultKeyShowPreviewInGlyphWindow, fallback=1)

		self.requiredGlyphsForPartialTempFont = set(['space'])

		# Stems are rounded to a multiple of that value
		# FIXME: Check if this is still used? If so, check if we can get rid of it?
		self.roundFactor_Stems = 15
		# FIXME: Describe this
		# FIXME: Check if this is still used? If so, check if we can get rid of it?
		self.roundFactor_Stems = 15
		self.roundFactor_Jumps = 20

		# The min and max size of a stem (as the vector between a pair of control points)
		# FIXME: Maybe this should go in the FontModel ? (but should stay here if this is not stored anywhere in the UFO)
		self.minStemX = 20
		self.minStemY = 20
		self.maxStemX = 1000
		self.maxStemY = 1000

		# Angle tolerance for 'parallel' lines/vectors
		self.angleTolerance = 10.0

		# TTHFont instances for each opened font
		self._fontModels = {}

	def __del__(self):
		pass

	def fontModelForFont(self, font):
		key = font.fileName
		if key not in self._fontModels:
			model = TTHFont.TTHFont(font)
			self._fontModels[key] = model
			return model
		return self._fontModels[key]

	def delFontModelForFont(self, font):
		key = font.fileName
		if key in self._fontModels:
			model = self._fontModels[key]
			del model
			del self._fontModels[key]

	def fontModelForGlyph(self, g):
		if g is None:
			return None
		return self.fontModelForFont(g.getParent())

	def delFontModelForGlyph(self, g):
		if g != None:
			return self.delFontModelForFont(g.getParent())

	def setSize(self, size):
		s = int(size+0.5)
		self._PPM_Size = s
		setExtensionDefault(defaultKeyCurrentPPMSize, s)

	def setDeltaRange1(self, value):
		self.deltaRange1 = int(value)

	def setDeltaRange2(self, value):
		self.deltaRange2 = int(value)

	def setPreviewString(self, previewString):
		if previewString != None:
			self.previewString = previewString
		else:
			self.previewString = '/?'

	def setPreviewInGlyphWindowState(self, onOff):
		self.showPreviewInGlyphWindow = onOff
		setExtensionDefault(defaultKeyShowPreviewInGlyphWindow, onOff)

	def setShowBitmap(self, onOff):
		self.showBitmap = onOff
		setExtensionDefault(defaultKeyShowBitmap, onOff)

	def setBitmapOpacity(self, value):
		self.bitmapOpacity = value
		setExtensionDefault(defaultKeyBitmapOpacity, value)

	def setShowOutline(self, onOff):
		self.showOutline = onOff
		setExtensionDefault(defaultKeyShowOutline, onOff)

	def setOutlineThickness(self, value):
		self.outlineThickness = value
		setExtensionDefault(defaultKeyOutlineThickness, value)

	def setShowGrid(self, onOff):
		self.showGrid = onOff
		setExtensionDefault(defaultKeyShowGrid, onOff)

	def setGridOpacity(self, value):
		self.gridOpacity = value
		setExtensionDefault(defaultKeyGridOpacity, value)

	def setShowCenterPixels(self, onOff):
		self.showCenterPixel = onOff
		setExtensionDefault(defaultKeyShowCenterPixels, onOff)

	def setCenterPixelSize(self, value):
		self.centerPixelSize = value
		setExtensionDefault(defaultKeyCenterPixelSize, value)

# THE UNIQUE INSTANCE
uniqueInstance = TTHTool()
