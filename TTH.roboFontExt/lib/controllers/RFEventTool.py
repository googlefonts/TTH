#coding=utf-8
from mojo.extensions    import ExtensionBundle, setExtensionDefault
from mojo.events        import BaseEventTool,addObserver, removeObserver
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
from commons import helperFunctions, HotKeys
from drawing import textRenderer, geom, utilities as DR
# reloaded elsewhere
from models import TTHGlyph
from ps import parametric
from mojo.drawingTools import drawGlyph, save, restore, stroke, fill, strokeWidth, fontSize, text

reload(helperFunctions)
reload(textRenderer)
reload(geom)
reload(DR)
reload(parametric)
reload(TTHGlyph)

kTTProgramKey = 'com.fontlab.ttprogram'

toolbarIcon = ExtensionBundle("TTH").get("toolbarIcon")

centerpixelsColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.5)
gridColor         = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.1)
stemColor         = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .8, 0, 1)
whiteColor        = NSColor.whiteColor()
zoneColor         = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .7, .2, .2)
zoneColorLabel    = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .7, .2, 1)
outlinecolor 	  = NSColor.colorWithCalibratedRed_green_blue_alpha_(.4, .8, 1, 1)

class TTH_RF_EventTool(BaseEventTool):

	def __init__(self):
		super(TTH_RF_EventTool, self).__init__()

		# Remembers the cruve drawing preference of RF prior to forcing
		# quadratic-style
		self.originalCurveDrawingPref = None

		# Precomputed NSBezierPath'es
		self.cachedPathes = {'grid':None, 'centers':None}

		# The scale of the glyph window drawing from the last draw
		self.glyphWindowScale = 1.0

		# The 'radius' of pixel centers from the last 'draw()' call.
		# Used in drawCenterPixel()
		self.cachedCenterRadius = None

		# Set to True when the current font document is about to be closed.
		self.popOverIsOpened = False

		# Stores the current popover panel when one is opened
		self.currentPopover = None

		# Stores the click position during mouseDown event
		self.mouseDownClickPos = None

		# Storage to save the current tool name when CONTROL-clicking
		self.nonControlKeyToolName = None

	def __del__(self):
		pass

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

	def didUndo(self, font):
		gm, fm = tthTool.getGlyphAndFontModel()
		gm.loadFromUFO(fm)
		gm.updateGlyphProgram(fm)

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
		 	#FabMessage("This is not a Quadratic UFO,\nyou must convert it before.")
		 	# save the original curve drawing mode
			self.originalCurveDrawingPref = getDefault('drawingSegmentType')
			# and set cubic mode
			if self.originalCurveDrawingPref != 'curve':
				setDefault('drawingSegmentType', 'curve')
		else:
			# save the original curve drawing mode
			self.originalCurveDrawingPref = getDefault('drawingSegmentType')
			# and set quadratic mode
			if self.originalCurveDrawingPref != 'qcurve':
				setDefault('drawingSegmentType', 'qcurve')
		self.sizeHasChanged()
		tthTool.becomeActive()
		addObserver(self, "drawHintedGlyphsInFontOverview", "glyphCollectionDraw")
		addObserver(self, "TTHMenu", "fontOverviewAdditionContextualMenuItems")

	def becomeInactive(self):
		'''This function is called by RF when another tool button is
		pressed'''
		tthTool.becomeInactive()

		# restore the original curve drawing mode
		setDefault('drawingSegmentType', self.originalCurveDrawingPref)
		removeObserver(self, "glyphCollectionDraw")
		removeObserver(self, "fontOverviewAdditionContextualMenuItems")

	def viewDidChangeGlyph(self):
		'''This function is called by RF when the Glyph View shows another
		glyph'''
		#print "[TTH RF EVENT] View did change glyph"
		if tthTool.parametricPreviewPanel != None:
			tthTool.parametricPreviewPanel.updateDisplay()
		tthTool.showOrHide()
		tthTool.updatePartialFontIfNeeded()
		tthTool.updateDisplay()

	def currentGlyphChanged(self):
		'''This function is called by RF when the Current Glyph changed'''
		#print "[TTH RF EVENT] Current glyph changed"
		if tthTool.parametricPreviewPanel != None:
			tthTool.parametricPreviewPanel.updateDisplay()
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
		#print "[TTH RF EVENT] Font became current", font.fileName
		tthTool.showOrHide()
		tthTool.currentFontHasChanged(font)

	def fontDidOpen(self, font):
		'''This function is called by RF when a new Font did Open'''
		tthTool.showOrHide()
		tthTool.currentFontHasChanged(font)

	def glyphWindowWillOpen(self, window):
		pass

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

	def TTHMenu(self, notification):
		menus = notification["additionContextualMenuItems"]
		fm = tthTool.getFontModel()
		names = fm.f.selection
		gmList = []
		for name in names:
			g = fm.f[name]
			gm = fm.glyphModelForGlyph(g)
			gmList.append(gm)

		menus.append(['Apply Parametric For Selection', TTHGlyph.ApplyParametricForMultipleGlyphs(gmList, fm)])

	def drawHintedGlyphsInFontOverview(self, notification):
		self.drawKerningview = notification["view"]
		allGlyphs = self.drawKerningview._glyphs
		for g in allGlyphs:
			rect = self.drawKerningview.getGlyphRect(g)
			if not rect: continue
			x, y, w, h = rect
			if kTTProgramKey in g.lib:
				ttprogram = g.lib[kTTProgramKey].data
				if len(ttprogram) > 13:
					fill(0, .7, .2, 1)
					fontSize(w*.14)
					text(u'H', (x+w*.75, y+h*.760))

	def drawParametricGlyph(self, scale, thickness, outline=False):
		gm, fm = tthTool.getGlyphAndFontModel()
		if gm == None or helperFunctions.fontIsQuadratic(fm.f): return
		pGlyph = gm._pg
		if pGlyph == None:
			parametric.processParametric(fm, gm)
			pGlyph = gm._pg
		save()
		if outline:
			stroke(0.2, .8, .8, 1)
			fill(None)
			strokeWidth(scale*thickness)
		else:
			fill(0.2, .8, .8, .5)

		drawGlyph(pGlyph)

		restore()

	def drawPreview(self, scale):
		self.drawParametricGlyph(scale, tthTool.outlineThickness, outline=False)

	def drawBackground(self, scale):
		'''This function is called by RF whenever the Background of the
		glyph Window needs redraw'''

		self.glyphWindowScale = scale

		if 0 == self.numberOfRectsToDraw(): return

		g, fm = tthTool.getRGAndFontModel()

		if fm is None: return

		# test if quadratic or cubic font
		fontIsQuad = helperFunctions.fontIsQuadratic(fm.f)

		# we do this here, because it fails to do it in `becomeActive` :-(
		# (The NSView's superview seems not ready at that time)
		if fm.createPreviewInGlyphWindowIfNeeded(self.getNSView()):
			self.refreshView()

		if g == None: return

		if fontIsQuad:
			pitch = fm.getPitch()

			tool = tthTool.selectedHintingTool
			simpleDrawing = tool and tool.dragging

			if tthTool.showGrid == 1 and ((not simpleDrawing) or 'Delta' in tool.name):
				self.drawGrid(scale, pitch, tthTool.gridOpacity, fm)

			DR.drawSideBearingsPointsOfGlyph(scale, 5, g)

			if simpleDrawing: return

			self.drawZones(scale, pitch, fm)

			tr = fm.textRenderer
			tr.set_cur_size(tthTool.PPM_Size)
			tr.set_pen((0, 0))

			if tr != None and tr.isOK():
				if tthTool.showBitmap == 1:
					tr.render_named_glyph_list([g.name], pitch, tthTool.bitmapOpacity)
				if tthTool.showOutline == 1:
					tr.drawOutlineOfName(scale, pitch, g.name, tthTool.outlineThickness)
					self.drawSideBearings(scale, pitch, g.name, fm)

			if tthTool.showCenterPixel == 1:
				self.drawCenterPixel(scale, pitch, tthTool.centerPixelSize)

			self.drawAscentDescent(scale, pitch, fm)
		
		else:
			tool = tthTool.selectedHintingTool
			simpleDrawing = tool and tool.dragging
			DR.drawSideBearingsPointsOfGlyph(scale, 5, g)
			if simpleDrawing: return
			if tthTool.showOutline == 1:
				self.drawParametricGlyph(scale, tthTool.outlineThickness, outline=True)
			self.drawZones(scale, None, fm)



	def draw(self, scale):
		'''This function is called by RF whenever the Foreground of the
		glyph Window needs redraw'''
		if 0 == self.numberOfRectsToDraw(): return

		g, fm = tthTool.getRGAndFontModel()
		if len(g.components) > 0:
			DR.drawComponentsPoints(scale, g, fm)

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
		if clickCount == 2:
			if tool: self.nonControlKeyToolName = tool.name
			tthTool.setTool('Selection')
			tool = tthTool.getTool('Selection')
		if tool: tool.mouseDown(point, clickCount, self.glyphWindowScale)

	def mouseMoved(self, point):
		'''This function is called by RF at mouse moved (while not clicked)'''
		if self.mouseDragged(point, geom.Point(0,0)):
			self.refreshView()

	def mouseDragged(self, point, delta):
		'''This function is called by RF at mouse dragged (while left-clicked)'''
		tool = tthTool.selectedHintingTool
		if tool is None: return False
		if not tool.dragging: return False
		tool.mouseDragged(point, self.glyphWindowScale)
		return True

	def mouseUp(self, point):
		'''This function is called by RF at mouse Up'''
		gm, fm = tthTool.getGlyphAndFontModel()
		upPoint = geom.makePoint(point)

		thresh = 5.0 * self.glyphWindowScale
		thresh = thresh * thresh
		realClick = (upPoint - self.mouseDownClickPos).squaredLength() <= thresh
		# Handle click in PIGW
		if fm != None and realClick:
			pigw = fm.previewInGlyphWindow
			if pigw != None: pigw.handleClick()

		if self.currentPopover != None:
			self.currentPopover.close()
		tool = tthTool.selectedHintingTool
		if tool != None:
			tool.mouseUp(point, self.glyphWindowScale)
		if self.nonControlKeyToolName != None:
			tthTool.setTool(self.nonControlKeyToolName)
			self.nonControlKeyToolName = None

	def rightMouseDown(self, point, clickCount):
		gm, fm = tthTool.getGlyphAndFontModel()
		separator = NSMenuItem.separatorItem()
		separator2 = NSMenuItem.separatorItem()
		separator3 = NSMenuItem.separatorItem()
		items = []
		menu = NSMenu.alloc().init()
		menuController = BaseMenu()
		cmd = gm.commandClicked(geom.makePoint(point))
		if cmd is None:
			items.append(('Clear All Program', gm.deleteAllCommands))
			items.append(('Clear X Commands', gm.deleteXCommands))
			items.append(('Clear Y Commands', gm.deleteYCommands))
			items.append(separator)
			items.append(('Clear All Deltas', gm.deleteAllDeltas))
			items.append(('Clear X Deltas', gm.deleteXDeltas))
			items.append(('Clear Y Deltas', gm.deleteYDeltas))
			items.append(separator2)
			items.append(('Deactivate All Commands', gm.deactivateAllCommands))
			items.append(('Activate All Commands', gm.activateAllCommands))
			items.append(separator3)
			items.append(('Apply Parametric', TTHGlyph.ApplyParametric(gm, fm)))
		else:
			items.append(('Delete Command', TTHGlyph.CommandRemover(gm, cmd)))
			code = cmd.get('code')
			if 'double' in code:
				items.append(('Convert to Single Link', TTHGlyph.CommandConverter(gm, cmd)))
			if 'single' in code:
				items.append(('Reverse Direction', TTHGlyph.CommandReverser(gm, cmd)))
				items.append(('Convert to Double Link', TTHGlyph.CommandConverter(gm, cmd)))
		if hasattr(menuController, 'buildAdditionContextualMenuItems'):
			menuController.buildAdditionContextualMenuItems(menu, items)
		else:
			menuController.buildAdditionContectualMenuItems(menu, items)
		if cmd != None:
			menu.insertItem_atIndex_(separator, 1)
		NSMenu.popUpContextMenu_withEvent_forView_(menu, self.getCurrentEvent(), self.getNSView())
