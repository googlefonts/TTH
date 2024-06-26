from mojo.extensions import getExtensionDefault, setExtensionDefault
from lib.UI.spaceCenter.glyphSequenceEditText import splitText
from mojo.UI import UpdateCurrentGlyphView
from mojo.roboFont import CurrentFont, CurrentGlyph, AllFonts
from mojo.events import getActiveEventTool

import string
from datetime import datetime
from commons import helperFunctions

# IMPORTANT: All the modules that use the unique instance of TTHTool and are
# used in this file should be imported at the bottom of this file.

DefaultKeyStub = "com.sansplomb.TTH."

defaultKeyLastTool                 = DefaultKeyStub + "lastTool"
defaultKeyCurrentPPMSize           = DefaultKeyStub + "currentPPMSize"
defaultKeySelectedAxis             = DefaultKeyStub + "selectedAxis"
defaultKeyPreviewSampleStrings     = DefaultKeyStub + "previewSampleStrings"
defaultKeyPreviewFrom              = DefaultKeyStub + "previewFrom"
defaultKeyPreviewTo                = DefaultKeyStub + "previewTo"
defaultKeyAlwaysRefresh            = DefaultKeyStub + "alwaysRefresh"
defaultKeyShowOutline              = DefaultKeyStub + "showOutline"
defaultKeyOutlineThickness         = DefaultKeyStub + "outlineThickness"
defaultKeyShowBitmap               = DefaultKeyStub + "showBitmap"
defaultKeyBitmapOpacity            = DefaultKeyStub + "bitmapOpacity"
defaultKeyShowGrid                 = DefaultKeyStub + "showGrid"
defaultKeyGridOpacity              = DefaultKeyStub + "gridOpacity"
defaultKeyShowCenterPixels         = DefaultKeyStub + "showCenterPixels"
defaultKeyCenterPixelSize          = DefaultKeyStub + "centerPixelSize"
defaultKeyShowPreviewInGlyphWindow = DefaultKeyStub + "showPreviewInGlyphWindow"
defaultKeyCurrentPointSize         = DefaultKeyStub + "currentPointSize"

class TTHTool(object):
	def __init__(self):

		# For debugging the (re)loading order of the modules
		self._printLoadings = True

		print "\n *** NEW TTHTool model created ",
		print datetime.today()

		# The current Point/Pixel Per Em size for displaying the hinted preview
		self.PPM_Size = getExtensionDefault(defaultKeyCurrentPPMSize, fallback=9)
		# The current hinting axis: 'X' or 'Y'
		self.selectedAxis = getExtensionDefault(defaultKeySelectedAxis, fallback='X')

		self.hintingTools = {}
		# The CURRENT hinting tool
		self.selectedHintingTool = None

		self.previewString = '/?'

		self.parametricPreviewSize = getExtensionDefault(defaultKeyCurrentPointSize, fallback=30)

		self.previewSampleStringsList = getExtensionDefault(defaultKeyPreviewSampleStrings,\
				fallback=['/?', 'HH/?HH/?OO/?OO/?', 'nn/?nn/?oo/?oo/?', '0123456789',\
						string.uppercase, string.lowercase])
		self.previewFrom      = getExtensionDefault(defaultKeyPreviewFrom,      fallback=9)
		self.previewTo        = getExtensionDefault(defaultKeyPreviewTo,        fallback=72)
		self.alwaysRefresh    = getExtensionDefault(defaultKeyAlwaysRefresh,    fallback=1)
		self.showOutline      = getExtensionDefault(defaultKeyShowOutline,      fallback=0)
		self.outlineThickness = getExtensionDefault(defaultKeyOutlineThickness, fallback=2)
		self.showBitmap       = getExtensionDefault(defaultKeyShowBitmap,       fallback=0)
		self.bitmapOpacity    = getExtensionDefault(defaultKeyBitmapOpacity,    fallback=0.4)
		self.showGrid         = getExtensionDefault(defaultKeyShowGrid,         fallback=0)
		self.gridOpacity      = getExtensionDefault(defaultKeyGridOpacity,      fallback=0.4)
		self.showCenterPixel  = getExtensionDefault(defaultKeyShowCenterPixels, fallback=0)
		self.centerPixelSize  = getExtensionDefault(defaultKeyCenterPixelSize,  fallback=3)
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

		# TTHFont instances for each opened font
		self._fontModels = {}

		# Other windows of the TTH extension
		self.mainPanel      = None
		self.previewPanel   = None
		self.parametricPreviewPanel   = None
		self.assemblyWindow = None
		self.programWindow  = None
		self.TTHWindows     = []

		# Tool activation
		self.isActive = False

	def __del__(self):
		pass

