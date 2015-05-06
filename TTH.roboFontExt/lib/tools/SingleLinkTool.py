
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool
from drawing import geom, utilities as DR

class SingleLinkTool(TTHCommandTool):

	def __init__(self):
		super(SingleLinkTool, self).__init__('Single Link')
		self.allowedAlignments = TTHCommandTool.allowedAlignmentTypesWithNone
		self.stemNameX = 'Guess'
		self.stemNameY = 'Guess'
		self.roundDistance = False

	def updateUI(self):
		self.updateAlignmentUI(withNone = True)
		self.updateStemUI()

		self.hideUI()
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools
		#update round distance boolean
		w.RoundDistanceCheckBox.set(self.roundDistance)

		w.AlignmentTypeText.show(True)
		w.AlignmentTypePopUpButton.show(True)
		w.StemTypeText.show(True)
		w.StemTypePopUpButton.show(True)
		w.RoundDistanceText.show(True)
		w.RoundDistanceCheckBox.show(True)

	def setRoundDistance(self, value):
		self.roundDistance = (value == 1)

	# - - - - DRAW

	def draw(self, scale):
		if not self.dragging: return
		DR.drawSingleArrow(scale, geom.makePoint(self.startPoint[0]), self.mouseDraggedPos, DR.kLinkColor, 30)
