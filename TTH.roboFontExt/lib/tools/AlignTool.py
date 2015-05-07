
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool
from drawing import geom, utilities as DR

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

	def mouseUp(self, point):
		self.dragging = False
		if not self.realClick(point): return
		#gm, fm = tthTool.getGlyphAndFontModel()

	def draw(self, scale):
		if not self.dragging: return
		if not self.realClick(self.mouseDraggedPos): return
		if tthTool.selectedAxis == 'X':
			direction = geom.Point(1, 0)
		else:
			direction = geom.Point(0, 1)
		pos = geom.makePoint(self.startPoint[0])
		DR.drawArrowAtPoint(scale, 20, direction, pos, DR.kArrowColor)
		DR.drawArrowAtPoint(scale, 20, direction.opposite(), pos, DR.kArrowColor)
