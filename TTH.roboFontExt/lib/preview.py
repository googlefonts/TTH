from AppKit import *
from math import ceil

from mojo.canvas import Canvas

# class PreviewArea(NSView):

# 	def init_withTTHToolInstance(self, TTHToolInstance):
# 		self.init()
# 		self.TTHToolInstance = TTHToolInstance
# 		return self

# 	def drawRect_(self, rect):
# 		self.TTHToolInstance.drawPreviewWindow()


class PreviewInGlyphWindow(NSView):

	def init_withTTHToolInstance(self, TTHToolInstance):
		self.init()
		self.TTHToolInstance = TTHToolInstance
		return self

	def drawRect_(self, rect):
		self.clickableSizesGlyphWindow = {}

		if self.TTHToolInstance.tthtm.g.unicode == None:
			return
		tr = self.TTHToolInstance.tthtm.textRenderer
		advance = 30
		for size in range(self.TTHToolInstance.tthtm.previewFrom, self.TTHToolInstance.tthtm.previewTo + 1, 1):

			self.clickableSizesGlyphWindow[(advance, 20)] = size

			tr.set_cur_size(size)
			tr.set_pen((advance, 50))
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

