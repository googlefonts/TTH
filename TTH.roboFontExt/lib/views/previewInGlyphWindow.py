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

	def init_withTTHToolInstance(self, TTHToolInstance):
		self.init()
		self.TTHToolController = TTHToolInstance

		backPath = NSBezierPath.bezierPath()
		backPath.appendBezierPathWithRoundedRect_xRadius_yRadius_(((30, 65), (190, 190)), 3, 3)

		yAxisPath = NSBezierPath.bezierPath()
		yAxisPath.moveToPoint_((240, 85))
		yAxisPath.lineToPoint_((230, 75))
		yAxisPath.lineToPoint_((230, 245))
		yAxisPath.lineToPoint_((240, 235))
		yAxisPath.setLineWidth_(1)

		xAxisPath = NSBezierPath.bezierPath()
		xAxisPath.moveToPoint_((50, 275))
		xAxisPath.lineToPoint_((40, 265))
		xAxisPath.lineToPoint_((210, 265))
		xAxisPath.lineToPoint_((200, 275))
		xAxisPath.setLineWidth_(1)
		return self

	def drawRect_(self, rect):
		
		bkgColor.set()
		backPath.fill()

		tthtm = self.TTHToolController.TTHToolModel

		blackColor.set()
		if tthtm.selectedAxis == 'Y':
			yAxisPath.stroke()
		else:
			xAxisPath.stroke()

		self.clickableSizesGlyphWindow = {}

		glyph = self.TTHToolController.getGlyph()
		if glyph == None: return
		tr = self.TTHToolController.c_fontModel.textRenderer
		tr.set_cur_size(size)
		advance = 40
		glyphname = [glyph.name]
		color = blackColor
		heightOfTextSize = 20
		for size in range(tthtm.previewFrom, tthtm.previewTo + 1, 1):

			self.clickableSizesGlyphWindow[(advance, heightOfTextSize)] = size

			tr.set_pen((advance, 40))
			delta_pos = tr.render_named_glyph_list(glyphname)

			#print advance,rect
			
			if size == tthtm.PPM_Size: color = redColor
			DR.drawPreviewSize(str(size), advance, heightOfTextSize, color)
			if size == tthtm.PPM_Size: color = blackColor
			advance += delta_pos[0] + 5

		tr.set_cur_size(tthtm.PPM_Size)
		tr.set_pen((40, 110))
		scale = 170.0/tthtm.PPM_Size
		delta_pos = tr.render_named_glyph_list(glyphname, scale, 1)

