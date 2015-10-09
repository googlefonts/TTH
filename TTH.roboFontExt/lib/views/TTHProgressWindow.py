
from vanilla import FloatingWindow, ProgressBar, TextBox
from AppKit import NSAttributedString, NSFont, \
	NSFontAttributeName, NSForegroundColorAttributeName

kTitleTextAttributes = {
		NSFontAttributeName : NSFont.boldSystemFontOfSize_(14)
		}

class TTHProgressWindow(object):
	def __init__(self, title, maxi):
		w       = FloatingWindow((200, 100, 300, 90), "TTH Progress Bar", closable = False)
		t       = NSAttributedString.alloc().initWithString_attributes_(title, kTitleTextAttributes)
		w.title = TextBox((10, 10, -10, 20), t)
		w.info  = TextBox((10, 40, -10, 20), "")
		w.bar   = ProgressBar((10, 70, -10, 10), maxValue = maxi)
		w.center()
		w.open()
		self.w = w

	def increment(self, value=1):
		self.w.bar.increment(value)

	def set(self, v):
		self.w.bar.set(v)

	def show(self, v):
		self.w.bar.show(v)
	
	def setTitle(self, title):
		t = NSAttributedString.alloc().initWithString_attributes_(title, kTitleTextAttributes)
		self.w.title.set(t)
		self.w.title._nsObject.displayIfNeeded()
	
	def setInfo(self, t):
		self.w.info.set(t)
		self.w.info._nsObject.displayIfNeeded()

	def close(self):
		self.w.close()
