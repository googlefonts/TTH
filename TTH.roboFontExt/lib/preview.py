#coding=utf-8

from AppKit import *
from math import ceil

bkgColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, .8)

class PreviewInGlyphWindow(NSView):

	def init_withTTHToolInstance(self, TTHToolInstance):
		self.init()
		self.TTHToolInstance = TTHToolInstance
		return self

	def drawRect_(self, rect):
		
		path = NSBezierPath.bezierPath()
		path.appendBezierPathWithRoundedRect_xRadius_yRadius_(((30, 65), (190, 190)), 3, 3)
		#path.appendBezierPathWithRoundedRect_xRadius_yRadius_(((30, 0), (5000, 250)), 5, 5)
		bkgColor.set()
		path.fill()

		if self.TTHToolInstance.tthtm.selectedAxis == 'X':
			text = u'⬌'
		else:
			text = u'⬍'
		self.TTHToolInstance.drawRawTextAtPoint(1, text, 250, 190, 120)

		self.clickableSizesGlyphWindow = {}
		if self.TTHToolInstance.tthtm.g == None:
			return
		if self.TTHToolInstance.tthtm.g.unicode == None:
			return
		tr = self.TTHToolInstance.tthtm.textRenderer
		advance = 40
		for size in range(self.TTHToolInstance.tthtm.previewFrom, self.TTHToolInstance.tthtm.previewTo + 1, 1):

			self.clickableSizesGlyphWindow[(advance, 20)] = size

			tr.set_cur_size(size)
			tr.set_pen((advance, 40))
			delta_pos = tr.render_text(unichr(self.TTHToolInstance.tthtm.g.unicode))
			if size == self.TTHToolInstance.tthtm.PPM_Size:
				color = NSColor.redColor()
			else:
				color = NSColor.blackColor()
			self.TTHToolInstance.drawPreviewSize(str(size), advance, 20, color)
			advance += delta_pos[0] + 5

		tr.set_cur_size(self.TTHToolInstance.tthtm.PPM_Size)
		tr.set_pen((40, 110))
		scale = ceil(120/float(self.TTHToolInstance.tthtm.PPM_Size))
		delta_pos = tr.render_text_with_scale_and_alpha(unichr(self.TTHToolInstance.tthtm.g.unicode), scale, 1)

