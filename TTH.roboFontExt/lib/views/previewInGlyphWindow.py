#coding=utf-8

from AppKit import NSView, NSBezierPath, NSColor
from mojo.events import getActiveEventTool
from freetype import FT_RENDER_MODE_LCD

from drawing import utilities as DR

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

		tr = self.fontModel.textRenderer
		if not tr: return
		if not tr.isOK(): return

		# Draw main glyph enlarged in frame

		glyphname = [glyph.name]

		ppem = self.tthTool.PPM_Size
		drawScale = 170.0/ppem
		tr.set_cur_size(ppem)

		TRGlyph = tr.get_name_bitmap(glyphname[0])
		if tr.render_mode != FT_RENDER_MODE_LCD:
			gWidth = TRGlyph.bitmap.width
			gHeight = TRGlyph.bitmap.rows
			left = TRGlyph.left
			top = TRGlyph.top
		else:
			gWidth = TRGlyph[0].bitmap.width/3.0
			gHeight = TRGlyph[0].bitmap.rows
			left = TRGlyph[0].left
			top = TRGlyph[0].top


		margin = 30
		frameOriginX = 50
		frameOriginY = 100
		frameWidth  = gWidth  * drawScale+2*margin
		frameHeight = gHeight * drawScale+2*margin
		#print ppem,gWidth,gHeight,frameWidth, frameHeight

		
		tr.set_pen((frameOriginX-left*drawScale+margin, frameOriginY+(gHeight-top)*drawScale+margin))

		backPath = NSBezierPath.bezierPath()
		backPath.appendBezierPathWithRoundedRect_xRadius_yRadius_(((frameOriginX, frameOriginY), (frameWidth, frameHeight)), 3, 3)
		bkgColor.set()
		backPath.fill()

		blackColor.set()
		yAxisPath = NSBezierPath.bezierPath()
		yAxisPath.moveToPoint_((frameOriginX+frameWidth+10, frameOriginY +10))
		yAxisPath.lineToPoint_((frameOriginX+frameWidth, frameOriginY))
		yAxisPath.lineToPoint_((frameOriginX+frameWidth, frameOriginY+frameHeight))
		yAxisPath.lineToPoint_((frameOriginX+frameWidth+10, frameOriginY+frameHeight-10))
		yAxisPath.setLineWidth_(1)
		self.yAxisPath = yAxisPath

		xAxisPath = NSBezierPath.bezierPath()
		xAxisPath.moveToPoint_((frameOriginX+10, frameOriginY+frameHeight+10))
		xAxisPath.lineToPoint_((frameOriginX, frameOriginY+frameHeight))
		xAxisPath.lineToPoint_((frameOriginX+frameWidth, frameOriginY+frameHeight))
		xAxisPath.lineToPoint_((frameOriginX+frameWidth-10, frameOriginY+frameHeight+10))
		xAxisPath.setLineWidth_(1)
		self.xAxisPath = xAxisPath
		if self.tthTool.selectedAxis == 'Y':
			self.yAxisPath.stroke()
		else:
			self.xAxisPath.stroke()

		delta_pos = tr.render_named_glyph_list(glyphname, drawScale, 1)

		# Draw waterfall of ppem for glyph
		advance = 40
		color = blackColor
		heightOfTextSize = 20
		for size in range(self.tthTool.previewFrom, self.tthTool.previewTo + 1, 1):

			self.clickableSizesGlyphWindow[(advance, heightOfTextSize)] = size

			tr.set_cur_size(size)
			tr.set_pen((advance, 40))
			delta_pos = tr.render_named_glyph_list(glyphname)
	
			if size == ppem: color = redColor
			DR.drawPreviewSize(str(size), advance, heightOfTextSize, color)
			if size == ppem: color = blackColor
			advance += delta_pos[0] + 5

		

		
