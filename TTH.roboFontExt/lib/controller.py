#coding=utf-8

from mojo.events import *
from mojo.UI import *
from mojo.extensions import *
from mojo.drawingTools import *
from mojo.canvas import Canvas
from lib.doodleMenus import BaseMenu
from lib.tools.defaults import getDefault, setDefault
from robofab.plistlib import Data
from robofab.world import *
import robofab.interface.all.dialogs as Dialogs
from mojo.roboFont import *
from vanilla import *
from defconAppKit.windows.baseWindow import BaseWindowController
from lib.UI.spaceCenter.glyphSequenceEditText import splitText
import tempfile
import time

import tt_tables
import TTHintAsm
import view
import TextRenderer as TR
import preview

import xml.etree.ElementTree as ET
import math, os

FL_tth_key = "com.fontlab.v2.tth"

toolbarIcon = ExtensionBundle("TTH").get("toolbarIcon")

cursorDefaultPath = ExtensionBundle("TTH").get("cursorDefaultTTH")
cursorDefault = CreateCursor(cursorDefaultPath, hotSpot=(2, 2))

cursorAlignPath = ExtensionBundle("TTH").get("cursorAlign")
cursorAlign = CreateCursor(cursorAlignPath, hotSpot=(2, 2))

cursorSingleLinkPath = ExtensionBundle("TTH").get("cursorSingleLink")
cursorSingleLink = CreateCursor(cursorSingleLinkPath, hotSpot=(2, 2))

cursorDoubleLinkPath = ExtensionBundle("TTH").get("cursorDoubleLink")
cursorDoubleLink = CreateCursor(cursorDoubleLinkPath, hotSpot=(2, 2))

cursorInterpolationPath = ExtensionBundle("TTH").get("cursorInterpolation")
cursorInterpolation = CreateCursor(cursorInterpolationPath, hotSpot=(2, 2))

cursorMiddleDeltaPath = ExtensionBundle("TTH").get("cursorMiddleDelta")
cursorMiddleDelta = CreateCursor(cursorMiddleDeltaPath, hotSpot=(2, 2))

cursorFinalDeltaPath = ExtensionBundle("TTH").get("cursorFinalDelta")
cursorFinalDelta = CreateCursor(cursorFinalDeltaPath, hotSpot=(2, 2))


whiteColor = NSColor.whiteColor()
blackColor = NSColor.blackColor()
axisColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.3)
gridColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.1)
centerpixelsColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.5)
zonecolor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .7, .2, .2)
zonecolorLabel = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .7, .2, 1)
arrowColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .25, .5, 1)
outlineColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, .5)
discColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .3, .94, 1)
lozengeColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 0, 0, 1)
linkColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.5, 0, 0, 1)
stemColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .8, 0, 1)
doublinkColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .25, 1, 1)
interpolatecolor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.25, .8, 0, 1)
deltacolor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .5, 0, 1)
finaldeltacolor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.73, .3, .8, 1)
sidebearingColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .3, .94, 1)
borderColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, .8)
shadowColor =  NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, .8)


def topologicalSort(l, f):
	n = len(l)
	preds = [[] for i in l]
	visited = [False for i in l]
	loop = list(visited) # separate copy of visited
	# build the list of predecessors for each element of |l|
	for i in range(n):
		for j in range(i+1,n):
			(comp, swap) = f(l[i], l[j])
			if not comp:
				continue
			if swap:
				preds[i].append(j)
			else:
				preds[j].append(i)
	result = []
	def visit(i):
		if loop[i]:
			raise Exception("loop")
		if visited[i]:
			return
		loop[i] = True
		for p in preds[i]:
			visit(p)
		loop[i] = False
		visited[i] = True
		result.append(l[i])
	try:
		for i in range(n):
			visit(i)
		return result
	except:
		pass
	print "ERROR: Found a loop in topological sort"
	return l

def pointsApproxEqual(p_glyph, p_cursor):
	return (abs(p_glyph[0] - p_cursor[0]) < 10) and (abs(p_glyph[1] - p_cursor[1]) < 10)

def pointInCommand(commandPos, p_cursor):
	x = commandPos[0][0]
	y = commandPos[0][1]
	width = commandPos[1][0]
	height = commandPos[1][1]
	return (p_cursor[0] >= (x-width/2) and p_cursor[0] <= (x+width/2) and p_cursor[1] >= (y-height/2) and p_cursor[1] <= (y+height/2))


def find_closest(l, p, point):
	if l == []:
		return None
	candidate = (l[0], distance(l[0], point))
	for e in l:
		if p(e):
			if distance(e, point) < candidate[1]:
				candidate = (e, distance(e, point))
	if p(candidate[0]):
		return candidate[0]
	return None

def find_in_list(l, p):
	for e in l:
		if p(e):
			return e
	return None

def find_in_dict(d, p):
	for k, v in d.iteritems():
		if p(k, v):
			return k
	return None

def getOrNone(dico, key):
	try:
		return dico[key]
	except:
		return None

def loadFonts():
	af = AllFonts()
	if not af:
		return
	return af

def loadCurrentFont(allFonts):
	cf = CurrentFont()
	for f in allFonts:
		if f.fileName == cf.fileName:
			return cf


def getGlyphNameByUnicode(unicodeToNameDict, unicodeChar):
	return unicodeToNameDict[unicodeChar]

def difference(point1, point2):
	return ((point1[0] - point2[0]), (point1[1] - point2[1]))

def distance(point1, point2):
	return math.sqrt((point2[0]-point1[0])*(point2[0]-point1[0]) + (point2[1]-point1[1])*(point2[1]-point1[1]))

def getAngle((x1, y1), (x2, y2)):
	xDiff = x2-x1
	yDiff= y2-y1 
	return math.atan2(yDiff, xDiff)

def checkDrawingPreferences():
	return (getDefault('drawingSegmentType') == 'qcurve')

def checkSegmentType(font):
	try:
		segmentType = font.preferredSegmentType
	except:
		segmentType = font.preferedSegmentType
	return (segmentType == 'qcurve' or segmentType == 'qCurve')

class callbackAlignment():
	def __init__(self, TTHtoolInstance, alignmentType):
		self.ttht = TTHtoolInstance
		self.alignmentType = alignmentType

	def __call__(self, item):
		cmdIndex = self.ttht.commandRightClicked
		self.ttht.tthtm.g.prepareUndo('Alignment')
		self.ttht.glyphTTHCommands[cmdIndex]['align'] = self.alignmentType
		if 'round' in self.ttht.glyphTTHCommands[cmdIndex]:
			del self.ttht.glyphTTHCommands[cmdIndex]['round']
		if 'stem' in self.ttht.glyphTTHCommands[cmdIndex]:
			del self.ttht.glyphTTHCommands[cmdIndex]['stem']
		if self.ttht.glyphTTHCommands[cmdIndex]['code'] in ['alignt', 'alignb']:
			self.ttht.glyphTTHCommands[cmdIndex]['code'] = 'alignv'
			del self.ttht.glyphTTHCommands[cmdIndex]['zone']

		self.ttht.updateGlyphProgram()
		if self.ttht.tthtm.alwaysRefresh == 1:
			self.ttht.refreshGlyph()
		self.ttht.tthtm.g.performUndo()

class callbackZoneAlignment():
	def __init__(self, TTHtoolInstance, alignmentZone):
		self.ttht = TTHtoolInstance
		self.alignmentZone = alignmentZone

	def __call__(self, item):
		cmdIndex = self.ttht.commandRightClicked
		self.ttht.tthtm.g.prepareUndo('Zone Alignment')
		cmd = 'alignb'
		if 'top' in self.ttht.tthtm.zones[self.alignmentZone]:
			if self.ttht.tthtm.zones[self.alignmentZone]['top']:
				cmd = 'alignt'
			else:
				cmd = 'alignb'
		command = self.ttht.glyphTTHCommands[cmdIndex]
		command['code'] = cmd
		if 'align' in command:
			del command['align']

		command['zone'] = self.alignmentZone
		self.ttht.updateGlyphProgram()
		if self.ttht.tthtm.alwaysRefresh == 1:
			self.ttht.refreshGlyph()
		self.ttht.tthtm.g.performUndo()

class callbackDistance():
	def __init__(self, TTHtoolInstance, stemName):
		self.ttht = TTHtoolInstance
		self.stemName = stemName

	def __call__(self, item):
		cmdIndex = self.ttht.commandRightClicked
		self.ttht.tthtm.g.prepareUndo('Distance Alignment')
		self.ttht.glyphTTHCommands[cmdIndex]['stem'] = self.stemName
		if 'round' in self.ttht.glyphTTHCommands[cmdIndex]:
			del self.ttht.glyphTTHCommands[cmdIndex]['round']
		if 'align' in self.ttht.glyphTTHCommands[cmdIndex]:
			del self.ttht.glyphTTHCommands[cmdIndex]['align']
		self.ttht.updateGlyphProgram()
		if self.ttht.tthtm.alwaysRefresh == 1:
			self.ttht.refreshGlyph()
		self.ttht.tthtm.g.performUndo()

class callbackSetDeltaValue():
	def __init__(self, TTHtoolInstance, value):
		self.ttht = TTHtoolInstance
		self.value = str(value)

	def __call__(self, item):
		cmdIndex = self.ttht.commandRightClicked
		self.ttht.tthtm.g.prepareUndo('Delta Value')
		self.ttht.glyphTTHCommands[cmdIndex]['delta'] = self.value
		self.ttht.updateGlyphProgram()
		if self.ttht.tthtm.alwaysRefresh == 1:
			self.ttht.refreshGlyph()
		self.ttht.tthtm.g.performUndo()

