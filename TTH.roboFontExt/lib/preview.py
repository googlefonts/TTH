from AppKit import *

class PreviewArea(NSView):

	def init_withTTHToolInstance(self, TTHToolInstance):
		self.init()
		self.TTHToolInstance = TTHToolInstance
		return self

	def drawRect_(self, rect):
		self.TTHToolInstance.drawPreviewWindow()


class PreviewInGlyphWindow(NSView):

	def init_withTTHToolInstance(self, TTHToolInstance):
		self.init()
		self.TTHToolInstance = TTHToolInstance
		return self

	def drawRect_(self, rect):
		tr = self.TTHToolInstance.tthtm.textRenderer
		tr.set_cur_size(self.TTHToolInstance.tthtm.PPM_Size)
		tr.set_pen((20, 20))
		tr.render_text('Hello')