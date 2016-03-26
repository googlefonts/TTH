#coding=utf-8

from AppKit import NSView, NSBezierPath, NSColor
from mojo.events import getActiveEventTool
from freetype import FT_RENDER_MODE_LCD
from mojo.drawingTools import *

from drawing import utilities as DR
from commons import helperFunctions as HF
from models import TTHGlyph
from ps import parametric

from fontTools.pens.cocoaPen import CocoaPen

reload(HF)
reload(TTHGlyph)
reload(parametric)

bkgColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, .8)
blackColor = NSColor.blackColor()
redColor = NSColor.redColor()

# This NSView is integrated in the GlyphWindow, as a subview, so that it gets
# drawn on top of the GlyphWindow's main view.

class PreviewInGlyphWindow(NSView):

	def initWithFontAndTool(self, fontModel, tthTool):
		self.init()
		self.fontModel = fontModel
		self.tthTool = tthTool
		return self

	def die(self):
		self.tthTool = None
		self.fontModel = None

	def recomputeFrame(self):
		frame = self.superview().frame()
		frame.size.width -= 30
		frame.origin.x = 0
		self.setFrame_(frame)

	def handleClick(self):
		if not self.tthTool: return
		if self.isHidden(): return
		loc = getActiveEventTool().getCurrentEvent().locationInWindow()
		for p, s in self.clickableSizesGlyphWindow.iteritems():
			if (p[0] <= loc.x <= p[0]+10) and (p[1] <= loc.y <= p[1]+20):
				self.tthTool.changeSize(s)

	def drawRect_(self, rect):
		if not self.tthTool: return

		self.recomputeFrame()
		self.clickableSizesGlyphWindow = {}
		eventController = getActiveEventTool()
		if eventController is None: return

		glyph = eventController.getGlyph()

		if glyph == None: return

		yAsc  = self.fontModel.ascent
		yDesc = self.fontModel.descent
		if None == yAsc or None == yDesc: 
			yAsc  = 750
			yDesc = -250

		glyphHeight = yAsc - yDesc

		margin = 30
		frameOriginX = 50
		frameOriginY = 100
		frameWidth  = glyph.width  * .2 + 2*margin
		frameHeight = glyphHeight * .2 + 2*margin

		backPath = NSBezierPath.bezierPath()
		backPath.appendBezierPathWithRoundedRect_xRadius_yRadius_(((frameOriginX, frameOriginY), (frameWidth, frameHeight)), 3, 3)
		bkgColor.set()
		backPath.fill()

		blackColor.set()
		if self.tthTool.selectedAxis == 'Y':
			yAxisPath = NSBezierPath.bezierPath()
			yAxisPath.moveToPoint_((frameOriginX+frameWidth+10, frameOriginY +10))
			yAxisPath.lineToPoint_((frameOriginX+frameWidth, frameOriginY))
			yAxisPath.lineToPoint_((frameOriginX+frameWidth, frameOriginY+frameHeight))
			yAxisPath.lineToPoint_((frameOriginX+frameWidth+10, frameOriginY+frameHeight-10))
			yAxisPath.setLineWidth_(1)
			yAxisPath.stroke()
		else:
			xAxisPath = NSBezierPath.bezierPath()
			xAxisPath.moveToPoint_((frameOriginX+10, frameOriginY+frameHeight+10))
			xAxisPath.lineToPoint_((frameOriginX, frameOriginY+frameHeight))
			xAxisPath.lineToPoint_((frameOriginX+frameWidth, frameOriginY+frameHeight))
			xAxisPath.lineToPoint_((frameOriginX+frameWidth-10, frameOriginY+frameHeight+10))
			xAxisPath.setLineWidth_(1)
			xAxisPath.stroke()

		if HF.fontIsQuadratic(self.fontModel.f):

			tr = self.fontModel.textRenderer
			if not tr: return
			if not tr.isOK(): return

			# Draw main glyph enlarged in frame or preview string is preview panel checkbox True

			if self.tthTool.previewPanel.window.showStringInGlyphWindowCheckBox.get():
				(namedGlyphList, curGlyphName) = self.tthTool.prepareText(glyph, self.fontModel.f)
				glyphList = namedGlyphList
			else:
				glyphList = [glyph.name]
			
			ppem = self.tthTool.PPM_Size
			drawScale = 170.0/ppem
			tr.set_cur_size(ppem)

			gWidth = 0
			gHeightList = []
			topsList = []
			for i, glyphName in enumerate(glyphList):
				TRGlyph = tr.get_name_bitmap(glyphName)
				if tr.render_mode == FT_RENDER_MODE_LCD:
					TRGlyph = TRGlyph[0]
					gWidth += (tr.get_name_advance(glyphName)[0]+32)/64
				else:
					gWidth += (tr.get_name_advance(glyphName)[0]+32)/64
				gHeightList.append(TRGlyph.bitmap.rows)
				if i == 0:
					left = TRGlyph.left
				topsList.append(TRGlyph.top)
			top = max(topsList)
			gHeight = max(gHeightList)

			tr.set_pen((frameOriginX-left*drawScale+margin, frameOriginY+(gHeight-top)*drawScale+margin))
			delta_pos = tr.render_named_glyph_list(glyphList, drawScale, 1)

			# Draw waterfall of ppem for glyph
			advance = 40
			color = blackColor
			heightOfTextSize = 20
			for size in range(self.tthTool.previewFrom, self.tthTool.previewTo + 1, 1):

				self.clickableSizesGlyphWindow[(advance, heightOfTextSize)] = size

				tr.set_cur_size(size)
				tr.set_pen((advance, 40))
				delta_pos = tr.render_named_glyph_list(glyphList)

				if size == ppem: color = redColor
				DR.drawPreviewSize(str(size), advance, heightOfTextSize, color)
				if size == ppem: color = blackColor
				advance += delta_pos[0] + 5

		else:
			gmCopy = TTHGlyph.TTHGlyph(glyph.copy(), self.fontModel)
			parametric.processParametric(self.fontModel, gmCopy)
			g = gmCopy.RFGlyph
			pen = CocoaPen(g.getParent())
			g.draw(pen)
			translate(frameOriginX + margin, frameOriginY + margin - yDesc*.2)
			scale(.2, .2)
			NSColor.blackColor().set()
			pen.path.fill()

