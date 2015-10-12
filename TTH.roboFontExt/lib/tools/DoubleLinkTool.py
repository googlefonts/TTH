
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

	def addCommand(self, targetLoc):
		gm, fm = tthTool.getGlyphAndFontModel()
		if tthTool.selectedAxis == 'X':
			code = 'doubleh'
			stem = self.stemNameX
		else:
			code = 'doublev'
			stem = self.stemNameY
		cmd = self.genNewCommand()
		cmd.set('code', code)
		self.setupCommandPointFromLoc('point1', cmd, self.startPoint)
		self.setupCommandPointFromLoc('point2', cmd, targetLoc)
		align = self.getAlignment()
		if align != 'None':
			cmd.set('align', align)
		if stem == 'None':
			stem = None
		if stem == 'Guess':
			stem = fm.guessStem(self.startPoint.rfPoint, targetLoc.rfPoint)
		if stem != None:
			cmd.set('stem', stem)
		else:
			cmd.set('round', 'true')
		gm.addCommand(fm, cmd)

	def mouseUp(self, point, scale):
		if not self.dragging: return
		gm, fm = tthTool.getGlyphAndFontModel()
		tgt = gm.pointClicked(geom.makePoint(point), fm, scale, alsoOff=self.worksOnOFF)
		loc = tgt[0]
		if loc:
			s = self.startPoint.pos
			t = loc.pos
			if (s.x != t.x or s.y != t.y):
				self.addCommand(loc)
		super(DoubleLinkTool, self).mouseUp(point, scale)

	# - - - - DRAW

	def draw(self, scale):
		if not self.dragging: return
		locked, p = self.magnet(scale)
		DR.drawDoubleArrow(scale, self.startPoint.pos, p, True, DR.kDoublinkColor, 20)
		if locked:
			DR.drawCircleAtPoint(10*scale, 2*scale, p.x, p.y, DR.kDoublinkColor)
