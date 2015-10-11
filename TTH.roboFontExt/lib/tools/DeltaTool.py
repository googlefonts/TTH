
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool
from models.TTHGlyph import PointLocation
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
		self.editedCommand = None
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
		gm, fm = tthTool.getGlyphAndFontModel()
		if self.offset == 0:
			if self.editedCommand != None:
				gm.removeHintingCommand(self.editedCommand)
				self.editedCommand = None
			return
		if self.final:
			code = 'fdelta'
		else:
			code = 'mdelta'
		if tthTool.selectedAxis == 'X':
			code += 'h'
		else:
			code += 'v'
		doModify = False
		if self.editedCommand is None:
			cmd = self.genNewCommand()
		else:
			cmd = self.editedCommand
			doModify = True
			self.editedCommand = None
		cmd.set('code',  code)
		cmd.set('delta', str(self.offset))
		cmd.set('active', 'true')
		if not doModify:
			self.setupCommandPointFromLoc('point', cmd, self.startPoint)
			cmd.set('ppm1',  str(self.range1))
			cmd.set('ppm2',  str(self.range2))
			if self.gray:
				cmd.set('gray', 'true')
			else:
				cmd.set('gray', 'false')
			if self.mono:
				cmd.set('mono', 'true')
			else:
				cmd.set('mono', 'false')
			gm.addCommand(fm, cmd)
		else:
			gm.updateGlyphProgram(fm)

	def mouseDown(self, point, clickCount):
		super(DeltaTool, self).mouseDown(point, clickCount)
		self.pitch = tthTool.getFontModel().getPitch()
		self.originalOffset = self.offset
		self.cancel = False
		if self.dragging: return
		gm, fm = tthTool.getGlyphAndFontModel()
		clickedPoint = geom.makePoint(point)
		listDistCmd = []
		for c in gm.hintingCommands:
			cmd_code = c.get('code')
			if c.get('active', 'true') == 'false': continue
			X = (tthTool.selectedAxis == 'X')
			Y = not X
			if self.final:
				if (X and cmd_code != 'fdeltah'): continue
				if (Y and cmd_code != 'fdeltav'): continue
			else:
				if (X and cmd_code != 'mdeltah'): continue
				if (Y and cmd_code != 'mdeltav'): continue
			if not (int(c.get('ppm1')) <= tthTool.PPM_Size <= int(c.get('ppm2'))): continue
			offset = int(c.get('delta'))
			deltaPoint = gm.positionForPointName(c.get('point'), fm, c.get('base'))
			if X and cmd_code[-1] == 'h':
				deltaPoint += geom.Point((offset/8.0)*self.pitch, 0)
			elif Y and cmd_code[-1] == 'v':
				deltaPoint += geom.Point(0, (offset/8.0)*self.pitch)
			d = (clickedPoint - deltaPoint).squaredLength()
			listDistCmd.append((d, c))
		if listDistCmd != []:
			d, c = min(listDistCmd)
			if d <= 10.0*10.0:
				c.set('active', 'false')
				cont, seg, idx = gm.csiOfPointName(c.get('point'), fm, c.get('base'))
				compIdx = c.get('base')
				offset = None
				if compIdx:
					compIdx = int(compIdx)
					compo = gm.RFGlyph.components[compIdx]
					g = fm.f[compo.baseGlyph]
					offset = geom.makePointForPair(compo.offset)
				else:
					g = gm.RFGlyph
				self.startPoint = PointLocation(g[cont][seg][idx], cont, seg, idx, compIdx, offset)
				self.dragging = True
				self.editedCommand = c

	def mouseUp(self, point):
		if not self.dragging: return
		self.dragging = False
		if self.cancel:
			self.cancel = False
			self.editedCommand = None
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
		startPt = self.startPoint.pos
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
