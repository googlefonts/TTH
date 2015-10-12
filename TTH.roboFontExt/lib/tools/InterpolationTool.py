
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool
from drawing import geom, utilities as DR

class InterpolationTool(TTHCommandTool):

	def __init__(self):
		super(InterpolationTool, self).__init__("Interpolation")
		self.allowedAlignments = TTHCommandTool.allowedAlignmentTypesWithNone
		self.interpolatedPoint1 = None
		self.interpolatedPoint = None
		self.lookingForPoint2 = False

	def reset(self):
		super(InterpolationTool, self).reset()
		self.interpolatedPoint1 = None
		self.interpolatedPoint = None
		self.lookingForPoint2 = False

	def updateUI(self):
		self.updateAlignmentUI(withNone = True)
		self.hideUI()
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools
		w.AlignmentTypeText.show(True)
		w.AlignmentTypePopUpButton.show(True)

	def addCommand(self):
		gm, fm = tthTool.getGlyphAndFontModel()
		if tthTool.selectedAxis == 'X':
			code = 'interpolateh'
		else:
			code = 'interpolatev'
		cmd = self.genNewCommand()
		cmd.set('code',   code)
		self.setupCommandPointFromLoc('point1', cmd, self.interpolatedPoint1)
		self.setupCommandPointFromLoc('point',  cmd, self.interpolatedPoint)
		self.setupCommandPointFromLoc('point2', cmd, self.startPoint)
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
		if src:
			self.dragging = True
			self.startPoint = src # a quadruple (onCurve, cont, seg, idx)
		elif self.lookingForPoint2:
			self.startPoint = None
			return
		else:
			self.dragging = False
			self.startPoint = None

	def mouseUp(self, point, scale):
		if not self.dragging: return
		if not self.lookingForPoint2:
			gm, fm = tthTool.getGlyphAndFontModel()
			mid = gm.pointClicked(geom.makePoint(point), fm, scale, alsoOff=self.worksOnOFF)
			mid = mid[0]
			s = self.startPoint.pos
			if mid: m = mid.pos
			if mid and (s.x != m.x or s.y != m.y):
				self.interpolatedPoint1 = self.startPoint
				self.interpolatedPoint = mid # a quadruple (onCurve, cont, seg, idx)
				self.lookingForPoint2 = True
			else:
				self.dragging = False
				self.interpolatedPoint = None
				self.startPoint = None
		else:
			if not self.realClick(point): return
			gm = tthTool.getGlyphModel()
			if self.startPoint:
				e = self.startPoint.pos
				s = self.interpolatedPoint1.pos
				m = self.interpolatedPoint.pos
				if (s.x != e.x or s.y != e.y) and (m.x != e.x or m.y != e.y):
					self.addCommand()
			self.lookingForPoint2 = False
			self.dragging = False
			self.interpolatedPoint = None
			self.interpolatedPoint1 = None
			self.startPoint = None

	def draw(self, scale):
		if not self.dragging: return
		locked, p = self.magnet(scale)
		if self.lookingForPoint2:
			startPos = self.interpolatedPoint1.pos
			midPos = self.interpolatedPoint.pos
			DR.drawDoubleArrow(scale, midPos, startPos, True, DR.kInterpolateColor, 20)
			DR.drawDoubleArrow(scale, midPos, p, True, DR.kInterpolateColor, -20)
		else:
			startPos = self.startPoint.pos
			DR.drawDoubleArrow(scale, p, startPos, True, DR.kInterpolateColor, 20)
		if locked:
			DR.drawCircleAtPoint(10*scale, 2*scale, p.x, p.y, DR.kInterpolateColor)
