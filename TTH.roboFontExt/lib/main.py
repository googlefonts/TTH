from mojo.events import *
from mojo.UI import *
from mojo.drawingTools import *
from vanilla import *
from lib.doodleMenus import BaseMenu
from robofab.plistlib import Data
import fontTools

import fl_tth
import tt_tables
import preview
import TTHintAsm
import TTHToolModel
import TextRenderer as TR

import xml.etree.ElementTree as ET
import math, os

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

	def __init__(self):
		BaseEventTool.__init__(self)
		self.ready = False
		self.unicodeToNameDict = createUnicodeToNameDict()
		self.p_glyphList = []
		self.commandLabelPos = {}

		#self.f = None
		#self.g = None
		#self.UPM = 1000
		#self.PPM_Size = 9
		#tthtm.pitch = self.UPM/self.PPM_Size
		#self.bitmapPreviewSelection = 'Monochrome'
		#self.selectedHintingTool = 'Align'
		self.selectedAlignmentType = 'round'
		self.selectedStem = None
		self.roundBool = 0
		self.textRenderer = None

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
		return tthtm.PPM_Size

	def changeSize(self, size):
		try:
			size = int(size)
		except ValueError:
			size = 9

		tthtm.PPM_Size = size
		sizeIndex = self.getSizeListIndex(size)
		self.centralWindow.wCentral.PPEMSizePopUpButton.set(sizeIndex)
		self.centralWindow.wCentral.PPEMSizeEditText.set(size)

		tthtm.resetPitch()

		self.previewWindow.view.setNeedsDisplay_(True)
		UpdateCurrentGlyphView()

	def changeAxis(self, axis):
		tthtm.setAxis(axis)
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
		tthtm.setBitmapPreview(preview)
		self.textRenderer = TR.TextRenderer(self.fulltempfontpath, preview)
		previewIndex = self.getPreviewListIndex(preview)
		self.centralWindow.wCentral.BitmapPreviewPopUpButton.set(previewIndex)

		if tthtm.g == None:
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
		tthtm.setHintingTool(hintingTool)
		hintingToolIndex = self.getHintingToolIndex(hintingTool)
		self.centralWindow.wCentral.HintingToolPopUpButton.set(hintingToolIndex)
		if hintingToolIndex == 0:
			self.centralWindow.centralWindowAlignSettings()
		if hintingToolIndex in [1, 2]:
			self.centralWindow.centralWindowLinkSettings()
		if hintingToolIndex == 3:
			self.centralWindow.centralWindowInterpolationSettings()
		if hintingToolIndex in [4, 5]:
			self.centralWindow.centralWindowDeltaSettings()


	def isOnPoint(self, p_cursor):
		def pred0(p_glyph):
			return pointsApproxEqual(p_glyph, p_cursor)
		touched_p_glyph = find_in_list(self.p_glyphList, pred0)

		return touched_p_glyph

	def isOnCommand(self, p_cursor):
		if tthtm.selectedAxis == 'X':
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
		for zone in self.FL_Windows.topUIZones:
			y_min = int(zone['Position'])
			y_max = int(zone['Position']) + int(zone['Width'])

			if self.isInZone(point, y_min, y_max):
				return zone['Name']
		return None

	def isInBottomZone(self, point):
		for zone in self.FL_Windows.bottomUIZones:
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
		print 'glyph start point:', self.startPoint
		if self.startPoint in self.pointCoordinatesToUniqueID:
			print 'point UniqueID:', self.pointCoordinatesToUniqueID[self.startPoint]

	def mouseUp(self, point):
		self.p_cursor = (int(point.x), int(point.y))
		self.endPoint = self.isOnPoint(self.p_cursor)
		print 'glyph end point:', self.endPoint
		if self.endPoint == None:
				return

		cmdIndex = len(self.glyphTTHCommands)
		newCommand = {}

		if tthtm.selectedHintingTool == 'Align':
			newCommand['point'] = self.pointCoordinatesToName[self.endPoint]
			if tthtm.selectedAxis == 'X':
				newCommand['code'] = 'alignh'
				newCommand['align'] = self.selectedAlignmentType
			else:
				if self.isInTopZone(self.endPoint):
					newCommand['code'] = 'alignt'
					newCommand['zone'] = self.isInTopZone(self.endPoint)
				elif self.isInBottomZone(self.endPoint):
					newCommand['code'] = 'alignb'
					newCommand['zone'] = self.isInBottomZone(self.endPoint)
				else:
					newCommand['code'] = 'alignv'
					newCommand['align'] = self.selectedAlignmentType

		if tthtm.selectedHintingTool == 'Single Link':
			if tthtm.selectedAxis == 'X':
				newCommand['code'] = 'singleh'
			else:
				newCommand['code'] = 'singlev'

			newCommand['point1'] = self.pointCoordinatesToName[self.startPoint]
			newCommand['point2'] = self.pointCoordinatesToName[self.endPoint]
			if self.selectedAlignmentType != None:
				newCommand['align'] = self.selectedAlignmentType

			if self.selectedStem != None and self.selectedStem != 'None':
				newCommand['stem'] = self.selectedStem

			if self.roundBool != 0:
				newCommand['round'] = 'true'

		self.glyphTTHCommands.append(newCommand)	
		self.updateGlyphProgram()



	def deleteCommandCallback(self, item):
		ttprogram = tthtm.g.lib['com.fontlab.ttprogram']
		#print 'delete command:', self.commandRightClicked
		self.glyphTTHCommands.pop(self.commandRightClicked)
		self.commandLabelPos = {}
		XMLGlyphTTProgram = ET.Element('ttProgram')
		for child in self.glyphTTHCommands:
			ttc = ET.SubElement(XMLGlyphTTProgram, 'ttc')
			for k, v in child.iteritems():
				ttc.set(k, v)
		strGlyphTTProgram = ET.tostring(XMLGlyphTTProgram)
		tthtm.g.lib['com.fontlab.ttprogram'] = Data(strGlyphTTProgram)

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
		self.writeGlyphFLTTProgram(tthtm.g)

		TTHintAsm.writeAssembly(tthtm.g, self.glyphTTHCommands, self.pointNameToUniqueID, self.pointNameToIndex)

		self.generateMiniTempFont()
		self.mergeMiniAndFullTempFonts()
		self.resetglyph()
		UpdateCurrentGlyphView()



	def rightMouseDown(self, point, event):
		self.p_cursor = (int(point.x), int(point.y))
		self.commandRightClicked = self.isOnCommand(self.p_cursor)
		#print 'command point:', self.commandRightClicked
		if self.commandRightClicked != None:
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

				if tthtm.selectedAxis == 'X':
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
		tthtm.setFont(loadCurrentFont(self.allFonts))
		tthtm.resetPitch()
		self.selectedAlignmentType = 'round'

		if createWindows:
			self.FL_Windows = fl_tth.FL_TTH_Windows(tthtm.f, self)
			self.centralWindow = centralWindow(tthtm.f, self)
			self.previewWindow = previewWindow(tthtm.f, self)

		tt_tables.writeCVTandPREP(tthtm.f, tthtm.UPM, self.FL_Windows.alignppm, self.FL_Windows.stems, self.FL_Windows.zones, self.FL_Windows.codeppm)
		tt_tables.writeFPGM(tthtm.f)

		for g in tthtm.f:
			glyphTTHCommands = self.readGlyphFLTTProgram(g)
			if glyphTTHCommands != None:
				TTHintAsm.writeAssembly(g, glyphTTHCommands, self.pointNameToUniqueID, self.pointNameToIndex)

		self.generateFullTempFont()
		self.indexOfGlyphNames = dict([(self.fullTempUFO.lib['public.glyphOrder'][idx], idx) for idx in range(len(self.fullTempUFO.lib['public.glyphOrder']))])

		self.changeSize(tthtm.PPM_Size)
		self.changeAxis(tthtm.selectedAxis)
		self.changeBitmapPreview(tthtm.bitmapPreviewSelection)
		self.changeSelectedHintingTool(tthtm.selectedHintingTool)

	def resetglyph(self):
		tthtm.setGlyph(CurrentGlyph())
		if tthtm.g == None:
			return

		self.textRenderer = TR.TextRenderer(self.fulltempfontpath, tthtm.bitmapPreviewSelection)

		glyphTTHCommands = self.readGlyphFLTTProgram(tthtm.g)
		self.commandLabelPos = {}
		self.pointUniqueIDToCoordinates = self.makePointUniqueIDToCoordinatesDict(tthtm.g)
		self.pointCoordinatesToUniqueID = self.makePointCoordinatesToUniqueIDDict(tthtm.g)
		self.pointCoordinatesToName = self.makePointCoordinatesToNameDict(tthtm.g)
		print 'full temp font loaded'
		self.ready = True
		self.previewWindow.view.setNeedsDisplay_(True)

		self.p_glyphList = ([(0, 0), (tthtm.g.width, 0)])

		for c in tthtm.g:
			for p in c.points:
				if p.type != 'offCurve':
					self.p_glyphList.append((p.x, p.y))


	def generateFullTempFont(self):
		root = os.path.split(tthtm.f.path)[0]
		tail = 'Fulltemp.ttf'
		self.fulltempfontpath = os.path.join(root, tail)

		tthtm.f.generate(self.fulltempfontpath,'ttf', decompose = False, checkOutlines = False, autohint = False, releaseMode = False, glyphOrder=None, progressBar = None )
		print 'full font generated'
		self.fullTempUFO = OpenFont(self.fulltempfontpath, showUI=False)
		self.textRenderer = TR.TextRenderer(self.fulltempfontpath, tthtm.bitmapPreviewSelection)

	def generateMiniTempFont(self):
		root = os.path.split(tthtm.f.path)[0]
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
		

		tempFont.newGlyph(tthtm.g.name)
		tempFont[tthtm.g.name] = tthtm.g
		if 'com.robofont.robohint.assembly' in tthtm.g.lib:
			tempFont[tthtm.g.name].lib['com.robofont.robohint.assembly'] = tthtm.g.lib['com.robofont.robohint.assembly']

		tempFont.generate(self.tempfontpath, 'ttf', decompose = False, checkOutlines = False, autohint = False, releaseMode = False, glyphOrder=None, progressBar = None )
		print 'mini font generated'

	def mergeMiniAndFullTempFonts(self):
		root = os.path.split(tthtm.f.path)[0]
		tail = 'tempTemp.ttf'
		tempTempfontpath = os.path.join(root, tail)

		ttFull = fontTools.ttLib.TTFont(self.fulltempfontpath)
		ttMini = fontTools.ttLib.TTFont(self.tempfontpath)
		gName = tthtm.g.name
		ttFull['glyf'][gName] = ttMini['glyf'][gName]
		ttFull.save(tempTempfontpath)
		os.remove(self.fulltempfontpath)
		os.rename(tempTempfontpath, self.fulltempfontpath)
		print 'temp fonts merged'

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

		for zone in self.FL_Windows.topUIZones:
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

		for zone in self.FL_Windows.bottomUIZones:
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

	def drawDiscAtPoint(self, r, x, y):
		NSColor.colorWithRed_green_blue_alpha_(1, 0, 0, 1).set()
		NSBezierPath.bezierPathWithOvalInRect_(((x-r, y-r), (r*2, r*2))).fill()

	def drawAlign(self, scale, pointID, angle, cmdIndex):

		x = None
		y = None
		if pointID != 'lsb' and pointID != 'rsb':
			for contour in tthtm.g:
				for point in contour.points:
					if point.naked().uniqueID == pointID:
						x = point.x
						y = point.y
		elif pointID == 'lsb':
			x, y = 0, 0
		elif pointID == 'rsb':
			x, y = tthtm.g.width, 0

		self.drawArrowAtPoint(scale, 10, angle, x, y)
		self.drawArrowAtPoint(scale, 10, angle+180, x, y)

		# compute x, y
		if cmdIndex != None and cmdIndex not in self.commandLabelPos:
			self.commandLabelPos[cmdIndex] = (x + 10, y - 10)

		extension = ''
		text = 'A'
		if 'align' in self.glyphTTHCommands[cmdIndex]:
			if tthtm.selectedAxis == 'Y' and self.glyphTTHCommands[cmdIndex]['align'] == 'right':
				extension = 'top'
			elif tthtm.selectedAxis == 'Y' and self.glyphTTHCommands[cmdIndex]['align'] == 'left':
				extension = 'bottom'
			else:
				extension = self.glyphTTHCommands[cmdIndex]['align']


			text += '_' + extension
		elif self.glyphTTHCommands[cmdIndex]['code'] == 'alignt' or self.glyphTTHCommands[cmdIndex]['code'] == 'alignb':
			text += '_' + self.glyphTTHCommands[cmdIndex]['zone']

		self.drawTextAtPoint(text, x + 10, y - 10, NSColor.blueColor())

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
			if tthtm.selectedAxis == 'Y' and self.glyphTTHCommands[cmdIndex]['align'] == 'right':
				extension = 'top'
			elif tthtm.selectedAxis == 'Y' and self.glyphTTHCommands[cmdIndex]['align'] == 'left':
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
		if 'align' in self.glyphTTHCommands[cmdIndex]:
			extension = self.glyphTTHCommands[cmdIndex]['align']

		if stemName == None:
			self.drawTextAtPoint('D_' + extension, (offcurve1[0] + offcurve2[0])/2, (offcurve1[1] + offcurve2[1])/2, doublinkColor)
		else:
			self.drawTextAtPoint('D_' + stemName, (offcurve1[0] + offcurve2[0])/2, (offcurve1[1] + offcurve2[1])/2, doublinkColor)

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
	 	path.lineToPoint_((point[0]+ (value[0]/8)*tthtm.pitch, point[1] + (value[1]/8)*tthtm.pitch))

	 	deltacolor.set()
		path.setLineWidth_(scale)
		path.stroke()

		# compute x, y
		if cmdIndex != None and cmdIndex not in self.commandLabelPos:
			self.commandLabelPos[cmdIndex] = (point[0] + 10, point[1] - 10)
		
		extension = ''
		text = 'delta'
		value = self.glyphTTHCommands[cmdIndex]['delta']
		if self.glyphTTHCommands[cmdIndex]['code'][:1] == 'm':
			extension = '_M'
		elif self.glyphTTHCommands[cmdIndex]['code'][:1] == 'f':
			extension = '_F'
		text += extension + ':' + value
		self.drawTextAtPoint(text, point[0]+10, point[1]-10, deltacolor)

	def drawSideBearings(self, scale, char):
		try:
			xPos = tthtm.pitch * self.textRenderer.get_char_advance(char)[0] / 64
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
		text = self.previewWindow.previewString.replace('@', curGlyphString)

		# replace /name pattern
		sp = text.split('/')
		nbsp = len(sp)
		for i in range(1,nbsp):
			sub = sp[i].split(' ', 1)
			if sub[0] in self.fullTempUFO:
				sp[i] = unichr(self.fullTempUFO[sub[0]].unicode) + (' '.join(sub[1:]))
		text = ''.join(sp)

		# render user string
		if self.textRenderer:
			self.textRenderer.set_cur_size(tthtm.PPM_Size)
			self.textRenderer.set_pen((10, 50))
			self.textRenderer.render_text(text)

			# render current glyph at various sizes
			advance = 10
			for size in range(9, 48, 1):
				self.textRenderer.set_cur_size(size)
				self.textRenderer.set_pen((advance, 100))
				delta_pos = self.textRenderer.render_text(curGlyphString)
				advance += delta_pos[0] + 5

	def drawBackground(self, scale):
		if tthtm.g == None:
			return

		curChar = unichr(CurrentGlyph().unicode)
		
		self.textRenderer.set_cur_size(tthtm.PPM_Size)
		self.textRenderer.set_pen((0, 0))
		self.textRenderer.render_text_with_scale_and_alpha(curChar, tthtm.pitch, 0.4)

		r = 5*scale
		self.drawDiscAtPoint(r, 0, 0)
		self.drawDiscAtPoint(r, tthtm.g.width, 0)

		self.drawGrid(scale, tthtm.pitch)
		self.drawZones(scale)

		self.textRenderer.drawOutline(scale, tthtm.pitch, curChar)
		self.drawSideBearings(scale, curChar)

	def draw(self, scale):
		if self.isDragging() and self.startPoint != None:
			x_start = self.startPoint[0]
			y_start = self.startPoint[1]
			self.drawDiscAtPoint(5*scale, x_start, y_start)
			touchedEnd = self.isOnPoint(self.currentPoint)
			if touchedEnd != None:
				x_end = touchedEnd[0]
				y_end = touchedEnd[1]
				self.drawDiscAtPoint(5*scale, x_end, y_end)


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
					if cmd_code in ['alignv', 'alignt', 'alignb'] and tthtm.selectedAxis == 'Y':
						self.drawAlign(scale, cmd_pt, angle, cmdIndex)
					elif cmd_code == 'alignh' and tthtm.selectedAxis == 'X':
						self.drawAlign(scale, cmd_pt, angle, cmdIndex)
				elif cmd_code in ['alignv', 'alignt', 'alignb'] and tthtm.selectedAxis == 'Y':
					self.drawAlign(scale, self.pointNameToUniqueID[cmd_pt], angle, cmdIndex)
				elif cmd_code == 'alignh' and tthtm.selectedAxis == 'X':
					self.drawAlign(scale, self.pointNameToUniqueID[cmd_pt], angle, cmdIndex)

			if cmd_code in ['singleh', 'singlev', 'doubleh', 'doublev']:
				if cmd_pt1 == 'lsb':
					startPoint = (0, 0)
				elif cmd_pt1== 'rsb':
					startPoint = (0, tthtm.g.width)
				else:
					startPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt1]]

				if cmd_pt2 == 'lsb':
					endPoint = (0, 0)
				elif cmd_pt2 == 'rsb':
					endPoint = (tthtm.g.width, 0)
				else:
					endPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt2]]

				if cmd_code in ['doubleh', 'doublev']:
					if tthtm.selectedAxis == 'X' and cmd_code == 'doubleh':
						self.drawDoubleLink(scale, startPoint, endPoint, cmd_stem, cmdIndex)
					elif tthtm.selectedAxis == 'Y' and cmd_code == 'doublev':
						self.drawDoubleLink(scale, startPoint, endPoint, cmd_stem, cmdIndex)
				elif tthtm.selectedAxis == 'X' and cmd_code == 'singleh':
					self.drawLink(scale, startPoint, endPoint, cmd_stem, cmdIndex)
				elif tthtm.selectedAxis == 'Y' and cmd_code == 'singlev':
					self.drawLink(scale, startPoint, endPoint, cmd_stem, cmdIndex)

			if cmd_code in ['interpolateh', 'interpolatev']:

				if cmd_pt == 'lsb':
					middlePoint = (0, 0)
				elif cmd_pt== 'rsb':
					middlePoint = (0, tthtm.g.width)
				else:
					middlePoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt]]

				if cmd_pt1 == 'lsb':
					startPoint = (0, 0)
				elif cmd_pt1== 'rsb':
					startPoint = (0, tthtm.g.width)
				else:
					startPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt1]]

				if cmd_pt2 == 'lsb':
					endPoint = (0, 0)
				elif cmd_pt2 == 'rsb':
					endPoint = (tthtm.g.width, 0)
				else:
					endPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt2]]

				if tthtm.selectedAxis == 'X' and cmd_code == 'interpolateh':
					self.drawInterpolate(scale, startPoint, endPoint, middlePoint, cmdIndex)
				elif tthtm.selectedAxis == 'Y' and cmd_code == 'interpolatev':
					self.drawInterpolate(scale, startPoint, endPoint, middlePoint, cmdIndex)

			if cmd_code in ['mdeltah', 'mdeltav', 'fdeltah', 'fdeltav']:

				if cmd_pt == 'lsb':
					point = (0, 0)
				elif cmd_pt== 'rsb':
					point = (tthtm.g.width, 0)
				else:
					point = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt]]

				if cmd_code[-1] == 'h':
					value = (int(c['delta']), 0)
				elif cmd_code[-1] == 'v':
					value = (0, int(c['delta']))
				else:
					value = 0

				if int(tthtm.PPM_Size) in range(int(c['ppm1']), int(c['ppm2'])+1, 1):
					if tthtm.selectedAxis == 'X' and cmd_code in ['mdeltah', 'fdeltah']:
						self.drawDelta(scale, point, value, cmdIndex)
					elif tthtm.selectedAxis == 'Y' and cmd_code in ['mdeltav', 'fdeltav']:
						self.drawDelta(scale, point, value, cmdIndex)




