
import xml.etree.ElementTree as ET
from models.TTHTool import uniqueInstance as tthTool
from drawing import geom

class TTHCommandTool(object):

	def __init__(self, name):
		self.name = name
		self.worksOnOFF = True
		self.alignment = 0
		self.allowedAlignments = ['Unused']
		self.reset()

	def reset(self):
		self.mouseDownClickPos = None
		self.mouseDraggedPos = None
		self.dragging = False
		self.startPoint = None
		self.roundDistance = False

	def genNewCommand(self):
		cmd = ET.Element('ttc')
		cmd.set('active', 'true')
		cmd.set('shift', '0')
		return cmd

	def setupCommandPointFromLoc(self, which, cmd, loc):
		'''parameter which is either 'point', 'point1' or 'point2'.'''
		if 'point' not in which:
			print "[TTH ERROR] in setupCommandPointFromLoc"
			raise Exception
			return
		c = which[-1]
		base = 'base'
		if c in '12': base = base + c
		cmd.set(which, loc.rfPoint.name)
		if loc.component != None:
			cmd.set(base, str(loc.component))

	def switchRounding(self):
		self.roundDistance = not self.roundDistance

	def changeAlignement(self):
		n = len(self.allowedAlignmentTypes)
		self.setAlignment((self.alignment+1)%n)

	allowedAlignmentTypes = ['round', 'left', 'right', 'center', 'double']
	displayX = [	'Closest Pixel Edge',
				'Left Edge',
				'Right Edge',
				'Center of Pixel',
				'Double Grid']
	displayY = [	'Closest Pixel Edge',
				'Bottom Edge',
				'Top Edge',
				'Center of Pixel',
				'Double Grid']
	allowedAlignmentTypesWithNone = ['None'] + allowedAlignmentTypes
	displayXWithNone = ['Do Not Align to Grid'] + displayX
	displayYWithNone = ['Do Not Align to Grid'] + displayY

	def hideUI(self):
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools
		w.AlignmentTypeText.show(False)
		w.AlignmentTypePopUpButton.show(False)
		w.RoundDistanceText.show(False)
		w.RoundDistanceCheckBox.show(False)
		w.StemTypeText.show(False)
		w.StemTypePopUpButton.show(False)
		w.DeltaOffsetText.show(False)
		w.DeltaOffsetSlider.show(False)
		w.DeltaRangeText.show(False)
		w.DeltaRange1ComboBox.show(False)
		w.DeltaRange2ComboBox.show(False)
		w.DeltaOffsetEditText.show(False)
		w.DeltaMonochromeText.show(False)
		w.DeltaMonochromeCheckBox.show(False)
		w.DeltaGrayText.show(False)
		w.DeltaGrayCheckBox.show(False)

	def updateUI(self):
		pass

	# Alignment UI

	def setAlignment(self, index):
		if index < 0 or index >= len(self.allowedAlignments):
			index = 0
		self.alignment = index
		#print "{}.setAlignment({}) --> {}".format(self.name, index, self.getAlignment())

	def getAlignment(self):
		return self.allowedAlignments[self.alignment]

	def updateAlignmentUI(self, withNone = True):
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools
		if tthTool.selectedAxis == 'X':
			if withNone:
				w.AlignmentTypePopUpButton.setItems(self.displayXWithNone)
			else:
				w.AlignmentTypePopUpButton.setItems(self.displayX)
		else:
			if withNone:
				w.AlignmentTypePopUpButton.setItems(self.displayYWithNone)
			else:
				w.AlignmentTypePopUpButton.setItems(self.displayY)
		w.AlignmentTypePopUpButton.set(self.alignment)

	# STEM UI

	def setStem(self, name):
		if tthTool.selectedAxis == 'X':
			self.stemNameX = name
		else:
			self.stemNameY = name

	def getStem(self, name):
		if tthTool.selectedAxis == 'X':
			return self.stemNameX
		else:
			return self.stemNameY

	def updateStemUI(self):
		if tthTool.mainPanel is None: return
		w = tthTool.mainPanel.wTools
		tthTool.mainPanel.makeStemsList()
		stems = tthTool.mainPanel.stemsList
		w.StemTypePopUpButton.setItems(stems)
		try:
			if tthTool.selectedAxis == 'X':
				i = stems.index(self.stemNameX)
			else:
				i = stems.index(self.stemNameY)
		except:
			i = 1 # 'Guess'
		if tthTool.selectedAxis == 'X':
			self.stemNameX = stems[i]
		else:
			self.stemNameY = stems[i]
		w.StemTypePopUpButton.set(i)

	# - - - - MOUSE EVENTS

	def magnet(self, scale):
		gm, fm = tthTool.getGlyphAndFontModel()
		tgt = gm.pointClicked(self.mouseDraggedPos, fm, scale, alsoOff=self.worksOnOFF)
		loc = tgt[0]
		if loc:
			return True, loc.pos
		else:
			return False, self.mouseDraggedPos

	def realClick(self, point):
		upPoint = geom.makePoint(point)
		return (upPoint - self.mouseDownClickPos).squaredLength() <= 42.0

	def mouseDown(self, point, clickCount, scale):
		self.mouseDownClickPos = geom.makePoint(point)
		self.mouseDraggedPos = self.mouseDownClickPos
		gm, fm = tthTool.getGlyphAndFontModel()
		src = gm.pointClicked(geom.makePoint(point), fm, scale, alsoOff=self.worksOnOFF)
		loc = src[0]
		if loc:
			self.dragging = True
			self.startPoint = loc
			# loc is an object of type TTHGlyph::PointLocation(rfPoint, cont, seg, idx, component) with
			# glyph[cont][seg].points[idx] == rfPoint
		else:
			self.dragging = False
			self.startPoint = None

	def mouseDragged(self, point, scale):
		self.mouseDraggedPos = geom.makePoint(point)

	def mouseUp(self, point, scale):
		self.dragging = False

	# - - - - DRAW

	def draw(self, scale):
		pass

# = = = = = = = = = = = = = = = = = = = = = = = = = = = FUNCTIONS

import tools.AlignTool as AT, tools.SingleLinkTool as SLT, tools.DoubleLinkTool as DLT
import tools.DiagonalLinkTool as DiagLT
import tools.InterpolationTool as IT, tools.DeltaTool as DT, tools.SelectionTool as ST
reload(AT)
reload(SLT)
reload(DLT)
reload(DiagLT)
reload(IT)
reload(DT)
reload(ST)

kCommandToolNames = ['Align',
		'Single Link',
		'Diagonal Single Link',
		'Double Link',
		'Diagonal Double Link',
		'Interpolation',
		'Middle Delta', 'Final Delta',
		'Selection']

def createTool(toolName):
	if toolName == 'Align':           return AT.AlignTool()
	elif toolName == 'Single Link':   return SLT.SingleLinkTool()
	elif toolName == 'Double Link':   return DLT.DoubleLinkTool()
	elif toolName == 'Diagonal Single Link': return DiagLT.SingleDiagonalLinkTool()
	elif toolName == 'Diagonal Double Link': return DiagLT.DoubleDiagonalLinkTool()
	elif toolName == 'Interpolation': return IT.InterpolationTool()
	elif toolName == 'Middle Delta':  return DT.DeltaTool(final=False)
	elif toolName == 'Final Delta':   return DT.DeltaTool(final=True)
	else:                             return ST.SelectionTool()