# - - - - - - - - - - - - - - - - - - - - - FONT MODELS

	def getRGAndFontModel(self):
		g = None
		eventController = getActiveEventTool()
		if eventController:
			g = eventController.getGlyph()
		if g is None:
			g = CurrentGlyph()
		fm = self.fontModelForGlyph(g)
		if fm == None:
			fm = self.fontModelForFont(CurrentFont())
		if g is None:
			g = fm.f[fm.f.selection[0]]
		return g, fm

	def getGlyphAndFontModel(self):
		g, fm = self.getRGAndFontModel()
		if fm:
			gm = fm.glyphModelForGlyph(g)
			return (gm, fm)
		return (None, None)

	def getGlyphModel(self):
		gm, fm = self.getGlyphAndFontModel()
		return gm

	def getFontModel(self):
		g, fm = self.getRGAndFontModel()
		return fm

	def fontModelForFont(self, font):
		# if not helperFunctions.fontIsQuadratic(font):
		# 	return None
		key = font.fileName
		if key not in self._fontModels:
			model = TTHFont.TTHFont(font)
			self._fontModels[key] = model
			return model
		return self._fontModels[key]

	def delFontModelForFont(self, font):
		if font is None: return
		key = font.fileName
		if key in self._fontModels:
			model = self._fontModels[key]
			del self._fontModels[key]

	def fontModelForGlyph(self, g):
		if g is None:
			return None
		f = g.getParent()
		if f is None:
			return None
		#print "Glyph",g.name,"from font",f.fileName
		return self.fontModelForFont(f)

	def delFontModelForGlyph(self, g):
		if g != None:
			return self.delFontModelForFont(g.getParent())

# - - - - - - - - - - - - - - - - - - - - - DISPLAY UPDATE

	def updateDisplay(self):
		if self.programWindow and self.programWindow.isVisible():
			self.programWindow.updateProgramList()
		if self.assemblyWindow and self.assemblyWindow.isVisible():
			self.assemblyWindow.updateAssemblyList()
		if self.previewPanel and self.previewPanel.isVisible():
			self.previewPanel.setNeedsDisplay()
		UpdateCurrentGlyphView()

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
		if self.mainPanel.curSheet:
			self.mainPanel.curSheet.resetUI()

	def changeSize(self, size):
		#print "Change size"
		try:
			size = int(size)
		except ValueError:
			size = 9
		if self.PPM_Size == size: return
		self.PPM_Size = size
		setExtensionDefault(defaultKeyCurrentPPMSize, size)
		eventController = getActiveEventTool()
		if eventController != None:
			eventController.sizeHasChanged()
		self.mainPanel.displayPPEMSize(size)
		for tool in ['Middle Delta', 'Final Delta']:
			self.getTool(tool).setRange(self.PPM_Size, self.PPM_Size)
		self.selectedHintingTool.updateUI()
		self.previewPanel.setNeedsDisplay()
		UpdateCurrentGlyphView()

# - - - - - - - - - - - - - - - - - - - - - - - PARAMETRIC PREVIEW POINT SIZE

	def changePointSize(self, size):
		try:
			size = int(size)
		except ValueError:
			size = 30
		if self.parametricPreviewSize == size: return
		self.parametricPreviewSize = size
		setExtensionDefault(defaultKeyCurrentPointSize, size)


# - - - - - - - - - - - - - - - - - - - - - - - WORKING AXIS

	def changeAxis(self, axis):
		self.selectedAxis = axis
		setExtensionDefault(defaultKeySelectedAxis, axis)
		if self.selectedHintingTool != None:
			self.selectedHintingTool.updateUI()
		if axis == 'X':
			self.mainPanel.wTools.axisSegmentedButton.set(0)
		else:
			self.mainPanel.wTools.axisSegmentedButton.set(1)

