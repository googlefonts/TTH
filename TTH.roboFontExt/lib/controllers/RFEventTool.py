from mojo.extensions    import ExtensionBundle, setExtensionDefault
from mojo.events        import BaseEventTool
from mojo.roboFont      import CurrentFont, AllFonts
from mojo.UI            import UpdateCurrentGlyphView
from lib.tools.defaults import getDefault, setDefault
from lib.doodleMenus import BaseMenu
from robofab.interface.all.dialogs import Message as FabMessage
from AppKit import NSColor, NSBezierPath, NSFontAttributeName, NSFont,\
                   NSForegroundColorAttributeName, NSAttributedString,\
			 NSShadow, NSGraphicsContext, NSMenu, NSMenuItem
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

blackColor        = NSColor.blackColor()
centerpixelsColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.5)
gridColor         = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.1)
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

		# Stores the current popover panel when one is opened
		self.currentPopover = None

		# Stores the click position during mouseDown event
		self.mouseDownClickPos = None

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

		self.sizeHasChanged()
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

		tool = tthTool.selectedHintingTool
		simpleDrawing = tool and tool.dragging

		if tthTool.showGrid == 1 and ((not simpleDrawing) or 'Delta' in tool.name):
			self.drawGrid(scale, pitch, tthTool.gridOpacity, fm)

		if simpleDrawing: return

		self.drawZones(scale, pitch, fm)

		tr = fm.textRenderer
		tr.set_cur_size(tthTool.PPM_Size)
		tr.set_pen((0, 0))

		if tthTool.showBitmap == 1 and tr != None:
			tr.render_named_glyph_list([g.name], pitch, tthTool.bitmapOpacity)

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
		tool = tthTool.selectedHintingTool
		if tool and tool.dragging:
			self.drawCommands(scale, True)
			tool.draw(scale)
		else:
			self.drawCommands(scale, False)

	def mouseDown(self, point, clickCount):
		'''This function is called by RF at mouse Down'''
		self.mouseDownClickPos = geom.makePoint(point)
		tool = tthTool.selectedHintingTool
		if tool: tool.mouseDown(point, clickCount)

	def mouseMoved(self, point):
		'''This function is called by RF at mouse moved (while not clicked)'''
		self.mouseDragged(point, geom.Point(0,0))
		self.refreshView()

	def mouseDragged(self, point, delta):
		'''This function is called by RF at mouse dragged (while left-clicked)'''
		tool = tthTool.selectedHintingTool
		if tool is None: return
		if not tool.dragging: return
		tool.mouseDragged(point)

	def mouseUp(self, point):
		'''This function is called by RF at mouse Up'''
		gm, fm = tthTool.getGlyphAndFontModel()
		upPoint = geom.makePoint(point)
		realClick = (upPoint - self.mouseDownClickPos).squaredLength() <= 25.0
		# Handle click in PIGW
		if fm != None and realClick:
			pigw = fm.previewInGlyphWindow
			if pigw != None: pigw.handleClick()

		if self.currentPopover != None:
			self.currentPopover.close()
		tool = tthTool.selectedHintingTool
		if tool != None:
			tool.mouseUp(point)

	def rightMouseDown(self, point, clickCount):
		gm = tthTool.getGlyphModel()
		separator = NSMenuItem.separatorItem()
		items = []
		menuAction = NSMenu.alloc().init()
		menuController = BaseMenu()
		src = gm.pointClicked(geom.makePoint(point))
		if src[0] == None:
			items.append(('Clear All Program', gm.deleteAllCommands))
			items.append(('Clear X Commands', gm.deleteXCommands))
			items.append(('Clear Y Commands', gm.deleteYCommands))
			items.append(('Clear All Deltas', gm.deleteAllDeltas))
			items.append(separator)
			items.append(('Deactivate All Commands', gm.deactivateAllCommands))
			items.append(('Activate All Commands', gm.activateAllCommands))
			menuController.buildAdditionContectualMenuItems(menuAction, items)
		else:
			return
			items.append(('Delete Command', self.deleteCommandCallback))

			if clickedCommand['code'] in ['doubleh', 'doublev']:
				if clickedCommand['code'] == 'doubleh':
					items.append(('Convert to Single Link', self.convertToSinglehCallback))
				else:
					items.append(('Convert to Single Link', self.convertToSinglevCallback))

			if clickedCommand['code'] in ['singleh', 'singlev']:
				items.append(('Reverse Direction', self.reverseSingleCallback))
				if clickedCommand['code'] == 'singleh':
					items.append(('Convert to Double Link', self.convertToDoublehCallback))
				else:
					items.append(('Convert to Double Link', self.convertToDoublevCallback))
			menuController.buildAdditionContectualMenuItems(menuAction, items)
			menuAction.insertItem_atIndex_(separator, 1)
		NSMenu.popUpContextMenu_withEvent_forView_(menuAction, self.getCurrentEvent(), self.getNSView())

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
			upm  = fontModel.UPM
			upm2 = 2.0 * upm
			pos  = -int(upm/pitch) * pitch
			upm  = -upm
			while pos < upm2:
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
			labelPos = geom.Point(-100*scale, y_start+y_end/2)
			labelSize = geom.Point(*DR.drawTextAtPoint(scale, zoneName, labelPos,\
					whiteColor, zoneColorLabel, self.getNSView(), active=True))

			# we store the label position and size directly in the zone's dictionary
			zone['labelPosSize'] = (labelPos, labelSize)

			point = (-100*scale, y_start+y_end/2)
			if 'delta' in zone:
				for deltaPPM, deltaValue in zone['delta'].iteritems():
					if int(deltaPPM) != tthTool.PPM_Size or deltaValue == 0:
						continue
					path = NSBezierPath.bezierPath()
					path.moveToPoint_(labelPos)
					endPos = labelPos + geom.Point(0.0, (deltaValue/8.0) * pitch)
					path.lineToPoint_(endPos)

					deltaColor.set()
					path.setLineWidth_(scale)
					path.stroke()
					DR.drawLozengeAtPoint(scale, 4, endPos.x, endPos.y, deltaColor)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - DRAWING HINTING COMMANDS

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

	def drawAlign(self, gm, cmd, scale, direction, simple):
		color = DR.kArrowColor
		if cmd['active'] == 'false':
			color = DR.kInactiveColor
		pos = gm.positionForPointName(cmd['point'])
		DR.drawArrowAtPoint(scale, 10, direction, pos, color)
		DR.drawArrowAtPoint(scale, 10, direction.opposite(), pos, color)
		if simple: return
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
				whiteColor, DR.kArrowColor, self.getNSView(), active))
		cmd['labelPosSize'] = (labelPos, labelSize)

	def drawDoubleLink(self, cmd, scale, gm, simple):
		active = helperFunctions.getOrPutDefault(cmd, 'active', 'true') == 'true'
		pos1 = gm.positionForPointName(cmd['point1'])
		pos2 = gm.positionForPointName(cmd['point2'])
		offCurve = DR.drawDoubleArrow(scale, pos1, pos2, active, kDoublinkColor)
		if simple: return
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
		labelSize = DR.drawTextAtPoint(scale, text, offCurve, whiteColor, kDoublinkColor,\
				self.getNSView(), active)
		cmd['labelPosSize'] = (offCurve, labelSize)

	def drawLink(self, cmd, scale, gm, simple):
		active = helperFunctions.getOrPutDefault(cmd, 'active', 'true') == 'true'
		if active:
			color = DR.kLinkColor
		else:
			color = DR.kInactiveColor
		pos1 = gm.positionForPointName(cmd['point1'])
		pos2 = gm.positionForPointName(cmd['point2'])
		offCurve = DR.drawSingleArrow(scale, pos1, pos2, color, 10)
		if simple: return

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
					color = DR.kInactiveColor
		labelSize = DR.drawTextAtPoint(scale, text, offCurve, textColor, color, self.getNSView(), active)
		cmd['labelPosSize'] = (offCurve, labelSize)

	def drawInterpolate(self, cmd, scale, gm, simple):
		active = helperFunctions.getOrPutDefault(cmd, 'active', 'true') == 'true'
		pos  = gm.positionForPointName(cmd['point'])
		pos1 = gm.positionForPointName(cmd['point1'])
		pos2 = gm.positionForPointName(cmd['point2'])
		offCurve = DR.drawDoubleArrow(scale, pos1, pos, active, DR.kInterpolateColor)
		offCurve = DR.drawDoubleArrow(scale, pos, pos2, active, DR.kInterpolateColor)
		if simple: return
		extension = self.getCommandAlignLabel(cmd)
		if extension == '':
			text = 'I'
		else:
			text = 'I_' + extension
		# square root takes the label a bit further when we zoom in
		pos = pos + math.sqrt(scale)*10.0*geom.Point(1.0, -1.0)
		labelSize = DR.drawTextAtPoint(scale, text, pos, whiteColor, DR.kInterpolateColor, self.getNSView(), active)
		cmd['labelPosSize'] = (pos, labelSize)

	def drawDelta(self, cmd, scale, gm, pitch, simple):
		pos  = gm.positionForPointName(cmd['point'])
		active = helperFunctions.getOrPutDefault(cmd, 'active', 'true') == 'true'
		cmd_code = cmd['code']
		if active:
			if cmd_code in ['mdeltah', 'mdeltav']:
				color = DR.kDeltaColor
			else: # final delta
				color = DR.kFinalDeltaColor
		else:
			color = DR.kInactiveColor
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
		if simple: return

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
		cmd['labelPosSize'] = (labelPos, labelSize)

	def drawCommands(self, scale, simple):
		gm, fm = tthTool.getGlyphAndFontModel()
		for c in gm.hintingCommands:
			cmd_code = helperFunctions.getOrNone(c, 'code')
			X = (tthTool.selectedAxis == 'X')
			Y = not X
			if Y and cmd_code in ['alignv', 'alignt', 'alignb']:
				self.drawAlign(gm, c, scale, geom.Point(0,1), simple)
			elif X and cmd_code == 'alignh':
				self.drawAlign(gm, c, scale, geom.Point(1,0), simple)
			elif (X and cmd_code == 'doubleh') or (Y and cmd_code == 'doublev'):
				self.drawDoubleLink(c, scale, gm, simple)
			elif (X and cmd_code == 'singleh') or (Y and cmd_code == 'singlev'):
				self.drawLink(c, scale, gm, simple)
			elif (X and cmd_code == 'interpolateh') or (Y and cmd_code == 'interpolatev'):
				self.drawInterpolate(c, scale, gm, simple)
			elif (X and cmd_code in ['mdeltah', 'fdeltah']) or (Y and cmd_code in ['mdeltav', 'fdeltav']):
				if int(c['ppm1']) <= tthTool.PPM_Size <= int(c['ppm2']):
					self.drawDelta(c, scale, gm, fm.getPitch(), simple)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if tthTool._printLoadings: print "RFEventTool, ",
