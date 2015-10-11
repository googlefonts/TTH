
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool
from drawing import geom, utilities as DR

class AlignTool(TTHCommandTool):

	def __init__(self):
		super(AlignTool, self).__init__("Align")
		self.allowedAlignments = TTHCommandTool.allowedAlignmentTypes

	def updateUI(self):
		self.updateAlignmentUI(withNone = False)
		self.hideUI()
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools
		w.AlignmentTypeText.show(True)
		w.AlignmentTypePopUpButton.show(True)

	def addCommand(self):
		gm, fm = tthTool.getGlyphAndFontModel()
		point = self.startPoint[0]
		zoneName, zone = fm.zoneAtPoint(point)
		align = self.getAlignment()
		cmd = self.genNewCommand()
		cmd.set('point', point.name)
		if self.startPoint[4]:
			cmd.set('base', self.startPoint[4].baseGlyph)
		if tthTool.selectedAxis == 'X':
			cmd.set('code', 'alignh')
			if align != 'None': cmd.set('align', align)
		elif zoneName != None:
			cmd.set('zone', zoneName)
			if zone['top']:
				cmd.set('code', 'alignt')
			else:
				cmd.set('code', 'alignb')
		else:
			cmd.set('code', 'alignv')
			if align != 'None': cmd.set('align', align)
		gm.addCommand(fm, cmd)

	def mouseUp(self, point):
		if not self.dragging: return
		self.dragging = False
		if not self.realClick(point): return
		if self.startPoint != None:
			self.addCommand()

	def draw(self, scale):
		if not self.dragging: return
		if not self.realClick(self.mouseDraggedPos): return
		if tthTool.selectedAxis == 'X':
			direction = geom.Point(1, 0)
		else:
			direction = geom.Point(0, 1)
		q = geom.makePoint(self.startPoint[0])
		compo = self.startPoint[4]
		if compo:
			q = q + geom.makePointForPair(compo.offset)
		DR.drawArrowAtPoint(scale, 20, direction, q, DR.kArrowColor)
		DR.drawArrowAtPoint(scale, 20, direction.opposite(), q, DR.kArrowColor)
