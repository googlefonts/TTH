from mojo.extensions import *

class TTHWindow(object):
	def __init__(self, posSizeKey, visibilityKey):
		self._window          = None
		self._posSizeKey      = posSizeKey # Key to access the position and size in the extension preference
		self._visibilityKey   = visibilityKey # Key to access the visibility in the extension preference

	def __del__(self):
		if self._window != None:
			self.window.unbind("move")
			self.window.unbind("resize")
			self.window.unbind("should close")
			self.window.close()

	@property
	def window(self):
		return self._window
	@window.setter
	def window(self, w):
		self._window = w
		w.bind("move", self.movedOrResized)
		w.bind("resize", self.movedOrResized)
		w.bind("should close", self.shouldClose)

	def isVisible(self):
		return self.window.isVisible()

	def showOrHide(self):
		if 1 == getExtensionDefault(self._visibilityKey, fallback=0):
			self.window.show()
		else:
			self.window.hide()

	def show(self):
		setExtensionDefault(self._visibilityKey, 1)
		self.showOrHide()

	def hide(self):
		self.window.hide()

	def setNeedsDisplay(self):
		self.window.getNSWindow()._setViewsNeedDisplay(True)

	###########
	# callbacks
	###########

	def shouldClose(self, sender):
		self.hide()
		setExtensionDefault(self._visibilityKey, 0)
		return False # which means, no please don't close the window

	def movedOrResized(self, sender):
		setExtensionDefault(self._posSizeKey, self.window.getPosSize())
