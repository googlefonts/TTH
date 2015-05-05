
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool

class InterpolationTool(TTHCommandTool):

	def __init__(self):
		super(InterpolationTool, self).__init__("Interpolation")
		self.allowedAlignments = TTHCommandTool.allowedAlignmentTypesWithNone

	def updateUI(self):
		#self.TTHToolInstance.selectedAlignmentTypeLink = self.alignmentTypeListLink[0]
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools

		if tthTool.selectedAxis == 'X':
			w.AlignmentTypePopUpButton.setItems(self.displayXWithNone)
		else:
			w.AlignmentTypePopUpButton.setItems(self.displayYWithNone)
		w.AlignmentTypePopUpButton.set(self.alignment)

		w.AlignmentTypeText.show(True)
		w.AlignmentTypePopUpButton.show(True)
		w.StemTypeText.show(False)
		w.StemTypePopUpButton.show(False)
		w.RoundDistanceText.show(False)
		w.RoundDistanceCheckBox.show(False)
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
