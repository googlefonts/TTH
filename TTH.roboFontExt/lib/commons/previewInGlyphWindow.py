#coding=utf-8

from AppKit import *
from math import ceil

bkgColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, .8)
blackColor = NSColor.blackColor()
redColor = NSColor.redColor()

class PreviewInGlyphWindow(NSView):

	def init_withTTHToolInstance(self, TTHToolInstance):
		self.init()
		self.TTHToolController = TTHToolInstance
		self.TTHToolModel = self.TTHToolController.TTHToolModel
		return self

	def drawRect_(self, rect):
		
		path = NSBezierPath.bezierPath()
		path.appendBezierPathWithRoundedRect_xRadius_yRadius_(((30, 65), (190, 190)), 3, 3)
		#path.appendBezierPathWithRoundedRect_xRadius_yRadius_(((30, 0), (5000, 250)), 5, 5)
		bkgColor.set()
		path.fill()

		if self.TTHToolModel.selectedAxis == 'Y':
			axisPath = NSBezierPath.bezierPath()
			axisPath.moveToPoint_((240, 85))
			axisPath.lineToPoint_((230, 75))
			axisPath.lineToPoint_((230, 245))
			axisPath.lineToPoint_((240, 235))
			blackColor.set()
			path.setLineWidth_(1)
			axisPath.stroke()
		else:
			axisPath = NSBezierPath.bezierPath()
			axisPath.moveToPoint_((50, 275))
			axisPath.lineToPoint_((40, 265))
			axisPath.lineToPoint_((210, 265))
			axisPath.lineToPoint_((200, 275))
			blackColor.set()
			path.setLineWidth_(1)
			axisPath.stroke()

		self.clickableSizesGlyphWindow = {}

		glyph = self.TTHToolController.getGlyph()
		if glyph == None: return
		tr = self.TTHToolController.c_fontModel.textRenderer
		advance = 40
		glyphname = [glyph.name]
		for size in range(self.TTHToolModel.previewFrom, self.TTHToolModel.previewTo + 1, 1):

			self.clickableSizesGlyphWindow[(advance, 20)] = size

			tr.set_cur_size(size)
			tr.set_pen((advance, 40))
			delta_pos = tr.render_named_glyph_list(glyphname)
			
			if size == self.TTHToolModel.PPM_Size:
				color = redColor
			else:
				color = blackColor
			self.TTHToolController.drawPreviewSize(str(size), advance, 20, color)
			advance += delta_pos[0] + 5

		tr.set_cur_size(self.TTHToolModel.PPM_Size)
		tr.set_pen((40, 110))
		scale = 170.0/self.TTHToolModel.PPM_Size
		delta_pos = tr.render_named_glyph_list(glyphname, scale, 1)

