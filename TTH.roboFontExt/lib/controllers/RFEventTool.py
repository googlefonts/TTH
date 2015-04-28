from mojo.extensions    import ExtensionBundle, setExtensionDefault
from mojo.events        import BaseEventTool#, getActiveEventTool
from mojo.roboFont      import CurrentFont, AllFonts
from mojo.UI            import UpdateCurrentGlyphView
from lib.tools.defaults import getDefault, setDefault
from robofab.interface.all.dialogs import Message as FabMessage
from AppKit import NSColor, NSBezierPath, NSFontAttributeName, NSFont,\
                   NSForegroundColorAttributeName, NSAttributedString,\
			 NSShadow, NSGraphicsContext
import math

# reloaded in main.py
from models.TTHTool import uniqueInstance as tthTool
# reloaded below
from commons import helperFunctions
from drawing import textRenderer, geom, utilities as DR
from views import popOvers

reload(helperFunctions)
reload(textRenderer)
reload(popOvers)
reload(geom)
reload(DR)

toolbarIcon = ExtensionBundle("TTH").get("toolbarIcon")

arrowColor        = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .25, .5, 1)
blackColor        = NSColor.blackColor()
centerpixelsColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.5)
deltaColor        = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .5, 0, 1)
doublinkColor     = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .25, 1, 1)
finalDeltaColor   = NSColor.colorWithCalibratedRed_green_blue_alpha_(.73, .3, .8, 1)
gridColor         = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.1)
interpolateColor  = NSColor.colorWithCalibratedRed_green_blue_alpha_(.25, .8, 0, 1)
linkColor         = NSColor.colorWithCalibratedRed_green_blue_alpha_(.5, 0, 0, 1)
stemColor         = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .8, 0, 1)
whiteColor        = NSColor.whiteColor()
zoneColor         = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .7, .2, .2)
zoneColorLabel    = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .7, .2, 1)

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

		# Stores the current popover panel when one is opened
		self.currentPopover = None

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
		#print "[TTH RF EVENT] Font resign current", font.fileName

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
		fm = tthTool.getFontModel()
		if fm is not None:
			fm.createPreviewInGlyphWindowIfNeeded()

	def glyphWindowWillClose(self, window):
		'''Destroy the previewInGlyphWindow'''
		fm = tthTool.getFontModel()
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

		g, fm = tthTool.getRGAndFontModel()

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
		self.drawCommands(scale)

	def mouseDown(self, point, clickCount):
		'''This function is called by RF at mouse Down'''
		self.mouseDownFontModel = tthTool.getFontModel()

	def mouseUp(self, point):
		'''This function is called by RF at mouse Up'''
		# Handle click in PIGW
		if self.mouseDownFontModel != None:
			pigw = self.mouseDownFontModel.previewInGlyphWindow
			if pigw != None: pigw.handleClick()
			self.mouseDownFontModel = None

		if self.currentPopover != None:
			self.currentPopover.close()
		# Has we clicked on a command label?
		gm, fm = tthTool.getGlyphAndFontModel()
		cmd = gm.commandClicked(point)
		if cmd != None:
			popOvers.openForCommand(cmd, point)
		
# - - - - - - - - - - - - - - - - - - - - - - - - MANAGING POPOVERS

	def popoverOpened(self, sender):
		#print "Current:", self.currentPopover, "-->", sender.controller
		self.currentPopover = sender.controller

	def popoverClosed(self, sender):
		closing = sender.controller
		#print "Current:", self.currentPopover, "-->",
		if self.currentPopover is closing:
			self.currentPopover = None
			#self.commandClicked = None
			#print "None."
		else:
			pass
			#print "stays the same."

