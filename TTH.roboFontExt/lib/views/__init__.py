from mojo.extensions import *

class TTHWindow(object):
	def __init__(self, defaultPosSize, posSizeKey, visibilityKey):
		self.window_          = None
		self.defaultPosSize_  = defaultPosSize
		self.posSizeKey_      = posSizeKey
		self.visibilityKey_   = visibilityKey
	def __del__(self):
		if self.window_ != None:
			self.window_.close()
	def window(self):
		return self.window_
	def setWindow(self, w):
		self.window_ = w
		w.bind("move", self.movedOrResized)
		w.bind("resize", self.movedOrResized)
		w.bind("should close", self.shouldClose)

	def isVisible(self):
		return self.window().isVisible()
	def showOrHide(self):
		if 1 == getExtensionDefault(self.visibilityKey_, fallback=0):
			self.window().show()
		else:
			self.window().hide()
	def show(self):
		setExtensionDefault(self.visibilityKey_, 1)
		self.showOrHide()
	def hide(self):
		self.window().hide()
	def setNeedsDisplay(self):
		self.window().getNSWindow().setViewsNeedDisplay_(True)
		
	###########
	# callbacks
	###########

	def shouldClose(self, sender):
		self.hide()
		setExtensionDefault(self.visibilityKey_, 0)
		return False # which means, no please don't close the window
	def movedOrResized(self, sender):
		setExtensionDefault(self.posSizeKey_, self.window().getPosSize())