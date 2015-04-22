from mojo.extensions import *
from mojo.events import *
from mojo.UI import *
from robofab.world import *
import robofab.interface.all.dialogs as Dialogs
from lib.tools.defaults import getDefault, setDefault
from lib.UI.spaceCenter.glyphSequenceEditText import splitText
from AppKit import *

from commons import helperFunctions, textRenderer, ttTablesWriter
from commons import drawing as DR
from models import TTHTool
from views import previewInGlyphWindow, mainPanel, previewPanel

reload(helperFunctions)
reload(textRenderer)
reload(ttTablesWriter)
reload(TTHTool)
reload(mainPanel)
reload(previewPanel)

tthTool = TTHTool.uniqueInstance

toolbarIcon = ExtensionBundle("TTH").get("toolbarIcon")

DefaultKeyStub = "com.sansplomb.TTH."

defaultKeyPreviewSampleStrings = DefaultKeyStub + "previewSampleStrings"
defaultKeyBitmapOpacity = DefaultKeyStub + "bitmapOpacity"
defaultKeyPreviewFrom = DefaultKeyStub + "previewFrom"
defaultKeyPreviewTo = DefaultKeyStub + "previewTo"

whiteColor = NSColor.whiteColor()
shadowColor =  NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, .8)
borderColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, .8)

gridColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.1)
centerpixelsColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.5)
zoneColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .7, .2, .2)
zoneColorLabel = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .7, .2, 1)
deltaColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .5, 0, 1)
#finalDeltaColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.73, .3, .8, 1)