class TTHTool(BaseEventTool):

	def __init__(self, tthtm):
		BaseEventTool.__init__(self)
		self.ready = False
		self.doneGeneratingPartialFont = False
		self.fontClosed = False
		self.p_glyphList = []
		self.glyphTTHCommands = []
		self.commandLabelPos = {}
		self.tthtm = tthtm
		self.startPoint = None

		temp = tempfile.NamedTemporaryFile(suffix='.ttf', delete=False)
		self.partialtempfontpath = temp.name
		temp.close()

		self.previewText = ''
		self.movingMouse = None

		self.testTextBox = TextBox((10, 10, 200, 22), "Hello this is a test", alignment="left", sizeStyle="regular")

		self.cachedPathes = {'grid':None, 'centers':None}

		self.previewInGlyphWindow = None
		self.messageInFront = False
		self.drawingPreferencesChanged = False


	### TTH Tool Icon and cursor ###
	def getToolbarIcon(self):
		## return the toolbar icon
		return toolbarIcon
		
	def getToolbarTip(self):
		return "TTH Hinting Tool"

	def getDefaultCursor(self):
		if self.tthtm.selectedHintingTool == "Align":
			return cursorAlign
		elif self.tthtm.selectedHintingTool == "Single Link":
			return cursorSingleLink
		elif self.tthtm.selectedHintingTool == "Double Link":
			return cursorDoubleLink
		elif self.tthtm.selectedHintingTool == "Interpolation":
			return cursorInterpolation
		elif self.tthtm.selectedHintingTool == "Middle Delta":
			return cursorMiddleDelta
		elif self.tthtm.selectedHintingTool == "Final Delta":
			return cursorFinalDelta
		return cursorDefault
	###############

	def becomeActive(self):
		self.previewInGlyphWindow = None
		if checkDrawingPreferences() == False:
			setDefault('drawingSegmentType', 'qcurve')
			self.drawingPreferencesChanged = True
			self.messageInFront = True
		 	Dialogs.Message("INFO:\nPreferences changed to\n'Draw with Quadratic (TrueType) curves'")
			self.messageInFront = False
		self.resetFonts(createWindows=True)
		self.updatePartialFont()

	def becomeInactive(self):
		if self.tthtm.showPreviewInGlyphWindow == 1 and self.previewInGlyphWindow != None:
			self.previewInGlyphWindow.removeFromSuperview()

		self.centralWindow.closeCentral()
		self.toolsWindow.closeTools()
		if self.tthtm.programWindowVisible == 1:
			self.programWindow.closeProgram()
		if self.tthtm.previewWindowVisible == 1:
			self.previewWindow.closePreview()
		if self.tthtm.assemblyWindowVisible == 1:
			self.assemblyWindow.closeAssembly()

		if self.drawingPreferencesChanged == True:
			setDefault('drawingSegmentType', 'curve')
			self.messageInFront = True
		 	Dialogs.Message("INFO:\nPreferences changed back to\n'Draw with Cubic (PostScript) curves'")
			self.messageInFront = False

	def fontResignCurrent(self, font):
		if self.fontClosed:
			return

		self.resetFonts(createWindows=False)

	def fontBecameCurrent(self, font):
		if self.fontClosed:
			return

		self.resetFonts(createWindows=False)
		self.updatePartialFont()
		self.fontClosed = False

	def fontWillClose(self, font):
		# 	return
		if len(AllFonts()) > 1:
			return

		self.centralWindow.wCentral.hide()
		self.toolsWindow.wTools.hide()
		if self.tthtm.programWindowVisible == 1:
			self.programWindow.wProgram.hide()
		if self.tthtm.previewWindowVisible == 1:
			self.previewWindow.wPreview.hide()
		if self.tthtm.assemblyWindowVisible == 1:
			self.assemblyWindow.wAssembly.hide()
		self.fontClosed = True

	def fontDidOpen(self, font):
		self.centralWindow.wCentral.show()
		self.toolsWindow.wTools.show()
		if self.tthtm.programWindowVisible == 1:
			self.programWindow.wProgram.show()
		if self.tthtm.previewWindowVisible == 1:
			self.previewWindow.wPreview.show()
		if self.tthtm.assemblyWindowVisible == 1:
			self.assemblyWindow.wAssembly.show()

		self.resetFonts(createWindows=False)
		self.updatePartialFont()

	def viewDidChangeGlyph(self):
		if self.fontClosed:
			return
		self.resetglyph()
		self.updatePartialFontIfNeeded()

	def currentGlyphChanged(self):
		self.resetglyph()
		self.updatePartialFontIfNeeded()

	def getSizeListIndex(self, size):
		sizeIndex = 0
		for i in range(len(self.centralWindow.PPMSizesList)):
			if self.centralWindow.PPMSizesList[i] == str(size):
				sizeIndex = i
		return sizeIndex

	def getSize(self):
		return self.tthtm.PPM_Size

	def setPreviewSize(self, size):
		try:
			size = int(size)
		except ValueError:
			size = 9

		return size

	def changePreviewSize(self, FromSize, ToSize):
		if FromSize > ToSize:
			FromSize = ToSize
		self.tthtm.previewFrom = FromSize
		self.tthtm.previewTo = ToSize
		self.previewWindow.wPreview.DisplayFromEditText.set(FromSize)
		self.previewWindow.wPreview.DisplayToEditText.set(ToSize)

	def changeSize(self, size):
		try:
			size = int(size)
		except ValueError:
			size = 9

		self.tthtm.setSize(size)
		sizeIndex = self.getSizeListIndex(self.tthtm.PPM_Size)
		self.centralWindow.wCentral.PPEMSizePopUpButton.set(sizeIndex)
		self.centralWindow.wCentral.PPEMSizeEditText.set(self.tthtm.PPM_Size)

		self.tthtm.resetPitch()

		self.cachedPathes['centers'] = None
		self.cachedPathes['grid'] = None
		self.cachedScale = None

		self.changeDeltaRange(self.tthtm.PPM_Size, self.tthtm.PPM_Size)
		if self.tthtm.previewWindowVisible == 1:
			self.previewWindow.wPreview.view.getNSView().setNeedsDisplay_(True)
		UpdateCurrentGlyphView()

	def changeAxis(self, axis):
		self.tthtm.setAxis(axis)
		if self.tthtm.selectedAxis == 'X':
			self.stemTypeList = self.tthtm.stemsListX
			self.toolsWindow.alignmentTypeListDisplay = ['Closest Pixel Edge', 'Left Edge', 'Right Edge', 'Center of Pixel', 'Double Grid']
			self.toolsWindow.alignmentTypeListLinkDisplay = ['Do Not Align to Grid', 'Closest Pixel Edge', 'Left Edge', 'Right Edge', 'Center of Pixel', 'Double Grid']
			self.toolsWindow.wTools.axisSegmentedButton.set(0)
		else:
			self.stemTypeList = self.tthtm.stemsListY
			self.toolsWindow.alignmentTypeListDisplay = ['Closest Pixel Edge', 'Bottom Edge', 'Top Edge', 'Center of Pixel', 'Double Grid']
			self.toolsWindow.alignmentTypeListLinkDisplay = ['Do Not Align to Grid', 'Closest Pixel Edge', 'Bottom Edge', 'Top Edge', 'Center of Pixel', 'Double Grid']
			self.toolsWindow.wTools.axisSegmentedButton.set(1)
		

		if self.tthtm.selectedHintingTool == "Align":
			self.toolsWindow.wTools.AlignmentTypePopUpButton.setItems(self.toolsWindow.alignmentTypeListDisplay)
			self.changeSelectedAlignmentTypeAlign(self.tthtm.selectedAlignmentTypeAlign)
		if self.tthtm.selectedHintingTool in ["Single Link", "Interpolation"]:
			self.toolsWindow.wTools.AlignmentTypePopUpButton.setItems(self.toolsWindow.alignmentTypeListLinkDisplay)
			self.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)

		UpdateCurrentGlyphView()

	def getPreviewListIndex(self, preview):
		previewIndex = 0
		for i in range(len(self.centralWindow.BitmapPreviewList)):
			if self.centralWindow.BitmapPreviewList[i] == preview:
				previewIndex = i
		return previewIndex

	def changeBitmapPreview(self, preview):
		if self.doneGeneratingPartialFont == False:
			return
		self.tthtm.setBitmapPreview(preview)
		self.tthtm.textRenderer = TR.TextRenderer(self.partialtempfontpath, preview, self)
		previewIndex = self.getPreviewListIndex(preview)
		self.centralWindow.wCentral.BitmapPreviewPopUpButton.set(previewIndex)

		if self.tthtm.g == None:
			return
		if self.tthtm.previewWindowVisible == 1:
			self.previewWindow.wPreview.view.getNSView().setNeedsDisplay_(True)
		UpdateCurrentGlyphView()

	def getHintingToolIndex(self, hintingTool):
		hintingToolIndex = 0
		for i in range(len(self.toolsWindow.hintingToolsList)):
			if self.toolsWindow.hintingToolsList[i] == hintingTool:
				hintingToolIndex = i
		return hintingToolIndex

	def changeSelectedHintingTool(self, hintingTool):
		self.tthtm.setHintingTool(hintingTool)
		hintingToolIndex = self.getHintingToolIndex(self.tthtm.selectedHintingTool)
		#self.centralWindow.wCentral.HintingToolPopUpButton.set(hintingToolIndex)
		if hintingToolIndex == 0:
			self.toolsWindow.AlignSettings()
			self.changeSelectedAlignmentTypeAlign(self.tthtm.selectedAlignmentTypeAlign)

			self.toolsWindow.wTools.toolsSegmentedButton.set(0)
			
		if hintingToolIndex == 1:
			self.toolsWindow.LinkSettings()
			self.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)
			if self.tthtm.selectedAxis == 'X':
				self.changeSelectedStemX(self.tthtm.selectedStemX)
			elif self.tthtm.selectedAxis == 'Y':
				self.changeSelectedStemY(self.tthtm.selectedStemY)
			self.changeRoundBool(self.tthtm.roundBool)

			self.toolsWindow.wTools.toolsSegmentedButton.set(1)

		if hintingToolIndex == 2:
			self.toolsWindow.DoubleLinkSettings()
			self.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)
			if self.tthtm.selectedAxis == 'X':
				self.changeSelectedStemX(self.tthtm.selectedStemX)
			elif self.tthtm.selectedAxis == 'Y':
				self.changeSelectedStemY(self.tthtm.selectedStemY)
			self.changeRoundBool(self.tthtm.roundBool)

			self.toolsWindow.wTools.toolsSegmentedButton.set(2)
			
		if hintingToolIndex == 3:
			self.toolsWindow.InterpolationSettings()
			self.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)

			self.toolsWindow.wTools.toolsSegmentedButton.set(3)

		if hintingToolIndex == 4:
			self.toolsWindow.DeltaSettings()

			self.toolsWindow.wTools.toolsSegmentedButton.set(4)

		if hintingToolIndex == 5:
			self.toolsWindow.DeltaSettings()

			self.toolsWindow.wTools.toolsSegmentedButton.set(5)


	def getAlignmentTypeAlignIndex(self, alignmentType):
		alignmentTypeIndex = 0
		for i in range(len(self.toolsWindow.alignmentTypeList)):
			if self.toolsWindow.alignmentTypeList[i] == alignmentType:
				alignmentTypeIndex = i
		return alignmentTypeIndex

	def changeSelectedAlignmentTypeAlign(self, alignmentType):
		self.tthtm.setAlignmentTypeAlign(alignmentType)
		alignmentTypeIndex = self.getAlignmentTypeAlignIndex(self.tthtm.selectedAlignmentTypeAlign)
		self.toolsWindow.wTools.AlignmentTypePopUpButton.set(alignmentTypeIndex)

	def getAlignmentTypeLinkIndex(self, alignmentType):
		alignmentTypeIndex = 0
		for i in range(len(self.toolsWindow.alignmentTypeListLink)):
			if self.toolsWindow.alignmentTypeListLink[i] == alignmentType:
				alignmentTypeIndex = i
		return alignmentTypeIndex

	def changeSelectedAlignmentTypeLink(self, alignmentType):
		self.tthtm.setAlignmentTypeLink(alignmentType)
		alignmentTypeIndex = self.getAlignmentTypeLinkIndex(self.tthtm.selectedAlignmentTypeLink)
		self.toolsWindow.wTools.AlignmentTypePopUpButton.set(alignmentTypeIndex)

	def swapAlignmentTypeLink(self):
		previousAlignmentTypeIndex = self.getAlignmentTypeLinkIndex(self.tthtm.selectedAlignmentTypeLink)
		if previousAlignmentTypeIndex < len(self.toolsWindow.alignmentTypeListLink)-1:
			self.changeSelectedAlignmentTypeLink(self.toolsWindow.alignmentTypeListLink[previousAlignmentTypeIndex+1])
		else:
			self.changeSelectedAlignmentTypeLink(self.toolsWindow.alignmentTypeListLink[0])

	def swapAlignmentTypeAlign(self):
		previousAlignmentTypeIndex = self.getAlignmentTypeAlignIndex(self.tthtm.selectedAlignmentTypeAlign)
		if previousAlignmentTypeIndex < len(self.toolsWindow.alignmentTypeList)-1:
			self.changeSelectedAlignmentTypeAlign(self.toolsWindow.alignmentTypeList[previousAlignmentTypeIndex+1])
		else:
			self.changeSelectedAlignmentTypeAlign(self.toolsWindow.alignmentTypeList[0])


	def getStemIndex(self, stemName, axis):
		stemIndex = 0
		if axis == 'X':
			stemsList = self.tthtm.stemsListX
		else:
			stemsList = self.tthtm.stemsListY

		for i in range(len(stemsList)):
			if stemsList[i] == stemName:
				stemIndex = i
		return stemIndex

	def changeSelectedStemX(self, stemName):
		self.tthtm.setStemX(stemName)
		stemIndex = self.getStemIndex(self.tthtm.selectedStemX, 'X')
		self.toolsWindow.wTools.StemTypePopUpButton.set(stemIndex)

	def changeSelectedStemY(self, stemName):
		self.tthtm.setStemY(stemName)
		stemIndex = self.getStemIndex(self.tthtm.selectedStemY, 'Y')
		self.toolsWindow.wTools.StemTypePopUpButton.set(stemIndex)

	def swapStemX(self):
		previousStemIndex = self.getStemIndex(self.tthtm.selectedStemX, 'X')
		if previousStemIndex < len(self.tthtm.stemsListX)-1:
			self.changeSelectedStemX(self.tthtm.stemsListX[previousStemIndex+1])
		else:
			self.changeSelectedStemX(self.tthtm.stemsListX[0])

	def swapStemY(self):
		previousStemIndex = self.getStemIndex(self.tthtm.selectedStemY, 'Y')
		if previousStemIndex < len(self.tthtm.stemsListY)-1:
			self.changeSelectedStemY(self.tthtm.stemsListY[previousStemIndex+1])
		else:
			self.changeSelectedStemY(self.tthtm.stemsListY[0])

	def changeRoundBool(self, roundBool):
		self.tthtm.setRoundBool(roundBool)
		self.toolsWindow.wTools.RoundDistanceCheckBox.set(self.tthtm.roundBool)

	def changeDeltaOffset(self, offset):
		try:
			offset = int(offset)
			if offset > 8:
				offset = 8
			if offset < -8:
				offset = -8
		except ValueError:
			offset = 0
		self.tthtm.setDeltaOffset(offset)
		self.toolsWindow.wTools.DeltaOffsetSlider.set(self.tthtm.deltaOffset + 8)
		self.toolsWindow.wTools.DeltaOffsetEditText.set(offset)

	def changeDeltaRange(self, value1, value2):
		try:
			value1 = int(value1)
		except ValueError:
			value1 = 9

		try:
			value2 = int(value2)
		except ValueError:
			value2 = 9

		self.tthtm.setDeltaRange1(value1)
		self.toolsWindow.wTools.DeltaRange1EditText.set(self.tthtm.deltaRange1)
		self.tthtm.setDeltaRange2(value2)
		self.toolsWindow.wTools.DeltaRange2EditText.set(self.tthtm.deltaRange2)

	def changeAlwaysRefresh(self, valueBool):
		self.tthtm.setAlwaysRefresh(valueBool)
		self.centralWindow.wCentral.AlwaysRefreshCheckBox.set(self.tthtm.alwaysRefresh)

	def changeStemSnap(self, value):
		try:
			value = int(value)
		except ValueError:
			value = 17
		self.tthtm.setStemsnap(value)
		self.tthtm.f.lib["com.fontlab.v2.tth"]["stemsnap"] = value

	def changeAlignppm(self, value):
		try:
			value = int(value)
		except ValueError:
			value = 48
		self.tthtm.setAlignppm(value)
		self.tthtm.f.lib["com.fontlab.v2.tth"]["alignppm"] = value

	def changeCodeppm(self, value):
		try:
			value = int(value)
		except ValueError:
			value = 48
		self.tthtm.setCodeppm(value)
		self.tthtm.f.lib["com.fontlab.v2.tth"]["codeppm"] = value

	def makeStemsListsPopUpMenu(self):
		self.tthtm.stemsListX = ['None', 'Guess']
		self.tthtm.stemsListY = ['None', 'Guess']

		for name, stem in self.tthtm.stems.iteritems():
			if stem['horizontal'] == True:
				self.tthtm.stemsListY.append(name)
			else:
				self.tthtm.stemsListX.append(name)

#============== Fonctions for zones

	def deltaDictFromString(self, s):
		try:
			if s == '0@0':
				return {}
			listOfLists = [[int(i) for i in reversed(x.split('@'))] for x in s.split(',')]
			for i in range(len(listOfLists)):
				listOfLists[i][0] = str(listOfLists[i][0])
			return dict(listOfLists)
		except:
			return {}

	def AddZone(self, name, newZone, zoneView):
		# add the zone in the model
		self.tthtm.zones[name] = newZone
		self.tthtm.f.lib[FL_tth_key]["zones"][name] = newZone
		# add the zone in the UI
		uiZone = self.tthtm.buildUIZoneDict(newZone, name)
		zoneView.box.zones_List.append(uiZone)
		zoneView.UIZones.append(uiZone)

	def deleteZones(self, selected, zoneView):
		for zoneName in selected:
			try:
				del self.tthtm.f.lib[FL_tth_key]["zones"][zoneName]
				del self.tthtm.zones[zoneName]
			except:
				pass
		for g in self.tthtm.f:
			commands = self.readGlyphFLTTProgram(g)
			if commands == None:
				continue
			for command in commands:
				if command['code'] in ['alignt', 'alignb']:
					if command['zone'] == zoneName:
						command['code'] = 'alignv'
						del command['zone']
						command['align'] = 'round'
			self.writeGlyphFLTTProgram(g)
		dummy = self.readGlyphFLTTProgram(self.tthtm.g) # recover the correct commands list
		zoneView.set(self.tthtm.buildUIZonesList(buildTop = (zoneView.ID == 'top')))

	def EditZone(self, oldZoneName, zoneName, zoneDict, isTop):
		self.storeZone(zoneName, zoneDict, isTop)
		self.tthtm.f.lib[FL_tth_key]["zones"] = self.tthtm.zones
		if oldZoneName != zoneName:
			for g in self.tthtm.f:
				commands = self.readGlyphFLTTProgram(g)
				if commands == None:
					continue
				for command in commands:
					if command['code'] in ['alignt', 'alignb']:
						if command['zone'] == oldZoneName:
							command['zone'] = zoneName
				self.writeGlyphFLTTProgram(g)
			dummy = self.readGlyphFLTTProgram(self.tthtm.g) # recover the correct commands list

	def storeZone(self, zoneName, entry, isTop):
		if zoneName not in self.tthtm.zones:
			self.tthtm.zones[zoneName] = {}
		zone = self.tthtm.zones[zoneName]
		zone['top'] = isTop
		if 'Position' in entry:
			zone['position'] = int(entry['Position'])
		else:
			zone['position'] = 0
			entry['Position'] = 0
		if 'Width' in entry:
			zone['width'] = int(entry['Width'])
		else:
			zone['width'] = 0
			entry['Width'] = 0
		if 'Delta' in entry:
			deltaDict = self.deltaDictFromString(entry['Delta'])
			if deltaDict != {}:
				zone['delta'] = deltaDict
			else:
				try:
					del zone['delta']
				except:
					pass
		else:
			zone['delta'] = {'0': 0}
			entry['Delta'] = '0@0'

