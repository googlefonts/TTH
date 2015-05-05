
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool

class DeltaTool(TTHCommandTool):

	def __init__(self, final = False):
		if final:
			super(DeltaTool, self).__init__("Final Delta")
		else:
			super(DeltaTool, self).__init__("Middle Delta")
		self.final = final

	def updateUI(self):
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools
		w.AlignmentTypeText.show(False)
		w.AlignmentTypePopUpButton.show(False)
		w.StemTypeText.show(False)
		w.StemTypePopUpButton.show(False)
		w.RoundDistanceText.show(False)
		w.RoundDistanceCheckBox.show(False)
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

