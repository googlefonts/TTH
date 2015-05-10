
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

	def addCommand(self, target):
		gm = tthTool.getGlyphModel()
		if tthTool.selectedAxis == 'X':
			code = 'singleh'
			stem = self.stemNameX
		else:
			code = 'singlev'
			stem = self.stemNameY
		cmd = {	'code': code,
				'point1': self.startPoint[0].name,
				'point2': target,
				'align': self.getAlignment(),
			}
		if stem != None:
			if stem == 'Guess':
				pass #TODO: guess stem
			else:
				cmd['stem'] = stem
		elif self.roundDistance:
			cmd['round'] = 'true'
		gm.addCommand(cmd)

	def mouseUp(self, point):
		gm = tthTool.getGlyphModel()
		tgt = gm.pointClicked(geom.makePoint(point))
		if tgt[0]:
			s = self.startPoint[0]
			t = tgt[0][0]
			if (s.x != t.x or s.y != t.y):
				self.addCommand(tgt[0][0].name)
		super(SingleLinkTool, self).mouseUp(point)

	# - - - - DRAW

	def draw(self, scale):
		if not self.dragging: return
		DR.drawSingleArrow(scale, geom.makePoint(self.startPoint[0]), self.mouseDraggedPos, DR.kLinkColor, 20)
