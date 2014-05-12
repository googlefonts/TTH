from AppKit import *

class PreviewArea(NSView):

	def init_withTTHToolInstance(self, TTHToolInstance):
		self.init()
		self.TTHToolInstance = TTHToolInstance
		return self

	def drawRect_(self, rect):
		self.TTHToolInstance.drawPreview()