class TTH_RF_EventTool(BaseEventTool):

	def __init__(self):
		super(TTH_RF_EventTool, self).__init__()

		# FIXME: Can we come up with a precise meaning for this boolean?
		self.ready = False
		self.doneGeneratingPartialFont = False
		self.drawingPreferencesChanged = False

		# Precomputed NSBezierPath'es
		self.cachedPathes = {'grid':None, 'centers':None}
		# The 'scale' parameter from the last 'draw()' call.
		# Used in drawCenterPixel()
		self.cachedScale = None
		# The 'size' parameter during the last 'draw()' call.
		# Used in drawCenterPixel()
		self.cachedSize = None
		
		# Set to True when the current font document is about to be closed.
		self.fontClosed = False
		self.popOverIsOpened = False
		self.messageInFront = False

		self.previewInGlyphWindow = {}

		self.zoneLabelPos = {}

		self.previewPanel  = previewPanel.PreviewPanel(self, (-510, 30, 500, 600))

	def getGAndFontModel(self):
		g = self.getGlyph()
		if g == None:
			return (None, None)
		return (g, tthTool.fontModelForGlyph(g))

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
		#self.calculateHdmx()

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
		print "Font resign current", font.fileName
		if self.fontClosed:
			return
		self.deletePreviewInGlyphWindow()
		self.resetFont(createWindows=False)

	###############################################################
	# This function is called by RF when a new Font becomes Current
	###############################################################
	def fontBecameCurrent(self, font):
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
		g, fm = self.getGAndFontModel()
		if g == None or self.doneGeneratingPartialFont == False:
			return

		pitch = fm.getPitch()

		self.drawZones(scale, pitch, fm)

		tr = fm.textRenderer
		tr.set_cur_size(tthTool.PPM_Size)
		tr.set_pen((0, 0))
		
		if tthTool.showBitmap == 1:
			tr.render_named_glyph_list([g.name], pitch, tthTool.bitmapOpacity)

		if tthTool.showGrid == 1:
			self.drawGrid(scale, pitch, tthTool.gridOpacity, fm)

		if tthTool.showCenterPixel == 1:
			self.drawCenterPixel(scale, pitch, tthTool.centerPixelSize)

		if tthTool.showOutline == 1:
			tr.drawOutlineOfNameWithThickness(scale, pitch, g.name, tthTool.outlineThickness)
			self.drawSideBearings(scale, pitch, g.name, fm)

		DR.drawSideBearingsPointsOfGlyph(scale, 5, g)
		self.drawAscentDescent(scale, pitch, fm)

	########################################################################################
	# This function is called by RF whenever the Foreground of the glyph Window needs redraw
	########################################################################################
	def draw(self, scale):
		#self.scale = scale
		g = self.getGlyph()
		if g == None:
			return
		fm = tthTool.fontModelForGlyph(g)

		# update the size of the waterfall subview
		name = fm.f.fileName
		drawPreview = False
		if name not in self.previewInGlyphWindow:
			if tthTool.showPreviewInGlyphWindow == 1:
				self.createPreviewInGlyphWindow()
				drawPreview = True
		else:
			superview = self.getNSView().enclosingScrollView().superview()
			frame = superview.frame()
			frame.size.width -= 30
			frame.origin.x = 0
			subView = self.previewInGlyphWindow[name]
			subView.setFrame_(frame)

	###########################################
	# This function is called by RF at mouse Up
	###########################################
	def mouseDown(self, point):
		g, fm = self.getGAndFontModel()
		self.c_fontModel = fm

	###########################################
	# This function is called by RF at mouse Up
	###########################################
	def mouseUp(self, point):
		if tthTool.showPreviewInGlyphWindow == 1:
			x = self.getCurrentEvent().locationInWindow().x
			y = self.getCurrentEvent().locationInWindow().y

			fname = self.c_fontModel.f.fileName
			if fname in self.previewInGlyphWindow:
				for i in self.previewInGlyphWindow[fname].clickableSizesGlyphWindow:
					if x >= i[0] and x <= i[0]+10 and y >= i[1] and y <= i[1]+20:
						self.changeSize(self.previewInGlyphWindow[fname].clickableSizesGlyphWindow[i])
		del self.c_fontModel

	def drawSideBearings(self, scale, pitch, name, fontModel):
		try:
			xPos = pitch * fontModel.textRenderer.get_name_advance(name)[0] / 64.0
		except:
			return
		DR.drawVerticalLines(scale*tthTool.outlineThickness, [0, xPos])

	def drawAscentDescent(self, scale, pitch, fontModel):
		yAsc  = fontModel.ascent
		yDesc = fontModel.descent
		if None == yAsc or None == yDesc: return
		yAsc  = helperFunctions.roundbase(yAsc,  pitch)
		yDesc = helperFunctions.roundbase(yDesc, pitch)
		DR.drawHorizontalLines(scale*tthTool.outlineThickness, [yAsc, yDesc])

	def drawGrid(self, scale, pitch, opacity, fontModel):
		if self.cachedPathes['grid'] == None:
			path = NSBezierPath.bezierPath()
			upm = fontModel.UPM
			pos = - int(upm/pitch) * pitch
			maxi = -2 * pos
			while pos < maxi:
				path.moveToPoint_((pos, -upm))
				path.lineToPoint_((pos, 2*upm))
				path.moveToPoint_((-upm, pos))
				path.lineToPoint_((2*upm, pos))
				pos += pitch
			self.cachedPathes['grid'] = path
		path = self.cachedPathes['grid']
		NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, opacity).set()
		path.setLineWidth_(scale)
		path.stroke()

	def drawCenterPixel(self, scale, pitch, size):
		if self.cachedPathes['centers'] == None or self.cachedScale != scale or self.cachedSize != size:
			self.cachedSize = size
			path = NSBezierPath.bezierPath()
			r = scale * size
			r = (r,r)
			x = - tthTool.PPM_Size * pitch + pitch/2 - r[0]/2
			yinit = x
			maxi = -2 * x
			while x < maxi:
				y = yinit
				while y < maxi:
					path.appendBezierPathWithOvalInRect_(((x, y), r))
					y += pitch
				x += pitch
			self.cachedScale = scale
			self.cachedPathes['centers'] = path
		path = self.cachedPathes['centers']
		centerpixelsColor.set()
		path.fill()

	def drawZones(self, scale, pitch, fontModel):
		xpos = 5 * fontModel.UPM
		for zoneName, zone in fontModel.zones.iteritems():
			y_start = int(zone['position'])
			y_end = int(zone['width'])
			if not zone['top']:
				y_end = - y_end
			pathZone = NSBezierPath.bezierPath()
			pathZone.moveToPoint_((-xpos, y_start))
			pathZone.lineToPoint_(( xpos, y_start))
			pathZone.lineToPoint_(( xpos, y_start+y_end))
			pathZone.lineToPoint_((-xpos, y_start+y_end))
			pathZone.closePath
			zoneColor.set()
			pathZone.fill()	
			(width, height) = self.drawTextAtPoint(scale, zoneName, -100*scale, y_start+y_end/2, whiteColor, zoneColorLabel, None)

			self.zoneLabelPos[zoneName] = ((-100*scale, y_start+y_end/2), (width, height))

			point = (-100*scale, y_start+y_end/2)
			if 'delta' in zone:
				for deltaPPM, deltaValue in zone['delta'].iteritems():
					if int(deltaPPM) != tthTool.PPM_Size or deltaValue == 0:
						continue
					path = NSBezierPath.bezierPath()
					path.moveToPoint_((point[0], point[1]))
					end_x = point[0]
					end_y = point[1] + (deltaValue/8.0) * pitch
					path.lineToPoint_((end_x, end_y))

					deltaColor.set()
					path.setLineWidth_(scale)
					path.stroke()
					r = 4
					DR.drawLozengeAtPoint(r*scale, scale, end_x, end_y, deltaColor)

	def drawTextAtPoint(self, scale, title, x, y, textColor, backgroundColor, cmdIndex):
		labelColor = backgroundColor

		if cmdIndex != None:
			if self.glyphTTHCommands[cmdIndex]['active'] == 'false':
				labelColor = inactiveColor
				textColor = whiteColor
			else:
				labelColor = backgroundColor

		currentTool = getActiveEventTool()
		view = currentTool.getNSView()

		attributes = {
			NSFontAttributeName : NSFont.boldSystemFontOfSize_(9),
			NSForegroundColorAttributeName : textColor,
			}
		backgroundStrokeColor = whiteColor

		text = NSAttributedString.alloc().initWithString_attributes_(title, attributes)
		width, height = text.size()
		fontSize = attributes[NSFontAttributeName].pointSize()
		width = width*scale
		width += 8.0*scale
		height = 13*scale
		x -= width / 2.0
		y -= fontSize*scale / 2.0
		
		shadow = NSShadow.alloc().init()
		shadow.setShadowColor_(shadowColor)
		shadow.setShadowOffset_((0, -1))
		shadow.setShadowBlurRadius_(2)

		if self.popOverIsOpened and cmdIndex == self.commandClicked and cmdIndex != None:
			selectedPath = NSBezierPath.bezierPath()
			selectedPath.appendBezierPathWithRoundedRect_xRadius_yRadius_(((x-2*scale, y-2*scale), (width+4*scale, height+4*scale)), 3*scale, 3*scale)
			selectedShadow = NSShadow.alloc().init()
			selectedShadow.setShadowColor_(selectedColor)
			selectedShadow.setShadowOffset_((0, 0))
			selectedShadow.setShadowBlurRadius_(10)
			
			selectedContext = NSGraphicsContext.currentContext()
			selectedContext.saveGraphicsState()

			selectedShadow.set()
			selectedColor.set()
			selectedPath.fill()

			selectedContext.restoreGraphicsState()

		thePath = NSBezierPath.bezierPath()
		thePath.appendBezierPathWithRoundedRect_xRadius_yRadius_(((x, y), (width, height)), 3*scale, 3*scale)
		
		context = NSGraphicsContext.currentContext()
		context.saveGraphicsState()
		shadow.set()
		thePath.setLineWidth_(scale)
		labelColor.set()
		thePath.fill()
		borderColor.set()
		thePath.stroke()

		context.restoreGraphicsState()
		
		view._drawTextAtPoint(title, attributes, (x+(width/2), y+(height/2)+1*scale), drawBackground=False)
		return (width, height)

	def deletePreviewInGlyphWindow(self):
		g, fm = self.getGAndFontModel()
		name = fm.f.fileName
		if name in self.previewInGlyphWindow:
			self.previewInGlyphWindow[name].removeFromSuperview()
			del self.previewInGlyphWindow[name]

	def changePreviewInGlyphWindowState(self, onOff):
		if onOff == 1 and tthTool.showPreviewInGlyphWindow == 0:
			self.createPreviewInGlyphWindow()
		elif onOff == 0 and tthTool.showPreviewInGlyphWindow == 1:
			self.deletePreviewInGlyphWindow()
		tthTool.setPreviewInGlyphWindowState(onOff)
		UpdateCurrentGlyphView()

	def createPreviewInGlyphWindow(self):
		g, fm = self.getGAndFontModel()
		name = fm.f.fileName
		if name in self.previewInGlyphWindow: return
		superview = self.getNSView().enclosingScrollView().superview()
		newView = previewInGlyphWindow.PreviewInGlyphWindow.alloc().init_withTTHEventTool(self)
		superview.addSubview_(newView)
		frame = superview.frame()
		frame.size.width -= 30
		frame.origin.x = 0
		newView.setFrame_(frame)
		self.previewInGlyphWindow[name] = newView

	def resetFont(self, createWindows=False):
		f = CurrentFont()
		if f == None:
			return

		if helperFunctions.checkSegmentType(f) == False:
			self.messageInFront = True
		 	Dialogs.Message("WARNING:\nThis is not a Quadratic UFO,\nyou must convert it before.")
			self.messageInFront = False
			return

		tthTool.fontModelForFont(f).setControlValues()

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

		self.zoneLabelPos = {}

	def updatePartialFont(self):
		"""Typically called directly when the current glyph has been modifed."""
		self.generatePartialTempFont()
		fontModel = tthTool.fontModelForFont(CurrentFont())
		fontModel.regenTextRenderer()

	def updatePartialFontIfNeeded(self):
		"""Re-create the partial font if new glyphs are required."""
		(text, curGlyphString) = self.prepareText()
		curSet = tthTool.requiredGlyphsForPartialTempFont
		newSet = self.defineGlyphsForPartialTempFont(text, curGlyphString)
		regenerate = not newSet.issubset(curSet)
		n = len(curSet)
		if (n > 128) and (len(newSet) < n):
			regenerate = True
		if regenerate:
			tthTool.requiredGlyphsForPartialTempFont = newSet
			self.updatePartialFont()

	def prepareText(self):
		g, fm = self.getGAndFontModel()
		unicodeToName = CurrentFont().getCharacterMapping()

		if g == None:
			curGlyphName = ''
		else:
			curGlyphName = g.name

		texts = tthTool.previewString.split('/?')
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
		fontModel = tthTool.fontModelForFont(CurrentFont())
		def addGlyph(s, name):
			try:
				s.add(name)
				for component in fontModel.f[name].components:
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

	def generateFullTempFont(self):
		fontModel = tthTool.fontModelForFont(CurrentFont())
		try:
			fontModel.f.generate(fontModel.fulltempfontpath, 'ttf', decompose = False, checkOutlines = False, autohint = False, releaseMode = False, glyphOrder=None, progressBar = None )
		except:
			print 'ERROR: Unable to generate full font'

	def generatePartialTempFont(self):
		fontModel = tthTool.fontModelForFont(CurrentFont())
		try:
			tempFont = RFont(showUI=False)
			tempFont.info.unitsPerEm = fontModel.f.info.unitsPerEm
			tempFont.info.ascender = fontModel.f.info.ascender
			tempFont.info.descender = fontModel.f.info.descender
			tempFont.info.xHeight = fontModel.f.info.xHeight
			tempFont.info.capHeight = fontModel.f.info.capHeight

			tempFont.info.familyName = fontModel.f.info.familyName
			tempFont.info.styleName = fontModel.f.info.styleName

			tempFont.glyphOrder = fontModel.f.glyphOrder

			if 'com.robofont.robohint.cvt ' in fontModel.f.lib:
				tempFont.lib['com.robofont.robohint.cvt '] = fontModel.f.lib['com.robofont.robohint.cvt ']
			if 'com.robofont.robohint.prep' in fontModel.f.lib:
				tempFont.lib['com.robofont.robohint.prep'] = fontModel.f.lib['com.robofont.robohint.prep']
			if 'com.robofont.robohint.fpgm' in fontModel.f.lib:
				tempFont.lib['com.robofont.robohint.fpgm'] = fontModel.f.lib['com.robofont.robohint.fpgm']
			if 'com.robofont.robohint.gasp' in fontModel.f.lib:
				tempFont.lib['com.robofont.robohint.gasp'] = fontModel.f.lib['com.robofont.robohint.gasp']
			if 'com.robofont.robohint.hdmx' in fontModel.f.lib:
				tempFont.lib['com.robofont.robohint.hdmx'] = fontModel.f.lib['com.robofont.robohint.hdmx']
			if 'com.robofont.robohint.maxp.maxStorage' in fontModel.f.lib:
				tempFont.lib['com.robofont.robohint.maxp.maxStorage'] = fontModel.f.lib['com.robofont.robohint.maxp.maxStorage']


			for gName in tthTool.requiredGlyphsForPartialTempFont:
				tempFont.newGlyph(gName)
				tempFont[gName] = fontModel.f[gName]
				tempFont[gName].unicode = fontModel.f[gName].unicode
				if 'com.robofont.robohint.assembly' in fontModel.f[gName].lib:
					tempFont[gName].lib['com.robofont.robohint.assembly'] = fontModel.f[gName].lib['com.robofont.robohint.assembly']

			tempFont.generate(fontModel.partialtempfontpath, 'ttf', decompose = False, checkOutlines = False, autohint = False, releaseMode = False, glyphOrder=None, progressBar = None )
			self.doneGeneratingPartialFont = True

		except:
			print 'ERROR: Unable to generate temporary font'

	def changeSize(self, size):
		try:
			size = int(size)
		except ValueError:
			size = 9

		tthTool.setSize(size)
		self.mainPanel.wTools.PPEMSizeComboBox.set(size)

		self.cachedPathes['centers'] = None
		self.cachedPathes['grid'] = None
		# FIXME: Sam thinks that cachedScale need not be reset here, but cachedSize should. Is this correct?
		self.cachedScale = None

		self.changeDeltaRange(tthTool.PPM_Size, tthTool.PPM_Size)
		if self.previewPanel.isVisible():
			self.previewPanel.setNeedsDisplay()

		if self.popOverIsOpened:
			fontModel = tthTool.fontModelForFont(CurrentFont())
			if hasattr(self.popover, 'ZoneDeltaOffsetSlider'):
				if 'delta' in fontModel.zones[self.selectedZoneName]:
					if str(size) in fontModel.zones[self.selectedZoneName]['delta']:
						self.popover.ZoneDeltaOffsetSlider.set(fontModel.zones[self.selectedZoneName]['delta'][str(size)] + 8)
					else:
						self.popover.ZoneDeltaOffsetSlider.set(8)
		UpdateCurrentGlyphView()

	def applySizeChange(self):
		fromS = tthTool.previewFrom
		toS = tthTool.previewTo
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

		tthTool.setDeltaRange1(value1)
		self.mainPanel.wTools.DeltaRange1ComboBox.set(tthTool.deltaRange1)
		tthTool.setDeltaRange2(value2)
		self.mainPanel.wTools.DeltaRange2ComboBox.set(tthTool.deltaRange2)

	def changeBitmapPreview(self, preview):
		fontModel.setBitmapPreview(preview)
		if self.getGlyph() == None:
			return
		if self.previewPanel.isVisible():
			self.previewPanel.setNeedsDisplay()
		UpdateCurrentGlyphView()

	def changeBitmapOpacity(self, value):
		tthTool.setBitmapOpacity(value)
		UpdateCurrentGlyphView()

	def changeShowBitmapState(self, onOff):
		tthTool.setShowBitmap(onOff)
		UpdateCurrentGlyphView()

	def changeShowOutlineState(self, onOff):
		tthTool.setShowOutline(onOff)
		UpdateCurrentGlyphView()

	def changeOutlineThickness(self, value):
		tthTool.setOutlineThickness(value)
		UpdateCurrentGlyphView()

	def changeShowGridState(self, onOff):
		tthTool.setShowGrid(onOff)
		UpdateCurrentGlyphView()

	def changeGridOpacity(self, value):
		tthTool.setGridOpacity(value)
		UpdateCurrentGlyphView()

	def changeShowCenterPixelState(self, onOff):
		tthTool.setShowCenterPixels(onOff)
		UpdateCurrentGlyphView()

	def changeCenterPixelSize(self, value):
		tthTool.setCenterPixelSize(value)
		UpdateCurrentGlyphView()

	def changeDisplayPreviewSizesFromTo(self, fromSize, toSize):
		tthTool.previewFrom = fromSize
		tthTool.previewTo = toSize
		setExtensionDefault(defaultKeyPreviewFrom, tthTool.previewFrom)
		setExtensionDefault(defaultKeyPreviewTo, tthTool.previewTo)
		self.previewPanel.setNeedsDisplay()

	def samplesStringsHaveChanged(self, sampleStrings):
		currentString = self.previewPanel.win.previewEditText.get()
		tthTool.previewSampleStringsList = sampleStrings
		setExtensionDefault(defaultKeyPreviewSampleStrings, tthTool.previewSampleStringsList)
		self.previewPanel.win.previewEditText.setItems(tthTool.previewSampleStringsList)
		self.resetPreviewComboBoxWithString(currentString)

	def resetPreviewComboBoxWithString(self, sampleString):
		tthTool.setPreviewString(sampleString)
		self.previewPanel.win.previewEditText.set(tthTool.previewString)
