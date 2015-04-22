from lib.UI.spaceCenter.glyphSequenceEditText import splitText
from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.roboFont import CurrentFont, RFont
from mojo.UI import UpdateCurrentGlyphView

from models import TTHFont
from views import previewPanel

import string

reload(TTHFont)
reload(previewPanel)

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

		self.eventController = None
		self._previewPanel  = None

	def __del__(self):
		pass

	@property
	def previewPanel(self):
		if self._previewPanel == None:
			self._previewPanel  = previewPanel.PreviewPanel()
		return self._previewPanel

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
			return None
		return self.fontModelForFont(g.getParent())

	def delFontModelForGlyph(self, g):
		if g != None:
			return self.delFontModelForFont(g.getParent())

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

	def setPreviewString(self, previewString):
		if previewString != None:
			self.previewString = previewString
		else:
			self.previewString = '/?'
		self.previewPanel.window.previewEditText.set(self.previewString)

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

	def samplesStringsHaveChanged(self, sampleStrings):
		currentString = self.previewPanel.window.previewEditText.get()
		self.previewSampleStringsList = sampleStrings
		setExtensionDefault(defaultKeyPreviewSampleStrings, self.previewSampleStringsList)
		self.previewPanel.window.previewEditText.setItems(self.previewSampleStringsList)
		self.setPreviewString(currentString)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - FONT GENERATION

	def generatePartialTempFont(self):
		#try:
			fontModel = self.fontModelForFont(CurrentFont())
			tempFont = RFont(showUI=False)
			info = fontModel.f.info
			tempFont.info.unitsPerEm = info.unitsPerEm
			tempFont.info.ascender   = info.ascender
			tempFont.info.descender  = info.descender
			tempFont.info.xHeight    = info.xHeight
			tempFont.info.capHeight  = info.capHeight
			tempFont.info.familyName = info.familyName
			tempFont.info.styleName  = info.styleName
			tempFont.glyphOrder = fontModel.f.glyphOrder
			lib = fontModel.f.lib
			for key in ['com.robofont.robohint.cvt ',
					'com.robofont.robohint.prep',
					'com.robofont.robohint.fpgm',
					'com.robofont.robohint.gasp',
					'com.robofont.robohint.hdmx',
					'com.robofont.robohint.maxp.maxStorage']:
				if key in lib:
					tempFont.lib[key] = lib[key]
			for name in self.requiredGlyphsForPartialTempFont:
				oldG = fontModel.f[name]
				tempFont[name] = oldG
				newG = tempFont[name]
				newG.unicode = oldG.unicode # FIXME: why?
				key = 'com.robofont.robohint.assembly'
				if key in oldG.lib:
					newG.lib[key] = oldG.lib[key]
			tempFont.generate(fontModel.partialtempfontpath, 'ttf', decompose = False, checkOutlines = False, autohint = False, releaseMode = False, glyphOrder=None, progressBar = None )
		#except:
		#	print 'ERROR: Unable to generate temporary font'

	def updatePartialFont(self):
		"""Typically called directly when the current glyph has been modifed."""
		self.generatePartialTempFont()
		fontModel = self.fontModelForFont(CurrentFont())
		fontModel.regenTextRenderer()

	def updatePartialFontIfNeeded(self):
		"""Re-create the partial font if new glyphs are required."""
		(text, curGlyphString) = self.prepareText()
		curSet = self.requiredGlyphsForPartialTempFont
		newSet = self.defineGlyphsForPartialTempFont(text, curGlyphString)
		regenerate = not newSet.issubset(curSet)
		n = len(curSet)
		if (n > 128) and (len(newSet) < n):
			regenerate = True
		if regenerate:
			self.requiredGlyphsForPartialTempFont = newSet
			self.updatePartialFont()

	def prepareText(self):
		g, fm = self.getGAndFontModel()
		if g == None:
			curGlyphName = ''
		else:
			curGlyphName = g.name

		texts = self.previewString.split('/?')
		udata = fm.f.naked().unicodeData
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

	def defineGlyphsForPartialTempFont(self, text, curGlyphName):
		font = CurrentFont()
		def addGlyph(s, name):
			try:
				s.add(name)
				for component in font[name].components:
					s.add(component.baseGlyph)
			except:
				pass
		glyphSet = set()
		addGlyph(glyphSet, 'space')
		#for i in string.lowercase:
		#	addGlyph(glyphSet, i)
		#for i in string.uppercase:
		#	addGlyph(glyphSet, i)
		#for i in ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'zero']:
		#	addGlyph(glyphSet, i)
		addGlyph(glyphSet, curGlyphName)
		for name in text:
			addGlyph(glyphSet, name)
		return glyphSet

# THE UNIQUE INSTANCE
uniqueInstance = TTHTool()
TTHFont.tthTool      = uniqueInstance
previewPanel.tthTool = uniqueInstance