# - - - - - - - - - - - - - - - - - - - - - - - - WHEN THE PPEM SIZE CHANGES

	def sizeHasChanged(self):
		'''This function tells the RFEventTool that the PPEM preview size
		has changed'''
		self.cachedPathes = {'grid':None, 'centers':None}

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
			upm = -fontModel.UPM
			upm2 = -2*upm
			pos = - int(upm/pitch) * pitch
			maxi = -2 * pos
			while pos < maxi:
				path.moveToPoint_((pos, upm))
				path.lineToPoint_((pos, upm2))
				path.moveToPoint_((upm, pos))
				path.lineToPoint_((upm2, pos))
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
			(width, height) = DR.drawTextAtPoint(scale, zoneName, geom.Point(-100*scale, y_start+y_end/2),\
					whiteColor, zoneColorLabel, self.getNSView(), False)

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
					DR.drawLozengeAtPoint(scale, 4, end_x, end_y, deltaColor)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - DRAWING HINTING COMMANDS

	def computeOffMiddlePoint(self, scale, pos1, pos2):
		#diff = (scale / 25.0) * (pos2 - pos1).rotateCCW()
		diff = (1.0 / 25.0) * (pos2 - pos1).rotateCCW()
		mid  = 0.5*(pos1 + pos2)
		return mid + diff

	def drawSingleEndedArrow(self, cmd, scale, gm, color):
		pos1 = gm.positionForPointName(cmd['point1'])
		pos2 = gm.positionForPointName(cmd['point2'])
		offCurve = self.computeOffMiddlePoint(scale, pos1, pos2)

		pathArrow, anchor = DR.makeArrowPathAndAnchor(scale, 10, offCurve-pos2, pos2)

		path = NSBezierPath.bezierPath()
		path.moveToPoint_(pos1)
		path.curveToPoint_controlPoint1_controlPoint2_(anchor, offCurve, offCurve)

		color.set()
		path.setLineWidth_(scale)
		pathArrow.fill()
		path.stroke()
		return offCurve

	def drawDoubleEndedArrow(self, scale, active, iColor, pos1, pos2):
		if active:
			color = iColor
		else:
			color = DR.kInactiveColor

		offCurve = self.computeOffMiddlePoint(scale, pos1, pos2)

		arrowPath, startAnchor = DR.makeArrowPathAndAnchor(scale, 10, offCurve-pos1, pos1)
		arrowPath, endAnchor   = DR.makeArrowPathAndAnchor(scale, 10, offCurve-pos2, pos2, arrowPath)

		path = NSBezierPath.bezierPath()
		path.moveToPoint_(startAnchor)
		path.curveToPoint_controlPoint1_controlPoint2_(endAnchor, offCurve, offCurve)

		color.set()
		path.setLineWidth_(scale)
		arrowPath.fill()
		path.stroke()
		return offCurve

	def getCommandAlignLabel(self, cmd):
		if 'align' in cmd:
			extension = cmd['align']
			if tthTool.selectedAxis == 'Y':
				if extension == 'right': return 'top'
				elif extension == 'left': return 'bottom'
			if extension == 'round': return 'closest' # FIXME: ?????
			return extension
		else:
			return ''

	def drawDeltaDragging(self, cmd, scale, gm, cursorPoint, pitch):
		point  = gm.positionForPointName(cmd['point'])
		if tthTool.selectedAxis == 'X':
			idx = 0
			unit = geom.Point(1.0,0.0)
		else:
			idx = 1
			unit = geom.Point(0.0,1.0)
		value = int((cursorPoint[idx]-point[idx])*8.0/pitch)
		value = min(8, max(-8, value))
		end = point + value/8.0 * unit
		# FIXME: should pass 'value' directly as argument and
		# call changeDeltaOffset in the caller
		#if value != 0:
		#	self.changeDeltaOffset(value_x)
		path = NSBezierPath.bezierPath()
		path.moveToPoint_(point)
		path.lineToPoint_(end)
		color.set()
		path.setLineWidth_(scale)
		path.stroke()
		DR.drawLozengeAtPoint(scale, 4, end.x, end.y, color)

	def drawAlign(self, gm, cmd, scale, direction):
		color = arrowColor
		if cmd['active'] == 'false':
			color = DR.kInactiveColor
		pos = gm.positionForPointName(cmd['point'])
		DR.drawArrowAtPoint(scale, 10, direction, pos, color)
		DR.drawArrowAtPoint(scale, 10, direction.opposite(), pos, color)
		if 'align' in cmd:
			text = 'A_' + self.getCommandAlignLabel(cmd)
		elif cmd['code'] == 'alignt' or cmd['code'] == 'alignb':
			text = 'A_' + cmd['zone']
		if cmd['code'] == 'alignt':
			labelPos = pos + scale * geom.Point(10,+20)
		else:
			labelPos = pos + scale * geom.Point(10,-20)
		active = helperFunctions.getOrPutDefault(cmd, 'active', 'true') == 'true'
		labelSize = geom.makePointForPair(DR.drawTextAtPoint(scale, text, labelPos,\
				whiteColor, arrowColor, self.getNSView(), active))
		cmd['labelPosSize'] = (labelPos, labelSize)

	def drawDoubleLink(self, cmd, scale, gm):
		active = helperFunctions.getOrPutDefault(cmd, 'active', 'true') == 'true'
		pos1 = gm.positionForPointName(cmd['point1'])
		pos2 = gm.positionForPointName(cmd['point2'])
		offCurve = self.drawDoubleEndedArrow(scale, active, doublinkColor, pos1, pos2)
		# Compute label text
		stemName = c['stem']
		isRound = helperFunctions.getOrDefault(cmd, 'round', 'false') == 'true'
		if isRound:
			if stemName != None: text = 'D_' + stemName
			else: text = 'R'
		elif stemName != None:
			text = 'D_' + stemName
		else:
			text = 'D'
		labelSize = DR.drawTextAtPoint(scale, text, offCurve, whiteColor, doublinkColor,\
				self.getNSView(), active)
		cmd['labelPosSize'] = (offCurve, labelSize)

	def drawLink(self, cmd, scale, gm):
		active = helperFunctions.getOrPutDefault(cmd, 'active', 'true') == 'true'
		if active:
			color = linkColor
		else:
			color = DR.kInactiveColor
		offCurve = self.drawSingleEndedArrow(cmd, scale, gm, color)

		Y = (tthTool.selectedAxis == 'Y')
		extension = self.getCommandAlignLabel(cmd)
		stemName = helperFunctions.getOrNone(cmd, 'stem')
		textColor = whiteColor
		isRound = helperFunctions.getOrDefault(cmd, 'round', 'false') == 'true'
		if isRound:
			if stemName == None and extension != '': text = 'R_' + extension
			elif stemName != None:                   text = 'R_' + stemName
			else:                                    text = 'R'
		else:
			text = 'S'
			if stemName == None and extension != '': text = 'S_' + extension
			elif stemName != None:
				text = 'S_' + stemName
				textColor = blackColor
				if active:
					color = stemColor
				else:
					color = inactiveColor
		labelSize = DR.drawTextAtPoint(scale, text, offCurve, textColor, color, self.getNSView(), active)
		cmd['labelPosSize'] = (offCurve, labelSize)

	def drawInterpolate(self, cmd, scale, gm):
		active = helperFunctions.getOrPutDefault(cmd, 'active', 'true') == 'true'
		pos  = gm.positionForPointName(cmd['point'])
		pos1 = gm.positionForPointName(cmd['point1'])
		pos2 = gm.positionForPointName(cmd['point2'])
		offCurve = self.drawDoubleEndedArrow(scale, active, interpolateColor, pos1, pos)
		offCurve = self.drawDoubleEndedArrow(scale, active, interpolateColor, pos, pos2)
		extension = self.getCommandAlignLabel(cmd)
		if extension == '':
			text = 'I'
		else:
			text = 'I_' + extension
		# square root takes the label a bit further when we zoom in
		pos = pos + math.sqrt(scale)*10.0*geom.Point(1.0, -1.0)
		labelSize = DR.drawTextAtPoint(scale, text, pos, whiteColor, interpolateColor, self.getNSView(), active)
		cmd['labelPosSize'] = (pos, labelSize)

	def drawDelta(self, cmd, scale, gm, pitch):
		pos  = gm.positionForPointName(cmd['point'])
		active = helperFunctions.getOrPutDefault(cmd, 'active', 'true') == 'true'
		cmd_code = cmd['code']
		if active:
			if cmd_code in ['mdeltah', 'mdeltav']:
				color = deltaColor
			else: # final delta
				color = finalDeltaColor
		else:
			color = inactiveColor
		if cmd_code[-1] == 'h':
			value = (int(cmd['delta']), 0)
		else:
			value = (0, int(cmd['delta']))

		endPt = pos + (1.0/8.0) * pitch * geom.makePointForPair(value)
		path = NSBezierPath.bezierPath()
		path.moveToPoint_(pos)
		path.lineToPoint_(endPt)

		color.set()
		path.setLineWidth_(scale)
		path.stroke()
		DR.drawLozengeAtPoint(scale, 4, endPt.x, endPt.y, color)

		value = cmd['delta']
		if cmd_code[0] == 'm':
			text = 'delta_M:'
		else:
			text = 'delta_F:'
		text = text + value

		if cmd['code'][-1] == 'v' and int(value) < 0:
			labelPos = pos + 10*scale*geom.Point(-1,+1)
		else:
			labelPos = pos + 10*scale*geom.Point(-1,-1)
		labelSize = DR.drawTextAtPoint(scale, text, labelPos, whiteColor, color, self.getNSView(), active)
		cmd['labelPosSize'] = (pos, labelSize)

	def drawCommands(self, scale):
		gm, fm = tthTool.getGlyphAndFontModel()
		for c in gm.hintingCommands:
			cmd_code = helperFunctions.getOrNone(c, 'code')
			X = (tthTool.selectedAxis == 'X')
			Y = not X
			if Y and cmd_code in ['alignv', 'alignt', 'alignb']:
				self.drawAlign(gm, c, scale, geom.Point(0,1))
			elif X and cmd_code == 'alignh':
				self.drawAlign(gm, c, scale, geom.Point(1,0))
			elif (X and cmd_code == 'doubleh') or (Y and cmd_code == 'doublev'):
				self.drawDoubleLink(c, scale, gm)
			elif (X and cmd_code == 'singleh') or (Y and cmd_code == 'singlev'):
				self.drawLink(c, scale, gm)
			elif (X and cmd_code == 'interpolateh') or (Y and cmd_code == 'interpolatev'):
				self.drawInterpolate(c, scale, gm)
			elif (X and cmd_code in ['mdeltah', 'fdeltah']) or (Y and cmd_code in ['mdeltav', 'fdeltav']):
				if int(c['ppm1']) <= tthTool.PPM_Size <= int(c['ppm2']):
					self.drawDelta(c, scale, gm, fm.getPitch())

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if tthTool._printLoadings: print "RFEventTool, ",
