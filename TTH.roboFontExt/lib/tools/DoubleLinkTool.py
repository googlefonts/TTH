
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

	def addCommand(self, target):
		gm, fm = tthTool.getGlyphAndFontModel()
		if tthTool.selectedAxis == 'X':
			code = 'doubleh'
			stem = self.stemNameX
		else:
			code = 'doublev'
			stem = self.stemNameY
		cmd = {	'code': code,
				'point1': self.startPoint[0].name,
				'point2': target.name,
			}
		align = self.getAlignment()
		if align != 'None':
			cmd['align'] = align
		if stem == 'None':
			stem = None
		if stem == 'Guess':
			stem = fm.guessStem(self.startPoint[0], target)
		if stem != None:
			cmd['stem'] = stem
		else:
			cmd['round'] = 'true'
		gm.addCommand(cmd)

	def mouseUp(self, point):
		if not self.dragging: return
		gm = tthTool.getGlyphModel()
		tgt = gm.pointClicked(geom.makePoint(point))
		if tgt[0]:
			s = self.startPoint[0]
			t = tgt[0][0]
			if (s.x != t.x or s.y != t.y):
				self.addCommand(tgt[0][0])
		super(DoubleLinkTool, self).mouseUp(point)

	# - - - - DRAW

	def draw(self, scale):
		if not self.dragging: return
		DR.drawDoubleArrow(scale, geom.makePoint(self.startPoint[0]), self.magnet(), True, DR.kDoublinkColor, 20)