# - - - - - - - - - - - - - - - - - - - - - - - - KEY EVENTS

	def keyUp(self, event):
		key = event.characters()
		mod = self.getModifiers()
		if mod['commandDown']: return
		if mod['optionDown']:  return
		if mod['controlDown']: return
		hot = HotKeys.gHotKeys.get(key, None)
		if hot is None: return
		tool = tthTool.selectedHintingTool
		if hot == HotKeys.kTTH_HotKey_Select_Align_Tool:
			if tool: tool.reset()
			tthTool.setTool('Align')
		elif hot == HotKeys.kTTH_HotKey_Select_Single_Link_Tool:
			if tool: tool.reset()
			tthTool.setTool('Single Link')
		elif hot == HotKeys.kTTH_HotKey_Select_Double_Link_Tool:
			if tool: tool.reset()
			tthTool.setTool('Double Link')
		elif hot == HotKeys.kTTH_HotKey_Select_Interpolate_Tool:
			if tool: tool.reset()
			tthTool.setTool('Interpolation')
		elif hot == HotKeys.kTTH_HotKey_Select_Middle_Delta_Tool:
			if tool: tool.reset()
			tthTool.setTool('Middle Delta')
		elif hot == HotKeys.kTTH_HotKey_Select_Final_Delta_Tool:
			if tool: tool.reset()
			tthTool.setTool('Final Delta')
		elif hot == HotKeys.kTTH_HotKey_Select_Selection_Tool:
			if tool: tool.reset()
			tthTool.setTool('Selection')
		elif hot == HotKeys.kTTH_HotKey_Switch_Show_Outline:
			tthTool.setShowOutline(not tthTool.showOutline)
			UpdateCurrentGlyphView()
		elif hot == HotKeys.kTTH_HotKey_Switch_Show_Bitmap:
			tthTool.setShowBitmap(not tthTool.showBitmap)
			UpdateCurrentGlyphView()
		elif hot == HotKeys.kTTH_HotKey_Switch_Show_Grid:
			tthTool.setShowGrid(not tthTool.showGrid)
			UpdateCurrentGlyphView()
		elif hot == HotKeys.kTTH_HotKey_Switch_Show_Center_Pixels:
			tthTool.setShowCenterPixels(not tthTool.showCenterPixel)
			UpdateCurrentGlyphView()
		elif hot == HotKeys.kTTH_HotKey_Change_Axis:
			if tthTool.selectedAxis == 'Y':
				tthTool.changeAxis('X')
			else:
				tthTool.changeAxis('Y')
			UpdateCurrentGlyphView()
		elif hot == HotKeys.kTTH_HotKey_Switch_Rounding:
			if tool != None:
				tool.switchRounding()
				tool.updateUI()
		elif hot == HotKeys.kTTH_HotKey_Change_Alignment:
			if tool != None:
				tool.changeAlignement()
				tool.updateUI()
		elif hot == HotKeys.kTTH_HotKey_Change_Size_Down:
			if tthTool.PPM_Size > 9:
				tthTool.changeSize(tthTool.PPM_Size-1)
		elif hot == HotKeys.kTTH_HotKey_Change_Size_Up:
			tthTool.changeSize(tthTool.PPM_Size+1)
		elif hot == HotKeys.kTTH_HotKey_Change_Preview_Mode:
			bitmapPreviewList = ['Monochrome', 'Grayscale', 'Subpixel']
			fm = tthTool.getFontModel()
			i = bitmapPreviewList.index(fm.bitmapPreviewMode)
			fm.bitmapPreviewMode = bitmapPreviewList[(i+1)%3]
			tthTool.updateDisplay()
		elif hot == HotKeys.kTTH_HotKey_Switch_Show_Preview_In_GW:
			fm = tthTool.getFontModel()
			cur = tthTool.showPreviewInGlyphWindow
			tthTool.setPreviewInGlyphWindowState(not cur)

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

	def drawZoneDelta(self, zone, scale, pitch, labelPos, fontModel):
		fontIsQuad = helperFunctions.fontIsQuadratic(fontModel.f)
		if not fontIsQuad: return
		for deltaPPM, deltaValue in zone['delta'].iteritems():
			if int(deltaPPM) != tthTool.PPM_Size or deltaValue == 0:
				continue
			path = NSBezierPath.bezierPath()
			path.moveToPoint_(labelPos)
			endPos = labelPos + geom.Point(0.0, (deltaValue/8.0) * pitch)
			path.lineToPoint_(endPos)

			DR.kDeltaColor.set()
			path.setLineWidth_(scale)
			path.stroke()
			DR.drawLozengeAtPoint(scale, 4, endPos.x, endPos.y, DR.kDeltaColor)

	def drawZones(self, scale, pitch, fontModel):
		xpos = 5 * fontModel.UPM
		fontModel.zoneLabels = {}
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
			fontModel.zoneLabels[zoneName] = (labelPos, labelSize)

			point = (-100*scale, y_start+y_end/2)
			if 'delta' in zone:
				self.drawZoneDelta(zone, scale, pitch, labelPos, fontModel)
				

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - DRAWING HINTING COMMANDS

	def getCommandAlignLabel(self, cmd):
		if helperFunctions.commandHasAttrib(cmd, 'align'):
			extension = cmd.get('align')
			if tthTool.selectedAxis == 'Y':
				if extension == 'right': return 'top'
				elif extension == 'left': return 'bottom'
			if extension == 'round': return 'closest' # FIXME: ?????
			return extension
		else:
			return ''

	def setLabelPosSize(self, cmd, pos, size):
		cmd.set('labelPosSize', '#'.join([str(pos), str(size)]))

	def drawAlign(self, fm, gm, cmd, scale, direction, simple):
		color = DR.kArrowColor
		active = cmd.get('active', 'true') == 'true'
		if not active:
			color = DR.kInactiveColor
		pos = gm.positionForPointName(cmd.get('point'), fm, cmd.get('base'))
		DR.drawArrowAtPoint(scale, 10, direction, pos, color)
		DR.drawArrowAtPoint(scale, 10, direction.opposite(), pos, color)
		if simple: return
		code = cmd.get('code')
		if helperFunctions.commandHasAttrib(cmd, 'align'):
			text = u'☩ ' + self.getCommandAlignLabel(cmd)
		elif code in ['alignt', 'alignb']:
			text = u'☩ '  + cmd.get('zone')
		if code == 'alignt':
			labelPos = pos + scale * geom.Point(10,+20)
		else:
			labelPos = pos + scale * geom.Point(10,-20)
		return DR.CommandLabel(cmd, scale, text, labelPos, whiteColor, DR.kArrowColor, active)

	def drawDoubleLink(self, cmd, scale, fm, gm, simple):
		active = cmd.get('active', 'true') == 'true'
		pos1 = gm.positionForPointName(cmd.get('point1'), fm, cmd.get('base1'))
		pos2 = gm.positionForPointName(cmd.get('point2'), fm, cmd.get('base2'))
		offCurve = DR.drawDoubleArrow(scale, pos1, pos2, active, DR.kDoublinkColor)
		if simple: return
		# Compute label text
		stemName = cmd.get('stem')
		isRound = cmd.get('round', 'false') == 'true'
		if isRound:
			if stemName != None: text = u'☊ ' + stemName
			else: text = 'R'
		elif stemName != None:
			text = u'☊ ' + stemName
		else:
			text = u'☊'
		#labelSize = DR.drawTextAtPoint(scale, text, offCurve, whiteColor, DR.kDoublinkColor,\
		#		self.getNSView(), active)
		return DR.CommandLabel(cmd, scale, text, offCurve, whiteColor, DR.kDoublinkColor, active)

	def drawLink(self, cmd, scale, fm, gm, simple):
		active = cmd.get('active', 'true') == 'true'
		if active:
			color = DR.kLinkColor
		else:
			color = DR.kInactiveColor
		pos1 = gm.positionForPointName(cmd.get('point1'), fm, cmd.get('base1'))
		pos2 = gm.positionForPointName(cmd.get('point2'), fm, cmd.get('base2'))
		offCurve = DR.drawSingleArrow(scale, pos1, pos2, color, 10)
		if simple: return

		Y = (tthTool.selectedAxis == 'Y')
		extension = self.getCommandAlignLabel(cmd)
		stemName = cmd.get('stem')
		textColor = whiteColor
		isRound = cmd.get('round', 'false') == 'true'
		if isRound:
			if stemName == None and extension != '': text = 'R_' + extension
			elif stemName != None:                   text = 'R_' + stemName
			else:                                    text = 'R'
		else:
			text = u'⤴'
			if stemName == None and extension != '': text = u'⤴ ' + extension
			elif stemName != None:
				text = u'⤴ ' + stemName
				textColor = DR.kBlackColor
				if active:
					color = stemColor
				else:
					color = DR.kInactiveColor
		#labelSize = DR.drawTextAtPoint(scale, text, offCurve, textColor, color, self.getNSView(), active)
		return DR.CommandLabel(cmd, scale, text, offCurve, textColor, color, active)

	def drawInterpolate(self, cmd, scale, fm, gm, simple):
		active = cmd.get('active', 'true') == 'true'
		pos  = gm.positionForPointName(cmd.get('point'), fm, cmd.get('base'))
		pos1 = gm.positionForPointName(cmd.get('point1'), fm, cmd.get('base1'))
		pos2 = gm.positionForPointName(cmd.get('point2'), fm, cmd.get('base2'))
		offCurve = DR.drawDoubleArrow(scale, pos1, pos, active, DR.kInterpolateColor)
		offCurve = DR.drawDoubleArrow(scale, pos, pos2, active, DR.kInterpolateColor)
		if simple: return
		extension = self.getCommandAlignLabel(cmd)
		if extension == '':
			text = u'⇹'
		else:
			text = u'⇹ ' + extension
		# square root takes the label a bit further when we zoom in
		pos = pos + math.sqrt(scale)*10.0*geom.Point(1.0, -1.0)
		#labelSize = DR.drawTextAtPoint(scale, text, pos, whiteColor, DR.kInterpolateColor, self.getNSView(), active)
		return DR.CommandLabel(cmd, scale, text, pos, whiteColor, DR.kInterpolateColor, active)

	def drawDelta(self, cmd, scale, fm, gm, pitch, simple):
		pos  = gm.positionForPointName(cmd.get('point'), fm, cmd.get('base'))
		active = cmd.get('active', 'true') == 'true'
		cmd_code = cmd.get('code')
		if active:
			if cmd_code in ['mdeltah', 'mdeltav']:
				color = DR.kDeltaColor
			else: # final delta
				color = DR.kFinalDeltaColor
		else:
			color = DR.kInactiveColor
		if cmd_code[-1] == 'h':
			value = (int(cmd.get('delta')), 0)
		else:
			value = (0, int(cmd.get('delta')))

		endPt = pos + (1.0/8.0) * pitch * geom.makePointForPair(value)
		path = NSBezierPath.bezierPath()
		path.moveToPoint_(pos)
		path.lineToPoint_(endPt)

		color.set()
		path.setLineWidth_(scale)
		path.stroke()
		DR.drawLozengeAtPoint(scale, 4, endPt.x, endPt.y, color)
		if simple: return

		value = cmd.get('delta')
		if cmd_code[0] == 'm':
			text = u'M ∆ '
		else:
			text = u'F ∆ '
		text = text + value

		if cmd.get('code')[-1] == 'v' and int(value) < 0:
			labelPos = pos + 10*scale*geom.Point(-1,+1)
		else:
			labelPos = pos + 10*scale*geom.Point(-1,-1)
		#labelSize = DR.drawTextAtPoint(scale, text, labelPos, whiteColor, color, self.getNSView(), active)
		#self.setLabelPosSize(cmd, labelPos, labelSize)
		return DR.CommandLabel(cmd, scale, text, labelPos, whiteColor, color, active)

	def drawCommands(self, scale, simple):
		gm, fm = tthTool.getGlyphAndFontModel()
		commandLabels = []
		for c in gm.hintingCommands:
			drawn = True
			cmd_code = c.get('code')
			X = (tthTool.selectedAxis == 'X')
			Y = not X
			label = None
			if Y and cmd_code in ['alignv', 'alignt', 'alignb']:
				label = self.drawAlign(fm, gm, c, scale, geom.Point(0,1), simple)
			elif X and cmd_code == 'alignh':
				label = self.drawAlign(fm, gm, c, scale, geom.Point(1,0), simple)
			elif (X and cmd_code == 'doubleh') or (Y and cmd_code == 'doublev'):
				label = self.drawDoubleLink(c, scale, fm, gm, simple)
			elif (X and cmd_code == 'singleh') or (Y and cmd_code == 'singlev'):
				label = self.drawLink(c, scale, fm, gm, simple)
			elif (X and cmd_code == 'interpolateh') or (Y and cmd_code == 'interpolatev'):
				label = self.drawInterpolate(c, scale, fm, gm, simple)
			elif (X and cmd_code in ['mdeltah', 'fdeltah']) or (Y and cmd_code in ['mdeltav', 'fdeltav']):
				if int(c.get('ppm1')) <= tthTool.PPM_Size <= int(c.get('ppm2')):
					label = self.drawDelta(c, scale, fm, gm, fm.getPitch(), simple)
				else:
					drawn = False
			else:
				drawn = False
			if drawn and (not simple):
				commandLabels.append(label)
			else: # make sure we can't click on the command's label
				self.setLabelPosSize(c, geom.Point(0.0, 0.0), geom.Point(-1.0, -1.0))
		if simple: return
		i = 1
		while i <= 10 and DR.untangleLabels(commandLabels):
			i += 1
		for c in commandLabels:
			self.setLabelPosSize(c.cmd, c.center, c.size)
			c.draw(scale, self.getNSView())

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if tthTool._printLoadings: print "RFEventTool, ",
