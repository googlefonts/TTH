
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool
from drawing import geom

class AlignTool(TTHCommandTool):

	def __init__(self):
		super(AlignTool, self).__init__("Align")
		self.allowedAlignments = TTHCommandTool.allowedAlignmentTypes

	def updateUI(self):
		self.updateAlignmentUI(withNone = False)
		self.hideUI()
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools
		w.AlignmentTypeText.show(True)
		w.AlignmentTypePopUpButton.show(True)

	def mouseDown(self, point, clickCount):
		self.mouseDownClickPos = geom.makePoint(point)
		self.dragging = False

	def mouseUp(self, point):
		if not self.realClick(point): return
		gm, fm = tthTool.getGlyphAndFontModel()
		# Have we clicked on a control point?
		(point, isOn, dist) = gm.pointClicked(geom.makePoint(point))
