
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool
from mojo.events import getActiveEventTool
from drawing import geom, utilities as DR

class DoubleDiagonalLinkTool(TTHCommandTool):

	def __init__(self):
		super(DoubleDiagonalLinkTool, self).__init__("Diagonal Link")
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
			stem = self.stemNameX
		else:
			stem = self.stemNameY
		code = 'doublediagonal'
		cmd = self.genNewCommand()
		cmd.set('code', code)
		self.setupCommandPointFromLoc('point1', cmd, self.startPoint)
		self.setupCommandPointFromLoc('point2', cmd, targetLoc)
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
		super(DoubleDiagonalLinkTool, self).mouseUp(point, scale)

	# - - - - DRAW

	def draw(self, scale):
		if not self.dragging: return
		locked, p = self.magnet(scale)
		DR.drawDoubleArrow(scale, self.startPoint.pos, p, True, DR.kDblDiaglinkColor, 20)
		if locked:
			DR.drawCircleAtPoint(10*scale, 2*scale, p.x, p.y, DR.kDblDiaglinkColor)

class SingleDiagonalLinkTool(TTHCommandTool):

	def __init__(self):
		super(SingleDiagonalLinkTool, self).__init__('Single Link')
		self.allowedAlignments = TTHCommandTool.allowedAlignmentTypesWithNone
		self.stemNameX = 'Guess'
		self.stemNameY = 'Guess'

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

	def addCommand(self, targetLoc):
		gm, fm = tthTool.getGlyphAndFontModel()
		if tthTool.selectedAxis == 'X':
			stem = self.stemNameX
		else:
			stem = self.stemNameY
		code = 'singlediagonal'
		cmd = self.genNewCommand()
		cmd.set('code', code)
		self.setupCommandPointFromLoc('point1',  cmd, self.startPoint)
		self.setupCommandPointFromLoc('point2',  cmd, targetLoc)
		shiftPressed = getActiveEventTool().getModifiers()['shiftDown']
		optionPressed = getActiveEventTool().getModifiers()['optionDown']
		if self.roundDistance or shiftPressed:
			cmd.set('round', 'true')
		elif optionPressed:
			stem = None
		else:
			if stem == 'None': stem = None
			if stem == 'Guess': stem = fm.guessStem(self.startPoint.rfPoint, targetLoc.rfPoint)
			if stem != None:
				cmd.set('stem', stem)
			else:
				align = self.getAlignment()
				if align != 'None':
					cmd.set('align', align)
		gm.addCommand(fm, cmd)

	def mouseUp(self, point, scale):
		if not self.dragging: return
		gm, fm = tthTool.getGlyphAndFontModel()
		tgt = gm.pointClicked(geom.makePoint(point), fm, scale, alsoOff=self.worksOnOFF)
		loc = tgt[0]
		if loc:
			s = self.startPoint.pos
			if (s.x != loc.pos.x or s.y != loc.pos.y):
				self.addCommand(loc)
		super(SingleDiagonalLinkTool, self).mouseUp(point, scale)

	# - - - - DRAW

	def draw(self, scale):
		if not self.dragging: return
		locked, p = self.magnet(scale)
		DR.drawSingleArrow(scale, self.startPoint.pos, p, DR.kSglDiaglinkColor, 20)
		if locked:
			DR.drawCircleAtPoint(10*scale, 2*scale, p.x, p.y, DR.kSglDiaglinkColor)
