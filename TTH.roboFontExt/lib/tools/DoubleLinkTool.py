
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
		cmd = self.genNewCommand()
		cmd.set('code', code)
		cmd.set('point1', self.startPoint[0].name)
		cmd.set('point2', target.name)
		align = self.getAlignment()
		if align != 'None':
			cmd.set('align', align)
		if stem == 'None':
			stem = None
		if stem == 'Guess':
			stem = fm.guessStem(self.startPoint[0], target)
		if stem != None:
			cmd.set('stem', stem)
		else:
			cmd.set('round', 'true')
		gm.addCommand(fm, cmd)

	def mouseUp(self, point):
		if not self.dragging: return
		gm, fm = tthTool.getGlyphAndFontModel()
		tgt = gm.pointClicked(geom.makePoint(point), fm, alsoOff=self.worksOnOFF)
		if tgt[0]:
			s = self.startPoint[0]
			t = tgt[0][0]
			if (s.x != t.x or s.y != t.y):
				self.addCommand(tgt[0][0])
		super(DoubleLinkTool, self).mouseUp(point)

	# - - - - DRAW

	def draw(self, scale):
		if not self.dragging: return
		locked, p = self.magnet()
		q = geom.makePoint(self.startPoint[0])
		compo = self.startPoint[4]
		if compo:
			q = q + geom.makePointForPair(compo.offset)
		DR.drawDoubleArrow(scale, q, p, True, DR.kDoublinkColor, 20)
		if locked:
			DR.drawCircleAtPoint(10*scale, 2*scale, p.x, p.y, DR.kDoublinkColor)
