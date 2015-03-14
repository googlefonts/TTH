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

whiteColor = NSColor.whiteColor()
shadowColor =  NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, .8)
borderColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, .8)

sidebearingColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.4, .8, 1, 1)
discColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .3, .94, 1)
gridColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.1)
centerpixelsColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.5)
zonecolor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .7, .2, .2)
zonecolorLabel = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .7, .2, 1)

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
		self.cachedSize = None
		
		self.fontClosed = False
		self.popOverIsOpened = False
		self.messageInFront = False

		self.previewInGlyphWindow = {}

		self.zoneLabelPos = {}

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

		self.drawZones(scale)

		tr = self.c_fontModel.textRenderer
		tr.set_cur_size(self.TTHToolModel.PPM_Size)
		tr.set_pen((0, 0))
		
		if self.TTHToolModel.showBitmap == 1:
			tr.render_named_glyph_list([g.name], self.TTHToolModel.fPitch, self.TTHToolModel.bitmapOpacity)

		if self.TTHToolModel.showGrid == 1:
			self.drawGrid(scale, self.TTHToolModel.fPitch, self.TTHToolModel.gridOpacity)

		if self.TTHToolModel.showCenterPixel == 1:
			self.drawCenterPixel(scale, self.TTHToolModel.fPitch, self.TTHToolModel.centerPixelSize)

		if self.TTHToolModel.showOutline == 1:
			tr.drawOutlineOfNameWithThickness(scale, self.TTHToolModel.fPitch, g.name, self.TTHToolModel.outlineThickness)
			self.drawSideBearings(scale, g.name)

		self.drawSideBearingsPointsOfGlyph(scale, 5, g)

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

	def drawDiscAtPoint(self, r, x, y, color):
		color.set()
		NSBezierPath.bezierPathWithOvalInRect_(((x-r, y-r), (r*2, r*2))).fill()

	def drawLozengeAtPoint(self, scale, r, x, y, color):
		color.set()
		path = NSBezierPath.bezierPath()
		path.moveToPoint_((x+r*5, y))
		path.lineToPoint_((x, y+r*5))
		path.lineToPoint_((x-r*5, y))
		path.lineToPoint_((x, y-r*5))
		path.lineToPoint_((x+r*5, y))
		path.fill()

	def drawSideBearingsPointsOfGlyph(self, scale, size, glyph):
		r = size*scale
		self.drawDiscAtPoint(r, 0, 0, discColor)
		self.drawDiscAtPoint(r, glyph.width, 0, discColor)

	def drawPreviewSize(self, title, x, y, color):
		attributes = {
			NSFontAttributeName : NSFont.boldSystemFontOfSize_(7),
			NSForegroundColorAttributeName : color,
			}

		text = NSAttributedString.alloc().initWithString_attributes_(title, attributes)
		text.drawAtPoint_((x, y))

	def drawSideBearings(self, scale, name):
		try:
			xPos = self.TTHToolModel.fPitch * self.c_fontModel.textRenderer.get_name_advance(name)[0] / 64
		except:
			return
		pathX = NSBezierPath.bezierPath()
		pathX.moveToPoint_((xPos, -5000))
		pathX.lineToPoint_((xPos, 5000))
		sidebearingColor.set()
		pathX.setLineWidth_(scale*self.TTHToolModel.outlineThickness)
		pathX.stroke()

		pathX = NSBezierPath.bezierPath()
		pathX.moveToPoint_((0, -5000))
		pathX.lineToPoint_((0, 5000))
		sidebearingColor.set()
		pathX.setLineWidth_(scale*self.TTHToolModel.outlineThickness)
		pathX.stroke()

	def drawGrid(self, scale, pitch, opacity):
		if self.cachedPathes['grid'] == None:
			path = NSBezierPath.bezierPath()
			pos = - int(1000*(self.c_fontModel.UPM/1000.0)/pitch) * pitch
			maxi = -2 * pos
			while pos < maxi:
				path.moveToPoint_((pos, -1000*(self.c_fontModel.UPM/1000.0)))
				path.lineToPoint_((pos, 2000*(self.c_fontModel.UPM/1000.0)))
				path.moveToPoint_((-1000*(self.c_fontModel.UPM/1000.0), pos))
				path.lineToPoint_((2000*(self.c_fontModel.UPM/1000.0), pos))
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
			x = - int(1000*(self.c_fontModel.UPM/1000.0)/pitch) * pitch + pitch/2 - r[0]/2
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

	def drawZones(self, scale):

		for zoneName, zone in self.c_fontModel.zones.iteritems():
			y_start = int(zone['position'])
			y_end = int(zone['width'])
			if not zone['top']:
				y_end = - y_end
			pathZone = NSBezierPath.bezierPath()
			pathZone.moveToPoint_((-5000*(self.c_fontModel.UPM/1000.0), y_start))
			pathZone.lineToPoint_((5000*(self.c_fontModel.UPM/1000.0), y_start))
			pathZone.lineToPoint_((5000*(self.c_fontModel.UPM/1000.0), y_start+y_end))
			pathZone.lineToPoint_((-5000*(self.c_fontModel.UPM/1000.0), y_start+y_end))
			pathZone.closePath
			zonecolor.set()
			pathZone.fill()	
			(width, height) = self.drawTextAtPoint(scale, zoneName, -100*scale, y_start+y_end/2, whiteColor, zonecolorLabel, None)

			self.zoneLabelPos[zoneName] = ((-100*scale, y_start+y_end/2), (width, height))

			point = (-100*scale, y_start+y_end/2)
			if 'delta' in zone:
				for deltaPPM, deltaValue in zone['delta'].iteritems():
					if int(deltaPPM) == self.tthtm.PPM_Size and deltaValue != 0:
						path = NSBezierPath.bezierPath()
					 	path.moveToPoint_((point[0], point[1]))
					 	end_x = point[0]
					 	end_y = point[1] + (deltaValue/8.0)*self.tthtm.pitch
					 	path.lineToPoint_((end_x, end_y))

					 	deltacolor.set()
						path.setLineWidth_(scale)
						path.stroke()
						r = 4
						self.drawLozengeAtPoint(r*scale, scale, end_x, end_y, deltacolor)

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
		backgroundStrokeColor = NSColor.whiteColor()

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

		self.zoneLabelPos = {}

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
		self.TTHToolModel.setBitmapOpacity(value)
		UpdateCurrentGlyphView()

	def changeShowBitmapState(self, onOff):
		self.TTHToolModel.setShowBitmap(onOff)
		UpdateCurrentGlyphView()

	def changeShowOutlineState(self, onOff):
		self.TTHToolModel.setShowOutline(onOff)
		UpdateCurrentGlyphView()

	def changeOutlineThickness(self, value):
		self.TTHToolModel.setOutlineThickness(value)
		UpdateCurrentGlyphView()

	def changeShowGridState(self, onOff):
		self.TTHToolModel.setShowGrid(onOff)
		UpdateCurrentGlyphView()

	def changeGridOpacity(self, value):
		self.TTHToolModel.setGridOpacity(value)
		UpdateCurrentGlyphView()

	def changeShowCenterPixelState(self, onOff):
		self.TTHToolModel.setShowCenterPixels(onOff)
		UpdateCurrentGlyphView()

	def changeCenterPixelSize(self, value):
		self.TTHToolModel.setCenterPixelSize(value)
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
