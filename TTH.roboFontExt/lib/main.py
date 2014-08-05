from mojo.events import *
from mojo.UI import *
from mojo.extensions import *
from mojo.drawingTools import *
from lib.doodleMenus import BaseMenu
from robofab.plistlib import Data
import fontTools

import fl_tth
import tt_tables
import TTHintAsm
import view
import TextRenderer as TR
import TTHToolModel

import xml.etree.ElementTree as ET
import math, os


toolbarIcon = ExtensionBundle("TTH").get("toolbarIcon")

def topologicalSort(l, f):
	n = len(l)
	preds = [[] for i in range(n)]
	visited = [False for i in l]
	loop = [False for i in l]
	for i in range(n):
		li = l[i]
		for j in range(n):
			if i == j:
				continue
			(comp, swap) = f(li, l[j])
			if comp:
				if swap:
					preds[i].append(j)
				else:
					preds[j].append(i)
	result = []
	def visit(i):
		if loop[i]:
			print "ERROR: Loop in topological sort"
			return l
		if visited[i]:
			return
		loop[i] = True
		for p in preds[i]:
			visit(p)
		loop[i] = False
		visited[i] = True
		result.append(l[i])
	for i in range(n):
		visit(i)
	result.reverse()
	return result

def pointsApproxEqual(p_glyph, p_cursor):
	return (abs(p_glyph[0] - p_cursor[0]) < 10) and (abs(p_glyph[1] - p_cursor[1]) < 10)

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

def createUnicodeToNameDict():
	glyphList = open('../resources/GlyphList.txt', 'r')
	unicodeToNameDict ={}
	for i in glyphList:
		if i[:1] != '#':
			name = i.split(';')[0]
			unicodeGlyph = '0x' + i.split(';')[1][:-1]
			unicodeGlyph = unicodeGlyph.split(' ')[0]
			if int(unicodeGlyph, 16) not in unicodeToNameDict:
				unicodeToNameDict[int(unicodeGlyph, 16)] = name
	return unicodeToNameDict


def getGlyphNameByUnicode(unicodeToNameDict, unicodeChar):
	return unicodeToNameDict[unicodeChar]

def difference(point1, point2):
	return ((point1[0] - point2[0]), (point1[1] - point2[1]))

def getAngle((x1, y1), (x2, y2)):
	xDiff = x2-x1
	yDiff= y2-y1 
	return math.atan2(yDiff, xDiff)

class callbackAlignment():
	def __init__(self, TTHtoolInstance, alignmentType):
		self.ttht = TTHtoolInstance
		self.alignmentType = alignmentType

	def __call__(self, item):
		cmdIndex = self.ttht.commandRightClicked
		self.ttht.glyphTTHCommands[cmdIndex]['align'] = self.alignmentType
		self.ttht.updateGlyphProgram()

class callbackZoneAlignment():
	def __init__(self, TTHtoolInstance, alignmentZone):
		self.ttht = TTHtoolInstance
		self.alignmentZone = alignmentZone

	def __call__(self, item):
		cmdIndex = self.ttht.commandRightClicked
		self.ttht.glyphTTHCommands[cmdIndex]['zone'] = self.alignmentZone
		self.ttht.updateGlyphProgram()

class callbackDistance():
	def __init__(self, TTHtoolInstance, stemName):
		self.ttht = TTHtoolInstance
		self.stemName = stemName

	def __call__(self, item):
		cmdIndex = self.ttht.commandRightClicked
		self.ttht.glyphTTHCommands[cmdIndex]['stem'] = self.stemName
		self.ttht.updateGlyphProgram()

class callbackSetDeltaValue():
	def __init__(self, TTHtoolInstance, value):
		self.ttht = TTHtoolInstance
		self.value = str(value)

	def __call__(self, item):
		cmdIndex = self.ttht.commandRightClicked
		self.ttht.glyphTTHCommands[cmdIndex]['delta'] = self.value
		self.ttht.updateGlyphProgram()


