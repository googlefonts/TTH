
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool
from drawing import geom, utilities as DR
from AppKit import NSBezierPath

class DeltaTool(TTHCommandTool):

	def __init__(self, final = False):
		if final:
			super(DeltaTool, self).__init__("Final Delta")
		else:
			super(DeltaTool, self).__init__("Middle Delta")
		self.worksOnOFF = True
		self.final = final
		self.mono  = True
		self.gray  = True
		self.offset = 0
		self.range1 = tthTool.PPM_Size
		self.range2 = tthTool.PPM_Size
		# for drawing
		self.pitch = tthTool.getFontModel().getPitch()
		if final:
			self.color = DR.kFinalDeltaColor
		else:
			self.color = DR.kDeltaColor

	def updateUI(self):
		self.hideUI()
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools

		w.DeltaMonochromeCheckBox.set(self.mono)
		w.DeltaGrayCheckBox.set(self.gray)
		w.DeltaOffsetSlider.set(self.offset + 8)
		tthTool.mainPanel.lock()
		w.DeltaOffsetEditText.set(str(self.offset))
		w.DeltaRange1ComboBox.set(str(self.range1))
		w.DeltaRange2ComboBox.set(str(self.range2))
		tthTool.mainPanel.unlock()

		w.DeltaOffsetText.show(True)
		w.DeltaOffsetSlider.show(True)
		w.DeltaRangeText.show(True)
		w.DeltaRange1ComboBox.show(True)
		w.DeltaRange2ComboBox.show(True)
		w.DeltaOffsetEditText.show(True)
		w.DeltaMonochromeText.show(True)
		w.DeltaMonochromeCheckBox.show(True)
		w.DeltaGrayText.show(True)
		w.DeltaGrayCheckBox.show(True)

	def setMono(self, mono):
		self.mono = mono

	def setGray(self, gray):
		self.gray = gray

	def setOffset(self, offset):
		try:
			offset = max(-8, min(8, int(offset)))
		except:
			offset = self.offset
		self.offset = offset
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools
		w.DeltaOffsetSlider.set(self.offset + 8)
		w.DeltaOffsetEditText.set(str(self.offset))

	def setRange(self, value1, value2):
		value1 = max(9, value1)
		value2 = max(9, value2)
		if value2 < value1:
			value2 = value1
		self.range1 = value1
		self.range2 = value2
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools
		w.DeltaRange1ComboBox.set(str(self.range1))
		w.DeltaRange2ComboBox.set(str(self.range2))

	def addCommand(self):
		if self.offset == 0:
			return
		gm, fm = tthTool.getGlyphAndFontModel()
		if self.final:
			code = 'fdelta'
		else:
			code = 'mdelta'
		if tthTool.selectedAxis == 'X':
			code += 'h'
		else:
			code += 'v'
		cmd = self.genNewCommand()
		cmd.set('code',  code)
		self.setupCommandPointFromLoc('point', cmd, self.startPoint)
		cmd.set('ppm1',  str(self.range1))
		cmd.set('ppm2',  str(self.range2))
		cmd.set('delta', str(self.offset))
		if self.gray:
			cmd.set('gray', 'true')
		else:
			cmd.set('gray', 'false')
		if self.mono:
			cmd.set('mono', 'true')
		else:
			cmd.set('mono', 'false')
		gm.addCommand(fm, cmd)

	def mouseDown(self, point, clickCount):
		super(DeltaTool, self).mouseDown(point, clickCount)
		self.pitch = tthTool.getFontModel().getPitch()
		self.originalOffset = self.offset
		self.cancel = False

	def mouseUp(self, point):
		if not self.dragging: return
		self.dragging = False
		if self.cancel:
			self.cancel = False
			return
		self.addCommand()

	def draw(self, scale):
		if not self.dragging: return
		unit = geom.Point(1.0,0.0)
		perp = geom.Point(0.0,1.0)
		if tthTool.selectedAxis == 'X':
			coord = 0
		else:
			coord = 1
			unit,perp = perp,unit
		startPt = geom.makePoint(self.startPoint.pos)
		value  = 8.0/self.pitch * (self.mouseDraggedPos[coord] - startPt[coord])
		pvalue = 8.0/self.pitch * (self.mouseDraggedPos[1-coord] - startPt[1-coord])
		if abs(pvalue) > abs(value):
			self.setOffset(self.originalOffset)
			self.cancel = True
			return
		self.cancel = False
		value = min(8, max(-8, int(value)))
		end = startPt + value*self.pitch/8.0 * unit
		self.setOffset(value)
		path = NSBezierPath.bezierPath()
		path.moveToPoint_(startPt)
		path.lineToPoint_(end)
		self.color.set()
		path.setLineWidth_(scale*2)
		path.stroke()
		DR.drawLozengeAtPoint(scale, 8, end.x, end.y, self.color)
