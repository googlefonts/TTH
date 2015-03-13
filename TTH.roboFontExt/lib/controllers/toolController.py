from mojo.extensions import *
from mojo.events import *
from mojo.UI import *
from robofab.world import *
import robofab.interface.all.dialogs as Dialogs
from lib.tools.defaults import getDefault, setDefault
from lib.UI.spaceCenter.glyphSequenceEditText import splitText
from AppKit import *

from commons import helperFunctions, textRenderer, previewInGlyphWindow
from models import fontModel
from views import mainPanel, previewPanel

reload(helperFunctions)
reload(textRenderer)
reload(fontModel)
reload(mainPanel)
reload(previewPanel)

toolbarIcon = ExtensionBundle("TTH").get("toolbarIcon")

DefaultKeyStub = "com.sansplomb.TTH."

defaultKeyPreviewSampleStrings = DefaultKeyStub + "previewSampleStrings"
defaultKeyBitmapOpacity = DefaultKeyStub + "bitmapOpacity"
defaultKeyPreviewFrom = DefaultKeyStub + "previewFrom"
defaultKeyPreviewTo = DefaultKeyStub + "previewTo"

class TTHTool(BaseEventTool):

	def __init__(self, TTHToolModel):
		BaseEventTool.__init__(self)

		self.c_fontModel = None

		self.TTHToolModel = TTHToolModel
		self.buildModelsForOpenFonts()

		self.ready = False
		self.doneGeneratingPartialFont = False
		self.drawingPreferencesChanged = False

		self.cachedPathes = {'grid':None, 'centers':None}
		self.cachedScale = None
		
		self.fontClosed = False
		self.popOverIsOpened = False
		self.messageInFront = False

		self.previewInGlyphWindow = {}

		self.previewPanel  = previewPanel.PreviewPanel(self, (-510, 30, 500, 600))

	#################################################################################
	# This function is called by RF on the parent class in order to get the tool icon
	#################################################################################
	def getToolbarIcon(self):
		return toolbarIcon

	def getToolbarTip(self):
		return "TTH"

	###############################################################
	# This function is called by RF when the tool button is pressed
	###############################################################
	def becomeActive(self):
		if helperFunctions.checkDrawingPreferences() == False:
			setDefault('drawingSegmentType', 'qcurve')
			self.drawingPreferencesChanged = True
		self.resetFont(createWindows=True)
		self.updatePartialFont()

	###################################################################
	# This function is called by RF when another tool button is pressed
	###################################################################
	def becomeInactive(self):
		self.deletePreviewInGlyphWindow()
		self.mainPanel.close()
		self.previewPanel.hide()
		if self.drawingPreferencesChanged == True:
			setDefault('drawingSegmentType', 'curve')

	###########################################################
	# This function is called by RF when the Glyph View changed
	###########################################################
	def viewDidChangeGlyph(self):
		if self.fontClosed:
			return
		self.resetglyph(self.getGlyph())
		self.updatePartialFontIfNeeded()

	##############################################################
	# This function is called by RF when the Current Glyph changed
	##############################################################
	def currentGlyphChanged(self):
		self.resetglyph(self.getGlyph())
		self.updatePartialFontIfNeeded()


	##############################################################
	# This function is called by RF before the Current Font closes
	##############################################################
	def fontWillClose(self, font):
		# We hide the pannels only if we close the last font opened
		if len(AllFonts()) > 1:
			return
		self.mainPanel.wTools.hide()
		self.previewPanel.hide()
		# self.programWindow.hide()
		# self.assemblyWindow.hide()
		self.fontClosed = True

	############################################################################
	# This function is called by RF when the Current Font is not Current anymore
	############################################################################
	def fontResignCurrent(self, font):
		if self.fontClosed:
			return
		self.deletePreviewInGlyphWindow()
		self.resetFont(createWindows=False)

	###############################################################
	# This function is called by RF when a new Font becomes Current
	###############################################################
	def fontBecameCurrent(self, font):
		self.setupCurrentModel(font)
		if self.fontClosed:
			return
		# if hasattr(self.toolsPanel, 'sheetControlValues'):
		# 	self.toolsPanel.sheetControlValues.c_fontModel = self.c_fontModel
		# 	self.toolsPanel.sheetControlValues.resetGeneralBox()
		# 	self.toolsPanel.sheetControlValues.resetStemBox()
		# 	self.toolsPanel.sheetControlValues.resetZoneBox()

		self.resetFont(createWindows=False)
		self.updatePartialFont()
		self.fontClosed = False

	########################################################
	# This function is called by RF when a new Font did Open
	########################################################
	def fontDidOpen(self, font):
		key = font.fileName
		if key not in self.fontModels:
			self.fontModels[key] = TTHToolModel.fontModel(font)

		self.mainPanel.wTools.show()
		self.previewPanel.showOrHide()
		# self.programWindow.showOrHide()
		# self.assemblyWindow.showOrHide()

		self.resetFont(createWindows=False)
		self.updatePartialFont()

	########################################################################################
	# This function is called by RF whenever the Background of the glyph Window needs redraw
	########################################################################################
	def drawBackground(self, scale):
		g = self.getGlyph()
		if g == None or self.doneGeneratingPartialFont == False:
			return

		r = 5*scale
		# self.drawDiscAtPoint(r, 0, 0, discColor)
		# self.drawDiscAtPoint(r, g.width, 0, discColor)

		# self.drawZones(scale)

		tr = self.c_fontModel.textRenderer
		tr.set_cur_size(self.TTHToolModel.PPM_Size)
		tr.set_pen((0, 0))
		
		if self.TTHToolModel.showBitmap == 1:
			tr.render_named_glyph_list([g.name], self.TTHToolModel.fPitch, self.TTHToolModel.bitmapOpacity)

		# if self.TTHToolModel.showGrid == 1:
		# 	self.drawGrid(scale, self.TTHToolModel.fPitch)

		# if self.TTHToolModel.showCenterPixel == 1:
		# 	self.drawCenterPixel(scale, self.TTHToolModel.fPitch)

		# if self.TTHToolModel.showOutline == 1:
		# 	tr.drawOutlineOfName(scale, self.TTHToolModel.fPitch, g.name)
		# 	self.drawSideBearings(scale, g.name)

	########################################################################################
	# This function is called by RF whenever the Foreground of the glyph Window needs redraw
	########################################################################################
	def draw(self, scale):
		self.scale = scale
		g = self.getGlyph()
		if g == None:
			return

		# update the size of the waterfall subview
		name = self.c_fontModel.f.fileName
		drawPreview = False
		if name not in self.previewInGlyphWindow:
			if self.TTHToolModel.showPreviewInGlyphWindow == 1:
				self.createPreviewInGlyphWindow()
				drawPreview = True
		else:
			subView = self.previewInGlyphWindow[name]
			superview = self.getNSView().enclosingScrollView().superview()
			frame = superview.frame()
			frame.size.width -= 30
			frame.origin.x = 0
			subView.setFrame_(frame)

	###########################################
	# This function is called by RF at mouse Up
	###########################################
	def mouseUp(self, point):
		if self.TTHToolModel.showPreviewInGlyphWindow == 1:
			x = self.getCurrentEvent().locationInWindow().x
			y = self.getCurrentEvent().locationInWindow().y

			fname = self.c_fontModel.f.fileName
			if fname in self.previewInGlyphWindow:
				for i in self.previewInGlyphWindow[fname].clickableSizesGlyphWindow:
					if x >= i[0] and x <= i[0]+10 and y >= i[1] and y <= i[1]+20:
						self.changeSize(self.previewInGlyphWindow[fname].clickableSizesGlyphWindow[i])

	def drawPreviewSize(self, title, x, y, color):
		attributes = {
			NSFontAttributeName : NSFont.boldSystemFontOfSize_(7),
			NSForegroundColorAttributeName : color,
			}

		text = NSAttributedString.alloc().initWithString_attributes_(title, attributes)
		text.drawAtPoint_((x, y))

	def deletePreviewInGlyphWindow(self):
		name = self.c_fontModel.f.fileName
		if name in self.previewInGlyphWindow:
			self.previewInGlyphWindow[name].removeFromSuperview()
			del self.previewInGlyphWindow[name]

	def changePreviewInGlyphWindowState(self, onOff):
		if onOff == 1 and self.TTHToolModel.showPreviewInGlyphWindow == 0:
			self.createPreviewInGlyphWindow()
		elif onOff == 0 and self.TTHToolModel.showPreviewInGlyphWindow == 1:
			self.deletePreviewInGlyphWindow()
		self.TTHToolModel.setPreviewInGlyphWindowState(onOff)
		UpdateCurrentGlyphView()

	def createPreviewInGlyphWindow(self):
		name = self.c_fontModel.f.fileName
		if name in self.previewInGlyphWindow: return
		superview = self.getNSView().enclosingScrollView().superview()
		newView = previewInGlyphWindow.PreviewInGlyphWindow.alloc().init_withTTHToolInstance(self)
		superview.addSubview_(newView)
		frame = superview.frame()
		frame.size.width -= 30
		frame.origin.x = 0
		newView.setFrame_(frame)
		self.previewInGlyphWindow[name] = newView

	def buildModelsForOpenFonts(self):
		self.fontModels = {}
		for f in AllFonts():
			key = f.fileName
			self.fontModels[key] = fontModel.FontModel(f)
		if CurrentFont() != None:
			self.c_fontModel = self.fontModels[CurrentFont().fileName]
		else:
			self.c_fontModel = None

	def setupCurrentModel(self, font):
		key = font.fileName
		if key not in self.fontModels:
			self.fontModels[key] = fontModel.FontModel(font)
		self.c_fontModel = self.fontModels[key]

	def resetFont(self, createWindows=False):
		c_f = CurrentFont()
		if c_f == None:
			return

		self.setupCurrentModel(c_f)
		self.c_fontModel.setFont(c_f)

		f = self.c_fontModel.f
		self.c_fontModel.setUPM(f.info.unitsPerEm)

		if helperFunctions.checkSegmentType(f) == False:
			self.messageInFront = True
		 	Dialogs.Message("WARNING:\nThis is not a Quadratic UFO,\nyou must convert it before.")
			self.messageInFront = False
			return

		self.TTHToolModel.resetPitch(self.c_fontModel.UPM)
		self.c_fontModel.setControlValues()

		if createWindows:
			self.mainPanel = mainPanel.MainPanel(self)
			self.previewPanel.showOrHide()

		self.resetglyph(self.getGlyph())

	def resetglyph(self, g):
		if g == None:
			return

		self.ready = True

		if self.previewPanel.isVisible():
			self.previewPanel.setNeedsDisplay()

	def updatePartialFont(self):
		"""Typically called directly when the current glyph has been modifed."""
		self.generatePartialTempFont()
		self.c_fontModel.regenTextRenderer()

	def updatePartialFontIfNeeded(self):
		"""Re-create the partial font if new glyphs are required."""
		(text, curGlyphString) = self.prepareText()
		curSet = self.TTHToolModel.requiredGlyphsForPartialTempFont
		newSet = self.defineGlyphsForPartialTempFont(text, curGlyphString)
		regenerate = not newSet.issubset(curSet)
		n = len(curSet)
		if (n > 128) and (len(newSet) < n):
			regenerate = True
		if regenerate:
			self.TTHToolModel.requiredGlyphsForPartialTempFont = newSet
			self.updatePartialFont()

	def prepareText(self):
		g = self.getGlyph()
		unicodeToName = CurrentFont().getCharacterMapping()

		if g == None:
			curGlyphName = ''
		else:
			curGlyphName = g.name

		texts = self.TTHToolModel.previewString.split('/?')
		udata = self.c_fontModel.f.naked().unicodeData
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
		def addGlyph(s, name):
			try:
				s.add(name)
				for component in self.c_fontModel.f[name].components:
					s.add(component.baseGlyph)
			except:
				pass
		glyphSet = set()
		addGlyph(glyphSet, curGlyphName)
		for name in text:
			addGlyph(glyphSet, name)
		return glyphSet

	def generatePartialTempFont(self):
		try:
			tempFont = RFont(showUI=False)
			tempFont.info.unitsPerEm = self.c_fontModel.f.info.unitsPerEm
			tempFont.info.ascender = self.c_fontModel.f.info.ascender
			tempFont.info.descender = self.c_fontModel.f.info.descender
			tempFont.info.xHeight = self.c_fontModel.f.info.xHeight
			tempFont.info.capHeight = self.c_fontModel.f.info.capHeight

			tempFont.info.familyName = self.c_fontModel.f.info.familyName
			tempFont.info.styleName = self.c_fontModel.f.info.styleName

			tempFont.glyphOrder = self.c_fontModel.f.glyphOrder

			if 'com.robofont.robohint.cvt ' in self.c_fontModel.f.lib:
				tempFont.lib['com.robofont.robohint.cvt '] = self.c_fontModel.f.lib['com.robofont.robohint.cvt ']
			if 'com.robofont.robohint.prep' in self.c_fontModel.f.lib:
				tempFont.lib['com.robofont.robohint.prep'] = self.c_fontModel.f.lib['com.robofont.robohint.prep']
			if 'com.robofont.robohint.fpgm' in self.c_fontModel.f.lib:
				tempFont.lib['com.robofont.robohint.fpgm'] = self.c_fontModel.f.lib['com.robofont.robohint.fpgm']
			if 'com.robofont.robohint.gasp' in self.c_fontModel.f.lib:
				tempFont.lib['com.robofont.robohint.gasp'] = self.c_fontModel.f.lib['com.robofont.robohint.gasp']
			if 'com.robofont.robohint.maxp.maxStorage' in self.c_fontModel.f.lib:
				tempFont.lib['com.robofont.robohint.maxp.maxStorage'] = self.c_fontModel.f.lib['com.robofont.robohint.maxp.maxStorage']


			for gName in self.TTHToolModel.requiredGlyphsForPartialTempFont:
				tempFont.newGlyph(gName)
				tempFont[gName] = self.c_fontModel.f[gName]
				tempFont[gName].unicode = self.c_fontModel.f[gName].unicode
				if 'com.robofont.robohint.assembly' in self.c_fontModel.f[gName].lib:
					tempFont[gName].lib['com.robofont.robohint.assembly'] = self.c_fontModel.f[gName].lib['com.robofont.robohint.assembly']

			tempFont.generate(self.c_fontModel.partialtempfontpath, 'ttf', decompose = False, checkOutlines = False, autohint = False, releaseMode = False, glyphOrder=None, progressBar = None )
			self.doneGeneratingPartialFont = True

		except:
			print 'ERROR: Unable to generate temporary font'

	def changeSize(self, size):
		try:
			size = int(size)
		except ValueError:
			size = 9

		self.TTHToolModel.setSize(size)
		self.mainPanel.wTools.PPEMSizeComboBox.set(self.TTHToolModel.PPM_Size)

		self.TTHToolModel.resetPitch(self.c_fontModel.UPM)

		self.cachedPathes['centers'] = None
		self.cachedPathes['grid'] = None
		self.cachedScale = None

		self.changeDeltaRange(self.TTHToolModel.PPM_Size, self.TTHToolModel.PPM_Size)
		if self.previewPanel.isVisible():
			self.previewPanel.setNeedsDisplay()

		if self.popOverIsOpened:
			if hasattr(self.popover, 'ZoneDeltaOffsetSlider'):
				if 'delta' in self.c_fontModel.zones[self.selectedZoneName]:
					if str(size) in self.c_fontModel.zones[self.selectedZoneName]['delta']:
						self.popover.ZoneDeltaOffsetSlider.set(self.c_fontModel.zones[self.selectedZoneName]['delta'][str(size)] + 8)
					else:
						self.popover.ZoneDeltaOffsetSlider.set(8)
		UpdateCurrentGlyphView()

	def applySizeChange(self):
		fromS = self.TTHToolModel.previewFrom
		toS = self.TTHToolModel.previewTo
		if fromS > toS:
			fromS = toS
		if toS > fromS + 100:
			toS = fromS + 100
		if hasattr(self.mainPanel, 'preferencesSheet'):
			self.mainPanel.preferencesSheet.w.viewAndSettingsBox.displayFromEditText.set(fromS)
			self.mainPanel.preferencesSheet.w.viewAndSettingsBox.displayToEditText.set(toS)
		self.changeDisplayPreviewSizesFromTo(fromS, toS)
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

		self.TTHToolModel.setDeltaRange1(value1)
		self.mainPanel.wTools.DeltaRange1ComboBox.set(self.TTHToolModel.deltaRange1)
		self.TTHToolModel.setDeltaRange2(value2)
		self.mainPanel.wTools.DeltaRange2ComboBox.set(self.TTHToolModel.deltaRange2)

	def changeBitmapPreview(self, preview):
		if not self.doneGeneratingPartialFont: return
		model = self.c_fontModel
		if model.bitmapPreviewSelection == preview: return
		model.setBitmapPreview(preview)
		model.textRenderer = textRenderer.TextRenderer(model.partialtempfontpath, model.bitmapPreviewSelection)

		if self.getGlyph() == None:
			return
		if self.previewPanel.isVisible():
			self.previewPanel.setNeedsDisplay()
		UpdateCurrentGlyphView()

	def changeBitmapOpacity(self, value):
		self.TTHToolModel.bitmapOpacity = value
		setExtensionDefault(defaultKeyBitmapOpacity, self.TTHToolModel.bitmapOpacity)
		UpdateCurrentGlyphView()

	def changeShowBitmapState(self, onOff):
		self.TTHToolModel.setShowBitmap(onOff)
		UpdateCurrentGlyphView()

	def changeDisplayPreviewSizesFromTo(self, fromSize, toSize):
		self.TTHToolModel.previewFrom = fromSize
		self.TTHToolModel.previewTo = toSize
		setExtensionDefault(defaultKeyPreviewFrom, self.TTHToolModel.previewFrom)
		setExtensionDefault(defaultKeyPreviewTo, self.TTHToolModel.previewTo)
		self.previewPanel.setNeedsDisplay()

	def samplesStringsHaveChanged(self, sampleStrings):
		currentString = self.previewPanel.win.previewEditText.get()
		self.TTHToolModel.previewSampleStringsList = sampleStrings
		setExtensionDefault(defaultKeyPreviewSampleStrings, self.TTHToolModel.previewSampleStringsList)
		self.previewPanel.win.previewEditText.setItems(self.TTHToolModel.previewSampleStringsList)
		self.resetPreviewComboBoxWithString(currentString)

	def resetPreviewComboBoxWithString(self, sampleString):
		self.TTHToolModel.setPreviewString(sampleString)
		self.previewPanel.win.previewEditText.set(self.TTHToolModel.previewString)
