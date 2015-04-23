#coding=utf-8

from AppKit import *
from math import ceil

from commons import drawing as DR

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

		backPath = NSBezierPath.bezierPath()
		backPath.appendBezierPathWithRoundedRect_xRadius_yRadius_(((30, 65), (190, 190)), 3, 3)
		self.backPath = backPath

		yAxisPath = NSBezierPath.bezierPath()
		yAxisPath.moveToPoint_((240, 85))
		yAxisPath.lineToPoint_((230, 75))
		yAxisPath.lineToPoint_((230, 245))
		yAxisPath.lineToPoint_((240, 235))
		yAxisPath.setLineWidth_(1)
		self.yAxisPath = yAxisPath

		xAxisPath = NSBezierPath.bezierPath()
		xAxisPath.moveToPoint_((50, 275))
		xAxisPath.lineToPoint_((40, 265))
		xAxisPath.lineToPoint_((210, 265))
		xAxisPath.lineToPoint_((200, 275))
		xAxisPath.setLineWidth_(1)
		self.xAxisPath = xAxisPath
		return self

	def recomputeFrame(self):
		frame = self.superview().frame()
		frame.size.width -= 30
		frame.origin.x = 0
		self.setFrame_(frame)

	def drawRect_(self, rect):
		self.recomputeFrame()
		bkgColor.set()
		self.backPath.fill()

		blackColor.set()
		if self.tthTool.selectedAxis == 'Y':
			self.yAxisPath.stroke()
		else:
			self.xAxisPath.stroke()

		self.clickableSizesGlyphWindow = {}

		glyph = self.tthTool.eventController.getGlyph()
		if glyph == None: return
		tr = self.fontModel.textRenderer
		advance = 40
		glyphname = [glyph.name]
		color = blackColor
		heightOfTextSize = 20
		for size in range(self.tthTool.previewFrom, self.tthTool.previewTo + 1, 1):

			self.clickableSizesGlyphWindow[(advance, heightOfTextSize)] = size

			tr.set_cur_size(size)
			tr.set_pen((advance, 40))
			delta_pos = tr.render_named_glyph_list(glyphname)

			#print advance,rect
			ppem = self.tthTool.PPM_Size
			if size == ppem: color = redColor
			DR.drawPreviewSize(str(size), advance, heightOfTextSize, color)
			if size == ppem: color = blackColor
			advance += delta_pos[0] + 5

		tr.set_cur_size(ppem)
		tr.set_pen((40, 110))
		scale = 170.0/ppem
		delta_pos = tr.render_named_glyph_list(glyphname, scale, 1)

