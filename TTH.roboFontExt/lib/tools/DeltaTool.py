
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool

class DeltaTool(TTHCommandTool):

	def __init__(self, final = False):
		if final:
			super(DeltaTool, self).__init__("Final Delta")
		else:
			super(DeltaTool, self).__init__("Middle Delta")
		self.final = final
		self.mono  = False
		self.gray  = False
		self.offset = 0
		self.range1 = 9
		self.range2 = 9

	def updateUI(self):
		self.hideUI()
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools

		w.DeltaMonochromeCheckBox.set(self.mono)
		w.DeltaGrayCheckBox.set(self.gray)
		w.DeltaOffsetSlider.set(self.offset + 8)
		tthTool.mainPanel.lock()
		w.DeltaOffsetEditText.set(str(self.offset))
		w.DeltaRange1ComboBox.set(str(self.range1))
		w.DeltaRange2ComboBox.set(str(self.range2))
		tthTool.mainPanel.unlock()

		w.DeltaOffsetText.show(True)
		w.DeltaOffsetSlider.show(True)
		w.DeltaRangeText.show(True)
		w.DeltaRange1ComboBox.show(True)
		w.DeltaRange2ComboBox.show(True)
		w.DeltaOffsetEditText.show(True)
		w.DeltaMonochromeText.show(True)
		w.DeltaMonochromeCheckBox.show(True)
		w.DeltaGrayText.show(True)
		w.DeltaGrayCheckBox.show(True)

	def setMono(self, mono):
		self.mono = mono

	def setGray(self, gray):
		self.gray = gray

	def setOffset(self, offset):
		try:
			offset = max(-8, min(8, int(offset)))
		except:
			offset = self.offset
		self.offset = offset
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools
		w.DeltaOffsetSlider.set(self.offset + 8)
		w.DeltaOffsetEditText.set(str(self.offset))

	def setRange(self, value1, value2):
		if value2 < value1:
			value2 = value1
		self.range1 = value1
		self.range2 = value2
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools
		w.DeltaRange1ComboBox.set(str(self.range1))
		w.DeltaRange2ComboBox.set(str(self.range2))