class TTHTool(BaseEventTool):

	def __init__(self, tthm):
		BaseEventTool.__init__(self)

		self.ready = False
		self.unicodeToNameDict = createUnicodeToNameDict()
		self.p_glyphList = []
		self.commandLabelPos = {}
		self.tthtm = tthtm

	### TTH Tool Icon ###
	def getToolbarIcon(self):
		## return the toolbar icon
		return toolbarIcon
		
	def getToolbarTip(self):
		return "TTH Hinting Tool"
	###############

	def becomeActive(self):
		self.resetFonts(createWindows=True)

	def becomeInactive(self):
		self.FL_Windows.closeAll()
		self.centralWindow.closeCentral()
		self.previewWindow.closePreview()

	def fontResignCurrent(self, font):
		self.FL_Windows.closeAll()
		self.centralWindow.closeCentral()
		self.previewWindow.closePreview()
		self.resetFonts(createWindows=True)

	def fontBecameCurrent(self, font):
		self.FL_Windows.closeAll()
		self.centralWindow.closeCentral()
		self.previewWindow.closePreview()
		self.resetFonts(createWindows=True)
		self.resetglyph()

	def viewDidChangeGlyph(self):
		self.resetglyph()

	def getSizeListIndex(self, size):
		sizeIndex = 0
		for i in range(len(self.centralWindow.PPMSizesList)):
			if self.centralWindow.PPMSizesList[i] == str(size):
				sizeIndex = i
		return sizeIndex

	def getSize(self):
		return self.tthtm.PPM_Size

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

		self.changeDeltaRange(self.tthtm.PPM_Size, self.tthtm.PPM_Size)

		self.previewWindow.view.setNeedsDisplay_(True)
		UpdateCurrentGlyphView()

	def changeAxis(self, axis):
		self.tthtm.setAxis(axis)
		if axis == 'X':
			axisIndex = 0
		elif axis == 'Y':
			axisIndex = 1
		self.centralWindow.wCentral.AxisPopUpButton.set(axisIndex)

	def getPreviewListIndex(self, preview):
		previewIndex = 0
		for i in range(len(self.centralWindow.BitmapPreviewList)):
			if self.centralWindow.BitmapPreviewList[i] == preview:
				previewIndex = i
		return previewIndex

	def changeBitmapPreview(self, preview):
		self.tthtm.setBitmapPreview(preview)
		self.tthtm.textRenderer = TR.TextRenderer(self.fulltempfontpath, preview)
		previewIndex = self.getPreviewListIndex(preview)
		self.centralWindow.wCentral.BitmapPreviewPopUpButton.set(previewIndex)

		if self.tthtm.g == None:
			return
		self.previewWindow.view.setNeedsDisplay_(True)
		UpdateCurrentGlyphView()

	def getHintingToolIndex(self, hintingTool):
		hintingToolIndex = 0
		for i in range(len(self.centralWindow.hintingToolsList)):
			if self.centralWindow.hintingToolsList[i] == hintingTool:
				hintingToolIndex = i
		return hintingToolIndex

	def changeSelectedHintingTool(self, hintingTool):
		self.tthtm.setHintingTool(hintingTool)
		hintingToolIndex = self.getHintingToolIndex(self.tthtm.selectedHintingTool)
		self.centralWindow.wCentral.HintingToolPopUpButton.set(hintingToolIndex)
		if hintingToolIndex == 0:
			self.centralWindow.centralWindowAlignSettings()
			self.changeSelectedAlignmentTypeAlign(self.tthtm.selectedAlignmentTypeAlign)
			
		if hintingToolIndex in [1, 2]:
			self.centralWindow.centralWindowLinkSettings()
			self.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)
			self.changeSelectedStemX(self.tthtm.selectedStemX)
			self.changeSelectedStemY(self.tthtm.selectedStemY)
			self.changeRoundBool(self.tthtm.roundBool)
			
		if hintingToolIndex == 3:
			self.centralWindow.centralWindowInterpolationSettings()
		if hintingToolIndex in [4, 5]:
			self.centralWindow.centralWindowDeltaSettings()

	def getAlignmentTypeAlignIndex(self, alignmentType):
		alignmentTypeIndex = 0
		for i in range(len(self.centralWindow.alignmentTypeList)):
			if self.centralWindow.alignmentTypeList[i] == alignmentType:
				alignmentTypeIndex = i
		return alignmentTypeIndex

	def changeSelectedAlignmentTypeAlign(self, alignmentType):
		self.tthtm.setAlignmentTypeAlign(alignmentType)
		alignmentTypeIndex = self.getAlignmentTypeAlignIndex(self.tthtm.selectedAlignmentTypeAlign)
		self.centralWindow.wCentral.AlignmentTypePopUpButton.set(alignmentTypeIndex)

	def getAlignmentTypeLinkIndex(self, alignmentType):
		alignmentTypeIndex = 0
		for i in range(len(self.centralWindow.alignmentTypeListLink)):
			if self.centralWindow.alignmentTypeListLink[i] == alignmentType:
				alignmentTypeIndex = i
		return alignmentTypeIndex

	def changeSelectedAlignmentTypeLink(self, alignmentType):
		self.tthtm.setAlignmentTypeLink(alignmentType)
		alignmentTypeIndex = self.getAlignmentTypeLinkIndex(self.tthtm.selectedAlignmentTypeLink)
		self.centralWindow.wCentral.AlignmentTypePopUpButton.set(alignmentTypeIndex)

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
		self.centralWindow.wCentral.StemTypePopUpButton.set(stemIndex)

	def changeSelectedStemY(self, stemName):
		self.tthtm.setStemY(stemName)
		stemIndex = self.getStemIndex(self.tthtm.selectedStemY, 'Y')
		self.centralWindow.wCentral.StemTypePopUpButton.set(stemIndex)

	def changeRoundBool(self, roundBool):
		self.tthtm.setRoundBool(roundBool)
		self.centralWindow.wCentral.RoundDistanceCheckBox.set(self.tthtm.roundBool)

	def changeDeltaOffset(self, offset):
		self.tthtm.setDeltaOffset(offset)
		self.centralWindow.wCentral.DeltaOffsetSlider.set(self.tthtm.deltaOffset + 8)

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
		self.centralWindow.wCentral.DeltaRange1EditText.set(self.tthtm.deltaRange1)
		self.tthtm.setDeltaRange2(value2)
		self.centralWindow.wCentral.DeltaRange2EditText.set(self.tthtm.deltaRange2)

	def makeStemsListsPopUpMenu(self):
		self.tthtm.stemsListX = ['None']
		self.tthtm.stemsListY = ['None']

		for name, stem in self.FL_Windows.stems.iteritems():
			if stem['horizontal'] == True:
				self.tthtm.stemsListY.append(name)
			else:
				self.tthtm.stemsListX.append(name)

	def showHidePreviewWindow(self, showHide):
		if showHide == 0:
			self.previewWindow.hidePreview()
		elif showHide == 1:
			self.previewWindow.showPreview()


	def isOnPoint(self, p_cursor):
		def pred0(p_glyph):
			return pointsApproxEqual(p_glyph, p_cursor)
		touched_p_glyph = find_in_list(self.p_glyphList, pred0)

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
			return pointsApproxEqual(commandPos, p_cursor)

		touched_p_command = find_in_dict(self.commandLabelPos, pred0)

		return touched_p_command

	def isInZone(self, point, y_min, y_max):
		if point[1]  >= y_min and point[1] <= y_max:
			return True
		else:
			return False

	def isInTopZone(self, point):
		for zone in self.FL_Windows.topZoneView.UIZones:
			y_min = int(zone['Position'])
			y_max = int(zone['Position']) + int(zone['Width'])

			if self.isInZone(point, y_min, y_max):
				return zone['Name']
		return None

	def isInBottomZone(self, point):
		for zone in self.FL_Windows.bottomZoneView.UIZones:
			y_max = int(zone['Position'])
			y_min = int(zone['Position']) - int(zone['Width'])

			if self.isInZone(point, y_min, y_max):
				return zone['Name']
		return None

	def keyDown(self, event):
		keyDict = {'a':('Anchor', 0), 's':('Single Link', 1), 'd':('Double Link', 2), 'i':('Interpolation', 3), 'm':('Middle Delta', 4), 'f':('Final Delta', 5)}
		if event.characters() in keyDict:
			val = keyDict[event.characters()]
			self.changeSelectedHintingTool(val[0])

	def mouseDown(self, point, clickCount):
		self.p_cursor = (int(point.x), int(point.y))
		self.startPoint = self.isOnPoint(self.p_cursor)
		#print 'glyph start point:', self.startPoint
		#if self.startPoint in self.pointCoordinatesToUniqueID:
		#	print 'point UniqueID:', self.pointCoordinatesToUniqueID[self.startPoint]

	def mouseUp(self, point):
		self.p_cursor = (int(point.x), int(point.y))
		self.endPoint = self.isOnPoint(self.p_cursor)
		#print 'glyph end point:', self.endPoint
		if self.endPoint == None:
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

		if self.tthtm.selectedHintingTool == 'Single Link' and self.startPoint != self.endPoint and self.startPoint != None:
			if self.tthtm.selectedAxis == 'X':
				newCommand['code'] = 'singleh'
				if self.tthtm.selectedStemX != 'None':
					newCommand['stem'] = self.tthtm.selectedStemX
			else:
				newCommand['code'] = 'singlev'
				if self.tthtm.selectedStemY != 'None':
					newCommand['stem'] = self.tthtm.selectedStemY

			newCommand['point1'] = self.pointCoordinatesToName[self.startPoint]
			newCommand['point2'] = self.pointCoordinatesToName[self.endPoint]
			if self.tthtm.selectedAlignmentTypeLink != 'None':
				newCommand['align'] = self.tthtm.selectedAlignmentTypeLink

			

			if self.tthtm.roundBool != 0:
				newCommand['round'] = 'true'

		if self.tthtm.selectedHintingTool == 'Double Link' and self.startPoint != self.endPoint and self.startPoint != None:
			if self.tthtm.selectedAxis == 'X':
				newCommand['code'] = 'doubleh'
				if self.tthtm.selectedStemX != 'None':
					newCommand['stem'] = self.tthtm.selectedStemX
				else:
					newCommand['round'] = 'true'
			else:
				newCommand['code'] = 'doublev'
				if self.tthtm.selectedStemY != 'None':
					newCommand['stem'] = self.tthtm.selectedStemY
				else:
					newCommand['round'] = 'true'

			newCommand['point1'] = self.pointCoordinatesToName[self.startPoint]
			newCommand['point2'] = self.pointCoordinatesToName[self.endPoint]

		if self.tthtm.selectedHintingTool == 'Interpolation' and self.startPoint != self.endPoint and self.startPoint != None:
			self.point1 = self.startPoint
			self.point = self.endPoint
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

			self.point1 = None
			self.point = None
			self.point2 = None

		if self.tthtm.selectedHintingTool in ['Middle Delta', 'Final Delta'] and self.endPoint != None:
			if self.tthtm.deltaOffset == 0:
				return
			newCommand['point'] = self.pointCoordinatesToName[self.endPoint]
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
			self.glyphTTHCommands.append(newCommand)	
			self.updateGlyphProgram()

	def compareCommands(self, A, B):
		order = None
		A_isAlign = False
		B_isAlign = False
		A_isSingleLink = False
		B_isSingleLink = False
		A_isInterpolate = False
		B_isInterpolate= False
		A_isMiddleDelta = False
		B_isMiddleDelta = False

		if A['code'] in ['alignh', 'alignv']:
			A_isAlign = True
		if B['code'] in ['alignh', 'alignv']:
			B_isAlign = True
		if A['code'] in ['singleh', 'singlev']:
			A_isSingleLink = True
		if B['code'] in ['singleh', 'singlev']:
			B_isSingleLink = True
		if A['code'] in ['interpolateh', 'interpolatev']:
			A_isInterpolate = True
		if B['code'] in ['interpolateh', 'interpolatev']:
			B_isInterpolate = True
		if A['code'] in ['mdeltah', 'mdeltav']:
			A_isMiddleDelta = True
		if B['code'] in ['mdeltah', 'mdeltav']:
			B_isMiddleDelta = True

		if A_isAlign and B_isAlign:
			if A['point'] == B['point']:
				order = 'BUG'
		elif A_isSingleLink and B_isAlign:
			if A['point1'] == B['point']:
				order = 2
		elif A_isAlign and B_isSingleLink:
			if A['point'] == B['point1']:
				order = 1
		elif A_isSingleLink and B_isSingleLink:
			if A['point1'] == B['point2']:
				order = 2
			elif A['point2'] == B['point1']:
				order = 1
			elif A['point2'] == B['point2']:
				order = 'BUG'
		elif A_isAlign and B_isInterpolate:
			if A['point'] == B['point1'] or A['point'] == B['point2']:
				order = 1
		elif A_isInterpolate and B_isAlign:
			if B['point'] == A['point1'] or B['point'] == A['point2']:
				order = 2
		elif A_isSingleLink and B_isInterpolate:
			if A['point2'] == B['point1'] or A['point2'] == B['point2']:
				order = 1
		elif A_isInterpolate and B_isSingleLink:
			if B['point2'] == A['point1'] or B['point2'] == A['point2']:
				order = 2
		elif A_isAlign and B_isMiddleDelta:
			if A['point'] == B['point']:
				order = 1
		elif A_isMiddleDelta and B_isMiddleDelta:
			if A['point'] == B['point']:
				order = 'BUG'
		elif A_isMiddleDelta and B_isAlign:
			if A['point'] == B['point']:
				order = 2
		elif A_isAlign and B_isMiddleDelta:
			if A['point'] == B['point']:
				order = 1
		elif A_isMiddleDelta and B_isSingleLink:
			if A['point'] == B['point1']:
				order = 1
			elif A['point'] == B['point2']:
				order = 2
		elif A_isSingleLink and B_isMiddleDelta:
			if A['point1'] == B['point']:
				order = 2
			elif A['point2'] == B['point']:
				order = 1
		elif A_isMiddleDelta and B_isInterpolate:
			if A['point'] == B['point1'] or A['point'] == B['point2']:
				order = 1
			elif A['point'] == B['point']:
				order = 2
		elif A_isInterpolate and B_isMiddleDelta:
			if A['point1'] == B['point'] or A['point2'] == B['point']:
				order = 2
			elif A['point'] == B['point']:
				order = 1
		if order == 1:
			return (True, False)
		elif order == 2:
			return (True, True)
		return (False, False)

	def prepareCommands(self):
		x = []
		ytb = []
		y = []
		fdeltah = []
		fdeltav = []
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

	def deleteCommandCallback(self, item):
		ttprogram = self.tthtm.g.lib['com.fontlab.ttprogram']
		#print 'delete command:', self.commandRightClicked
		self.glyphTTHCommands.pop(self.commandRightClicked)
		self.commandLabelPos = {}
		XMLGlyphTTProgram = ET.Element('ttProgram')
		for child in self.glyphTTHCommands:
			ttc = ET.SubElement(XMLGlyphTTProgram, 'ttc')
			for k, v in child.iteritems():
				ttc.set(k, v)
		strGlyphTTProgram = ET.tostring(XMLGlyphTTProgram)
		self.tthtm.g.lib['com.fontlab.ttprogram'] = Data(strGlyphTTProgram)

		self.updateGlyphProgram()

	def deleteAllCommandsCallback(self, item):
		emptyProgram = ''
		self.glyphTTHCommands = {}
		self.tthtm.g.lib['com.fontlab.ttprogram'] = Data(emptyProgram)
		self.updateGlyphProgram()


	def roundDistanceCallback(self, item):
		cmdIndex = self.commandRightClicked
		self.glyphTTHCommands[cmdIndex]['round'] = 'true'
		self.updateGlyphProgram()

	def dontRoundDistanceCallback(self, item):
		cmdIndex = self.commandRightClicked
		del self.glyphTTHCommands[cmdIndex]['round']
		self.updateGlyphProgram()

	def dontLinkToStemCallBack(self, item):
		cmdIndex = self.commandRightClicked
		del self.glyphTTHCommands[cmdIndex]['stem']
		self.updateGlyphProgram()

	def dontAlignCallBack(self, item):
		cmdIndex = self.commandRightClicked
		del self.glyphTTHCommands[cmdIndex]['align']
		self.updateGlyphProgram()

	def updateGlyphProgram(self):
		self.prepareCommands()
		self.writeGlyphFLTTProgram(self.tthtm.g)
		TTHintAsm.writeAssembly(self.tthtm.g, self.glyphTTHCommands, self.pointNameToUniqueID, self.pointNameToIndex)

		self.generateMiniTempFont()
		self.mergeMiniAndFullTempFonts()
		self.resetglyph()
		UpdateCurrentGlyphView()



	def rightMouseDown(self, point, event):
		self.p_cursor = (int(point.x), int(point.y))
		self.commandRightClicked = self.isOnCommand(self.p_cursor)
		#print 'command point:', self.commandRightClicked
		if self.commandRightClicked == None:
			self.menuAction = NSMenu.alloc().init()
			items = []
			items.append(('Delete All Commands', self.deleteAllCommandsCallback))
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
					deltaValues.append((str(value), callbackSetDeltaValue(self, value)))
				for value in range(1, 9):
					deltaValues.append((str(value), callbackSetDeltaValue(self, value)))
				items.append(("Set Middle Delta Value", deltaValues))


			if clickedCommand['code'] in ['interpolateh', 'interpolatev']:
				if 'align' in clickedCommand:
					alignments = [
								('Do Not Align to Grid', self.dontAlignCallBack),
								("Closest Pixel Edge", alignmentCallBack_Closest),
								("Left/Bottom Edge", alignmentCallBack_Left),
								("Right/Top Edge", alignmentCallBack_Right),
								("Center of Pixel", alignmentCallBack_Center),
								("Double Grid", alignmentCallBack_Double)
								]

					items.append(("Align Destination Position", alignments))

				else:
					alignments = [
								("Closest Pixel Edge", alignmentCallBack_Closest),
								("Left/Bottom Edge", alignmentCallBack_Left),
								("Right/Top Edge", alignmentCallBack_Right),
								("Center of Pixel", alignmentCallBack_Center),
								("Double Grid", alignmentCallBack_Double)
								]

					items.append(("Align Destination Position", alignments))


			if clickedCommand['code'] in ['alignh', 'alignv']:

				alignments = [
							("Closest Pixel Edge", alignmentCallBack_Closest),
							("Left/Bottom Edge", alignmentCallBack_Left),
							("Right/Top Edge", alignmentCallBack_Right),
							("Center of Pixel", alignmentCallBack_Center),
							("Double Grid", alignmentCallBack_Double)
							]

				items.append(("Alignment Type", alignments))

			if clickedCommand['code'] in ['alignt', 'alignb']:
				zonesListItems = []

				for zone in self.FL_Windows.zones:
					self.zoneAlignmentCallBack = callbackZoneAlignment(self, zone)
					zonesListItems.append((zone, self.zoneAlignmentCallBack))
				items.append(("Attach to Zone", zonesListItems))

			if clickedCommand['code'] in ['doubleh', 'doublev']:
				if 'stem' in clickedCommand:
					distances = [('Do Not Link to Stem', self.dontLinkToStemCallBack)]
				else:
					distances = []

				stemsHorizontal = []
				stemsVertical = []

				for name, stem in self.FL_Windows.stems.iteritems():
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
					items.append(('Do Not Round Distance', self.dontRoundDistanceCallback))


				if 'stem' in clickedCommand:
					distances = [('Do Not Link to Stem', self.dontLinkToStemCallBack)]
				else:
					distances = []

				stemsHorizontal = []
				stemsVertical = []

				for name, stem in self.FL_Windows.stems.iteritems():
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

				if 'align' in clickedCommand:
					alignments = [
								('Do Not Align to Grid', self.dontAlignCallBack),
								("Closest Pixel Edge", alignmentCallBack_Closest),
								("Left/Bottom Edge", alignmentCallBack_Left),
								("Right/Top Edge", alignmentCallBack_Right),
								("Center of Pixel", alignmentCallBack_Center),
								("Double Grid", alignmentCallBack_Double)
								]

					items.append(("Align Destination Position", alignments))

				else:
					alignments = [
								("Closest Pixel Edge", alignmentCallBack_Closest),
								("Left/Bottom Edge", alignmentCallBack_Left),
								("Right/Top Edge", alignmentCallBack_Right),
								("Center of Pixel", alignmentCallBack_Center),
								("Double Grid", alignmentCallBack_Double)
								]

					items.append(("Align Destination Position", alignments))



			menuController = BaseMenu()
			
			menuController.buildAdditionContectualMenuItems(self.menuAction, items)
			self.menuAction.insertItem_atIndex_(separator, 1)
			NSMenu.popUpContextMenu_withEvent_forView_(self.menuAction, self.getCurrentEvent(), self.getNSView())

	def resetFonts(self, createWindows=False):
		self.allFonts = loadFonts()
		if not self.allFonts:
			return
		self.tthtm.setFont(loadCurrentFont(self.allFonts))
		self.tthtm.resetPitch()

		if createWindows:
			self.FL_Windows = fl_tth.FL_TTH_Windows(self.tthtm.f, self)
			self.centralWindow = view.centralWindow(self, self.tthtm)
			self.previewWindow = view.previewWindow(self, self.tthtm)

		tt_tables.writeCVTandPREP(self.tthtm.f, self.tthtm.UPM, self.FL_Windows.alignppm, self.FL_Windows.stems, self.FL_Windows.zones, self.FL_Windows.codeppm)
		tt_tables.writeFPGM(self.tthtm.f)

		for g in self.tthtm.f:
			glyphTTHCommands = self.readGlyphFLTTProgram(g)
			if glyphTTHCommands != None:
				self.prepareCommands()
				TTHintAsm.writeAssembly(g, glyphTTHCommands, self.pointNameToUniqueID, self.pointNameToIndex)

		self.generateFullTempFont()
		self.indexOfGlyphNames = dict([(self.fullTempUFO.lib['public.glyphOrder'][idx], idx) for idx in range(len(self.fullTempUFO.lib['public.glyphOrder']))])

		self.changeSize(self.tthtm.PPM_Size)
		self.changeAxis(self.tthtm.selectedAxis)
		self.changeBitmapPreview(self.tthtm.bitmapPreviewSelection)
		self.changeSelectedHintingTool(self.tthtm.selectedHintingTool)
		self.changeSelectedAlignmentTypeAlign(self.tthtm.selectedAlignmentTypeAlign)
		self.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)
		self.makeStemsListsPopUpMenu()
		if self.tthtm.selectedAxis == 'X':
			self.centralWindow.wCentral.StemTypePopUpButton.setItems(self.tthtm.stemsListX)
			self.changeSelectedStemX(self.tthtm.selectedStemX)
		else:
			self.centralWindow.wCentral.StemTypePopUpButton.setItems(self.tthtm.stemsListY)
			self.changeSelectedStemY(self.tthtm.selectedStemY)
		self.changeRoundBool(self.tthtm.roundBool)
		self.changeDeltaOffset(self.tthtm.deltaOffset)
		self.changeDeltaRange(self.tthtm.deltaRange1, self.tthtm.deltaRange2)

		self.showHidePreviewWindow(self.tthtm.previewWindowVisible)

	def resetglyph(self):
		self.tthtm.setGlyph(CurrentGlyph())
		if self.tthtm.g == None:
			return

		self.tthtm.textRenderer = TR.TextRenderer(self.fulltempfontpath, self.tthtm.bitmapPreviewSelection)

		glyphTTHCommands = self.readGlyphFLTTProgram(self.tthtm.g)
		self.commandLabelPos = {}
		self.pointUniqueIDToCoordinates = self.makePointUniqueIDToCoordinatesDict(self.tthtm.g)
		self.pointCoordinatesToUniqueID = self.makePointCoordinatesToUniqueIDDict(self.tthtm.g)
		self.pointCoordinatesToName = self.makePointCoordinatesToNameDict(self.tthtm.g)
		#print 'full temp font loaded'
		self.ready = True
		self.previewWindow.view.setNeedsDisplay_(True)

		self.p_glyphList = ([(0, 0), (self.tthtm.g.width, 0)])

		for c in self.tthtm.g:
			for p in c.points:
				if p.type != 'offCurve':
					self.p_glyphList.append((p.x, p.y))


	def generateFullTempFont(self):
		root = os.path.split(self.tthtm.f.path)[0]
		tail = 'Fulltemp.ttf'
		self.fulltempfontpath = os.path.join(root, tail)

		self.tthtm.f.generate(self.fulltempfontpath,'ttf', decompose = False, checkOutlines = False, autohint = False, releaseMode = False, glyphOrder=None, progressBar = None )
		#print 'full font generated'
		self.fullTempUFO = OpenFont(self.fulltempfontpath, showUI=False)
		self.tthtm.textRenderer = TR.TextRenderer(self.fulltempfontpath, self.tthtm.bitmapPreviewSelection)

	def generateMiniTempFont(self):
		root = os.path.split(self.tthtm.f.path)[0]
		tail = 'Minitemp.ttf'
		self.tempfontpath = os.path.join(root, tail)

		tempFont = RFont(showUI=False)
		tempFont.preferredSegmentType = 'qCurve'
		tempFont.info.unitsPerEm = CurrentFont().info.unitsPerEm
		tempFont.info.ascender = CurrentFont().info.ascender
		tempFont.info.descender = CurrentFont().info.descender
		tempFont.info.xHeight = CurrentFont().info.xHeight
		tempFont.info.capHeight = CurrentFont().info.capHeight

		tempFont.info.familyName = CurrentFont().info.familyName
		tempFont.info.styleName = CurrentFont().info.styleName

		if 'com.robofont.robohint.cvt ' in CurrentFont().lib:
			tempFont.lib['com.robofont.robohint.cvt '] = CurrentFont().lib['com.robofont.robohint.cvt ']
		if 'com.robofont.robohint.prep' in CurrentFont().lib:
			tempFont.lib['com.robofont.robohint.prep'] = CurrentFont().lib['com.robofont.robohint.prep']
		if 'com.robofont.robohint.fpgm' in CurrentFont().lib:
			tempFont.lib['com.robofont.robohint.fpgm'] = CurrentFont().lib['com.robofont.robohint.fpgm']
		

		tempFont.newGlyph(self.tthtm.g.name)
		tempFont[self.tthtm.g.name] = self.tthtm.g
		if 'com.robofont.robohint.assembly' in self.tthtm.g.lib:
			tempFont[self.tthtm.g.name].lib['com.robofont.robohint.assembly'] = self.tthtm.g.lib['com.robofont.robohint.assembly']

		tempFont.generate(self.tempfontpath, 'ttf', decompose = False, checkOutlines = False, autohint = False, releaseMode = False, glyphOrder=None, progressBar = None )
		#print 'mini font generated'

	def mergeMiniAndFullTempFonts(self):
		root = os.path.split(self.tthtm.f.path)[0]
		tail = 'tempTemp.ttf'
		tempTempfontpath = os.path.join(root, tail)

		ttFull = fontTools.ttLib.TTFont(self.fulltempfontpath)
		ttMini = fontTools.ttLib.TTFont(self.tempfontpath)
		gName = self.tthtm.g.name
		ttFull['glyf'][gName] = ttMini['glyf'][gName]
		ttFull.save(tempTempfontpath)
		os.remove(self.fulltempfontpath)
		os.rename(tempTempfontpath, self.fulltempfontpath)
		#print 'temp fonts merged'

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


	def getGlyphIndexByName(self, glyphName):
		try:
			return self.indexOfGlyphNames[glyphName]
		except:
			return None

	def drawGrid(self, scale, pitch):
		for xPos in range(0, 5000, int(pitch)):
			pathX = NSBezierPath.bezierPath()
			pathX.moveToPoint_((xPos, -5000))
			pathX.lineToPoint_((xPos, 5000))
			NSColor.colorWithRed_green_blue_alpha_(0, 0, 0, 0.1).set()
			pathX.setLineWidth_(scale)
			pathX.stroke()
		for xPos in range(0, -5000, -int(pitch)):
			pathX = NSBezierPath.bezierPath()
			pathX.moveToPoint_((xPos, -5000))
			pathX.lineToPoint_((xPos, 5000))
			NSColor.colorWithRed_green_blue_alpha_(0, 0, 0, 0.1).set()
			pathX.setLineWidth_(scale)
			pathX.stroke()
		for yPos in range(0, 5000, int(pitch)):
			pathY = NSBezierPath.bezierPath()
			pathY.moveToPoint_((-5000, yPos))
			pathY.lineToPoint_((5000, yPos))
			NSColor.colorWithRed_green_blue_alpha_(0, 0, 0, 0.1).set()
			pathY.setLineWidth_(scale)
			pathY.stroke()
		for yPos in range(0, -5000, -int(pitch)):
			pathY = NSBezierPath.bezierPath()
			pathY.moveToPoint_((-5000, yPos))
			pathY.lineToPoint_((5000, yPos))
			NSColor.colorWithRed_green_blue_alpha_(0, 0, 0, 0.1).set()
			pathY.setLineWidth_(scale)
			pathY.stroke()

	def drawZones(self, scale):

		zonecolor = NSColor.colorWithRed_green_blue_alpha_(0/255, 180/255, 50/255, .2)
		zonecolorLabel = NSColor.colorWithRed_green_blue_alpha_(0/255, 180/255, 50/255, 1)

		for zone in self.FL_Windows.topZoneView.UIZones:
			y_start = int(zone['Position'])
			y_end = int(zone['Width'])
			pathZone = NSBezierPath.bezierPath()
			pathZone.moveToPoint_((-5000, y_start))
			pathZone.lineToPoint_((5000, y_start))
			pathZone.lineToPoint_((5000, y_start+y_end))
			pathZone.lineToPoint_((-5000, y_start+y_end))
			pathZone.closePath
			zonecolor.set()
			pathZone.fill()	

			self.drawTextAtPoint(zone['Name'], -100, y_start, zonecolorLabel)

		for zone in self.FL_Windows.bottomZoneView.UIZones:
			y_start = int(zone['Position'])
			y_end = int(zone['Width'])
			pathZone = NSBezierPath.bezierPath()
			pathZone.moveToPoint_((-5000, y_start))
			pathZone.lineToPoint_((5000, y_start))
			pathZone.lineToPoint_((5000, y_start-y_end))
			pathZone.lineToPoint_((-5000, y_start-y_end))
			pathZone.closePath
			zonecolor.set()
			pathZone.fill()	

			self.drawTextAtPoint(zone['Name'], -100, y_start, zonecolorLabel)


	def drawTextAtPoint(self, title, x, y, backgroundColor):
		currentTool = getActiveEventTool()
		view = currentTool.getNSView()

		attributes = {
			NSFontAttributeName : NSFont.boldSystemFontOfSize_(9),
			NSForegroundColorAttributeName : NSColor.whiteColor(),
			}
		backgroundStrokeColor = NSColor.whiteColor()

		view._drawTextAtPoint(title, attributes, (x, y), drawBackground=True, backgroundColor=backgroundColor, backgroundStrokeColor=backgroundStrokeColor)
			

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

		NSColor.colorWithRed_green_blue_alpha_(0/255, 0/255, 255/255, 1).set()
		pathArrow.setLineWidth_(scale)
		pathArrow.fill()
		NSColor.colorWithRed_green_blue_alpha_(1, 1, 1, .5).set()
		pathArrow.stroke()

	def drawDiscAtPoint(self, r, x, y, color):
		NSColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3]).set()
		NSBezierPath.bezierPathWithOvalInRect_(((x-r, y-r), (r*2, r*2))).fill()

	def drawLozengeAtPoint(self, scale, r, x, y, color):
		NSColor.colorWithRed_green_blue_alpha_(color[0], color[1], color[2], color[3]).set()
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

		# compute x, y
		if cmdIndex != None and cmdIndex not in self.commandLabelPos:
			self.commandLabelPos[cmdIndex] = (x + 10*scale, y - 10*scale)

		extension = ''
		text = 'A'
		if 'align' in self.glyphTTHCommands[cmdIndex]:
			if self.tthtm.selectedAxis == 'Y' and self.glyphTTHCommands[cmdIndex]['align'] == 'right':
				extension = 'top'
			elif self.tthtm.selectedAxis == 'Y' and self.glyphTTHCommands[cmdIndex]['align'] == 'left':
				extension = 'bottom'
			else:
				extension = self.glyphTTHCommands[cmdIndex]['align']


			text += '_' + extension
		elif self.glyphTTHCommands[cmdIndex]['code'] == 'alignt' or self.glyphTTHCommands[cmdIndex]['code'] == 'alignb':
			text += '_' + self.glyphTTHCommands[cmdIndex]['zone']

		self.drawTextAtPoint(text, x + 10*scale, y - 10*scale, NSColor.blueColor())

	def drawLink(self, scale, startPoint, endPoint, stemName, cmdIndex):
	 	
	 	start_end_diff = difference(startPoint, endPoint)
	 	dx, dy = start_end_diff[0]/2, start_end_diff[1]/2
	 	angle = getAngle((startPoint[0], startPoint[1]), (endPoint[0], endPoint[1])) + math.radians(90)
	 	offcurve1 = (startPoint[0] - dx + math.cos(angle)*10*scale, startPoint[1] - dy + math.sin(angle)*10*scale)

		r = 10
	 	arrowAngle = math.radians(20)
	 	initAngle = getAngle((endPoint[0], endPoint[1]), (offcurve1[0], offcurve1[1]))
	 	arrowPoint1_x = endPoint[0] + math.cos(initAngle+arrowAngle)*r*scale
		arrowPoint1_y = endPoint[1] + math.sin(initAngle+arrowAngle)*r*scale
		arrowPoint2_x = endPoint[0] + math.cos(initAngle-arrowAngle)*r*scale
		arrowPoint2_y = endPoint[1] + math.sin(initAngle-arrowAngle)*r*scale
		endPoint_x = (arrowPoint1_x + arrowPoint2_x) / 2
		endPoint_y = (arrowPoint1_y + arrowPoint2_y) / 2

		pathArrow = NSBezierPath.bezierPath()
	 	pathArrow.moveToPoint_((endPoint[0], endPoint[1]))
		pathArrow.lineToPoint_((arrowPoint1_x, arrowPoint1_y))
		pathArrow.lineToPoint_((arrowPoint2_x, arrowPoint2_y))

		path = NSBezierPath.bezierPath()
	 	path.moveToPoint_((startPoint[0], startPoint[1]))
	 	path.curveToPoint_controlPoint1_controlPoint2_((endPoint_x, endPoint_y), (offcurve1), (offcurve1) )
	 
		NSColor.colorWithRed_green_blue_alpha_(0/255, 0/255, 0/255, 1).set()
		path.setLineWidth_(scale)
		pathArrow.fill()
		path.stroke()

		# compute x, y
		if cmdIndex != None and cmdIndex not in self.commandLabelPos:
			self.commandLabelPos[cmdIndex] = (offcurve1[0], offcurve1[1])

		extension = ''
		if 'align' in self.glyphTTHCommands[cmdIndex]:
			if self.tthtm.selectedAxis == 'Y' and self.glyphTTHCommands[cmdIndex]['align'] == 'right':
				extension = 'top'
			elif self.tthtm.selectedAxis == 'Y' and self.glyphTTHCommands[cmdIndex]['align'] == 'left':
				extension = 'bottom'
			else:
				extension = self.glyphTTHCommands[cmdIndex]['align']

		if 'round' in self.glyphTTHCommands[cmdIndex]:
			if self.glyphTTHCommands[cmdIndex]['round'] == 'true':
				text = 'R'
				if stemName == None and extension != '':
					text += '_' + extension
				elif stemName != None:
					text += '_' + stemName
				#self.drawTextAtPoint(text, offcurve1[0], offcurve1[1], NSColor.blackColor())
		else:
			text = 'S'
			if stemName == None and extension != '':
				text += '_' + extension
			elif stemName != None:
				text += '_' + stemName

		self.drawTextAtPoint(text, offcurve1[0], offcurve1[1], NSColor.blackColor())


	def drawDoubleLink(self, scale, startPoint, endPoint, stemName, cmdIndex):
	 	
	 	start_end_diff = difference(endPoint, startPoint)
	 	dx, dy = -start_end_diff[1]/5, start_end_diff[0]/5
	 	offcurve1 = (startPoint[0] + dx, startPoint[1] + dy)
		offcurve2 = (endPoint[0] + dx, endPoint[1] + dy)

		path = NSBezierPath.bezierPath()
	 	path.moveToPoint_((startPoint[0], startPoint[1]))
	 	path.curveToPoint_controlPoint1_controlPoint2_((endPoint[0], endPoint[1]), (offcurve1), (offcurve2) )

	 	doublinkColor = NSColor.colorWithRed_green_blue_alpha_(215/255, 0/255, 215/255, 1)

		doublinkColor.set()
		path.setLineWidth_(scale)
		path.stroke()

		# compute x, y
		if cmdIndex != None and cmdIndex not in self.commandLabelPos:
			self.commandLabelPos[cmdIndex] = ((offcurve1[0] + offcurve2[0])/2, (offcurve1[1] + offcurve2[1])/2 )

		extension = ''
		text = 'R'
		if 'round' in self.glyphTTHCommands[cmdIndex]:
			if self.glyphTTHCommands[cmdIndex]['round'] == 'true':
				if stemName != None:
					text += '_' + stemName
		elif stemName != None:
			text += '_' + stemName

		self.drawTextAtPoint(text, (offcurve1[0] + offcurve2[0])/2, (offcurve1[1] + offcurve2[1])/2, doublinkColor)

	def drawInterpolate(self, scale, startPoint, endPoint, middlePoint, cmdIndex):

		start_middle_diff = difference(startPoint, middlePoint)
		dx, dy = start_middle_diff[0]/2, start_middle_diff[1]/2
		angle = getAngle((startPoint[0], startPoint[1]), (middlePoint[0], middlePoint[1])) + math.radians(90)
		center1 = (startPoint[0] - dx + math.cos(angle)*10, startPoint[1] - dy + math.sin(angle)*10)

		middle_end_diff = difference(middlePoint, endPoint)
		dx, dy = middle_end_diff[0]/2, middle_end_diff[1]/2
		angle = getAngle((middlePoint[0], middlePoint[1]), (endPoint[0], endPoint[1])) + math.radians(90)
		center2 = (middlePoint[0] - dx + math.cos(angle)*10, middlePoint[1] - dy + math.sin(angle)*10)

		path = NSBezierPath.bezierPath()
		path.moveToPoint_((startPoint[0], startPoint[1]))
		path.curveToPoint_controlPoint1_controlPoint2_((middlePoint[0], middlePoint[1]), (center1), (center1) )
		path.curveToPoint_controlPoint1_controlPoint2_((endPoint[0], endPoint[1]), (center2), (center2) )

		interpolatecolor = NSColor.colorWithRed_green_blue_alpha_(0/255, 215/255, 100/255, 1)
		interpolatecolor.set()
		path.setLineWidth_(scale)
		path.stroke()

		# compute x, y
		if cmdIndex != None and cmdIndex not in self.commandLabelPos:
			self.commandLabelPos[cmdIndex] = (middlePoint[0] + 10*scale, middlePoint[1] - 10*scale)

		extension = ''
		text = 'I'
		if 'align' in self.glyphTTHCommands[cmdIndex]:
			extension = self.glyphTTHCommands[cmdIndex]['align']
			text += '_' + extension

		self.drawTextAtPoint(text, middlePoint[0] + 10*scale, middlePoint[1] - 10*scale, interpolatecolor)

	def drawDelta(self, scale, point, value, cmdIndex):
		deltacolor = NSColor.colorWithRed_green_blue_alpha_(255/255, 128/255, 0/255, 1)

		path = NSBezierPath.bezierPath()
	 	path.moveToPoint_((point[0], point[1]))
	 	path.lineToPoint_((point[0]+ (value[0]/8)*self.tthtm.pitch, point[1] + (value[1]/8)*self.tthtm.pitch))

	 	deltacolor.set()
		path.setLineWidth_(scale)
		path.stroke()

		# compute x, y
		if cmdIndex != None and cmdIndex not in self.commandLabelPos:
			self.commandLabelPos[cmdIndex] = (point[0] - 10*scale, point[1] + 10*scale)
		
		extension = ''
		text = 'delta'
		value = self.glyphTTHCommands[cmdIndex]['delta']
		if self.glyphTTHCommands[cmdIndex]['code'][:1] == 'm':
			extension = '_M'
		elif self.glyphTTHCommands[cmdIndex]['code'][:1] == 'f':
			extension = '_F'
		text += extension + ':' + value
		self.drawTextAtPoint(text, point[0] - 10*scale, point[1] + 10*scale, deltacolor)

	def drawSideBearings(self, scale, char):
		try:
			xPos = self.tthtm.pitch * self.tthtm.textRenderer.get_char_advance(char)[0] / 64
		except:
			return
		pathX = NSBezierPath.bezierPath()
		pathX.moveToPoint_((xPos, -5000))
		pathX.lineToPoint_((xPos, 5000))
		NSColor.colorWithRed_green_blue_alpha_(1, 0, 0, 1).set()
		pathX.setLineWidth_(scale)
		pathX.stroke()

		pathX = NSBezierPath.bezierPath()
		pathX.moveToPoint_((0, -5000))
		pathX.lineToPoint_((0, 5000))
		NSColor.colorWithRed_green_blue_alpha_(1, 0, 0, 1).set()
		pathX.setLineWidth_(scale)
		pathX.stroke()

	def drawPreviewWindow(self):
		if self.ready == False:
			return
		if CurrentGlyph() == None:
			return

		curGlyphString = unichr(CurrentGlyph().unicode)

		# replace @ by current glyph
		#text = self.previewWindow.previewString.replace('@', curGlyphString)
		text = self.tthtm.previewString.replace('@', curGlyphString)

		# replace /name pattern
		sp = text.split('/')
		nbsp = len(sp)
		for i in range(1,nbsp):
			sub = sp[i].split(' ', 1)
			if sub[0] in self.fullTempUFO:
				sp[i] = unichr(self.fullTempUFO[sub[0]].unicode) + (' '.join(sub[1:]))
		text = ''.join(sp)

		# render user string
		if self.tthtm.textRenderer:
			self.tthtm.textRenderer.set_cur_size(self.tthtm.PPM_Size)
			self.tthtm.textRenderer.set_pen((10, 50))
			self.tthtm.textRenderer.render_text(text)

			# render current glyph at various sizes
			advance = 10
			for size in range(9, 48, 1):
				self.tthtm.textRenderer.set_cur_size(size)
				self.tthtm.textRenderer.set_pen((advance, 100))
				delta_pos = self.tthtm.textRenderer.render_text(curGlyphString)
				advance += delta_pos[0] + 5

	def drawBackground(self, scale):
		if self.tthtm.g == None:
			return

		curChar = unichr(CurrentGlyph().unicode)
		
		self.tthtm.textRenderer.set_cur_size(self.tthtm.PPM_Size)
		self.tthtm.textRenderer.set_pen((0, 0))
		self.tthtm.textRenderer.render_text_with_scale_and_alpha(curChar, self.tthtm.pitch, 0.4)

		r = 5*scale
		self.drawDiscAtPoint(r, 0, 0, (1, 0, 0, 1))
		self.drawDiscAtPoint(r, self.tthtm.g.width, 0, (1, 0, 0, 1))

		self.drawGrid(scale, self.tthtm.pitch)
		self.drawZones(scale)

		self.tthtm.textRenderer.drawOutline(scale, self.tthtm.pitch, curChar)
		self.drawSideBearings(scale, curChar)

	def draw(self, scale):
		if self.isDragging():
			if self.startPoint != None:
				x_start = self.startPoint[0]
				y_start = self.startPoint[1]
				self.drawLozengeAtPoint(5*scale, scale, x_start, y_start, (0/255, 180/255, 50/255, 1))
			touchedEnd = self.isOnPoint(self.currentPoint)
			if touchedEnd != None:
				x_end = touchedEnd[0]
				y_end = touchedEnd[1]
				self.drawLozengeAtPoint(5*scale, scale, x_end, y_end, (0/255, 180/255, 50/255, 1))


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
					startPoint = (0, self.tthtm.g.width)
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
						self.drawDelta(scale, point, value, cmdIndex)
					elif self.tthtm.selectedAxis == 'Y' and cmd_code in ['mdeltav', 'fdeltav']:
						self.drawDelta(scale, point, value, cmdIndex)



reload(TR)
reload(TTHintAsm)
reload(fl_tth)
reload(tt_tables)
reload(view)
reload(TTHToolModel)

tthtm = TTHToolModel.TTHToolModel()
installTool(TTHTool(tthtm))