class centralWindow(object):
	def __init__(self, f, TTHToolInstance):
		tthtm.f = f
		self.TTHToolInstance = TTHToolInstance
		self.wCentral = FloatingWindow((10, 30, 200, 600), "Central", closable = False)

		self.PPMSizesList = ['9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', 
							'21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
							'31', '32', '33', '34', '35', '36', '37', '38', '39', '40',
							'41', '42', '43', '44', '45', '46', '47', '48', '60', '72' ]
		self.axisList = ['X', 'Y']
		self.hintingToolsList = ['Align', 'Single Link', 'Double Link', 'Interpolation', 'Middle Delta', 'Final Delta']
		self.stemTypeList = ['None']
		self.stemsVertical = []
		for name, stem in self.TTHToolInstance.FL_Windows.stems.iteritems():
			if stem['horizontal'] == False:
				self.stemsVertical.append(name)
		self.stemTypeList.extend(self.stemsVertical)

		self.BitmapPreviewList = ['Monochrome', 'Grayscale', 'Subpixel']

		self.alignmentTypeListDisplay = ['Closest Pixel Edge', 'Left/Bottom Edge', 'Right/Top Edge', 'Center of Pixel', 'Double Grid']
		self.alignmentTypeList = ['round', 'left', 'right', 'center', 'double']

		self.alignmentTypeListLinkDisplay = ['Do Not Align to Grid', 'Closest Pixel Edge', 'Left/Bottom Edge', 'Right/Top Edge', 'Center of Pixel', 'Double Grid']
		self.alignmentTypeListLink = [None, 'round', 'left', 'right', 'center', 'double']

		self.wCentral.PPEMSizeText= TextBox((10, 10, 70, 14), "ppEm Size:", sizeStyle = "small")
		
		self.wCentral.PPEMSizeEditText = EditText((110, 8, 30, 19), sizeStyle = "small", 
				callback=self.PPEMSizeEditTextCallback)

		self.wCentral.PPEMSizeEditText.set(tthtm.PPM_Size)
		
		self.wCentral.PPEMSizePopUpButton = PopUpButton((150, 10, 40, 14),
				self.PPMSizesList, sizeStyle = "small",
				callback=self.PPEMSizePopUpButtonCallback)

		self.wCentral.BitmapPreviewText= TextBox((10, 30, 70, 14), "Preview:", sizeStyle = "small")
		self.wCentral.BitmapPreviewPopUpButton = PopUpButton((90, 30, 100, 14),
				self.BitmapPreviewList, sizeStyle = "small",
				callback=self.BitmapPreviewPopUpButtonCallback)

		self.wCentral.AxisText= TextBox((10, 50, 70, 14), "Axis:", sizeStyle = "small")
		self.wCentral.AxisPopUpButton = PopUpButton((150, 50, 40, 14),
				self.axisList, sizeStyle = "small",
				callback=self.AxisPopUpButtonCallback)

		self.wCentral.HintingToolText= TextBox((10, 70, 70, 14), "Tool:", sizeStyle = "small")
		self.wCentral.HintingToolPopUpButton = PopUpButton((90, 70, 100, 14),
				self.hintingToolsList, sizeStyle = "small",
				callback=self.HintingToolPopUpButtonCallback)

		self.wCentral.AlignmentTypeText = TextBox((10, 90, 70, 14), "Alignment:", sizeStyle = "small")
		self.wCentral.AlignmentTypePopUpButton = PopUpButton((90, 90, 100, 14),
				self.alignmentTypeListDisplay, sizeStyle = "small",
				callback=self.AlignmentTypePopUpButtonCallback)
		self.wCentral.AlignmentTypeText.show(True)
		self.wCentral.AlignmentTypePopUpButton.show(True)

		self.wCentral.StemTypeText = TextBox((10, 110, 70, 14), "Stem:", sizeStyle = "small")
		self.wCentral.StemTypePopUpButton = PopUpButton((90, 110, 100, 14),
				self.stemTypeList, sizeStyle = "small",
				callback=self.StemTypePopUpButtonCallback)
		self.wCentral.StemTypeText.show(False)
		self.wCentral.StemTypePopUpButton.show(False)

		self.wCentral.RoundDistanceText = TextBox((10, 130, 180, 14), "Round Distance:", sizeStyle = "small")
		self.wCentral.RoundDistanceCheckBox = CheckBox((-22, 125, -10, 22), "", sizeStyle = "small",
				callback=self.RoundDistanceCheckBoxCallback)
		self.wCentral.RoundDistanceText.show(False)
		self.wCentral.RoundDistanceCheckBox.show(False)

		self.wCentral.DeltaOffsetText = TextBox((10, 90, 120, 14), "Delta Offset:", sizeStyle = "small")
		self.wCentral.DeltaOffsetSlider = Slider((10, 110, -10, 15), maxValue=16, value=8, tickMarkCount=17, continuous=False, stopOnTickMarks=True, sizeStyle= "small",
				callback=self.DeltaOffsetSliderCallback)
		self.wCentral.DeltaOffsetText.show(False)
		self.wCentral.DeltaOffsetSlider.show(False)

		self.wCentral.DeltaRangeText = TextBox((10, 140, 120, 14), "Delta Range:", sizeStyle = "small")
		self.wCentral.DeltaRange1EditText = EditText((110, 138, 30, 19), sizeStyle = "small", 
				callback=self.DeltaRange1EditTextCallback)
		self.wCentral.DeltaRange2EditText = EditText((150, 138, 30, 19), sizeStyle = "small", 
				callback=self.DeltaRange2EditTextCallback)
		self.wCentral.DeltaRangeText.show(False)
		self.wCentral.DeltaRange1EditText.show(False)
		self.wCentral.DeltaRange2EditText.show(False)

		self.wCentral.ReadTTProgramButton = SquareButton((10, 180, -10, 22), "Read Glyph TT program", sizeStyle = 'small', 
				callback=self.ReadTTProgramButtonCallback)
	

		self.wCentral.PreviewShowButton = SquareButton((10, -98, -10, 22), "Show Preview", sizeStyle = 'small', 
				callback=self.PreviewShowButtonCallback)
		self.wCentral.PreviewHideButton = SquareButton((10, -98, -10, 22), "Hide Preview", sizeStyle = 'small', 
				callback=self.PreviewHideButtonCallback)
		self.wCentral.PreviewHideButton.show(False)

		self.wCentral.GeneralShowButton = SquareButton((10, -76, -10, 22), "Show General Options", sizeStyle = 'small', 
				callback=self.GeneralShowButtonCallback)
		self.wCentral.GeneralHideButton = SquareButton((10, -76, -10, 22), "Hide General Options", sizeStyle = 'small', 
				callback=self.GeneralHideButtonCallback)
		self.wCentral.GeneralHideButton.show(False)

		self.wCentral.StemsShowButton = SquareButton((10, -54, -10, 22), "Show Stems Settings", sizeStyle = 'small', 
				callback=self.StemsShowButtonCallback)
		self.wCentral.StemsHideButton = SquareButton((10, -54, -10, 22), "Hide Stems Settings", sizeStyle = 'small', 
				callback=self.StemsHideButtonCallback)
		self.wCentral.StemsHideButton.show(False)

		self.wCentral.ZonesShowButton = SquareButton((10, -32, -10, 22), "Show Zones Settings", sizeStyle = 'small', 
				callback=self.ZonesShowButtonCallback)
		self.wCentral.ZonesHideButton = SquareButton((10, -32, -10, 22), "Hide Zones Settings", sizeStyle = 'small', 
				callback=self.ZonesHideButtonCallback)
		self.wCentral.ZonesHideButton.show(False)


		self.wCentral.open()

	def closeCentral(self):
		self.wCentral.close()

	def PPEMSizeEditTextCallback(self, sender):
		self.TTHToolInstance.changeSize(sender.get())

	def PPEMSizePopUpButtonCallback(self, sender):
		if tthtm.g == None:
			return
		size = self.PPMSizesList[sender.get()]
		self.TTHToolInstance.changeSize(size)

	def BitmapPreviewPopUpButtonCallback(self, sender):
		self.TTHToolInstance.changeBitmapPreview(self.BitmapPreviewList[sender.get()])

	def AxisPopUpButtonCallback(self, sender):
		self.TTHToolInstance.changeAxis(self.axisList[sender.get()])
		#tthtm.selectedAxis = self.axisList[sender.get()]

		self.stemTypeList = ['None']
		self.stemsHorizontal = []
		self.stemsVertical = []

		for name, stem in self.TTHToolInstance.FL_Windows.stems.iteritems():
			if stem['horizontal'] == True:
				self.stemsHorizontal.append(name)
			else:
				self.stemsVertical.append(name)

		if tthtm.selectedAxis == 'X':
			self.stemTypeList.extend(self.stemsVertical)
		else:
			self.stemTypeList.extend(self.stemsHorizontal)

		self.wCentral.StemTypePopUpButton.setItems(self.stemTypeList)
		UpdateCurrentGlyphView()

	def centralWindowLinkSettings(self):
		self.TTHToolInstance.selectedAlignmentType = self.alignmentTypeListLink[0]
		self.wCentral.AlignmentTypePopUpButton.setItems(self.alignmentTypeListLinkDisplay)
		self.wCentral.AlignmentTypeText.show(True)
		self.wCentral.AlignmentTypePopUpButton.show(True)
		self.wCentral.StemTypeText.show(True)
		self.wCentral.StemTypePopUpButton.show(True)
		self.wCentral.RoundDistanceText.show(True)
		self.wCentral.RoundDistanceCheckBox.show(True)
		self.wCentral.DeltaOffsetText.show(False)
		self.wCentral.DeltaOffsetSlider.show(False)
		self.wCentral.DeltaRangeText.show(False)
		self.wCentral.DeltaRange1EditText.show(False)
		self.wCentral.DeltaRange2EditText.show(False)

	def centralWindowAlignSettings(self):
		self.TTHToolInstance.selectedAlignmentType = self.alignmentTypeList[0]
		self.wCentral.AlignmentTypePopUpButton.setItems(self.alignmentTypeListDisplay)
		self.wCentral.AlignmentTypeText.show(True)
		self.wCentral.AlignmentTypePopUpButton.show(True)
		self.wCentral.StemTypeText.show(False)
		self.wCentral.StemTypePopUpButton.show(False)
		self.wCentral.RoundDistanceText.show(False)
		self.wCentral.RoundDistanceCheckBox.show(False)
		self.wCentral.DeltaOffsetText.show(False)
		self.wCentral.DeltaOffsetSlider.show(False)
		self.wCentral.DeltaRangeText.show(False)
		self.wCentral.DeltaRange1EditText.show(False)
		self.wCentral.DeltaRange2EditText.show(False)

	def centralWindowInterpolationSettings(self):
		self.TTHToolInstance.selectedAlignmentType = self.alignmentTypeListLink[0]
		self.wCentral.AlignmentTypePopUpButton.setItems(self.alignmentTypeListLinkDisplay)
		self.wCentral.AlignmentTypeText.show(True)
		self.wCentral.AlignmentTypePopUpButton.show(True)
		self.wCentral.StemTypeText.show(False)
		self.wCentral.StemTypePopUpButton.show(False)
		self.wCentral.RoundDistanceText.show(False)
		self.wCentral.RoundDistanceCheckBox.show(False)
		self.wCentral.DeltaOffsetText.show(False)
		self.wCentral.DeltaOffsetSlider.show(False)
		self.wCentral.DeltaRangeText.show(False)
		self.wCentral.DeltaRange1EditText.show(False)
		self.wCentral.DeltaRange2EditText.show(False)

	def centralWindowDeltaSettings(self):
		self.wCentral.AlignmentTypeText.show(False)
		self.wCentral.AlignmentTypePopUpButton.show(False)
		self.wCentral.StemTypeText.show(False)
		self.wCentral.StemTypePopUpButton.show(False)
		self.wCentral.RoundDistanceText.show(False)
		self.wCentral.RoundDistanceCheckBox.show(False)
		self.wCentral.DeltaOffsetText.show(True)
		self.wCentral.DeltaOffsetSlider.show(True)
		self.wCentral.DeltaRangeText.show(True)
		self.wCentral.DeltaRange1EditText.show(True)
		self.wCentral.DeltaRange2EditText.show(True)



	def HintingToolPopUpButtonCallback(self, sender):
		self.TTHToolInstance.changeSelectedHintingTool(self.hintingToolsList[sender.get()])
		#print tthtm.selectedHintingTool
		if tthtm.selectedHintingTool in ['Single Link', 'Double Link']:
			self.centralWindowLinkSettings()
		elif tthtm.selectedHintingTool == 'Align':
			self.centralWindowAlignSettings()
		elif tthtm.selectedHintingTool == 'Interpolation':
			self.centralWindowInterpolationSettings()
		elif tthtm.selectedHintingTool in ['Middle Delta', 'Final Delta']:
			self.centralWindowDeltaSettings()
		else:
			self.wCentral.AlignmentTypeText.show(False)
			self.wCentral.AlignmentTypePopUpButton.show(False)
			self.wCentral.StemTypeText.show(False)
			self.wCentral.StemTypePopUpButton.show(False)
			self.wCentral.RoundDistanceText.show(False)
			self.wCentral.RoundDistanceCheckBox.show(False)
			self.wCentral.DeltaOffsetText.show(False)
			self.wCentral.DeltaOffsetSlider.show(False)
			self.wCentral.DeltaRangeText.show(False)
			self.wCentral.DeltaRange1EditText.show(False)
			self.wCentral.DeltaRange2EditText.show(False)


	def AlignmentTypePopUpButtonCallback(self, sender):
		if tthtm.selectedHintingTool in ['Single Link', 'Double Link', 'Interpolation']:
			self.TTHToolInstance.selectedAlignmentType = self.alignmentTypeListLink[sender.get()]
		elif tthtm.selectedHintingTool == 'Align':
			self.TTHToolInstance.selectedAlignmentType = self.alignmentTypeList[sender.get()]
		#print self.TTHToolInstance.selectedAlignmentType

	def StemTypePopUpButtonCallback(self, sender):
		self.TTHToolInstance.selectedStem = self.stemTypeList[sender.get()]
		print self.TTHToolInstance.selectedStem

	def RoundDistanceCheckBoxCallback(self, sender):
		self.TTHToolInstance.roundBool = sender.get()

	def DeltaOffsetSliderCallback(self, sender):
		print sender.get() - 8

	def DeltaRange1EditTextCallback(self, sender):
		print sender.get()

	def DeltaRange2EditTextCallback(self, sender):
		print sender.get()

	def ReadTTProgramButtonCallback(self, sender):
		FLTTProgram = self.TTHToolInstance.readGlyphFLTTProgram(tthtm.g)
		for i in FLTTProgram:
			print i

	def PreviewShowButtonCallback(self, sender):
		self.wCentral.PreviewHideButton.show(True)
		self.wCentral.PreviewShowButton.show(False)
		self.TTHToolInstance.previewWindow.showPreview()

	def PreviewHideButtonCallback(self, sender):
		self.wCentral.PreviewHideButton.show(False)
		self.wCentral.PreviewShowButton.show(True)
		self.TTHToolInstance.previewWindow.hidePreview()

	def GeneralShowButtonCallback(self, sender):
		self.wCentral.GeneralHideButton.show(True)
		self.wCentral.GeneralShowButton.show(False)
		self.TTHToolInstance.FL_Windows.showGeneral()

	def GeneralHideButtonCallback(self, sender):
		self.wCentral.GeneralHideButton.show(False)
		self.wCentral.GeneralShowButton.show(True)
		self.TTHToolInstance.FL_Windows.hideGeneral()

	def StemsShowButtonCallback(self, sender):
		self.wCentral.StemsHideButton.show(True)
		self.wCentral.StemsShowButton.show(False)
		self.TTHToolInstance.FL_Windows.showStems()

	def StemsHideButtonCallback(self, sender):
		self.wCentral.StemsHideButton.show(False)
		self.wCentral.StemsShowButton.show(True)
		self.TTHToolInstance.FL_Windows.hideStems()

	def ZonesShowButtonCallback(self, sender):
		self.wCentral.ZonesHideButton.show(True)
		self.wCentral.ZonesShowButton.show(False)
		self.TTHToolInstance.FL_Windows.showZones()

	def ZonesHideButtonCallback(self, sender):
		self.wCentral.ZonesHideButton.show(False)
		self.wCentral.ZonesShowButton.show(True)
		self.TTHToolInstance.FL_Windows.hideZones()


class previewWindow(object):
	def __init__(self, f, TTHToolInstance):
		tthtm.f = f
		self.TTHToolInstance = TTHToolInstance
		self.previewString = ''

		self.wPreview = FloatingWindow((210, 600, 600, 200), "Preview", closable = False, initiallyVisible=False)
		self.view = preview.PreviewArea.alloc().init_withTTHToolInstance(self.TTHToolInstance)

		self.view.setFrame_(((0, 0), (1500, 160)))
		self.wPreview.previewEditText = EditText((10, 10, -10, 22),
				callback=self.previewEditTextCallback)
		self.wPreview.previewScrollview = ScrollView((10, 50, -10, -10),
				self.view)

		self.wPreview.open()

	def closePreview(self):
		self.wPreview.close()

	def showPreview(self):
		self.wPreview.show()

	def hidePreview(self):
		self.wPreview.hide()

	def previewEditTextCallback(self, sender):
		self.previewString = sender.get()
		self.view.setNeedsDisplay_(True)


reload(TR)
reload(TTHintAsm)
reload(fl_tth)
reload(tt_tables)
reload(TTHToolModel)
tthtm = TTHToolModel.TTHToolModel()
installTool(TTHTool())
