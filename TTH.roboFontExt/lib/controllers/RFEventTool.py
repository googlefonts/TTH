from mojo.extensions    import ExtensionBundle, setExtensionDefault
from mojo.events        import BaseEventTool#, getActiveEventTool
from mojo.roboFont      import CurrentFont, AllFonts
from mojo.UI            import UpdateCurrentGlyphView
from lib.tools.defaults import getDefault, setDefault
from robofab.interface.all.dialogs import Message as FabMessage
from AppKit import NSColor, NSBezierPath, NSFontAttributeName, NSFont,\
                   NSForegroundColorAttributeName, NSAttributedString,\
			 NSShadow, NSGraphicsContext

# reloaded in main.py
from models.TTHTool import uniqueInstance as tthTool
# reloaded below
from commons import helperFunctions, textRenderer, drawing as DR

reload(helperFunctions)
reload(textRenderer)
reload(DR)

toolbarIcon = ExtensionBundle("TTH").get("toolbarIcon")

whiteColor  = NSColor.whiteColor()
shadowColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, .8)
borderColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, .8)

gridColor         = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.1)
centerpixelsColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.5)
zoneColor         = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .7, .2, .2)
zoneColorLabel    = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .7, .2, 1)
deltaColor        = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .5, 0, 1)
#finalDeltaColor   = NSColor.colorWithCalibratedRed_green_blue_alpha_(.73, .3, .8, 1)

