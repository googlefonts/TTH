
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool

class InterpolationTool(TTHCommandTool):

	def __init__(self):
		super(InterpolationTool, self).__init__("Interpolation")
		self.allowedAlignments = TTHCommandTool.allowedAlignmentTypesWithNone

	def updateUI(self):
		self.updateAlignmentUI(withNone = True)
		self.hideUI()
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools
		w.AlignmentTypeText.show(True)
		w.AlignmentTypePopUpButton.show(True)
