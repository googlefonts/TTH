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

reload(helperFunctions)
reload(textRenderer)
reload(geom)
reload(DR)

toolbarIcon = ExtensionBundle("TTH").get("toolbarIcon")

arrowColor        = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .25, .5, 1)
centerpixelsColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.5)
deltaColor        = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .5, 0, 1)
doublinkColor     = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .25, 1, 1)
#finalDeltaColor   = NSColor.colorWithCalibratedRed_green_blue_alpha_(.73, .3, .8, 1)
gridColor         = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.1)
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
		#print 'glyph has',len(gm.hintingCommands),'hinting commands'
		self.drawCommands(scale, fm, gm)

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
					r = 4
					DR.drawLozengeAtPoint(r*scale, scale, end_x, end_y, deltaColor)

	def drawAlign(self, gm, cmd, scale, direction):
		color = arrowColor
		if cmd['active'] == 'false':
			color = DR.kInactiveColor
		pos = gm.positionForPointName(cmd['point'])
		DR.drawArrowAtPoint(scale, 10, direction, pos, color)
		DR.drawArrowAtPoint(scale, 10, direction.opposite(), pos, color)

		if 'align' in cmd:
			extension = cmd['align']
			if tthTool.selectedAxis == 'Y':
				if extension == 'right':
					extension = 'top'
				elif extension == 'left':
					extension = 'bottom'
			if extension == 'round':
				extension = 'closest' # FIXME: ?????
			text = 'A_' + extension
		elif cmd['code'] == 'alignt' or cmd['code'] == 'alignb':
			text = 'A_' + cmd['zone']

		if cmd['code'] == 'alignt':
			labelPos = pos + scale * geom.Point(10,+20)
		else: 
			labelPos = pos + scale * geom.Point(10,-20)
		active = helperFunctions.getOrPutDefault(cmd, 'active', 'true') == 'true'
		labelSize = geom.makePointForPair(DR.drawTextAtPoint(scale, text, labelPos,\
				whiteColor, arrowColor, self.getNSView(), active))
		cmd['labelPos'] = (labelPos, labelSize)

	def drawDoubleLink(self, cmd, scale):
		pos1 = gm.positionForPointName(cmd['point1'])
		pos2 = gm.positionForPointName(cmd['point2'])
		#self.drawDoubleLinkDragging(scale, startPoint, endPoint, cmdIndex)
		mid  = 0.5*(pos1 + pos2)
		diff = (scale*1000.0/fm.UPM/25.0)*(pos2 - pos1).rotateCCW()
		offCurve = mid + diff
		# Comput label text
		text = 'D'
		stemName = c['stem']
		if 'round' in cmd:
			if cmd['round'] == 'true':
				if stemName != None:
					text = 'D_' + stemName
				else:
					text = 'R'
		elif stemName != None:
			text = 'D_' + stemName
		active = helperFunctions.getOrPutDefault(cmd, 'active', 'true') == 'true'
		labelSize = DR.drawTextAtPoint(scale, text, offCurve, whiteColor, doublinkColor,\
				self.getNSView(), active)
		# compute x, y
		cmd['labelPos'] = (offCurve, labelSize)

	def drawCommands(self, scale, fm, gm):
		for c in gm.hintingCommands:
			# search elements only once
			cmd_code = helperFunctions.getOrNone(c, 'code')
			#cmd_pt   = helperFunctions.getOrNone(c, 'point')
			#cmd_pt1  = helperFunctions.getOrNone(c, 'point1')
			#cmd_pt2  = helperFunctions.getOrNone(c, 'point2')
			#cmd_stem = helperFunctions.getOrNone(c, 'stem')

			X = (tthTool.selectedAxis == 'X')
			Y = not X
			
			if Y and cmd_code in ['alignv', 'alignt', 'alignb']:
				self.drawAlign(gm, c, scale, geom.Point(0,1))
			elif X and cmd_code == 'alignh':
				self.drawAlign(gm, c, scale, geom.Point(1,0))

			elif X and cmd_code == 'doubleh':
				self.drawDoubleLink(c, scale, fm)
			elif Y and cmd_code == 'doublev':
				self.drawDoubleLink(c, scale, fm)
			#elif X and cmd_code == 'singleh':
			#	self.drawLink(scale, startPoint, endPoint, cmd_stem, cmdIndex)
			#elif Y and cmd_code == 'singlev':
			#	self.drawLink(scale, startPoint, endPoint, cmd_stem, cmdIndex)

			#elif cmd_code in ['interpolateh', 'interpolatev']:

			#	if cmd_pt == 'lsb':
			#		middlePoint = (0, 0)
			#	elif cmd_pt== 'rsb':
			#		middlePoint = (0, g.width)
			#	else:
			#		middlePoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt]]

			#	if cmd_pt1 == 'lsb':
			#		startPoint = (0, 0)
			#	elif cmd_pt1== 'rsb':
			#		startPoint = (0, g.width)
			#	else:
			#		startPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt1]]

			#	if cmd_pt2 == 'lsb':
			#		endPoint = (0, 0)
			#	elif cmd_pt2 == 'rsb':
			#		endPoint = (g.width, 0)
			#	else:
			#		endPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt2]]

			#	if tthTool.selectedAxis == 'X' and cmd_code == 'interpolateh':
			#		self.drawInterpolate(scale, startPoint, endPoint, middlePoint, cmdIndex)
			#	elif tthTool.selectedAxis == 'Y' and cmd_code == 'interpolatev':
			#		self.drawInterpolate(scale, startPoint, endPoint, middlePoint, cmdIndex)

			#elif cmd_code in ['mdeltah', 'mdeltav', 'fdeltah', 'fdeltav']:
			#	if cmd_code in ['mdeltah', 'mdeltav']:
			#		color = deltacolor
			#	else:
			#		color = finaldeltacolor
			#	if cmd_pt == 'lsb':
			#		point = (0, 0)
			#	elif cmd_pt== 'rsb':
			#		point = (g.width, 0)
			#	else:
			#		point = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt]]

			#	if cmd_code[-1] == 'h':
			#		value = (int(c['delta']), 0)
			#	elif cmd_code[-1] == 'v':
			#		value = (0, int(c['delta']))
			#	else:
			#		value = 0

			#	if int(tthTool.PPM_Size) in range(int(c['ppm1']), int(c['ppm2'])+1, 1):
			#		if tthTool.selectedAxis == 'X' and cmd_code in ['mdeltah', 'fdeltah']:
			#			self.drawDelta(scale, point, value, cmdIndex, color)
			#		elif tthTool.selectedAxis == 'Y' and cmd_code in ['mdeltav', 'fdeltav']:
			#			self.drawDelta(scale, point, value, cmdIndex, color)
    

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

	def sizeHasChanged(self):
		'''This function tells the RFEventTool that the PPEM preview size
		has changed'''
		self.cachedPathes = {'grid':None, 'centers':None}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if tthTool._printLoadings: print "RFEventTool, ",