class TTH_RF_EventTool(BaseEventTool):

	def __init__(self):
		super(TTH_RF_EventTool, self).__init__()

		# Remembers the cruve drawing preference of RF prior to forcing
		# quadratic-style
		self.originalCurveDrawingPref = None

		# Precomputed NSBezierPath'es
		self.cachedPathes = {'grid':None, 'centers':None}

		# The 'radius' of pixel centers from the last 'draw()' call.
		# Used in drawCenterPixel()
		self.cachedCenterRadius = None

		# Set to True when the current font document is about to be closed.
		self.popOverIsOpened = False

		# To each zone, associate the position of its label in the GLyphWindow
		# Used when clicking
		self.zoneLabelPos = {}

		# Stores the current TTHFont model during mouseDown event
		self.mouseDownFontModel = None

	def __del__(self):
		pass

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

	def getToolbarIcon(self):
		'''This function is called by RF on the parent class in order to
		get the tool icon'''
		return toolbarIcon

	def getToolbarTip(self):
		'''This function is called by RF on the parent class in order to
		get the tool button tip'''
		return "TrueType Hinting"

	def becomeActive(self):
		'''This function is called by RF when the tool button is pressed'''
		f = CurrentFont()
		if (f is None) or (not helperFunctions.fontIsQuadratic(f)):
		 	FabMessage("WARNING:\nThis is not a Quadratic UFO,\nyou must convert it before.")
		else:
			# save the original curve drawing mode
			self.originalCurveDrawingPref = getDefault('drawingSegmentType')
			# and set quadratic mode
			if self.originalCurveDrawingPref != 'qcurve':
				setDefault('drawingSegmentType', 'qcurve')

		tthTool.becomeActive()
		#self.calculateHdmx()

	def becomeInactive(self):
		'''This function is called by RF when another tool button is
		pressed'''
		tthTool.becomeInactive()

		# restore the original curve drawing mode
		if self.originalCurveDrawingPref != 'qcurve':
			setDefault('drawingSegmentType', self.originalCurveDrawingPref)

	def viewDidChangeGlyph(self):
		'''This function is called by RF when the Glyph View shows another
		glyph'''
		#print "[TTH RF EVENT] View did change glyph"
		tthTool.showOrHide()
		tthTool.updatePartialFontIfNeeded()

	def currentGlyphChanged(self):
		'''This function is called by RF when the Current Glyph changed'''
		#print "[TTH RF EVENT] Current glyph changed"
		tthTool.showOrHide()
		tthTool.updatePartialFontIfNeeded()

	def fontWillClose(self, font):
		'''This function is called by RF before the Current Font closes'''
		#print "[TTH RF EVENT] Font will close", font.fileName
		tthTool.delFontModelForFont(font)
		# We hide the panels only if we close the last font opened
		if len(AllFonts()) <= 1:
			tthTool.hideWindows()

	def fontResignCurrent(self, font):
		'''This function is called by RF when the Current Font is not
		Current anymore'''
		print "[TTH RF EVENT] Font resign current", font.fileName

	def fontBecameCurrent(self, font):
		'''This function is called by RF when a new Font becomes Current'''
		# if hasattr(self.toolsPanel, 'sheetControlValues'):
		# 	self.toolsPanel.sheetControlValues.c_fontModel = self.c_fontModel
		# 	self.toolsPanel.sheetControlValues.resetGeneralBox()
		# 	self.toolsPanel.sheetControlValues.resetStemBox()
		# 	self.toolsPanel.sheetControlValues.resetZoneBox()
		#print "[TTH RF EVENT] Font became current", font.fileName
		tthTool.showOrHide()
		tthTool.currentFontHasChanged(font)

	def fontDidOpen(self, font):
		'''This function is called by RF when a new Font did Open'''
		tthTool.showOrHide()
		tthTool.currentFontHasChanged(font)

	def glyphWindowWillOpen(self, window):
		'''Install the previewInGlyphWindow'''
		g, fm = self.getGAndFontModel()
		if fm is not None:
			fm.createPreviewInGlyphWindowIfNeeded()

	def glyphWindowWillClose(self, window):
		'''Destroy the previewInGlyphWindow'''
		g, fm = self.getGAndFontModel()
		if fm is not None:
			fm.killPreviewInGlyphWindow()

	def numberOfRectsToDraw(self):
		view = self.getNSView()
		if view is None: return 0
		view = view.enclosingScrollView()
		if view is None: return 0
		rects, count = view.getRectsBeingDrawn_count_(None, None)
		return count

	def drawBackground(self, scale):
		'''This function is called by RF whenever the Background of the
		glyph Window needs redraw'''

		if 0 == self.numberOfRectsToDraw(): return
		
		g, fm = self.getGAndFontModel()

		if fm is None: return

		# we do this here, because it fails to do it in `becomeActive` :-(
		# (The NSView's superview seems not ready at that time)
		if fm.createPreviewInGlyphWindowIfNeeded():
			self.refreshView()

		if g == None: return

		pitch = fm.getPitch()

		self.drawZones(scale, pitch, fm)

		tr = fm.textRenderer
		tr.set_cur_size(tthTool.PPM_Size)
		tr.set_pen((0, 0))

		if tthTool.showBitmap == 1 and tr != None:
			tr.render_named_glyph_list([g.name], pitch, tthTool.bitmapOpacity)

		if tthTool.showGrid == 1:
			self.drawGrid(scale, pitch, tthTool.gridOpacity, fm)

		if tthTool.showCenterPixel == 1:
			self.drawCenterPixel(scale, pitch, tthTool.centerPixelSize)

		if tthTool.showOutline == 1 and tr != None:
			tr.drawOutlineOfNameWithThickness(scale, pitch, g.name, tthTool.outlineThickness)
			self.drawSideBearings(scale, pitch, g.name, fm)

		DR.drawSideBearingsPointsOfGlyph(scale, 5, g)
		self.drawAscentDescent(scale, pitch, fm)

	def draw(self, scale):
		'''This function is called by RF whenever the Foreground of the
		glyph Window needs redraw'''
		if 0 == self.numberOfRectsToDraw(): return
		
		g, fm = self.getGAndFontModel()
		if (fm is None) or (g is None): return
		gm = fm.glyphModelForGlyph(g)
		if gm is None:
			print "GlyphModel is None"
			return
		print 'glyph has',len(gm.hintingCommands),'hinting commands'

	def mouseDown(self, point, clickCount):
		'''This function is called by RF at mouse Down'''
		g, fm = self.getGAndFontModel()
		self.mouseDownFontModel = fm

	def mouseUp(self, point):
		'''This function is called by RF at mouse Up'''
		if self.mouseDownFontModel == None: return
		pigw = self.mouseDownFontModel.previewInGlyphWindow
		if pigw == None: return
		if pigw.isHidden(): return
		positions = pigw.clickableSizesGlyphWindow
		loc = self.getCurrentEvent().locationInWindow()
		for p, s in positions.iteritems():
			if (p[0] <= loc.x <= p[0]+10) and (p[1] <= loc.y <= p[1]+20):
				tthTool.changeSize(s)
		self.mouseDownFontModel = None

# - - - - - - - - - - - - - - - - - - - - - - - GETTING CURRENT GLYPH AND FONT

	def getGAndFontModel(self):
		'''Returns the current RGlyph and the RFont it belongs to.
		Used everywhere, since current glyph and current font are NOT
		remembered.'''
		g = self.getGlyph()
		return (g, tthTool.fontModelForGlyph(g))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - DRAWING FUNCTIONS

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
		r = scale * size
		if ( self.cachedPathes['centers'] == None or self.cachedCenterRadius != r ):
			self.cachedCenterRadius = r
			path = NSBezierPath.bezierPath()
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
			self.cachedPathes['centers'] = path
		path = self.cachedPathes['centers']
		centerpixelsColor.set()
		path.fill()

	def drawZones(self, scale, pitch, fontModel):
		xpos = 5 * fontModel.UPM
		self.zoneLabelPos = {}
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

		#currentTool = getActiveEventTool()
		#view = currentTool.getNSView()
		view = self.getNSView()

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

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

	def sizeHasChanged(self):
		'''This function tells the RFEventTool that the PPEM preview size
		has changed'''
		self.cachedPathes = {'grid':None, 'centers':None}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if tthTool._printLoadings: print "RFEventTool, ",
