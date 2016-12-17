
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool
from mojo.events import getActiveEventTool
from drawing import geom, utilities as DR
from math import atan2

class SingleDiagonalLinkTool(TTHCommandTool):

	def __init__(self, name = None):
		if name:
			super(SingleDiagonalLinkTool, self).__init__(name)
		else:
			super(SingleDiagonalLinkTool, self).__init__('Diagonal Single Link')
		self.allowedAlignments = TTHCommandTool.allowedAlignmentTypesWithNone
		self.stemNameX = 'Guess'
		self.stemNameY = 'Guess'
		self.point1 = None
		self.point2 = None
		self.lookingForProjection = False

	def reset(self):
		super(SingleDiagonalLinkTool, self).reset()
		self.point1 = None
		self.point2 = None
		self.lookingForProjection = False

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

	def addCommand(self):
		gm, fm = tthTool.getGlyphAndFontModel()
		if tthTool.selectedAxis == 'X':
			stem = self.stemNameX
		else:
			stem = self.stemNameY
		code = 'singlediagonal'
		cmd = self.genNewCommand()
		cmd.set('code', code)
		self.setupCommandPointFromLoc('point1',  cmd, self.point1)
		self.setupCommandPointFromLoc('point2',  cmd, self.point2)
		projDir = (self.startPoint - self.point1.pos)
		cmd.set('projection', str(atan2(projDir.y, projDir.x)))
		shiftPressed = getActiveEventTool().getModifiers()['shiftDown']
		optionPressed = getActiveEventTool().getModifiers()['optionDown']
		if self.roundDistance or shiftPressed:
			cmd.set('round', 'true')
		elif optionPressed:
			stem = None
		else:
			if stem == 'None': stem = None
			if stem == 'Guess': stem = fm.guessStem(self.point1.rfPoint, self.point2.rfPoint)
			if stem != None:
				cmd.set('stem', stem)
			else:
				align = self.getAlignment()
				if align != 'None':
					cmd.set('align', align)
		gm.addCommand(fm, cmd)

	def mouseDown(self, point, clickCount, scale):
		self.mouseDownClickPos = geom.makePoint(point)
		self.mouseDraggedPos = self.mouseDownClickPos
		gm, fm = tthTool.getGlyphAndFontModel()
		src = gm.pointClicked(geom.makePoint(point), fm, scale, alsoOff=self.worksOnOFF)
		src = src[0]
		if src and (not self.lookingForProjection):
			self.dragging = True
			self.startPoint = src
		elif self.lookingForProjection:
			if src:
				self.startPoint = geom.makePoint(src.pos)
			else:
				self.startPoint = geom.Point(point.x, point.y)
		else:
			self.dragging = False
			self.startPoint = None

	def mouseUp(self, point, scale):
		if not self.dragging: return
		if not self.lookingForProjection:
			gm, fm = tthTool.getGlyphAndFontModel()
			p2 = gm.pointClicked(geom.makePoint(point), fm, scale, alsoOff=self.worksOnOFF)
			p2 = p2[0] # a TTHGlyph::PointLocation
			s = self.startPoint.pos
			if p2 and (s.x != p2.pos.x or s.y != p2.pos.y):
				self.point1 = self.startPoint
				self.point2 = p2
				self.lookingForProjection = True
			else:
				self.dragging = False
				self.interpolatedPoint = None
				self.startPoint = None
		else:
			if not self.realClick(point): return
			gm = tthTool.getGlyphModel()
			if self.startPoint:
				e = self.startPoint#.pos
				s = self.point1.pos
				m = self.point2.pos
				if (s.x != e.x or s.y != e.y):
					self.addCommand()
			self.lookingForProjection = False
			self.dragging = False
			self.point1 = None
			self.point2 = None
			self.startPoint = None

	# - - - - DRAW

	def draw(self, scale):
		if not self.dragging: return
		locked, p = self.magnet(scale)
		if self.lookingForProjection:
			startPos = self.point1.pos
			midPos = self.point2.pos
			DR.drawSingleArrow(scale, startPos, midPos, DR.kSglDiaglinkColor, 20)
			DR.drawStraightSingleArrow(scale, startPos, p, DR.kSglDiaglinkColor, -20)
		else:
			DR.drawSingleArrow(scale, self.startPoint.pos, p, DR.kSglDiaglinkColor, 20)
		if locked:
			DR.drawCircleAtPoint(10*scale, 2*scale, p.x, p.y, DR.kSglDiaglinkColor)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class DoubleDiagonalLinkTool(SingleDiagonalLinkTool):

	def __init__(self):
		super(DoubleDiagonalLinkTool, self).__init__("Diagonal Double Link")
		self.stemNameX = 'Guess'
		self.stemNameY = 'Guess'

	def updateUI(self):
		self.updateStemUI()
		self.hideUI()
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools
		w.StemTypeText.show(True)
		w.StemTypePopUpButton.show(True)

	def addCommand(self):
		gm, fm = tthTool.getGlyphAndFontModel()
		if tthTool.selectedAxis == 'X':
			stem = self.stemNameX
		else:
			stem = self.stemNameY
		code = 'doublediagonal'
		cmd = self.genNewCommand()
		cmd.set('code', code)
		self.setupCommandPointFromLoc('point1',  cmd, self.point1)
		self.setupCommandPointFromLoc('point2',  cmd, self.point2)
		projDir = (self.startPoint - self.point1.pos)
		cmd.set('projection', str(atan2(projDir.y, projDir.x)))
		if stem == 'None': stem = None
		if stem == 'Guess': stem = fm.guessStem(self.point1.rfPoint, self.point2.rfPoint)
		if stem != None:
			cmd.set('stem', stem)
		else:
			cmd.set('round', 'true')
		gm.addCommand(fm, cmd)

	# - - - - DRAW

	def draw(self, scale):
		if not self.dragging: return
		locked, p = self.magnet(scale)
		if self.lookingForProjection:
			pos1 = self.point1.pos
			pos2 = self.point2.pos
			DR.drawDoubleArrow(scale, pos1, pos2, True, DR.kDblDiaglinkColor, 20)
			DR.drawStraightSingleArrow(scale, pos1, p, DR.kDblDiaglinkColor, -20)
		else:
			DR.drawDoubleArrow(scale, self.startPoint.pos, p, True, DR.kDblDiaglinkColor, 20)
		if locked:
			DR.drawCircleAtPoint(10*scale, 2*scale, p.x, p.y, DR.kDblDiaglinkColor)