#================ Functions for Stems

	def storeStem(self, stemName, entry, horizontal):
		stem = self.tthtm.getOrPutDefault(self.tthtm.stems, stemName, {})
		stem['width'] = self.tthtm.getOrDefault(entry, 'Width', 0)
		stem['horizontal'] = horizontal
		# stems round dict
		sr = {}
		stem['round'] = sr
		def addRound(colName, val, col):
			if colName in entry:
				sr[str(entry[colName])] = col
			else:
				print("DOES THAT REALLY HAPPEN!?")
				sr[val] = col
		width =  int(self.tthtm.stems[stemName]['width'])
		stemPitch = float(self.tthtm.UPM)/width
		addRound('1 px', '0', 1)
		addRound('2 px', str(int(2*stemPitch)), 2)
		addRound('3 px', str(int(3*stemPitch)), 3)
		addRound('4 px', str(int(4*stemPitch)), 4)
		addRound('5 px', str(int(5*stemPitch)), 5)
		addRound('6 px', str(int(6*stemPitch)), 6)

	def EditStem(self, oldStemName, newStemName, stemDict, horizontal):
		self.storeStem(newStemName, stemDict, horizontal)
		self.tthtm.f.lib[FL_tth_key]["stems"] = self.tthtm.stems
		if self.tthtm.selectedStemX == oldStemName:
			self.changeSelectedStemX(newStemName)
		if self.tthtm.selectedStemY == oldStemName:
			self.changeSelectedStemY(newStemName)

		if oldStemName != newStemName:
			for g in self.tthtm.f:
				commands = self.readGlyphFLTTProgram(g)
				if commands == None:
					continue
				for command in commands:
					if 'stem' in command:
						if command['stem'] == oldStemName:
							command['stem'] = newStemName
				self.writeGlyphFLTTProgram(g)
			dummy = self.readGlyphFLTTProgram(self.tthtm.g) # recover the correct commands list


	def deleteStems(self, selected, stemView):
		for name in selected:
			try:
				del self.tthtm.f.lib[FL_tth_key]["stems"][name]
				del self.tthtm.stems[name]
			except:
				pass

			for g in self.tthtm.f:
				commands = self.readGlyphFLTTProgram(g)
				if commands == None:
					continue
				for command in commands:
					if 'stem' in command:
						if command['stem'] == name:
							del command['stem']
				self.writeGlyphFLTTProgram(g)
			dummy = self.readGlyphFLTTProgram(self.tthtm.g) # recover the correct commands list

		self.changeSelectedStemX('None')
		self.changeSelectedStemY('None')
		tth_lib = self.tthtm.getOrPutDefault(self.tthtm.f.lib, FL_tth_key, {})
		self.tthtm.stems = self.tthtm.getOrPutDefault(tth_lib, "stems", {})
		stemView.set(self.tthtm.buildStemsUIList(stemView.isHorizontal))


	def addStem(self, name, stemDict, stemView):
		self.tthtm.stems[name] = stemDict
		self.tthtm.f.lib[FL_tth_key]["stems"][name] = stemDict
		stemView.set(self.tthtm.buildStemsUIList(stemView.isHorizontal))

	# def showHidePreviewWindow(self, showHide):
	# 	if showHide == 0:
	# 		self.previewWindow.hidePreview()
	# 	elif showHide == 1:
	# 		self.previewWindow.showPreview()

	def isOnPoint(self, p_cursor):
		def pred0(p_glyph):
			return pointsApproxEqual(p_glyph, p_cursor)
		touched_p_glyph = find_closest(self.p_glyphList, pred0, p_cursor)

		return touched_p_glyph

	def isOffPoint(self, p_cursor):
		def pred0(p_glyph):
			return pointsApproxEqual(p_glyph, p_cursor)
		touched_p_glyph = find_closest(self.pOff_glyphList, pred0, p_cursor)	

		return touched_p_glyph

	def isOffOnPoint(self, p_cursor):
		def pred0(p_glyph):
			return pointsApproxEqual(p_glyph, p_cursor)
		touched_p_glyph = find_closest(self.pOffOn_glyphList, pred0, p_cursor)
		

		return touched_p_glyph


	def isOnCommand(self, p_cursor):
		if self.tthtm.selectedAxis == 'X':
			skipper = ['v','t','b']
		else:
			skipper = ['h']

		def pred0(cmdIdx, commandPos):
			if cmdIdx == None:
				return False
			if self.glyphTTHCommands[cmdIdx]['code'][-1] in skipper:
				return False
			return pointInCommand(commandPos, p_cursor)

		touched_p_command = find_in_dict(self.commandLabelPos, pred0)

		return touched_p_command

	def isInZone(self, point, y_min, y_max):
		if point[1]  >= y_min and point[1] <= y_max:
			return True
		else:
			return False

	def isInTopZone(self, point):
		for name, zone in self.tthtm.zones.iteritems():
			if not zone['top']:
				continue
			y_min = int(zone['position'])
			y_max = int(zone['position']) + int(zone['width'])
			if self.isInZone(point, y_min, y_max):
				return name
		return None

	def isInBottomZone(self, point):
		for name, zone in self.tthtm.zones.iteritems():
			if zone['top']:
				continue
			y_max = int(zone['position'])
			y_min = int(zone['position']) - int(zone['width'])
			if self.isInZone(point, y_min, y_max):
				return name
		return None

	def keyDown(self, event):
		keyDict = {'a':('Align', 0), 's':('Single Link', 1), 'd':('Double Link', 2), 'i':('Interpolation', 3), 'm':('Middle Delta', 4), 'f':('Final Delta', 5)}
		if event.characters() in keyDict:
			val = keyDict[event.characters()]
			self.changeSelectedHintingTool(val[0])

		elif event.characters() == 'o':
			if self.tthtm.showOutline == 1:
				self.tthtm.showOutline = 0
			else:
				self.tthtm.showOutline = 1
			UpdateCurrentGlyphView()
		elif event.characters() == 'B':
			if self.tthtm.showBitmap == 1:
				self.tthtm.showBitmap = 0
			else:
				self.tthtm.showBitmap = 1
			UpdateCurrentGlyphView()
		elif event.characters() == 'G':
			if self.tthtm.showGrid == 1:
				self.tthtm.showGrid = 0
			else:
				self.tthtm.showGrid = 1
			UpdateCurrentGlyphView()
		elif event.characters() == 'c':
			if self.tthtm.showCenterPixel == 1:
				self.tthtm.showCenterPixel = 0
			else:
				self.tthtm.showCenterPixel = 1
			UpdateCurrentGlyphView()
		elif event.characters() == 'S':
			if self.tthtm.selectedAxis == 'Y':
				self.swapStemY()
			elif self.tthtm.selectedAxis == 'X':
				self.swapStemX()

		elif event.characters() == 'R':
			if self.tthtm.roundBool == 0:
				self.changeRoundBool(1)
			else:
				self.changeRoundBool(0)

		elif event.characters() == 'A':
			if self.tthtm.selectedHintingTool in ['Single Link', 'Interpolation']:
				self.swapAlignmentTypeLink()
			elif self.tthtm.selectedHintingTool == 'Align':
				self.swapAlignmentTypeAlign()

		elif event.characters() in ['h', 'v']:
			if self.tthtm.selectedAxis == 'Y':
				self.changeAxis('X')
				self.makeStemsListsPopUpMenu()
				self.toolsWindow.wTools.StemTypePopUpButton.setItems(self.tthtm.stemsListX)
				self.changeSelectedStemX(self.tthtm.selectedStemX)
			else:
				self.changeAxis('Y')
				self.makeStemsListsPopUpMenu()
				self.toolsWindow.wTools.StemTypePopUpButton.setItems(self.tthtm.stemsListY)
				self.changeSelectedStemY(self.tthtm.selectedStemY)

		elif event.characters() == '-':
			if self.tthtm.PPM_Size > 9:
				self.changeSize(self.tthtm.PPM_Size-1)
		elif event.characters() == '=' or event.characters() == '+':
			self.changeSize(self.tthtm.PPM_Size+1)

		elif event.characters() == 'p':
			bitmappreviewIndex = self.centralWindow.wCentral.BitmapPreviewPopUpButton.get()
			if bitmappreviewIndex < 2:
				bitmapPreviewSelection = self.centralWindow.BitmapPreviewList[bitmappreviewIndex+1]
			else:
				bitmapPreviewSelection = self.centralWindow.BitmapPreviewList[0]
			self.changeBitmapPreview(bitmapPreviewSelection)

		elif event.characters() == 'P':
			if self.tthtm.showPreviewInGlyphWindow == 1:
				self.tthtm.showPreviewInGlyphWindow = 0
				self.previewInGlyphWindow.removeFromSuperview()
				self.previewInGlyphWindow = None
			else:
				self.tthtm.showPreviewInGlyphWindow = 1
				UpdateCurrentGlyphView()

	def mouseDown(self, point, clickCount):
		self.p_cursor = (int(point.x), int(point.y))
		self.startPoint = self.isOnPoint(self.p_cursor)
		#print 'glyph start point:', self.startPoint
		#if self.startPoint in self.pointCoordinatesToUniqueID:
		#	print 'point UniqueID:', self.pointCoordinatesToUniqueID[self.startPoint]

	def getDistance(self, point1, point2, axis):
		x1 = point1[0]
		x2 = point2[0]
		y1 = point1[1]
		y2 = point2[1]

		if axis == 'X':
			return abs(x2-x1)
		elif axis == 'Y':
			return abs(y2-y1)

	def guessStem(self, point1, point2):
		dist = self.getDistance(point1, point2, self.tthtm.selectedAxis)
		candidatesList = []
		horizontal = (self.tthtm.selectedAxis == 'Y')
		for stemName, stem in self.tthtm.stems.iteritems():
			if stem['horizontal'] == horizontal:
				w = int(stem['width'])
				candidatesList.append((abs(w - dist), stemName))
		candidatesList.sort()
		if len(candidatesList) == 0:
			return None
		return candidatesList[0][1]

	def didUndo(self, font):
		self.readGlyphFLTTProgram(self.tthtm.g)
		self.updateGlyphProgram()
		if self.tthtm.alwaysRefresh == 1:
		 	self.refreshGlyph()

	def mouseUp(self, point):
		if self.tthtm.showPreviewInGlyphWindow == 1:
			x = self.getCurrentEvent().locationInWindow().x
			y = self.getCurrentEvent().locationInWindow().y

			for i in self.previewInGlyphWindow.clickableSizesGlyphWindow:
				if x >= i[0] and x <= i[0]+10 and y >= i[1] and y <= i[1]+20:
					self.changeSize(self.previewInGlyphWindow.clickableSizesGlyphWindow[i])

		self.p_cursor = (int(point.x), int(point.y))
		self.endPoint = self.isOnPoint(self.p_cursor)
		self.endPointOff = self.isOffPoint(self.p_cursor)
		#print 'glyph end point:', self.endPoint
		if self.endPoint == None and self.endPointOff == None:
			self.startPoint = None
			return

		cmdIndex = len(self.glyphTTHCommands)
		newCommand = {}

		if self.tthtm.selectedHintingTool == 'Align' and self.endPoint != None:
			newCommand['point'] = self.pointCoordinatesToName[self.endPoint]
			if self.tthtm.selectedAxis == 'X':
				newCommand['code'] = 'alignh'
				newCommand['align'] = self.tthtm.selectedAlignmentTypeAlign
			else:
				if self.isInTopZone(self.endPoint):
					newCommand['code'] = 'alignt'
					newCommand['zone'] = self.isInTopZone(self.endPoint)
				elif self.isInBottomZone(self.endPoint):
					newCommand['code'] = 'alignb'
					newCommand['zone'] = self.isInBottomZone(self.endPoint)
				else:
					newCommand['code'] = 'alignv'
					newCommand['align'] = self.tthtm.selectedAlignmentTypeAlign

		if self.tthtm.selectedHintingTool == 'Single Link' and self.startPoint != self.endPoint and self.startPoint != None and self.endPoint != None:
			if self.tthtm.selectedAxis == 'X':
				newCommand['code'] = 'singleh'
				if self.tthtm.selectedStemX != 'None' and self.tthtm.selectedStemX != 'Guess' and self.tthtm.roundBool != 1:
					newCommand['stem'] = self.tthtm.selectedStemX
				elif self.tthtm.selectedStemX == 'Guess' and self.tthtm.roundBool != 1:
					stem = self.guessStem(self.startPoint, self.endPoint)
					if stem != None:
						newCommand['stem'] = stem
				elif self.tthtm.roundBool == 1:
					newCommand['round'] = 'true'
			else:
				newCommand['code'] = 'singlev'
				if self.tthtm.selectedStemY != 'None' and self.tthtm.selectedStemY != 'Guess' and self.tthtm.roundBool != 1:
					newCommand['stem'] = self.tthtm.selectedStemY
				elif self.tthtm.selectedStemY == 'Guess' and self.tthtm.roundBool != 1:
					stem = self.guessStem(self.startPoint, self.endPoint)
					if stem != None:
						newCommand['stem'] = stem
				elif self.tthtm.roundBool == 1:
					newCommand['round'] = 'true'

			newCommand['point1'] = self.pointCoordinatesToName[self.startPoint]
			newCommand['point2'] = self.pointCoordinatesToName[self.endPoint]
			if self.tthtm.selectedAlignmentTypeLink != 'None' and self.tthtm.roundBool == 0 and 'stem' not in newCommand:
				newCommand['align'] = self.tthtm.selectedAlignmentTypeLink
			elif self.tthtm.roundBool == 1:
				newCommand['round'] = 'true'

		if self.tthtm.selectedHintingTool == 'Double Link' and self.startPoint != self.endPoint and self.startPoint != None and self.endPoint != None:
			if self.tthtm.selectedAxis == 'X':
				newCommand['code'] = 'doubleh'
				if self.tthtm.selectedStemX != 'None' and self.tthtm.selectedStemX != 'Guess':
					newCommand['stem'] = self.tthtm.selectedStemX
				elif self.tthtm.selectedStemX == 'Guess':
					stem = self.guessStem(self.startPoint, self.endPoint)
					if stem != None:
						newCommand['stem'] = stem
				else:
					newCommand['round'] = 'true'
			else:
				newCommand['code'] = 'doublev'
				if self.tthtm.selectedStemY != 'None' and self.tthtm.selectedStemY != 'Guess':
					newCommand['stem'] = self.tthtm.selectedStemY
				elif self.tthtm.selectedStemY == 'Guess':
					stem = self.guessStem(self.startPoint, self.endPoint)
					if stem != None:
						newCommand['stem'] = stem
				else:
					newCommand['round'] = 'true'

			newCommand['point1'] = self.pointCoordinatesToName[self.startPoint]
			newCommand['point2'] = self.pointCoordinatesToName[self.endPoint]

		if self.tthtm.selectedHintingTool == 'Interpolation' and self.startPoint != self.endPoint and self.startPoint != None and self.endPoint != None:
			self.point1 = self.startPoint
			self.point = self.endPoint

			self.endDraggingPoint = self.point
			self.movingMouse = self.point
			self.endPointInterpolate1 = self.endPoint
			self.startPointInterpolate1 = self.startPoint
			addObserver(self, "giveMouseCoordinates", 'mouseMoved')
			addObserver(self, "drawInterpolateMouseMoved", "draw")

		if self.tthtm.selectedHintingTool == 'Interpolation' and self.startPoint == self.endPoint and self.startPoint != None and self.point1 != None and self.point != None:
			self.point2 = self.endPoint
			if self.tthtm.selectedAxis == 'X':
				newCommand['code'] = 'interpolateh'
			else:
				newCommand['code'] = 'interpolatev'
			newCommand['point1'] = self.pointCoordinatesToName[self.point1]
			newCommand['point'] = self.pointCoordinatesToName[self.point]
			newCommand['point2'] = self.pointCoordinatesToName[self.point2]
			if self.tthtm.selectedAlignmentTypeLink != 'None':
				newCommand['align'] = self.tthtm.selectedAlignmentTypeLink

			self.endDraggingPoint = self.endPoint
			self.movingMouse = self.point
			self.point1 = None
			self.point = None
			self.point2 = None

			removeObserver(self, "mouseMoved")
			removeObserver(self, "draw")

		if self.tthtm.selectedHintingTool in ['Middle Delta', 'Final Delta'] and (self.endPoint != None or self.endPointOff != None):
			if self.tthtm.deltaOffset == 0:
				return
			if self.endPoint != None:
				newCommand['point'] = self.pointCoordinatesToName[self.endPoint]
			if self.endPointOff != None:
				newCommand['point'] = self.pointCoordinatesToName[self.endPointOff]
			newCommand['ppm1'] = str(self.tthtm.deltaRange1)
			newCommand['ppm2'] = str(self.tthtm.deltaRange2)
			newCommand['delta'] = str(self.tthtm.deltaOffset)
			if self.tthtm.selectedHintingTool == 'Middle Delta':
				if self.tthtm.selectedAxis == 'X':
					newCommand['code'] = 'mdeltah'
				else:
					newCommand['code'] = 'mdeltav'
			if self.tthtm.selectedHintingTool == 'Final Delta':
				if self.tthtm.selectedAxis == 'X':
					newCommand['code'] = 'fdeltah'
				else:
					newCommand['code'] = 'fdeltav'

		if newCommand != {}:
			self.tthtm.g.prepareUndo("New Command")
			self.glyphTTHCommands.append(newCommand)	
			self.updateGlyphProgram()
			if self.tthtm.alwaysRefresh == 1:
				self.refreshGlyph()
			self.tthtm.g.performUndo()

		self.endPoint = None
		self.startPoint = None
		self.endPointOff = None

	def compareCommands(self, A, B):
		order = None
		ab = 1
		ba = 2

		A_isAlign	= A['code'] in ['alignh', 'alignv']
		B_isAlign	= B['code'] in ['alignh', 'alignv']
		A_isSingleLink	= A['code'] in ['singleh', 'singlev']
		B_isSingleLink	= B['code'] in ['singleh', 'singlev']
		A_isInterpolate = A['code'] in ['interpolateh', 'interpolatev']
		B_isInterpolate = B['code'] in ['interpolateh', 'interpolatev']
		A_isMiddleDelta = A['code'] in ['mdeltah', 'mdeltav']
		B_isMiddleDelta = B['code'] in ['mdeltah', 'mdeltav']

		if A_isAlign and B_isAlign:
			if A['point'] == B['point']:
				order = 'BUG'
		elif A_isSingleLink and B_isAlign:
			if A['point1'] == B['point']:
				order = ba
		elif A_isAlign and B_isSingleLink:
			if A['point'] == B['point1']:
				order = ab
		elif A_isSingleLink and B_isSingleLink:
			if A['point1'] == B['point2']:
				order = ba
			elif A['point2'] == B['point1']:
				order = ab
			elif A['point2'] == B['point2']:
				order = 'BUG'
		elif A_isAlign and B_isInterpolate:
			if A['point'] == B['point1'] or A['point'] == B['point2']:
				order = ab
		elif A_isInterpolate and B_isAlign:
			if B['point'] == A['point1'] or B['point'] == A['point2']:
				order = ba
		elif A_isSingleLink and B_isInterpolate:
			if A['point2'] == B['point1'] or A['point2'] == B['point2']:
				order = ab
			elif A['point1'] == B['point']:
				order = ba
		elif A_isInterpolate and B_isSingleLink:
			if B['point2'] == A['point1'] or B['point2'] == A['point2']:
				order = ba
			elif A['point'] == B['point1']:
				order = ab
		elif A_isAlign and B_isMiddleDelta:
			if A['point'] == B['point']:
				order = ab
		elif A_isMiddleDelta and B_isMiddleDelta:
			if A['point'] == B['point']:
				order = 'BUG'
		elif A_isMiddleDelta and B_isAlign:
			if A['point'] == B['point']:
				order = ba
		elif A_isAlign and B_isMiddleDelta:
			if A['point'] == B['point']:
				order = ab
		elif A_isMiddleDelta and B_isSingleLink:
			if A['point'] == B['point1']:
				order = ab
			elif A['point'] == B['point2']:
				order = ba
		elif A_isSingleLink and B_isMiddleDelta:
			if A['point1'] == B['point']:
				order = ba
			elif A['point2'] == B['point']:
				order = ab
		elif A_isMiddleDelta and B_isInterpolate:
			if A['point'] == B['point1'] or A['point'] == B['point2']:
				order = ab
			elif A['point'] == B['point']:
				order = ba
		elif A_isInterpolate and B_isMiddleDelta:
			if A['point1'] == B['point'] or A['point2'] == B['point']:
				order = ba
			elif A['point'] == B['point']:
				order = ab
		if order == ab:
			return (True, False)
		elif order == ba:
			return (True, True)
		return (False, False)

	def prepareCommands(self):
		x, ytb, y, fdeltah, fdeltav = [], [], [], [], []
		for e in self.glyphTTHCommands:
			code = e['code']
			if code == 'fdeltah':
				fdeltah.append(e)
			elif code == 'fdeltav':
				fdeltav.append(e)
			elif code[-1] in ['h']:
				x.append(e)
			elif code[-1] in ['v']:
				y.append(e)
			elif code[-1] in ['t', 'b']:
				ytb.append(e)
			else:
				y.append(e)
		x = topologicalSort(x, self.compareCommands)
		x.extend(ytb)
		self.glyphTTHCommands = sum([topologicalSort(l, self.compareCommands) for l in [y,fdeltah,fdeltav]], x)

	def rewriteGlyphXML(self):
		XMLGlyphTTProgram = ET.Element('ttProgram')
		for child in self.glyphTTHCommands:
			ttc = ET.SubElement(XMLGlyphTTProgram, 'ttc')
			for k, v in child.iteritems():
				ttc.set(k, v)
		strGlyphTTProgram = ET.tostring(XMLGlyphTTProgram)
		self.tthtm.g.lib['com.fontlab.ttprogram'] = Data(strGlyphTTProgram)

	def deleteCommandCallback(self, item):
		ttprogram = self.tthtm.g.lib['com.fontlab.ttprogram']
		self.tthtm.g.prepareUndo('Delete Command')
		self.glyphTTHCommands.pop(self.commandRightClicked)
		self.commandLabelPos = {}
		self.rewriteGlyphXML()
		self.tthtm.g.performUndo()

		self.updateGlyphProgram()
		if self.tthtm.alwaysRefresh == 1:
			self.refreshGlyph()

	def deleteAllCommandsCallback(self, item):
		emptyProgram = ''
		self.glyphTTHCommands = []
		self.commandLabelPos = {}
		self.tthtm.g.prepareUndo('Clear Program')
		self.tthtm.g.lib['com.fontlab.ttprogram'] = Data(emptyProgram)
		self.updateGlyphProgram()
		if self.tthtm.alwaysRefresh == 1:
			self.refreshGlyph()
		self.tthtm.g.performUndo()

	def deleteXCommandsCallback(self, item):
		self.tthtm.g.prepareUndo('Clear X Commands')
		commandsToDelete = [cmd for cmd in self.glyphTTHCommands if cmd['code'][-1:] == 'h']
		for cmd in commandsToDelete:
			self.glyphTTHCommands.remove(cmd)

		self.rewriteGlyphXML()

		self.updateGlyphProgram()
		if self.tthtm.alwaysRefresh == 1:
			self.refreshGlyph()
		self.tthtm.g.performUndo()

	def deleteYCommandsCallback(self, item):
		self.tthtm.g.prepareUndo('Clear Y Commands')
		commandsToDelete = [cmd for cmd in self.glyphTTHCommands if cmd['code'][-1:] in ['v', 't', 'b']]
		for cmd in commandsToDelete:
			self.glyphTTHCommands.remove(cmd)

		self.rewriteGlyphXML()

		self.updateGlyphProgram()
		if self.tthtm.alwaysRefresh == 1:
			self.refreshGlyph()
		self.tthtm.g.performUndo()

	def deleteAllDeltasCallback(self, item):
		self.tthtm.g.prepareUndo('Clear All Deltas')
		commandsToDelete = [cmd for cmd in self.glyphTTHCommands if cmd['code'] in ['mdeltav', 'mdeltah', 'fdeltav', 'fdeltah']]
		for cmd in commandsToDelete:
			self.glyphTTHCommands.remove(cmd)
		
		self.rewriteGlyphXML()

		self.updateGlyphProgram()
		if self.tthtm.alwaysRefresh == 1:
			self.refreshGlyph()

		self.tthtm.g.performUndo()


	def roundDistanceCallback(self, item):
		cmdIndex = self.commandRightClicked
		self.tthtm.g.prepareUndo('Round Distance')
		self.glyphTTHCommands[cmdIndex]['round'] = 'true'
		if 'stem' in self.glyphTTHCommands[cmdIndex]:
			del self.glyphTTHCommands[cmdIndex]['stem']
		if 'align' in self.glyphTTHCommands[cmdIndex]:
			del self.glyphTTHCommands[cmdIndex]['align']
		self.updateGlyphProgram()
		if self.tthtm.alwaysRefresh == 1:
			self.refreshGlyph()
		self.tthtm.g.performUndo()

	def dontRoundDistanceCallback(self, item):
		cmdIndex = self.commandRightClicked
		self.tthtm.g.prepareUndo('Do Not Round Distance')
		del self.glyphTTHCommands[cmdIndex]['round']
		self.updateGlyphProgram()
		if self.tthtm.alwaysRefresh == 1:
			self.refreshGlyph()
		self.tthtm.g.performUndo()

	def dontLinkToStemCallBack(self, item):
		cmdIndex = self.commandRightClicked
		self.tthtm.g.prepareUndo('Do Not Link to Stem')
		if 'stem' in self.glyphTTHCommands[cmdIndex]:
			del self.glyphTTHCommands[cmdIndex]['stem']
		self.updateGlyphProgram()
		if self.tthtm.alwaysRefresh == 1:
			self.refreshGlyph()
		self.tthtm.g.performUndo()

	def dontAlignCallBack(self, item):
		cmdIndex = self.commandRightClicked
		self.tthtm.g.prepareUndo('Do Not Align')
		del self.glyphTTHCommands[cmdIndex]['align']
		self.updateGlyphProgram()
		if self.tthtm.alwaysRefresh == 1:
			self.refreshGlyph()
		self.tthtm.g.performUndo()

	def updateGlyphProgram(self):
		self.prepareCommands()
		self.writeGlyphFLTTProgram(self.tthtm.g)
		TTHintAsm.writeAssembly(self.tthtm.g, self.glyphTTHCommands, self.pointNameToUniqueID, self.pointNameToIndex)

	def refreshGlyph(self):
		self.updatePartialFont() # to update the newly modified current glyph
		self.resetglyph()
		UpdateCurrentGlyphView()

	def rightMouseDown(self, point, event):
		self.p_cursor = (int(point.x), int(point.y))
		self.commandRightClicked = self.isOnCommand(self.p_cursor)
		#print 'command point:', self.commandRightClicked
		if self.commandRightClicked == None:
			self.menuAction = NSMenu.alloc().init()
			items = []
			items.append(('Clear All Program', self.deleteAllCommandsCallback))
			items.append(('Clear X Commands', self.deleteXCommandsCallback))
			items.append(('Clear Y Commands', self.deleteYCommandsCallback))
			items.append(('Clear All Deltas', self.deleteAllDeltasCallback))
			menuController = BaseMenu()
			menuController.buildAdditionContectualMenuItems(self.menuAction, items)
			NSMenu.popUpContextMenu_withEvent_forView_(self.menuAction, self.getCurrentEvent(), self.getNSView())

		else:
			self.menuAction = NSMenu.alloc().init()
			separator = NSMenuItem.separatorItem()

			alignmentCallBack_Closest = callbackAlignment(self, 'round')
			alignmentCallBack_Left = callbackAlignment(self, 'left')
			alignmentCallBack_Right = callbackAlignment(self, 'right')
			alignmentCallBack_Center = callbackAlignment(self, 'center')
			alignmentCallBack_Double = callbackAlignment(self, 'double')

			items = []
			items.append(('Delete Command', self.deleteCommandCallback))

			clickedCommand = self.glyphTTHCommands[self.commandRightClicked]

			if clickedCommand['code'] in ['mdeltah', 'mdeltav', 'fdeltah', 'fdeltav']:
				deltaValues = []
				for value in range(-8, 0):
					valueContext = str(value)
					if str(value) == str(clickedCommand['delta']):
						valueContext = u"✓ " + str(value)
					deltaValues.append((valueContext, callbackSetDeltaValue(self, value)))
				for value in range(1, 9):
					valueContext = str(value)
					if str(value) == str(clickedCommand['delta']):
						valueContext = u"✓ " + str(value)
					deltaValues.append((valueContext, callbackSetDeltaValue(self, value)))
				items.append(("Set Middle Delta Value", deltaValues))


			if clickedCommand['code'] in ['interpolateh', 'interpolatev']:
			
				doNotAlignContext = 'Do Not Align to Grid'
				closestContext = "Closest Pixel Edge"
				leftContext = "Left/Bottom Edge"
				rightContext = "Right/Top Edge"
				centerContext = "Center of Pixel"
				doubleContext = "Double Grid"
				if 'align' in clickedCommand:
					if clickedCommand['align'] == 'round':
						closestContext = u"✓ Closest Pixel Edge"
					elif clickedCommand['align'] == 'left':
						leftContext = u"✓ Left/Bottom Edge"
					elif clickedCommand['align'] == 'right':
						rightContext = u"✓ Right/Top Edge"
					elif clickedCommand['align'] == 'center':
						centerContext = u"✓ Center of Pixel"
					elif clickedCommand['align'] == 'double':
						doubleContext = u"✓ Double Grid"
				else:
					doNotAlignContext = u'✓Do Not Align to Grid'

				alignments = [
							(doNotAlignContext, self.dontAlignCallBack),
							(closestContext, alignmentCallBack_Closest),
							(leftContext, alignmentCallBack_Left),
							(rightContext, alignmentCallBack_Right),
							(centerContext, alignmentCallBack_Center),
							(doubleContext, alignmentCallBack_Double)
							]

				items.append(("Align Destination Position", alignments))


			if clickedCommand['code'] in ['alignh', 'alignv', 'alignt', 'alignb']:

				closestContext = "Closest Pixel Edge"
				leftContext = "Left/Bottom Edge"
				rightContext = "Right/Top Edge"
				centerContext = "Center of Pixel"
				doubleContext = "Double Grid"
				if 'align' in clickedCommand:
					if clickedCommand['align'] == 'round':
						closestContext = u"✓ Closest Pixel Edge"
					elif clickedCommand['align'] == 'left':
						leftContext = u"✓ Left/Bottom Edge"
					elif clickedCommand['align'] == 'right':
						rightContext = u"✓ Right/Top Edge"
					elif clickedCommand['align'] == 'center':
						centerContext = u"✓ Center of Pixel"
					elif clickedCommand['align'] == 'double':
						doubleContext = u"✓ Double Grid"

				zonesListItems = []

				for zoneName in self.tthtm.zones:
					zoneContext = zoneName
					if 'zone' in clickedCommand:
						if zoneName == clickedCommand['zone']:
							zoneContext = u'✓ ' + str(zoneName) # FIXME: useless conversion from string to string
					self.zoneAlignmentCallBack = callbackZoneAlignment(self, zoneName)
					zonesListItems.append((zoneContext, self.zoneAlignmentCallBack))
				#items.append(("Attach to Zone", zonesListItems))


				alignments = [
							(closestContext, alignmentCallBack_Closest),
							(leftContext, alignmentCallBack_Left),
							(rightContext, alignmentCallBack_Right),
							(centerContext, alignmentCallBack_Center),
							(doubleContext, alignmentCallBack_Double),
							("Attach to Zone", zonesListItems)
							]
				if clickedCommand['code'] == 'alignh':
					alignments = [
							(closestContext, alignmentCallBack_Closest),
							(leftContext, alignmentCallBack_Left),
							(rightContext, alignmentCallBack_Right),
							(centerContext, alignmentCallBack_Center),
							(doubleContext, alignmentCallBack_Double),
							]

				items.append(("Alignment Type", alignments))

			# if clickedCommand['code'] in ['alignt', 'alignb']:
			# 	zonesListItems = []

			# 	for zoneName in self.tthtm.zones:
			# 		zoneContext = zoneName
			# 		if zoneName == clickedCommand['zone']:
			# 			zoneContext = u'✓ ' + str(zoneName)
			# 		self.zoneAlignmentCallBack = callbackZoneAlignment(self, zoneName)
			# 		zonesListItems.append((zoneContext, self.zoneAlignmentCallBack))
			# 	items.append(("Attach to Zone", zonesListItems))

			if clickedCommand['code'] in ['doubleh', 'doublev']:
				if 'stem' in clickedCommand:
					distances = [('Do Not Link to Stem', self.dontLinkToStemCallBack)]
				else:
					distances = []

				stemsHorizontal = []
				stemsVertical = []

				for name, stem in self.tthtm.stems.iteritems():
					if stem['horizontal'] == True:
						stemsHorizontal.append(name)
					else:
						stemsVertical.append(name)

				if self.tthtm.selectedAxis == 'X':
					stems = stemsVertical
				else:
					stems = stemsHorizontal

				for i in stems:
					self.distanceCallback = callbackDistance(self, i)
					distances.append((i, self.distanceCallback))

				items.append(("Distance Alignment", distances))



			if clickedCommand['code'] in ['singleh', 'singlev']:
				if 'round' not in clickedCommand:
					items.append(('Round Distance', self.roundDistanceCallback))
				else:
					items.append((u'✓ Round Distance', self.dontRoundDistanceCallback))

				stemsHorizontal = []
				stemsVertical = []

				for name, stem in self.tthtm.stems.iteritems():
					if stem['horizontal'] == True:
						stemsHorizontal.append(name)
					else:
						stemsVertical.append(name)

				if self.tthtm.selectedAxis == 'X':
					stems = stemsVertical
				else:
					stems = stemsHorizontal


				if 'stem' in clickedCommand:
					distances = [('Do Not Link to Stem', self.dontLinkToStemCallBack)]
					for i in stems:
						self.distanceCallback = callbackDistance(self, i)
						if clickedCommand['stem'] == i:
							stemContext = u'✓ ' + str(i)
						else:
							stemContext = str(i)
						distances.append((stemContext, self.distanceCallback))
				else:
					distances = [(u'✓ Do Not Link to Stem', self.dontLinkToStemCallBack)]
					for i in stems:
						self.distanceCallback = callbackDistance(self, i)
						distances.append((i, self.distanceCallback))

				
				items.append(("Distance Alignment", distances))

				doNotAlignContext = 'Do Not Align to Grid'
				closestContext = "Closest Pixel Edge"
				leftContext = "Left/Bottom Edge"
				rightContext = "Right/Top Edge"
				centerContext = "Center of Pixel"
				doubleContext = "Double Grid"
				if 'align' in clickedCommand:
					if clickedCommand['align'] == 'round':
						closestContext = u"✓ Closest Pixel Edge"
					elif clickedCommand['align'] == 'left':
						leftContext = u"✓ Left/Bottom Edge"
					elif clickedCommand['align'] == 'right':
						rightContext = u"✓ Right/Top Edge"
					elif clickedCommand['align'] == 'center':
						centerContext = u"✓ Center of Pixel"
					elif clickedCommand['align'] == 'double':
						doubleContext = u"✓ Double Grid"
				else:
					doNotAlignContext = u'✓ Do Not Align to Grid'

				alignments = [
							(doNotAlignContext, self.dontAlignCallBack),
							(closestContext, alignmentCallBack_Closest),
							(leftContext, alignmentCallBack_Left),
							(rightContext, alignmentCallBack_Right),
							(centerContext, alignmentCallBack_Center),
							(doubleContext, alignmentCallBack_Double)
							]

				items.append(("Align Destination Position", alignments))



			menuController = BaseMenu()
			
			menuController.buildAdditionContectualMenuItems(self.menuAction, items)
			self.menuAction.insertItem_atIndex_(separator, 1)
			NSMenu.popUpContextMenu_withEvent_forView_(self.menuAction, self.getCurrentEvent(), self.getNSView())

	def resetFonts(self, createWindows=False):
		if CurrentFont() == None:
			return
		self.tthtm.setFont(CurrentFont())
		if checkSegmentType(self.tthtm.f) == False:
			self.messageInFront = True
		 	Dialogs.Message("WARNING:\nThis is not a Quadratic UFO,\nyou must convert it before.")
			self.messageInFront = False
		self.unicodeToNameDict = self.buildUnicodeToNameDict(self.tthtm.f)
		self.tthtm.resetPitch()
		self.tthtm.setControlValues()

		if createWindows:
			#self.FL_Windows = fl_tth.FL_TTH_Windows(self.tthtm.f, self)
			self.centralWindow = view.centralWindow(self)
			self.toolsWindow = view.toolsWindow(self)
			# if self.tthtm.previewWindowVisible == 1:
			# 	self.previewWindow = view.previewWindow(self, self.tthtm)

		tt_tables.writeCVTandPREP(self.tthtm.f, self.tthtm.UPM, self.tthtm.alignppm, self.tthtm.stems, self.tthtm.zones, self.tthtm.codeppm)
		tt_tables.writeFPGM(self.tthtm.f)
		tt_tables.writeMAXPandGASP(self.tthtm.f, self.tthtm.codeppm)

		for g in self.tthtm.f:
			glyphTTHCommands = self.readGlyphFLTTProgram(g)
			if glyphTTHCommands != None:
				self.prepareCommands()
				TTHintAsm.writeAssembly(g, glyphTTHCommands, self.pointNameToUniqueID, self.pointNameToIndex)

		#self.generateFullTempFont()
		self.resetglyph()

		#self.indexOfGlyphNames = dict([(self.partialTempUFO.lib['public.glyphOrder'][idx], idx) for idx in range(len(self.partialTempUFO.lib['public.glyphOrder']))])

		self.changeSize(self.tthtm.PPM_Size)
		self.changeAxis(self.tthtm.selectedAxis)
		self.changeBitmapPreview(self.tthtm.bitmapPreviewSelection)
		self.changeSelectedHintingTool(self.tthtm.selectedHintingTool)
		self.changeSelectedAlignmentTypeAlign(self.tthtm.selectedAlignmentTypeAlign)
		self.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)
		self.makeStemsListsPopUpMenu()
		if self.tthtm.selectedAxis == 'X':
			self.toolsWindow.wTools.StemTypePopUpButton.setItems(self.tthtm.stemsListX)
			self.changeSelectedStemX(self.tthtm.selectedStemX)
		else:
			self.toolsWindow.wTools.StemTypePopUpButton.setItems(self.tthtm.stemsListY)
			self.changeSelectedStemY(self.tthtm.selectedStemY)
		self.changeRoundBool(self.tthtm.roundBool)
		self.changeDeltaOffset(self.tthtm.deltaOffset)
		self.changeDeltaRange(self.tthtm.deltaRange1, self.tthtm.deltaRange2)

		#self.showHidePreviewWindow(self.tthtm.previewWindowVisible)

	def updatePartialFontIfNeeded(self):
		"""Re-create the partial font if new glyphs are required."""
		(text, curGlyphString) = self.prepareText()
		curSet = self.tthtm.requiredGlyphsForPartialTempFont
		newSet = self.defineGlyphsForPartialTempFont(text, curGlyphString)
		regenerate = not newSet.issubset(curSet)
		n = len(curSet)
		if (n > 128) and (len(newSet) < n):
			regenerate = True
		if regenerate:
			self.tthtm.requiredGlyphsForPartialTempFont = newSet
			self.updatePartialFont()

	def updatePartialFont(self):
		"""Typically called directly when the current glyph has been modifed."""
		self.generatePartialTempFont()
		self.tthtm.textRenderer = TR.TextRenderer(self.partialtempfontpath, self.tthtm.bitmapPreviewSelection, self)

	def resetglyph(self):
		self.tthtm.setGlyph(self.getGlyph())
		if self.tthtm.g == None:
			return
		glyphTTHCommands = self.readGlyphFLTTProgram(self.tthtm.g)
		if glyphTTHCommands != None and self.tthtm.programWindowVisible == 1:
			self.programWindow.updateProgramList(glyphTTHCommands)
		elif self.tthtm.programWindowVisible == 1:
			self.programWindow.updateProgramList([])

		if 'com.robofont.robohint.assembly' in self.tthtm.g.lib and self.tthtm.assemblyWindowVisible == 1:
			self.assemblyWindow.updateAssemblyList(self.tthtm.g.lib['com.robofont.robohint.assembly'])
		elif self.tthtm.assemblyWindowVisible == 1:
			self.assemblyWindow.updateAssemblyList([])

		self.commandLabelPos = {}
		self.pointUniqueIDToCoordinates = self.makePointUniqueIDToCoordinatesDict(self.tthtm.g)
		self.pointCoordinatesToUniqueID = self.makePointCoordinatesToUniqueIDDict(self.tthtm.g)
		self.pointCoordinatesToName = self.makePointCoordinatesToNameDict(self.tthtm.g)
		#print 'full temp font loaded'
		self.ready = True
		if self.tthtm.previewWindowVisible == 1:
			self.previewWindow.wPreview.view.getNSView().setNeedsDisplay_(True)

		self.p_glyphList = ([(0, 0), (self.tthtm.g.width, 0)])
		self.pOff_glyphList = []

		for c in self.tthtm.g:
			for p in c.points:
				if p.type != 'offCurve':
					self.p_glyphList.append((p.x, p.y))
				else:
					self.pOff_glyphList.append((p.x, p.y))

		self.pOffOn_glyphList = list(self.p_glyphList)
		self.pOffOn_glyphList.extend(self.pOff_glyphList)

	def buildUnicodeToNameDict(self, f):
		unicodeToNameDict = {}
		for g in f:
			unicodeToNameDict[g.unicode] = g.name
		return unicodeToNameDict

	def defineGlyphsForPartialTempFont(self, text, curGlyphString):
		def addGlyph(s, c):
			try:
				name = self.unicodeToNameDict[ord(c)]
				s.add(name)
				for component in self.tthtm.f[name].components:
					s.add(component.baseGlyph)
			except:
				#print("WARNING: character "+c+" is not in the font...")
				pass
		glyphSet = set()
		addGlyph(glyphSet, curGlyphString)
		for c in text:
			addGlyph(glyphSet, c)
		return glyphSet

	def generatePartialTempFont(self):
		#start = time.time()
		try:
			tempFont = RFont(showUI=False)
			#tempFont.lib['com.typemytype.robofont.segmentType'] = 'qCurve'
			tempFont.info.unitsPerEm = self.tthtm.f.info.unitsPerEm
			tempFont.info.ascender = self.tthtm.f.info.ascender
			tempFont.info.descender = self.tthtm.f.info.descender
			tempFont.info.xHeight = self.tthtm.f.info.xHeight
			tempFont.info.capHeight = self.tthtm.f.info.capHeight

			tempFont.info.familyName = self.tthtm.f.info.familyName
			tempFont.info.styleName = self.tthtm.f.info.styleName

			tempFont.glyphOrder = self.tthtm.f.glyphOrder

			if 'com.robofont.robohint.cvt ' in self.tthtm.f.lib:
				tempFont.lib['com.robofont.robohint.cvt '] = self.tthtm.f.lib['com.robofont.robohint.cvt ']
			if 'com.robofont.robohint.prep' in self.tthtm.f.lib:
				tempFont.lib['com.robofont.robohint.prep'] = self.tthtm.f.lib['com.robofont.robohint.prep']
			if 'com.robofont.robohint.fpgm' in self.tthtm.f.lib:
				tempFont.lib['com.robofont.robohint.fpgm'] = self.tthtm.f.lib['com.robofont.robohint.fpgm']

			for gName in self.tthtm.requiredGlyphsForPartialTempFont:
				tempFont.newGlyph(gName)
				tempFont[gName] = self.tthtm.f[gName]
				tempFont[gName].unicode = self.tthtm.f[gName].unicode
				if 'com.robofont.robohint.assembly' in self.tthtm.f[gName].lib:
					tempFont[gName].lib['com.robofont.robohint.assembly'] = self.tthtm.f[gName].lib['com.robofont.robohint.assembly']

			tempFont.generate(self.partialtempfontpath, 'ttf', decompose = False, checkOutlines = False, autohint = False, releaseMode = False, glyphOrder=None, progressBar = None )

			#finishedin = time.time() - start
			
			#print 'partial temp font generated in %f seconds' % finishedin
			#self.partialTempUFO = OpenFont(self.partialtempfontpath, showUI=False)
			self.doneGeneratingPartialFont = True
		except:
			print 'ERROR: Unable to generate temporary font'
			#print 'DONE generating partialtemp font with glyphs:', self.tthtm.requiredGlyphsForPartialTempFont

	def makePointNameToIndexDict(self, g):
		result = {}
		index = 0
		for contour in g:
			for point in contour.points:
				uniqueID = point.naked().uniqueID
				if point.name:
					name = point.name.split(',')[0]
					if name != 'inserted':
						result[name] = index
					else:
						result[uniqueID] = index
						point.name = uniqueID
				else:
					result[uniqueID] = index
				index += 1
		return result

	def makePointNameToUniqueIDDict(self, g):
		pointNameToUniqueID = {}
		for contour in g:
			for point in contour.points:
				uniqueID = point.naked().uniqueID
				if point.name:
					name = point.name.split(',')[0]
					if name != 'inserted':
						pointNameToUniqueID[name] = uniqueID
					else:
						pointNameToUniqueID[uniqueID] = uniqueID
						point.name = uniqueID
				else:
					pointNameToUniqueID[uniqueID] = uniqueID
		return pointNameToUniqueID

	def makePointUniqueIDToCoordinatesDict(self, g):
		pointUniqueIDToCoordinates = {}
		for contour in g:
			for point in contour.points:
				pointUniqueIDToCoordinates[point.naked().uniqueID] = ((point.x, point.y))
		return pointUniqueIDToCoordinates

	def makePointCoordinatesToUniqueIDDict(self, g):
		pointCoordinatesToUniqueID = {}
		pointCoordinatesToUniqueID[(0,0)] = 'lsb'
		pointCoordinatesToUniqueID[(g.width,0)] = 'rsb'
		for contour in g:
			for point in contour.points:
				pointCoordinatesToUniqueID[(point.x, point.y)] = (point.naked().uniqueID)
		return pointCoordinatesToUniqueID

	def makePointCoordinatesToNameDict(self, g):
		pointCoordinatesToName = {}
		pointCoordinatesToName[(0,0)] = 'lsb'
		pointCoordinatesToName[(g.width,0)] = 'rsb'
		for contour in g:
			for point in contour.points:
				pointCoordinatesToName[(point.x, point.y)] = (point.name.split(',')[0])
		return pointCoordinatesToName

	def readGlyphFLTTProgram(self, g):
		if g == None:
			return
		self.pointNameToUniqueID = self.makePointNameToUniqueIDDict(g)
		self.pointNameToIndex = self.makePointNameToIndexDict(g)
		self.glyphTTHCommands = []
		if 'com.fontlab.ttprogram' not in g.lib:
			return None
		ttprogram = g.lib['com.fontlab.ttprogram']
		strTTProgram = str(ttprogram)
		if strTTProgram[:4] == 'Data' and strTTProgram[-3:] == "n')":
			ttprogram = strTTProgram[6:-4]
		else:
			ttprogram = strTTProgram[6:-2]
		root = ET.fromstring(ttprogram)
		for child in root:
			self.glyphTTHCommands.append(child.attrib)
		return self.glyphTTHCommands

	def writeGlyphFLTTProgram(self, g):
		if g == None:
			return
		root = ET.Element('ttProgram')
		for command in self.glyphTTHCommands:
			com = ET.SubElement(root, 'ttc')
			com.attrib = command
		text = ET.tostring(root)
		g.lib['com.fontlab.ttprogram'] = Data(text)


	# def getGlyphIndexByName(self, glyphName):
	# 	try:
	# 		return self.indexOfGlyphNames[glyphName]
	# 	except:
	# 		return None

	def drawGrid(self, scale, pitch):
		if self.cachedPathes['grid'] == None:
			path = NSBezierPath.bezierPath()
			pos = - int(1000/pitch) * pitch
			maxi = -2 * pos
			while pos < maxi:
				path.moveToPoint_((pos, -1000))
				path.lineToPoint_((pos, 2000))
				path.moveToPoint_((-1000, pos))
				path.lineToPoint_((2000, pos))
				pos += pitch
			self.cachedPathes['grid'] = path
		path = self.cachedPathes['grid']
		gridColor.set()
		path.setLineWidth_(scale)
		path.stroke()

	def drawCenterPixel(self, scale, pitch):
		#nsView = self.getNSView()
		#super = nsView.superview()
		#print "NSView frame", nsView.frame()
		#print "NSView bounds", nsView.bounds()
		#print "super frame", nsView.superview().frame()
		#print "super bounds", nsView.superview().bounds()
		#lower_left_corner = nsView.convertPoint_fromView_(super.bounds().origin, super)
		#import Quartz
		#port = NSGraphicsContext.currentContext().graphicsPort()
		#m = Quartz.CGContextGetCTM(port)
		#print "Lower-left is ", lower_left_corner
		#print "Translation is ", (m.tx, m.ty)
		#m = (m.tx + lower_left_corner.x / scale, m.ty + lower_left_corner.y / scale)
		#print "Glyph origin in canvas lies at", m
		#m = Quartz.CGContextConvertPointToDeviceSpace(port, (0.0, 0.0))
		#print super.convertPoint_fromView_(m, nsView)
		#return
		if self.cachedPathes['centers'] == None or self.cachedScale != scale:
			path = NSBezierPath.bezierPath()
			r = scale * 3
			r = (r,r)
			x = - int(1000/pitch) * pitch + pitch/2 - r[0]/2
			yinit = x
			maxi = -2 * x
			while x < maxi:
				y = yinit
				while y < maxi:
					path.appendBezierPathWithOvalInRect_(((x, y), r))
					y += pitch
				x += pitch
			self.cachedScale = scale
			self.cachedPathes['centers'] = path
		path = self.cachedPathes['centers']
		centerpixelsColor.set()
		path.fill()

	def drawZones(self, scale):

		for zoneName, zone in self.tthtm.zones.iteritems():
			y_start = int(zone['position'])
			y_end = int(zone['width'])
			if not zone['top']:
				y_end = - y_end
			pathZone = NSBezierPath.bezierPath()
			pathZone.moveToPoint_((-5000, y_start))
			pathZone.lineToPoint_((5000, y_start))
			pathZone.lineToPoint_((5000, y_start+y_end))
			pathZone.lineToPoint_((-5000, y_start+y_end))
			pathZone.closePath
			zonecolor.set()
			pathZone.fill()	
			self.drawTextAtPoint(scale, zoneName, -100, y_start+y_end/2, whiteColor, zonecolorLabel)

	def drawTextAtPoint(self, scale, title, x, y, textColor, backgroundColor):
		currentTool = getActiveEventTool()
		view = currentTool.getNSView()

		attributes = {
			NSFontAttributeName : NSFont.boldSystemFontOfSize_(9),
			NSForegroundColorAttributeName : textColor,
			}
		backgroundStrokeColor = NSColor.whiteColor()

		text = NSAttributedString.alloc().initWithString_attributes_(title, attributes)
		width, height = text.size()
		fontSize = attributes[NSFontAttributeName].pointSize()
		width = width*scale
		width += 8.0*scale
		height = 13*scale
		x -= width / 2.0
		y -= fontSize*scale / 2.0
		
		
		#NSRectFill(((x, y), (width, height)))
		shadow = NSShadow.alloc().init()
		shadow.setShadowColor_(shadowColor)
		shadow.setShadowOffset_((0, -1))
		shadow.setShadowBlurRadius_(2)
		thePath = NSBezierPath.bezierPath()
		thePath.appendBezierPathWithRoundedRect_xRadius_yRadius_(((x, y), (width, height)), 3*scale, 3*scale)
		
		context = NSGraphicsContext.currentContext()
		context.saveGraphicsState()

		shadow.set()
		thePath.setLineWidth_(scale)
		backgroundColor.set()
		thePath.fill()
		borderColor.set()
		thePath.stroke()
		#text.drawAtPoint_((int(x+4.0*scale), int(y+2.0*scale)))
		context.restoreGraphicsState()
		
		view._drawTextAtPoint(title, attributes, (x+(width/2), y+(height/2)+1*scale), drawBackground=False)
		return (width, height)

	def drawRawTextAtPoint(self, scale, title, x, y, size):
		currentTool = getActiveEventTool()
		view = currentTool.getNSView()
		if scale != 0:
			scaledSize = size/scale
		else:
			scaledSize = size
		attributes = {
			NSFontAttributeName : NSFont.boldSystemFontOfSize_(scaledSize),
			NSForegroundColorAttributeName : axisColor,
			}

		text = NSAttributedString.alloc().initWithString_attributes_(title, attributes)
		width, height = text.size()
		fontSize = attributes[NSFontAttributeName].pointSize()
		width = width*scale
		width += 8.0*scale
		height = 13*scale
		x -= width / 2.0
		y -= fontSize*scale / 2.0
		
		view._drawTextAtPoint(title, attributes, (x+(width/2), y+(height/2)+1*scale), drawBackground=False)
		return (width, height)


	def drawPreviewSize(self, title, x, y, color):
		#currentview = self.previewWindow.view

		attributes = {
			NSFontAttributeName : NSFont.boldSystemFontOfSize_(7),
			NSForegroundColorAttributeName : color,
			}

		text = NSAttributedString.alloc().initWithString_attributes_(title, attributes)
		text.drawAtPoint_((x, y))

	def drawArrowAtPoint(self, scale, r, a, x, y):
		if x == None or y == None:
			return

	 	arrowAngle = math.radians(20)
	 	initAngle = math.radians(a)

		arrowPoint1_x = x + math.cos(initAngle+arrowAngle)*r*scale
		arrowPoint1_y = y + math.sin(initAngle+arrowAngle)*r*scale
		arrowPoint2_x = x + math.cos(initAngle-arrowAngle)*r*scale
		arrowPoint2_y = y + math.sin(initAngle-arrowAngle)*r*scale

		pathArrow = NSBezierPath.bezierPath()
	 	pathArrow.moveToPoint_((x, y))
		pathArrow.lineToPoint_((arrowPoint1_x, arrowPoint1_y))
		pathArrow.lineToPoint_((arrowPoint2_x, arrowPoint2_y))
		pathArrow.lineToPoint_((x, y))

		arrowColor.set()
		pathArrow.setLineWidth_(scale)
		pathArrow.fill()
		outlineColor.set()
		pathArrow.stroke()

	def drawDiscAtPoint(self, r, x, y, color):
		color.set()
		NSBezierPath.bezierPathWithOvalInRect_(((x-r, y-r), (r*2, r*2))).fill()

	def drawLozengeAtPoint(self, scale, r, x, y, color):
		color.set()
		path = NSBezierPath.bezierPath()
		path.moveToPoint_((x+r*5, y))
		path.lineToPoint_((x, y+r*5))
		path.lineToPoint_((x-r*5, y))
		path.lineToPoint_((x, y-r*5))
		path.lineToPoint_((x+r*5, y))
		#path.setLineWidth_(scale)
		path.fill()

	def drawAlign(self, scale, pointID, angle, cmdIndex):

		x = None
		y = None
		if pointID != 'lsb' and pointID != 'rsb':
			for contour in self.tthtm.g:
				for point in contour.points:
					if point.naked().uniqueID == pointID:
						x = point.x
						y = point.y
		elif pointID == 'lsb':
			x, y = 0, 0
		elif pointID == 'rsb':
			x, y = self.tthtm.g.width, 0

		self.drawArrowAtPoint(scale, 10, angle, x, y)
		self.drawArrowAtPoint(scale, 10, angle+180, x, y)

		extension = ''
		text = 'A'
		if 'align' in self.glyphTTHCommands[cmdIndex]:
			if self.tthtm.selectedAxis == 'Y' and self.glyphTTHCommands[cmdIndex]['align'] == 'right':
				extension = 'top'
			elif self.tthtm.selectedAxis == 'Y' and self.glyphTTHCommands[cmdIndex]['align'] == 'left':
				extension = 'bottom'
			else:
				extension = self.glyphTTHCommands[cmdIndex]['align']
				if extension == 'round':
					extension = 'closest'


			text += '_' + extension
		elif self.glyphTTHCommands[cmdIndex]['code'] == 'alignt' or self.glyphTTHCommands[cmdIndex]['code'] == 'alignb':
			text += '_' + self.glyphTTHCommands[cmdIndex]['zone']

		if self.glyphTTHCommands[cmdIndex]['code'] == 'alignt':
			(width, height) = self.drawTextAtPoint(scale, text, x + 10*scale, y + 20*scale, whiteColor, arrowColor)
		else:
			(width, height) = self.drawTextAtPoint(scale, text, x + 10*scale, y - 20*scale, whiteColor, arrowColor)

		# compute x, y
		if cmdIndex != None:
			if self.glyphTTHCommands[cmdIndex]['code'] == 'alignt':
				self.commandLabelPos[cmdIndex] = ((x + 10*scale, y + 20*scale), (width, height))
			else:
				self.commandLabelPos[cmdIndex] = ((x + 10*scale, y - 20*scale), (width, height))


	def drawArrowAtPoint_FromPoint_WithScale(self, endPoint, fromPoint, scale):
		r = 10
	 	arrowAngle = math.radians(20)

	 	initAngle = getAngle(endPoint, fromPoint)
	 	arrowPoint1_x = endPoint[0] + math.cos(initAngle+arrowAngle)*r*scale
		arrowPoint1_y = endPoint[1] + math.sin(initAngle+arrowAngle)*r*scale
		arrowPoint2_x = endPoint[0] + math.cos(initAngle-arrowAngle)*r*scale
		arrowPoint2_y = endPoint[1] + math.sin(initAngle-arrowAngle)*r*scale
		junction = ( ((arrowPoint1_x + arrowPoint2_x) / 2), ((arrowPoint1_y + arrowPoint2_y) / 2) )

		pathArrow = NSBezierPath.bezierPath()
	 	pathArrow.moveToPoint_(endPoint)
		pathArrow.lineToPoint_((arrowPoint1_x, arrowPoint1_y))
		pathArrow.lineToPoint_((arrowPoint2_x, arrowPoint2_y))

		return pathArrow, junction

	def drawLinkArrow(self, scale, startPoint, endPoint, color):
		start_end_diff = difference(startPoint, endPoint)
	 	dx, dy = start_end_diff[0]/2, start_end_diff[1]/2
	 	angle = getAngle((startPoint[0], startPoint[1]), (endPoint[0], endPoint[1])) + math.radians(90)
	 	offcurve1 = (startPoint[0] - dx + math.cos(angle)*(distance(startPoint, endPoint)/25)*scale, startPoint[1] - dy + math.sin(angle)*(distance(startPoint, endPoint)/25)*scale)

		pathArrow, junction_pathArrow = self.drawArrowAtPoint_FromPoint_WithScale(endPoint, offcurve1, scale)

		path = NSBezierPath.bezierPath()
	 	path.moveToPoint_((startPoint[0], startPoint[1]))
	 	path.curveToPoint_controlPoint1_controlPoint2_(junction_pathArrow, (offcurve1), (offcurve1) )
	 	
		color.set()
		path.setLineWidth_(scale)
		pathArrow.fill()
		path.stroke()


	def drawLink(self, scale, startPoint, endPoint, stemName, cmdIndex):
	 	color = linkColor
	 	textColor = whiteColor

	 	start_end_diff = difference(startPoint, endPoint)
	 	dx, dy = start_end_diff[0]/2, start_end_diff[1]/2
	 	angle = getAngle((startPoint[0], startPoint[1]), (endPoint[0], endPoint[1])) + math.radians(90)
	 	offcurve1 = (startPoint[0] - dx + math.cos(angle)*(distance(startPoint, endPoint)/25)*scale, startPoint[1] - dy + math.sin(angle)*(distance(startPoint, endPoint)/25)*scale)

		extension = ''
		if 'align' in self.glyphTTHCommands[cmdIndex]:
			if self.tthtm.selectedAxis == 'Y' and self.glyphTTHCommands[cmdIndex]['align'] == 'right':
				extension = 'top'
			elif self.tthtm.selectedAxis == 'Y' and self.glyphTTHCommands[cmdIndex]['align'] == 'left':
				extension = 'bottom'
			else:
				extension = self.glyphTTHCommands[cmdIndex]['align']
				if extension == 'round':
					extension = 'closest'

		if 'round' in self.glyphTTHCommands[cmdIndex]:
			if self.glyphTTHCommands[cmdIndex]['round'] == 'true':
				text = 'R'
				if stemName == None and extension != '':
					text += '_' + extension
				elif stemName != None:
					text += '_' + stemName
		else:
			text = 'S'
			if stemName == None and extension != '':
				text += '_' + extension
			elif stemName != None:
				color = stemColor
				textColor = blackColor
				text += '_' + stemName

		self.drawLinkArrow(scale, startPoint, endPoint, color)
		(width, height) = self.drawTextAtPoint(scale, text, offcurve1[0], offcurve1[1], textColor, color)

		# compute x, y
		if cmdIndex != None:
			self.commandLabelPos[cmdIndex] = ((offcurve1[0], offcurve1[1]), (width, height))

	def drawDoubleLinkDragging(self, scale, startPoint, endPoint):
		start_end_diff = difference(startPoint, endPoint)
	 	dx, dy = start_end_diff[0]/2, start_end_diff[1]/2
	 	angle = getAngle((startPoint[0], startPoint[1]), (endPoint[0], endPoint[1])) + math.radians(90)
	 	offcurve1 = (startPoint[0] - dx + math.cos(angle)*(distance(startPoint, endPoint)/25)*scale, startPoint[1] - dy + math.sin(angle)*(distance(startPoint, endPoint)/25)*scale)


		pathArrowStart, junction_pathArrowStart = self.drawArrowAtPoint_FromPoint_WithScale(startPoint, offcurve1, scale)
		pathArrowEnd, junction_pathArrowEnd = self.drawArrowAtPoint_FromPoint_WithScale(endPoint, offcurve1, scale)


		path = NSBezierPath.bezierPath()
	 	path.moveToPoint_(junction_pathArrowStart)
	 	path.curveToPoint_controlPoint1_controlPoint2_(junction_pathArrowEnd, (offcurve1), (offcurve1) )

		doublinkColor.set()
		path.setLineWidth_(scale)
		pathArrowEnd.fill()
		pathArrowStart.fill()
		path.stroke()

	def drawDoubleLink(self, scale, startPoint, endPoint, stemName, cmdIndex):

	 	self.drawDoubleLinkDragging(scale, startPoint, endPoint)

	 	start_end_diff = difference(startPoint, endPoint)
	 	dx, dy = start_end_diff[0]/2, start_end_diff[1]/2
	 	angle = getAngle((startPoint[0], startPoint[1]), (endPoint[0], endPoint[1])) + math.radians(90)
	 	offcurve1 = (startPoint[0] - dx + math.cos(angle)*(distance(startPoint, endPoint)/25)*scale, startPoint[1] - dy + math.sin(angle)*(distance(startPoint, endPoint)/25)*scale)

		extension = ''
		text = 'D'
		if 'round' in self.glyphTTHCommands[cmdIndex]:
			if self.glyphTTHCommands[cmdIndex]['round'] == 'true':
				if stemName != None:
					text += '_' + stemName
				else:
					text = 'R'
		elif stemName != None:
			text += '_' + stemName

		(width, height) = self.drawTextAtPoint(scale, text, offcurve1[0], offcurve1[1], whiteColor, doublinkColor)

		# compute x, y
		if cmdIndex != None:
			self.commandLabelPos[cmdIndex] = ( (offcurve1), (width, height) )

	def drawInterpolateDragging(self, scale, startPoint, middlePoint):
		if middlePoint == None or startPoint == None:
			return
		start_middle_diff = difference(startPoint, middlePoint)
		dx, dy = start_middle_diff[0]/2, start_middle_diff[1]/2
		angle = getAngle((startPoint[0], startPoint[1]), (middlePoint[0], middlePoint[1])) + math.radians(90)
		center1 = (startPoint[0] - dx + math.cos(angle)*(distance(startPoint, middlePoint)/25)*scale, startPoint[1] - dy + math.sin(angle)*(distance(startPoint, middlePoint)/25)*scale)

		pathArrowStart, junction_pathArrowStart = self.drawArrowAtPoint_FromPoint_WithScale(startPoint, center1, scale)
		pathArrowEnd, junction_pathArrowEnd = self.drawArrowAtPoint_FromPoint_WithScale(middlePoint, center1, scale)

		path = NSBezierPath.bezierPath()
		path.moveToPoint_(junction_pathArrowStart)
		path.curveToPoint_controlPoint1_controlPoint2_(junction_pathArrowEnd, (center1), (center1) )

		interpolatecolor.set()
		path.setLineWidth_(scale)
		pathArrowEnd.fill()
		pathArrowStart.fill()
		path.stroke()

	def giveMouseCoordinates(self, info):
		self.movingMouse = info['point']
		UpdateCurrentGlyphView()

	def drawInterpolateMouseMoved(self, info): 
		scale = info['scale']
		touchedEnd = self.isOnPoint(self.movingMouse)
		if touchedEnd != None:
			self.endPoint = touchedEnd
			self.movingMouse = touchedEnd
			x_end = touchedEnd[0]
			y_end = touchedEnd[1]
			self.drawLozengeAtPoint(5*scale, scale, x_end, y_end, lozengeColor)

		self.drawInterpolateDragging(scale, self.startPointInterpolate1, self.endPointInterpolate1)
		self.drawInterpolateDragging(scale, self.endDraggingPoint, self.movingMouse)


	def drawInterpolate(self, scale, startPoint, endPoint, middlePoint, cmdIndex):

		start_middle_diff = difference(startPoint, middlePoint)
		dx, dy = start_middle_diff[0]/2, start_middle_diff[1]/2
		angle = getAngle((startPoint[0], startPoint[1]), (middlePoint[0], middlePoint[1])) + math.radians(90)
		center1 = (startPoint[0] - dx + math.cos(angle)*(distance(startPoint, middlePoint)/25)*scale, startPoint[1] - dy + math.sin(angle)*(distance(startPoint, middlePoint)/25)*scale)

		pathArrowStart, junction_pathArrowStart = self.drawArrowAtPoint_FromPoint_WithScale(startPoint, center1, scale)
		pathArrowEnd, junction_pathArrowEnd = self.drawArrowAtPoint_FromPoint_WithScale(middlePoint, center1, scale)

		middle_end_diff = difference(middlePoint, endPoint)
		dx, dy = middle_end_diff[0]/2, middle_end_diff[1]/2
		angle = getAngle((middlePoint[0], middlePoint[1]), (endPoint[0], endPoint[1])) + math.radians(90)
		center2 = (middlePoint[0] - dx + math.cos(angle)*(distance(middlePoint, endPoint)/25)*scale, middlePoint[1] - dy + math.sin(angle)*(distance(middlePoint, endPoint)/25)*scale)

		pathArrowStart2, junction_pathArrowStart2 = self.drawArrowAtPoint_FromPoint_WithScale(endPoint, center2, scale)
		pathArrowEnd2, junction_pathArrowEnd2 = self.drawArrowAtPoint_FromPoint_WithScale(middlePoint, center2, scale)

		path = NSBezierPath.bezierPath()
		path.moveToPoint_(junction_pathArrowStart)
		path.curveToPoint_controlPoint1_controlPoint2_(junction_pathArrowEnd, (center1), (center1) )	
		path.moveToPoint_(junction_pathArrowStart2)
		path.curveToPoint_controlPoint1_controlPoint2_(junction_pathArrowEnd2, (center2), (center2) )

		interpolatecolor.set()
		path.setLineWidth_(scale*1.3)
		pathArrowEnd.fill()
		pathArrowStart.fill()
		pathArrowEnd2.fill()
		pathArrowStart2.fill()
		path.stroke()

		extension = ''
		text = 'I'
		if 'align' in self.glyphTTHCommands[cmdIndex]:
			if self.tthtm.selectedAxis == 'Y' and self.glyphTTHCommands[cmdIndex]['align'] == 'right':
				extension = 'top'
				text += '_' + extension
			elif self.tthtm.selectedAxis == 'Y' and self.glyphTTHCommands[cmdIndex]['align'] == 'left':
				extension = 'bottom'
				text += '_' + extension
			else:
				extension = self.glyphTTHCommands[cmdIndex]['align']
				if extension == 'round':
					extension = 'closest'
				text += '_' + extension

		(width, height) =self.drawTextAtPoint(scale, text, middlePoint[0] + 10*scale, middlePoint[1] - 10*scale, whiteColor, interpolatecolor)

		# compute x, y
		if cmdIndex != None:
			self.commandLabelPos[cmdIndex] = ((middlePoint[0] + 10*scale, middlePoint[1] - 10*scale), (width, height))

	def drawDelta(self, scale, point, value, cmdIndex, color):

		path = NSBezierPath.bezierPath()
	 	path.moveToPoint_((point[0], point[1]))
	 	end_x = point[0] + (value[0]/8.0)*self.tthtm.pitch
	 	end_y = point[1] + (value[1]/8.0)*self.tthtm.pitch
	 	path.lineToPoint_((end_x, end_y))

	 	color.set()
		path.setLineWidth_(scale)
		path.stroke()
		r = 4
		#NSBezierPath.bezierPathWithOvalInRect_(((end_x-r*scale, end_y-r*scale), (r*2*scale, r*2*scale))).fill()
		self.drawLozengeAtPoint(r*scale, scale, end_x, end_y, color)
		
		extension = ''
		text = 'delta'
		value = self.glyphTTHCommands[cmdIndex]['delta']
		if self.glyphTTHCommands[cmdIndex]['code'][:1] == 'm':
			extension = '_M'
		elif self.glyphTTHCommands[cmdIndex]['code'][:1] == 'f':
			extension = '_F'
		text += extension + ':' + value

		
		if self.glyphTTHCommands[cmdIndex]['code'][-1:] == 'v' and int(value) < 0:
			(width, height) = self.drawTextAtPoint(scale, text, point[0] - 10*scale, point[1] + 10*scale, whiteColor, color)
		else:
			(width, height) = self.drawTextAtPoint(scale, text, point[0] - 10*scale, point[1] - 10*scale, whiteColor, color)

		# compute x, y
		if cmdIndex != None:
			if self.glyphTTHCommands[cmdIndex]['code'][-1:] == 'v' and int(value) < 0:
				self.commandLabelPos[cmdIndex] = ((point[0] - 10*scale, point[1] + 10*scale), (width, height))
			else:
				self.commandLabelPos[cmdIndex] = ((point[0] - 10*scale, point[1] - 10*scale), (width, height))
			

	def drawSideBearings(self, scale, char):
		try:
			xPos = self.tthtm.pitch * self.tthtm.textRenderer.get_char_advance(char)[0] / 64
		except:
			return
		pathX = NSBezierPath.bezierPath()
		pathX.moveToPoint_((xPos, -5000))
		pathX.lineToPoint_((xPos, 5000))
		sidebearingColor.set()
		pathX.setLineWidth_(scale)
		pathX.stroke()

		pathX = NSBezierPath.bezierPath()
		pathX.moveToPoint_((0, -5000))
		pathX.lineToPoint_((0, 5000))
		sidebearingColor.set()
		pathX.setLineWidth_(scale)
		pathX.stroke()

	def prepareText(self):
		if self.tthtm.g == None:
			return (' ', ' ')
		if self.tthtm.g.unicode == None:
			print 'Glyph %s must have Unicode value to be hinted' % self.tthtm.g.name
			return (' ', ' ')

		curGlyphString = unichr(self.tthtm.g.unicode)

		# replace @ by current glyph
		#text = self.previewWindow.previewString.replace('@', curGlyphString)
		text = self.tthtm.previewString.replace('/?', curGlyphString)

		# replace /name pattern
		sp = text.split('/')
		nbsp = len(sp)
		for i in range(1,nbsp):
			sub = sp[i].split(' ', 1)
			if sub[0] in self.tthtm.f:
				sp[i] = unichr(self.tthtm.f[sub[0]].unicode) + (' '.join(sub[1:]))
			else:
				sp[i] = ''
		text = ''.join(sp)
		self.previewText = text
		return (text, curGlyphString)

	def drawPreviewWindow(self):
		if self.ready == False:
			return
		if self.tthtm.g == None:
			return

		self.clickableSizes= {}

		if not self.tthtm.textRenderer:
			return

		advanceWidthUserString = self.tthtm.previewWindowViewSize[0]
		advanceWidthCurrentGlyph = self.tthtm.previewWindowViewSize[0]
		(text, curGlyphString) = self.prepareText()
		# render user string
		self.tthtm.textRenderer.set_cur_size(self.tthtm.PPM_Size)

		self.tthtm.textRenderer.set_pen((20, self.tthtm.previewWindowPosSize[3] - 250))
		self.tthtm.textRenderer.render_text(text)

		self.clickableGlyphs = {}
		pen = (20, self.tthtm.previewWindowPosSize[3] - 250)
		for c in text:
			adv = self.tthtm.textRenderer.get_char_advance(c)
			newpen = pen[0]+int(adv[0]/64), pen[1]+int(adv[1]/64)
			rect = (pen[0], pen[1], newpen[0], pen[1]+self.tthtm.PPM_Size)
			self.clickableGlyphs[rect] = splitText(c, self.tthtm.f.naked().unicodeData)
			pen = newpen

		# render user string at various sizes
		y = self.tthtm.previewWindowPosSize[3] - 310
		x = 30
		for size in range(self.tthtm.previewFrom, self.tthtm.previewTo+1, 1):

			self.clickableSizes[(x-20, y)] = size

			displaysize = str(size)
			if size == self.tthtm.PPM_Size and text != '':
				self.drawPreviewSize(displaysize, x-20, y, NSColor.redColor())
			elif text != '':
				self.drawPreviewSize(displaysize, x-20, y, NSColor.blackColor())

			self.tthtm.textRenderer.set_cur_size(size)
			self.tthtm.textRenderer.set_pen((x, y))
			self.tthtm.textRenderer.render_text(text)
			y -= size + 1
			if y < 0:
				width, height = self.tthtm.textRenderer.pen
				x = width+40
				y = self.tthtm.previewWindowPosSize[3] - 310
				advanceWidthUserString = self.tthtm.textRenderer.get_pen()[0]


		# render current glyph at various sizes
		advance = 10
		
		for size in range(self.tthtm.previewFrom, self.tthtm.previewTo+1, 1):

			self.clickableSizes[(advance, self.tthtm.previewWindowPosSize[3] - 200)] = size

			displaysize = str(size)
			if size == self.tthtm.PPM_Size:
				self.drawPreviewSize(displaysize, advance, self.tthtm.previewWindowPosSize[3] - 200, NSColor.redColor())
			else:
				self.drawPreviewSize(displaysize, advance, self.tthtm.previewWindowPosSize[3] - 200, NSColor.blackColor())
			
			self.tthtm.textRenderer.set_cur_size(size)
			self.tthtm.textRenderer.set_pen((advance, self.tthtm.previewWindowPosSize[3] - 165))
			delta_pos = self.tthtm.textRenderer.render_text(curGlyphString)
			advance += delta_pos[0] + 5
			advanceWidthCurrentGlyph = advance


		self.tthtm.previewWindowViewSize = (self.tthtm.previewWindowPosSize[2]-35, self.tthtm.previewWindowViewSize[1])

		if advanceWidthCurrentGlyph > self.tthtm.previewWindowViewSize[0] and advanceWidthUserString > advanceWidthCurrentGlyph:
			self.tthtm.previewWindowViewSize = (advanceWidthUserString, self.tthtm.previewWindowViewSize[1])
		else:
			self.tthtm.previewWindowViewSize = (advanceWidthCurrentGlyph, self.tthtm.previewWindowViewSize[1])
				

	def drawBackground(self, scale):
		if self.tthtm.g == None or self.doneGeneratingPartialFont == False:
			return
		if self.tthtm.g.unicode == None:
			return

		if self.tthtm.selectedAxis == 'X':
			text = u'⬌'
		else:
			text = u'⬍'
		self.drawRawTextAtPoint(scale, text, -100, 120, 120)

		r = 5*scale
		self.drawDiscAtPoint(r, 0, 0, discColor)
		self.drawDiscAtPoint(r, self.tthtm.g.width, 0, discColor)

		self.drawZones(scale)

		curChar = unichr(self.tthtm.g.unicode)
		self.tthtm.textRenderer.set_cur_size(self.tthtm.PPM_Size)
		self.tthtm.textRenderer.set_pen((0, 0))

		if self.tthtm.showBitmap == 1:
			self.tthtm.textRenderer.render_text_with_scale_and_alpha(curChar, self.tthtm.pitch, 0.4)

		if self.tthtm.showGrid == 1:
			self.drawGrid(scale, self.tthtm.pitch)

		if self.tthtm.showCenterPixel == 1:
			self.drawCenterPixel(scale, self.tthtm.pitch)

		if self.tthtm.showOutline == 1:
			self.tthtm.textRenderer.drawOutline(scale, self.tthtm.pitch, curChar)
			self.drawSideBearings(scale, curChar)


	def draw(self, scale):
		self.scale = scale
		if self.tthtm.g == None:
			return
			
		if self.isDragging():
			self.endPoint = self.currentPoint
			touchedEnd = self.isOnPoint(self.currentPoint)
			if self.tthtm.selectedHintingTool in ['Middle Delta', 'Final Delta']:
				touchedEnd = self.isOffOnPoint(self.currentPoint)
			if touchedEnd != None:
				self.endPoint = touchedEnd
				x_end = touchedEnd[0]
				y_end = touchedEnd[1]
				self.drawLozengeAtPoint(5*scale, scale, x_end, y_end, lozengeColor)
			if self.startPoint != None and self.tthtm.selectedHintingTool != 'Align':
				x_start = self.startPoint[0]
				y_start = self.startPoint[1]
				self.drawLozengeAtPoint(5*scale, scale, x_start, y_start, lozengeColor)
				if self.tthtm.selectedHintingTool == 'Single Link':
					self.drawLinkArrow(scale, self.startPoint, self.endPoint, linkColor)
				elif self.tthtm.selectedHintingTool == 'Double Link':
					self.drawDoubleLinkDragging(scale, self.startPoint, self.endPoint)
				elif self.tthtm.selectedHintingTool == 'Interpolation':
					self.drawInterpolateDragging(scale, self.startPoint, self.endPoint)


		for cmdIndex, c in enumerate(self.glyphTTHCommands):
			# search elements only once
			cmd_code = getOrNone(c, 'code')
			cmd_pt   = getOrNone(c, 'point')
			cmd_pt1  = getOrNone(c, 'point1')
			cmd_pt2  = getOrNone(c, 'point2')
			cmd_stem = getOrNone(c, 'stem')
			if cmd_code in ['alignh', 'alignv', 'alignt', 'alignb']:
				angle = 90
				if cmd_code == 'alignh':
					angle = 180
				if cmd_pt in ['lsb', 'rsb']:
					if cmd_code in ['alignv', 'alignt', 'alignb'] and self.tthtm.selectedAxis == 'Y':
						self.drawAlign(scale, cmd_pt, angle, cmdIndex)
					elif cmd_code == 'alignh' and self.tthtm.selectedAxis == 'X':
						self.drawAlign(scale, cmd_pt, angle, cmdIndex)
				elif cmd_code in ['alignv', 'alignt', 'alignb'] and self.tthtm.selectedAxis == 'Y':
					self.drawAlign(scale, self.pointNameToUniqueID[cmd_pt], angle, cmdIndex)
				elif cmd_code == 'alignh' and self.tthtm.selectedAxis == 'X':
					self.drawAlign(scale, self.pointNameToUniqueID[cmd_pt], angle, cmdIndex)

			if cmd_code in ['singleh', 'singlev', 'doubleh', 'doublev']:
				if cmd_pt1 == 'lsb':
					startPoint = (0, 0)
				elif cmd_pt1== 'rsb':
					startPoint = (self.tthtm.g.width, 0)
				else:
					startPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt1]]

				if cmd_pt2 == 'lsb':
					endPoint = (0, 0)
				elif cmd_pt2 == 'rsb':
					endPoint = (self.tthtm.g.width, 0)
				else:
					endPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt2]]

				if cmd_code in ['doubleh', 'doublev']:
					if self.tthtm.selectedAxis == 'X' and cmd_code == 'doubleh':
						self.drawDoubleLink(scale, startPoint, endPoint, cmd_stem, cmdIndex)
					elif self.tthtm.selectedAxis == 'Y' and cmd_code == 'doublev':
						self.drawDoubleLink(scale, startPoint, endPoint, cmd_stem, cmdIndex)
				elif self.tthtm.selectedAxis == 'X' and cmd_code == 'singleh':
					self.drawLink(scale, startPoint, endPoint, cmd_stem, cmdIndex)
				elif self.tthtm.selectedAxis == 'Y' and cmd_code == 'singlev':
					self.drawLink(scale, startPoint, endPoint, cmd_stem, cmdIndex)

			if cmd_code in ['interpolateh', 'interpolatev']:

				if cmd_pt == 'lsb':
					middlePoint = (0, 0)
				elif cmd_pt== 'rsb':
					middlePoint = (0, self.tthtm.g.width)
				else:
					middlePoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt]]

				if cmd_pt1 == 'lsb':
					startPoint = (0, 0)
				elif cmd_pt1== 'rsb':
					startPoint = (0, self.tthtm.g.width)
				else:
					startPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt1]]

				if cmd_pt2 == 'lsb':
					endPoint = (0, 0)
				elif cmd_pt2 == 'rsb':
					endPoint = (self.tthtm.g.width, 0)
				else:
					endPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt2]]

				if self.tthtm.selectedAxis == 'X' and cmd_code == 'interpolateh':
					self.drawInterpolate(scale, startPoint, endPoint, middlePoint, cmdIndex)
				elif self.tthtm.selectedAxis == 'Y' and cmd_code == 'interpolatev':
					self.drawInterpolate(scale, startPoint, endPoint, middlePoint, cmdIndex)

			if cmd_code in ['mdeltah', 'mdeltav', 'fdeltah', 'fdeltav']:
				if cmd_code in ['mdeltah', 'mdeltav']:
					color = deltacolor
				else:
					color = finaldeltacolor
				if cmd_pt == 'lsb':
					point = (0, 0)
				elif cmd_pt== 'rsb':
					point = (self.tthtm.g.width, 0)
				else:
					point = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt]]

				if cmd_code[-1] == 'h':
					value = (int(c['delta']), 0)
				elif cmd_code[-1] == 'v':
					value = (0, int(c['delta']))
				else:
					value = 0

				if int(self.tthtm.PPM_Size) in range(int(c['ppm1']), int(c['ppm2'])+1, 1):
					if self.tthtm.selectedAxis == 'X' and cmd_code in ['mdeltah', 'fdeltah']:
						self.drawDelta(scale, point, value, cmdIndex, color)
					elif self.tthtm.selectedAxis == 'Y' and cmd_code in ['mdeltav', 'fdeltav']:
						self.drawDelta(scale, point, value, cmdIndex, color)


		if self.tthtm.showPreviewInGlyphWindow == 1 and not self.messageInFront:
			superview = self.getNSView().enclosingScrollView().superview()
			if self.previewInGlyphWindow == None:
				self.previewInGlyphWindow = preview.PreviewInGlyphWindow.alloc().init_withTTHToolInstance(self)
				superview.addSubview_(self.previewInGlyphWindow)
			frame = superview.frame()
			frame.size.width -= 30
			frame.origin.x = 0
			self.previewInGlyphWindow.setFrame_(frame)
			self.previewInGlyphWindow.setNeedsDisplay_(True)
			UpdateCurrentGlyphView()


reload(TR)
reload(TTHintAsm)
reload(tt_tables)
reload(view)

