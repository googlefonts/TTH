from AppKit import NSComboBoxCell, NSView

class HiddenComboBoxListCell(NSComboBoxCell):
	def drawWithFrame_inView_(self, frame, view):
		NSView.alloc().init()