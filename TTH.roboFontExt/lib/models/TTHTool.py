from mojo.extensions import getExtensionDefault, setExtensionDefault
from lib.UI.spaceCenter.glyphSequenceEditText import splitText
from mojo.UI import UpdateCurrentGlyphView
from mojo.roboFont import CurrentFont

import string

# IMPORTANT: All the modules that use the unique instance of TTHTool and are
# used in this file should be imported at the bottom of this file.

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

		self.requiredGlyphsForPartialTempFont = set()

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

		#print "INITIALIZING Event Controller to None"
		self.eventController = None
		self._previewPanel  = None

	def __del__(self):
		pass

# - - - - - - - - - - - - - - - - - - - - - FONT MODELS

	def getGAndFontModel(self):
		if self.eventController != None:
			return self.eventController.getGAndFontModel()
		return (None, None)

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
			f = CurrentFont()
		else:
			f = g.getParent()
		if f is None:
			return None
		return self.fontModelForFont(f)

	def delFontModelForGlyph(self, g):
		if g != None:
			return self.delFontModelForFont(g.getParent())

# - - - - - - - - - - - - - - - - - - - - - PREVIEW and CURRENT SIZE

	def setPreviewSizeRange(self, fromS, toS, prefsSheet):
		fromS = min(200, max(fromS, 8))
		toS   = min(fromS+100, max(toS, fromS))
		self.previewFrom = fromS
		self.previewTo   = toS
		prefsSheet.w.viewAndSettingsBox.displayFromEditText.set(fromS)
		prefsSheet.w.viewAndSettingsBox.displayToEditText.set(toS)
		setExtensionDefault(defaultKeyPreviewFrom, fromS)
		setExtensionDefault(defaultKeyPreviewTo, toS)
		self.previewPanel.setNeedsDisplay()
		UpdateCurrentGlyphView()

	def setSize(self, s):
		self._PPM_Size = s
		setExtensionDefault(defaultKeyCurrentPPMSize, s)

	def changeSize(self, size):
		try:
			size = int(size)
		except ValueError:
			size = 9

		self.setSize(size)
		self.eventController.mainPanel.displayPPEMSize(size)
		self.eventController.sizeHasChanged()
		self.changeDeltaRange(self.PPM_Size, self.PPM_Size)
		self.previewPanel.setNeedsDisplay()
		UpdateCurrentGlyphView()

# - - - - - - - - - - - - - - - - - - - - - - - DELTA RANGE

	def changeDeltaRange(self, value1, value2):
		try:
			value1 = int(value1)
		except ValueError:
			value1 = 9
		try:
			value2 = int(value2)
		except ValueError:
			value2 = 9
		if value2 < value1:
			value2 = value1
		self.deltaRange1 = value1
		self.deltaRange2 = value2
		self.eventController.mainPanel.displayDeltaRange(value1, value2)

# - - - - - - - - - - - - - - - - - - - - - - - PREVIEW STRING

	def setPreviewString(self, previewString):
		if previewString != None:
			self.previewString = previewString
		else:
			self.previewString = '/?'
		self.previewPanel.window.previewEditText.set(self.previewString)

	def samplesStringsHaveChanged(self, sampleStrings):
		currentString = self.previewPanel.window.previewEditText.get()
		self.previewSampleStringsList = sampleStrings
		setExtensionDefault(defaultKeyPreviewSampleStrings, self.previewSampleStringsList)
		self.previewPanel.window.previewEditText.setItems(self.previewSampleStringsList)
		self.setPreviewString(currentString)

# - - - - - - - - - - - - - - - - - - - - PREVIEW PANEL & IN GLYPH-WINDOW

	@property
	def previewPanel(self):
		if self._previewPanel == None:
			self._previewPanel  = previewPanel.PreviewPanel()
		return self._previewPanel

	def setPreviewInGlyphWindowState(self, onOff):
		self.showPreviewInGlyphWindow = onOff
		setExtensionDefault(defaultKeyShowPreviewInGlyphWindow, onOff)
		for fm in self._fontModels.itervalues():
			fm.setPreviewInGlyphWindowVisibility(onOff)
		UpdateCurrentGlyphView()

# - - - - - - - - - - - - - - - - - - - ACTIVE / INACTIVE

	def becomeActive(self):
		self.updatePartialFontIfNeeded()
		for fm in self._fontModels.itervalues():
			fm.setPreviewInGlyphWindowVisibility(self.showPreviewInGlyphWindow)
		UpdateCurrentGlyphView()

	def becomeInactive(self):
		self.previewPanel.hide()
		for fm in self._fontModels.itervalues():
			fm.killPreviewInGlyphWindow()
		UpdateCurrentGlyphView()

# - - - - - - - - - - - - - - - - - - - GLYPH WINDOW DRAWING OPTIONS

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

# - - - - - - - - - - - - - - - - - - - - - - - -

	def updatePartialFontIfNeeded(self):
		g, fm = self.getGAndFontModel()
		self.requiredGlyphsForPartialTempFont = fm.updatePartialFontIfNeeded(g, self.requiredGlyphsForPartialTempFont)

	def prepareText(self, g, font):
		if g == None:
			curGlyphName = '.notdef'
		else:
			curGlyphName = g.name

		texts = self.previewString.split('/?')
		udata = font.naked().unicodeData
		output = []

		for text in texts:
			# replace /name pattern
			sp = text.split('/')
			nbsp = len(sp)
			output = output + splitText(sp[0], udata)
			for i in range(1,nbsp):
				sub = sp[i].split(' ', 1)
				output.append(str(sub[0]))
				if len(sub) > 1:
					output = output + splitText(sub[1], udata)
			output.append(curGlyphName)
		output = output[:-1]
		return (output, curGlyphName)


# THE UNIQUE INSTANCE
uniqueInstance = TTHTool()

from models import TTHFont
from views import previewPanel
reload(TTHFont)
reload(previewPanel)