# - - - - - - - - - - - - - - - - - - - - - - - DELTA

	def changeDeltaOffset(self, toolName, value):
		self.getTool(toolName).setOffset(value)

# - - - - - - - - - - - - - - - - - - - - - - - TOOL

	def getTool(self, toolName):
		if toolName not in self.hintingTools:
			self.hintingTools[toolName] = tools.createTool(toolName)
		return self.hintingTools[toolName]

	def setTool(self, toolName):
		self.selectedHintingTool = self.getTool(toolName)
		setExtensionDefault(defaultKeyLastTool, toolName)
		toolIndex = tools.kCommandToolNames.index(toolName)
		if self.mainPanel != None:
			self.mainPanel.wTools.toolsSegmentedButton.set(toolIndex)
		self.selectedHintingTool.updateUI()

	def changeSelectedHintingTool(self, toolIndex):
		self.setTool(tools.kCommandToolNames[toolIndex])

# - - - - - - - - - - - - - - - - - - - - - - - PREVIEW STRING

	def setPreviewString(self, previewString):
		if previewString != None:
			self.previewString = previewString
		else:
			self.previewString = '/?'
		self.previewPanel.window.previewEditText.set(self.previewString)
		self.parametricPreviewPanel.window.previewEditText.set(self.previewString)

	def samplesStringsHaveChanged(self, sampleStrings):
		currentString = self.previewPanel.window.previewEditText.get()
		self.previewSampleStringsList = sampleStrings
		setExtensionDefault(defaultKeyPreviewSampleStrings, self.previewSampleStringsList)
		self.previewPanel.window.previewEditText.setItems(self.previewSampleStringsList)
		self.setPreviewString(currentString)

# - - - - - - - - - - - - - - - - - - - - PREVIEW PANEL & IN GLYPH-WINDOW

	def setPreviewInGlyphWindowState(self, onOff):
		self.showPreviewInGlyphWindow = onOff
		setExtensionDefault(defaultKeyShowPreviewInGlyphWindow, onOff)
		for fm in self._fontModels.itervalues():
			fm.setPreviewInGlyphWindowVisibility(onOff)
		UpdateCurrentGlyphView()
		if self.mainPanel.curSheet:
			self.mainPanel.curSheet.resetUI()

	def setAlwaysRefreshState(self, onOff):
		self.alwaysRefresh = onOff
		setExtensionDefault(defaultKeyAlwaysRefresh, onOff)

# - - - - - - - - - - - - - - - - - - - ACTIVE / INACTIVE

	def hideWindows(self):
		for w in self.TTHWindows:
			w.hide()
		if self.mainPanel is not None:
			self.mainPanel.hide()

	def showWindows(self):
		for w in self.TTHWindows:
			w.showOrHide()
		if self.mainPanel is not None:
			self.mainPanel.show()

	def showOrHide(self):
		fm = self.getFontModel()
		if fm is None:
			self.hideWindows()
		else:
			self.showWindows()

	def createWindows(self):
		self.previewPanel   = previewPanel.PreviewPanel()
		self.programWindow  = ProgramWindow.ProgramWindow()
		self.assemblyWindow = AssemblyWindow.AssemblyWindow()
		self.parametricPreviewPanel   = parametricPreviewPanel.parametricPreview()
		self.TTHWindows     = [self.previewPanel, self.assemblyWindow, self.programWindow, self.parametricPreviewPanel]
		self.mainPanel      = mainPanel.MainPanel()

		lastToolUsed = getExtensionDefault(defaultKeyLastTool, fallback='Selection')
		self.setTool(lastToolUsed)

	def deleteWindows(self):
		self.hideWindows()
		self.TTHWindows = []

		if self.mainPanel:
			self.mainPanel.close()
			self.mainPanel    = None

		del self.previewPanel
		self.previewPanel = None
		del self.parametricPreviewPanel
		self.parametricPreviewPanel = None
		del self.assemblyWindow
		self.assemblyWindow = None
		del self.programWindow
		self.programWindow = None

	def becomeActive(self):
		self.isActive = True
		for f in AllFonts():
			fm = self.fontModelForFont(f)
		self.updatePartialFontIfNeeded()
		for fm in self._fontModels.itervalues():
			fm.setPreviewInGlyphWindowVisibility(self.showPreviewInGlyphWindow)
		# Create the various windows and panels
		self.createWindows()
		self.showOrHide()
		#UpdateCurrentGlyphView()

	def becomeInactive(self):
		self.isActive = False
		for fm in self._fontModels.itervalues():
			fm.killPreviewInGlyphWindow()
		for f in AllFonts():
			self.delFontModelForFont(f)
		# Kill the various windows and panels
		self.deleteWindows()

