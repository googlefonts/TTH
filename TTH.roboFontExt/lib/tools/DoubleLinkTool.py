
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool

class DoubleLinkTool(TTHCommandTool):

	def __init__(self):
		super(DoubleLinkTool, self).__init__("Double Link")

	def updateUI(self):
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools

		w.AlignmentTypeText.show(False)
		w.AlignmentTypePopUpButton.show(False)
		w.StemTypeText.show(True)
		w.StemTypePopUpButton.show(True)
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

