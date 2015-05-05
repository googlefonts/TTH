
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool

class SingleLinkTool(TTHCommandTool):

	def __init__(self):
		super(SingleLinkTool, self).__init__("Single Link")
		self.allowedAlignments = TTHCommandTool.allowedAlignmentTypesWithNone

	def updateUI(self):
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools
		
		if tthTool.selectedAxis == 'X':
			w.AlignmentTypePopUpButton.setItems(self.displayXWithNone)
		else:
			w.AlignmentTypePopUpButton.setItems(self.displayYWithNone)
		w.AlignmentTypePopUpButton.set(self.alignment)

		w.AlignmentTypeText.show(True)
		w.AlignmentTypePopUpButton.show(True)
		w.StemTypeText.show(True)
		w.StemTypePopUpButton.show(True)
		w.RoundDistanceText.show(True)
		w.RoundDistanceCheckBox.show(True)
		w.DeltaOffsetText.show(False)
		w.DeltaOffsetSlider.show(False)
		w.DeltaRangeText.show(False)
		w.DeltaRange1ComboBox.show(False)
		w.DeltaRange2ComboBox.show(False)
		w.DeltaOffsetEditText.show(False)
		w.DeltaMonochromeText.show(False)
		w.DeltaMonochromeCheckBox.show(False)
		w.DeltaGrayText.show(False)
		w.DeltaGrayCheckBox.show(False)
