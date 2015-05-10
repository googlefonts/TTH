
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
		cmd = {	'code': code,
				'point1': self.interpolatedPoint1[0].name,
				'point': self.interpolatedPoint[0].name,
				'point2': self.startPoint[0].name,
			}
		align = self.getAlignment()
		if align != 'None':
			cmd['align'] = align
		gm.addCommand(cmd)

	def mouseDown(self, point, clickCount):
		self.mouseDownClickPos = geom.makePoint(point)
		self.mouseDraggedPos = self.mouseDownClickPos
		gm = tthTool.getGlyphModel()
		src = gm.pointClicked(geom.makePoint(point))
		if src[0]:
			self.dragging = True
			self.startPoint = src[0] # a quadruple (onCurve, cont, seg, 0)
		elif self.lookingForPoint2:
			self.startPoint = None
			return
		else:
			self.dragging = False
			self.startPoint = None

	def mouseUp(self, point):
		if not self.dragging: return
		if not self.lookingForPoint2:
			gm = tthTool.getGlyphModel()
			mid = gm.pointClicked(geom.makePoint(point))
			s = self.startPoint[0]
			if mid[0]: m = mid[0][0]
			if mid[0] and (s.x != m.x or s.y != m.y):
				self.interpolatedPoint1 = self.startPoint
				self.interpolatedPoint = mid[0] # a quadruple (onCurve, cont, seg, 0)
				self.lookingForPoint2 = True
			else:
				self.dragging = False
				self.interpolatedPoint = None
				self.startPoint = None
		else:
			if not self.realClick(point): return
			gm = tthTool.getGlyphModel()
			if self.startPoint:
				e = self.startPoint[0]
				s = self.interpolatedPoint1[0]
				m = self.interpolatedPoint[0]
				if (s.x != e.x or s.y != e.y) and (m.x != e.x or m.y != e.y):
					self.addCommand()
			self.lookingForPoint2 = False
			self.dragging = False
			self.interpolatedPoint = None
			self.interpolatedPoint1 = None
			self.startPoint = None

	def draw(self, scale):
		if not self.dragging: return
		if self.lookingForPoint2:
			startPos = geom.makePoint(self.interpolatedPoint1[0])
			midPos = geom.makePoint(self.interpolatedPoint[0])
			DR.drawDoubleArrow(scale, midPos, startPos, True, DR.kInterpolateColor, 20)
			DR.drawDoubleArrow(scale, midPos, self.mouseDraggedPos, True, DR.kInterpolateColor, -20)
		else:
			startPos = geom.makePoint(self.startPoint[0])
			DR.drawDoubleArrow(scale, self.mouseDraggedPos, startPos, True, DR.kInterpolateColor, 20)
