
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool
from drawing import geom, utilities as DR

class DoubleLinkTool(TTHCommandTool):

	def __init__(self):
		super(DoubleLinkTool, self).__init__("Double Link")
		self.stemNameX = 'Guess'
		self.stemNameY = 'Guess'

	def updateUI(self):
		self.updateStemUI()
		self.hideUI()
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools
		w.StemTypeText.show(True)
		w.StemTypePopUpButton.show(True)

	# - - - - DRAW

	def draw(self, scale):
		if not self.dragging: return
		DR.drawDoubleArrow(scale, geom.makePoint(self.startPoint[0]), self.mouseDraggedPos, True, DR.kDoublinkColor, 20)