# - - - - - - - - - - - - - - - - - - - GLYPH WINDOW DRAWING OPTIONS

	def setShowBitmap(self, onOff):
		self.showBitmap = onOff
		setExtensionDefault(defaultKeyShowBitmap, onOff)
		if self.mainPanel.curSheet:
			self.mainPanel.curSheet.resetUI()

	def setBitmapOpacity(self, value):
		self.bitmapOpacity = value
		setExtensionDefault(defaultKeyBitmapOpacity, value)
		if self.mainPanel.curSheet:
			self.mainPanel.curSheet.resetUI()

	def setShowOutline(self, onOff):
		self.showOutline = onOff
		setExtensionDefault(defaultKeyShowOutline, onOff)
		if self.mainPanel.curSheet:
			self.mainPanel.curSheet.resetUI()

	def setOutlineThickness(self, value):
		self.outlineThickness = value
		setExtensionDefault(defaultKeyOutlineThickness, value)
		if self.mainPanel.curSheet:
			self.mainPanel.curSheet.resetUI()

	def setShowGrid(self, onOff):
		self.showGrid = onOff
		setExtensionDefault(defaultKeyShowGrid, onOff)
		if self.mainPanel.curSheet:
			self.mainPanel.curSheet.resetUI()

	def setGridOpacity(self, value):
		self.gridOpacity = value
		setExtensionDefault(defaultKeyGridOpacity, value)
		if self.mainPanel.curSheet:
			self.mainPanel.curSheet.resetUI()

	def setShowCenterPixels(self, onOff):
		self.showCenterPixel = onOff
		setExtensionDefault(defaultKeyShowCenterPixels, onOff)
		if self.mainPanel.curSheet:
			self.mainPanel.curSheet.resetUI()

	def setCenterPixelSize(self, value):
		self.centerPixelSize = value
		setExtensionDefault(defaultKeyCenterPixelSize, value)
		if self.mainPanel.curSheet:
			self.mainPanel.curSheet.resetUI()

# - - - - - - - - - - - - - - - - - - - - - - - -

	def hintingProgramHasChanged(self, fm):
		if not self.isActive: return
		fm.updatePartialFont(self.requiredGlyphsForPartialTempFont)
		self.updateDisplay()

	def currentFontHasChanged(self, font):
		fm = self.fontModelForFont(font)
		if fm is None: return
		fm.updatePartialFont(self.requiredGlyphsForPartialTempFont)
		if self.mainPanel.curSheet != None:
			self.mainPanel.curSheet.close()
			self.mainPanel.curSheet = None

	def updatePartialFontIfNeeded(self):
		gm, fm = self.getGlyphAndFontModel()
		if fm is None or not helperFunctions.fontIsQuadratic(fm.f): return
		self.requiredGlyphsForPartialTempFont =\
			fm.updatePartialFontIfNeeded(gm.RFGlyph, self.requiredGlyphsForPartialTempFont)

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

# - - - - - - - - - - - - - - - - - - - - - - - -

# THE UNIQUE INSTANCE
uniqueInstance = TTHTool()

# - - - - - - - - - - - - - - - - - - - - - - - -

if uniqueInstance._printLoadings: print "TTHTool, ",

from models import TTHFont
from views import parametricPreviewPanel, previewPanel, mainPanel, AssemblyWindow, ProgramWindow
import tools
reload(TTHFont)
reload(AssemblyWindow)
reload(ProgramWindow)
reload(parametricPreviewPanel)
reload(previewPanel)
reload(mainPanel)
reload(tools)
