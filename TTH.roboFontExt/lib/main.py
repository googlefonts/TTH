from mojo.events import *
from mojo.UI import *
from mojo.drawingTools import *

from fl_tth import *
import tt_tables
import preview

import math, os
import freetype
import Quartz
from objc import allocateBuffer

def pointsApproxEqual(p_glyph, p_cursor):
	return (abs(p_glyph[0] - p_cursor[0]) < 5) and (abs(p_glyph[1] - p_cursor[1]) < 5)

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

stepToSelector = {-8: 0, -7: 1, -6: 2, -5: 3, -4: 4, -3: 5, -2: 6, -1: 7, 1: 8, 2: 9, 3: 10, 4: 11, 5: 12, 6: 13, 7: 14, 8: 15}

class TTHTool(BaseEventTool):

	def __init__(self):
		BaseEventTool.__init__(self)
		self.f = None
		self.g = None
		self.UPM = 1000
		self.PPM_Size = 9
		self.pitch = self.UPM/self.PPM_Size
		self.face = None
		self.bitmapPreviewSelection = 'Monochrome'
		self.unicodeToNameDict = createUnicodeToNameDict()
		self.ready = False
		self.p_glyphList = []
		self.commandLabelPos = {}

	def becomeActive(self):
		self.bitmapPreviewSelection = 'Monochrome'
		self.resetfonts()

	def becomeInactive(self):
		self.FL_Windows.closeAll()
		self.centralWindow.closeCentral()
		self.previewWindow.closePreview()

	def fontResignCurrent(self, font):
		self.FL_Windows.closeAll()
		self.centralWindow.closeCentral()
		self.previewWindow.closePreview()
		self.resetfonts()

	def fontBecameCurrent(self, font):
		self.FL_Windows.closeAll()
		self.centralWindow.closeCentral()
		self.previewWindow.closePreview()
		self.resetfonts()
		self.resetglyph()

	def viewDidChangeGlyph(self):
		self.resetglyph()

	def isOnPoint(self, p_cursor):
		def pred0(p_glyph):
			return pointsApproxEqual(p_glyph, p_cursor)
		touched_p_glyph = find_in_list(self.p_glyphList, pred0)

		return touched_p_glyph

	def isOnCommand(self, p_cursor):
		if self.centralWindow.selectedAxis == 'X':
			 skipper = ['v','t','b']
		else:
		    skipper = ['h']

		def pred0(cmdIdx, commandPos):
			if self.glyphTTHCommands[cmdIdx]['code'][-1] in skipper:
				return False
			return pointsApproxEqual(commandPos, p_cursor)

		touched_p_command = find_in_dict(self.commandLabelPos, pred0)

		return touched_p_command

	def mouseDown(self, point, clickCount):
		self.p_cursor = (int(point.x), int(point.y))
		self.startPoint = self.isOnPoint(self.p_cursor)
		self.commandPoint = self.isOnCommand(self.p_cursor)
		print 'glyph point:', self.startPoint
		print 'command point:', self.commandPoint

	def resetfonts(self):
		self.allFonts = loadFonts()
		if not self.allFonts:
			return
		self.f = loadCurrentFont(self.allFonts)
		self.UPM = self.f.info.unitsPerEm
		self.PPM_Size = 9
		self.pitch = int(self.UPM) / int(self.PPM_Size)

		self.FL_Windows = FL_TTH_Windows(self.f)
		self.centralWindow = centralWindow(self.f, self)
		self.previewWindow = previewWindow(self.f, self)

		tt_tables.writeCVTandPREP(self.f, self.UPM, self.FL_Windows.alignppm, self.FL_Windows.stems, self.FL_Windows.zones, self.FL_Windows.codeppm)
		tt_tables.writeFPGM(self.f)

		for g in self.f:
			glyphTTHCommands = self.readGlyphFLTTProgram(g)
			if glyphTTHCommands != None:
				self.writeAssembly(g, glyphTTHCommands)

		self.generateFullTempFont()
		self.indexOfGlyphNames = dict([(self.fullTempUFO.lib['public.glyphOrder'][idx], idx) for idx in range(len(self.fullTempUFO.lib['public.glyphOrder']))])

	def resetglyph(self):
		self.g = CurrentGlyph()
		if self.g == None:
			return
		glyphTTHCommands = self.readGlyphFLTTProgram(self.g)
		self.commandLabelPos = {}
		self.pointNameToUniqueID = self.makePointNameToUniqueIDDict(self.g)
		self.pointUniqueIDToCoordinates = self.makePointUniqueIDToCoordinatesDict(self.g)
		self.generateMiniTempFont()
		self.face = freetype.Face(self.fulltempfontpath)
		self.ready = True
		self.previewWindow.view.setNeedsDisplay_(True)

		self.p_glyphList.extend([(0, 0), (self.g.width, 0)])

		for c in self.g:
			for p in c.points:
				if p.type != 'offCurve':
					self.p_glyphList.append((p.x, p.y))


	def generateFullTempFont(self):
		root =  os.path.split(self.f.path)[0]
		tail = 'Fulltemp.ttf'
		self.fulltempfontpath = os.path.join(root, tail)

		self.f.generate(self.fulltempfontpath,'ttf', decompose = False, checkOutlines = False, autohint = False, releaseMode = False, glyphOrder=None, progressBar = None )
		print 'full font generated'
		self.fullTempUFO = OpenFont(self.fulltempfontpath, showUI=False)

	def generateMiniTempFont(self):
		root =  os.path.split(self.f.path)[0]
		tail = 'Minitemp.ttf'
		self.tempfontpath = os.path.join(root, tail)

		tempFont = RFont(showUI=False)
		tempGlyph = self.g.copy()

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
		

		tempFont.newGlyph(self.g.name)
		tempFont[self.g.name] = tempGlyph
		if 'com.robofont.robohint.assembly' in self.g.lib:
			tempFont[self.g.name].lib['com.robofont.robohint.assembly'] = self.g.lib['com.robofont.robohint.assembly']

		tempFont.generate(self.tempfontpath, 'ttf', decompose = False, checkOutlines = False, autohint = False, releaseMode = False, glyphOrder=None, progressBar = None )
		print 'mini font generated'

	def makePointNameToUniqueIDDict(self, g):
		pointNameToUniqueID = {}
		for contour in g:
			for point in contour.points:
				if point.name:
					name =  point.name.split(',')[0]
					uniqueID = point.naked().uniqueID
					pointNameToUniqueID[name] = uniqueID
		return pointNameToUniqueID

	def pointIndexFromUniqueID(self, g, pointUniqueID):
		pointIndex = 0
		for contour in g:
			for point in contour.points:
				if pointUniqueID == point.naked().uniqueID:
					return pointIndex
				pointIndex += 1
		return None

	def makePointUniqueIDToCoordinatesDict(self, g):
		pointUniqueIDToCoordinates = {}
		for contour in g:
			for point in contour.points:
				pointUniqueIDToCoordinates[point.naked().uniqueID] = ((point.x, point.y))
		return pointUniqueIDToCoordinates

	def readGlyphFLTTProgram(self, g):
		if g == None:
			return
		self.pointNameToUniqueID = self.makePointNameToUniqueIDDict(g)
		self.glyphTTHCommands = []
		if 'com.fontlab.ttprogram' not in g.lib:
			return None
		ttprogram = g.lib['com.fontlab.ttprogram']
		ttprogram = str(ttprogram).split('\\n')
		for line in ttprogram[1:-2]:
			TTHCommandList = []
			TTHCommandDict = {}
			for settings in line[9:-2].split('='):
				setting = settings.split ('"')
				for command in setting:
					if command != '':
						if command[0] == ' ':
							command = command[1:]
						TTHCommandList.append(command)
			for i in range(0, len(TTHCommandList), 2):
				TTHCommandDict[TTHCommandList[i]] = TTHCommandList[i+1]
			self.glyphTTHCommands.append(TTHCommandDict)
		return self.glyphTTHCommands

	def writeAssembly(self, g, glyphTTHCommands):
		if g == None:
			return

		nbPointsContour = 0
		for contour in g:
			nbPointsContour += len(contour.points)

		lsbIndex = nbPointsContour
		rsbIndex = nbPointsContour+1

		assembly = []
		g.lib['com.robofont.robohint.assembly'] = []
		x_instructions = ['SVTCA[1]']
		y_instructions = ['SVTCA[0]']
		RP0 = RP1 = RP2 = None
		pointUniqueID = None
		point1UniqueID = None
		point2UniqueID = None
		touchedPoints = []
		finalDeltasH = []
		finalDeltasV = []

		for TTHCommand in glyphTTHCommands:
			if TTHCommand['code'] == 'alignt' or TTHCommand['code'] == 'alignb':
				if TTHCommand['point'] == 'lsb':
					pointIndex = lsbIndex
				elif TTHCommand['point'] == 'rsb':
					pointIndex = rsbIndex
				else:
					pointUniqueID = self.pointNameToUniqueID[TTHCommand['point']]
					pointIndex = self.pointIndexFromUniqueID(g, pointUniqueID)
				zoneCV = tt_tables.zone_to_cvt[TTHCommand['zone']]
				alignToZone = [
						'PUSHW[ ] 0',
						'RCVT[ ]',
						'IF[ ]',
						'PUSHW[ ] ' + str(pointIndex),
						'MDAP[1]',
						'ELSE[ ]',
						'PUSHW[ ] ' + str(pointIndex) + ' ' + str(zoneCV),
						'MIAP[0]',
						'EIF[ ]'
						]
				y_instructions.extend(alignToZone)

			if TTHCommand['code'] == 'alignh' or TTHCommand['code'] == 'alignv':
				if TTHCommand['point'] == 'lsb':
					pointIndex = lsbIndex
				elif TTHCommand['point'] == 'rsb':
					pointIndex = rsbIndex
				else:
					pointUniqueID = self.pointNameToUniqueID[TTHCommand['point']]
					pointIndex = self.pointIndexFromUniqueID(g, pointUniqueID)

					if pointUniqueID not in touchedPoints:
							touchedPoints.append(pointUniqueID)

				RP0 = pointIndex
				RP1 = pointIndex

				if TTHCommand['align'] == 'round':
					align = [
							'PUSHW[ ] ' + str(pointIndex),
							'MDAP[1]'
							]
				elif TTHCommand['align'] == 'left' or TTHCommand['align'] == 'bottom':
					align = [
							'RDTG[ ]',
							'PUSHW[ ] ' + str(pointIndex),
							'MDAP[1]'
							'RTG[ ]'
							]
				elif TTHCommand['align'] == 'right' or TTHCommand['align'] == 'top':
					align = [
							'RUTG[ ]',
							'PUSHW[ ] ' + str(pointIndex),
							'MDAP[1]'
							'RTG[ ]'
							]
				elif TTHCommand['align'] == 'double':
					align = [
							'RTDG[ ]',
							'PUSHW[ ] ' + str(pointIndex),
							'MDAP[1]'
							'RTG[ ]'
							]
				elif TTHCommand['align'] == 'center':
					align = [
							'RTHG[ ]',
							'PUSHW[ ] ' + str(pointIndex),
							'MDAP[1]'
							'RTG[ ]'
							]
				if TTHCommand['code'] == 'alignh':
					x_instructions.extend(align)
				elif TTHCommand['code'] == 'alignv':
					y_instructions.extend(align)


			if TTHCommand['code'] == 'doubleh' or TTHCommand['code'] == 'doublev':
				if TTHCommand['point1'] == 'lsb':
					point1Index = lsbIndex
				elif TTHCommand['point1'] == 'rsb':
					point1Index = rsbIndex
				else:
					point1UniqueID = self.pointNameToUniqueID[TTHCommand['point1']]
					point1Index = self.pointIndexFromUniqueID(g, point1UniqueID)
					if point1UniqueID not in touchedPoints:
							touchedPoints.append(point1UniqueID)

				if TTHCommand['point2'] == 'lsb':
					point2Index = lsbIndex
				elif TTHCommand['point2'] == 'rsb':
					point2Index = rsbIndex
				else:
					point2UniqueID = self.pointNameToUniqueID[TTHCommand['point2']]
					point2Index = self.pointIndexFromUniqueID(g, point2UniqueID)
					if point2UniqueID not in touchedPoints:
							touchedPoints.append(point2UniqueID)

				if 'stem' in TTHCommand:
					stemCV = tt_tables.stem_to_cvt[TTHCommand['stem']]
					double = [
							'PUSHW[ ] ' + str(point2Index) + ' ' +  str(stemCV) + ' ' + str(point1Index) + ' 4',
          					'CALL[ ]'
							]
				elif 'round' in TTHCommand:
					double = [
							'PUSHW[ ] ' + str(point2Index) + ' ' + str(point1Index) + ' 3',
          					'CALL[ ]'
							]
				if TTHCommand['code'] == 'doubleh':
					x_instructions.extend(double)
				elif TTHCommand['code'] == 'doublev':
					y_instructions.extend(double)


			if TTHCommand['code'] == 'interpolateh' or TTHCommand['code'] == 'interpolatev':

				if TTHCommand['point1'] == 'lsb':
					point1Index = lsbIndex
				elif TTHCommand['point1'] == 'rsb':
					point1Index = rsbIndex
				else:
					point1UniqueID = self.pointNameToUniqueID[TTHCommand['point1']]
					point1Index = self.pointIndexFromUniqueID(g, point1UniqueID)
					if point1UniqueID not in touchedPoints:
							touchedPoints.append(point1UniqueID)

				if TTHCommand['point2'] == 'lsb':
					point2Index = lsbIndex
				elif TTHCommand['point2'] == 'rsb':
					point2Index = rsbIndex
				else:
					point2UniqueID = self.pointNameToUniqueID[TTHCommand['point2']]
					point2Index = self.pointIndexFromUniqueID(g, point2UniqueID)
					if point2UniqueID not in touchedPoints:
							touchedPoints.append(point2UniqueID)

				if TTHCommand['point'] == 'lsb':
					pointIndex = lsbIndex
				elif TTHCommand['point'] == 'rsb':
					pointIndex = rsbIndex
				else:
					pointUniqueID = self.pointNameToUniqueID[TTHCommand['point']]
					pointIndex = self.pointIndexFromUniqueID(g, pointUniqueID)
					if pointUniqueID not in touchedPoints:
							touchedPoints.append(pointUniqueID)

				interpolate = [
								'PUSHW[ ] ' + str(pointIndex) + ' ' + str(point1Index) + ' ' + str(point2Index),
								'SRP1[ ]',
								'SRP2[ ]',
								'IP[ ]'
								]
				if 'align' in TTHCommand:
					if TTHCommand['align'] == 'round':
						align = [
								'PUSHW[ ] ' + str(pointIndex),
								'MDAP[1]'
								]
					elif TTHCommand['align'] == 'left' or TTHCommand['align'] == 'bottom':
						align = [
								'RDTG[ ]',
								'PUSHW[ ] ' + str(pointIndex),
								'MDAP[1]'
								'RTG[ ]'
								]
					elif TTHCommand['align'] == 'right' or TTHCommand['align'] == 'top':
						align = [
								'RUTG[ ]',
								'PUSHW[ ] ' + str(pointIndex),
								'MDAP[1]'
								'RTG[ ]'
								]
					elif TTHCommand['align'] == 'double':
						align = [
								'RTDG[ ]',
								'PUSHW[ ] ' + str(pointIndex),
								'MDAP[1]'
								'RTG[ ]'
								]
					elif TTHCommand['align'] == 'center':
						align = [
								'RTHG[ ]',
								'PUSHW[ ] ' + str(pointIndex),
								'MDAP[1]'
								'RTG[ ]'
								]
				else:
					align = []
				interpolate.extend(align)

				if TTHCommand['code'] == 'interpolateh':
					x_instructions.extend(interpolate)
				elif TTHCommand['code'] == 'interpolatev':
					y_instructions.extend(interpolate)


			if TTHCommand['code'] == 'singleh' or TTHCommand['code'] == 'singlev':

				if TTHCommand['point1'] == 'lsb':
					point1Index = lsbIndex
				elif TTHCommand['point1'] == 'rsb':
					point1Index = rsbIndex
				else:
					point1UniqueID = self.pointNameToUniqueID[TTHCommand['point1']]
					point1Index = self.pointIndexFromUniqueID(g, point1UniqueID)

				if TTHCommand['point2'] == 'lsb':
					point2Index = lsbIndex
				elif TTHCommand['point2'] == 'rsb':
					point2Index = rsbIndex
				else:
					point2UniqueID = self.pointNameToUniqueID[TTHCommand['point2']]
					point2Index = self.pointIndexFromUniqueID(g, point2UniqueID)

				singleLink = []
				if RP0 == None or point1UniqueID not in touchedPoints:
					singleLink = [
									'PUSHW[ ] ' + str(point1Index),
									'MDAP[1]'
									]
					RP0 = point1Index
					RP1 = point1Index
					touchedPoints.append(point1UniqueID)

				else:
					singleLink = [
									'PUSHW[ ] ' + str(point1Index),
									'SRP0[ ]',
									]
					RP0 = point1Index
					if point1UniqueID not in touchedPoints:
						touchedPoints.append(point1UniqueID)

				singleLink2 = []
				align2 = []
				if 'stem' in TTHCommand:
					stemCV = tt_tables.stem_to_cvt[TTHCommand['stem']]
					singleLink2 = [
									'PUSHW[ ] ' + str(point2Index) + ' ' + str(stemCV),
									'MIRP[10100]'
									]
					RP1 = RP0 = RP2 = point2Index
					if point2UniqueID not in touchedPoints:
						touchedPoints.append(point2UniqueID)

				elif 'round' in TTHCommand:
					singleLink2 = [
									'PUSHW[ ] ' + str(point2Index),
									'MDRP[11100]'
									]
					RP1 = RP0 = RP2 = point2Index
					if point2UniqueID not in touchedPoints:
						touchedPoints.append(point2UniqueID)

				elif 'align' in TTHCommand:
					singleLink2 = [
									'PUSHW[ ] ' + str(point2Index),
									'MDRP[10000]'
									]
					if TTHCommand['align'] == 'round':
						singleLink2 = [
									'PUSHW[ ] ' + str(point2Index),
									'MDRP[10100]'
									]
						align2 = [
										'PUSHW[ ] ' + str(point2Index),
										'MDAP[1]'
										]
						RP1 = RP0 = RP2 = point2Index
						if point2UniqueID not in touchedPoints:
							touchedPoints.append(point2UniqueID)

					if TTHCommand['align'] in ['left', 'bottom']:
						align2 = [		
										'RDTG[ ]',
										'PUSHW[ ] ' + str(point2Index),
										'MDAP[1]',
										'RTG[]'
										]
						RP1 = RP0 = RP2 = point2Index
						if point2UniqueID not in touchedPoints:
							touchedPoints.append(point2UniqueID)

					if TTHCommand['align'] in ['right', 'top']:
						align2 = [		
										'RUTG[ ]',
										'PUSHW[ ] ' + str(point2Index),
										'MDAP[1]',
										'RTG[]'
										]
						RP1 = RP0 = RP2 = point2Index
						if point2UniqueID not in touchedPoints:
							touchedPoints.append(point2UniqueID)

					elif TTHCommand['align'] == 'double':
						align2 = [		
										'RTDG[ ]',
										'PUSHW[ ] ' + str(point2Index),
										'MDAP[1]',
										'RTG[]'
										]
						RP1 = RP0 = RP2 = point2Index
						if point2UniqueID not in touchedPoints:
							touchedPoints.append(point2UniqueID)

					elif TTHCommand['align'] == 'center':
						align2 = [		
										'RTHG[ ]',
										'PUSHW[ ] ' + str(point2Index),
										'MDAP[1]',
										'RTG[]'
										]
						RP1 = RP0 = RP2 = point2Index
						if point2UniqueID not in touchedPoints:
							touchedPoints.append(point2UniqueID)

					else:
						align2 = []

						
				else:
					singleLink2 = [
									'PUSHW[ ] ' + str(point2Index),
									'MDRP[10000]'
									]
					RP1 = RP0 = RP2 = point2Index
					if point2UniqueID not in touchedPoints:
						touchedPoints.append(point2UniqueID)

				singleLink.extend(singleLink2)
				singleLink.extend(align2)

				if TTHCommand['code'] == 'singleh':
					x_instructions.extend(singleLink)
				elif TTHCommand['code'] == 'singlev':
					y_instructions.extend(singleLink)



			if TTHCommand['code'] in ['mdeltah', 'mdeltav', 'fdeltah', 'fdeltav']:
				middleDeltas = []
				if TTHCommand['point'] == 'lsb':
					pointIndex = lsbIndex
				elif TTHCommand['point'] == 'rsb':
					pointIndex = rsbIndex
				else:
					pointUniqueID = self.pointNameToUniqueID[TTHCommand['point']]
					pointIndex = self.pointIndexFromUniqueID(g, pointUniqueID)
					if pointUniqueID not in touchedPoints:
							touchedPoints.append(pointUniqueID)

				ppm1 = TTHCommand['ppm1']
				ppm2 = TTHCommand['ppm2']
				step = int(TTHCommand['delta'])
				nbDelta = 1 + int(ppm2) - int(ppm1)
				deltasP1 = []
				deltasP2 = []
				deltasP3 = []
				for i in range(nbDelta):
					ppm = int(ppm1) + i
					relativeSize = int(ppm) - 9
					if 0 <= relativeSize <= 15:
						deltasP1.append(relativeSize)
					elif 16 <= relativeSize <= 31:
						deltasP2.append(relativeSize)
					elif 32 <= relativeSize <= 47:
						deltasP3.append(relativeSize)
					else:
						print 'delta out of range'
				deltaPString = 'PUSHW[ ]'
				if deltasP1:
					for i in range(len(deltasP1)):
						relativeSize = deltasP1[i]
						arg = (relativeSize << 4 ) + stepToSelector[step]
						deltaPString += ' ' + str(arg) + ' ' + str(pointIndex)
					
					deltaPString += ' ' + str(len(deltasP1))
					middleDeltas.append(deltaPString)
					middleDeltas.append('DELTAP1[ ]')

				if deltasP2:
					for i in range(len(deltasP2)):
						relativeSize = deltasP2[i]
						arg = ((relativeSize -16) << 4 ) + stepToSelector[step]
						deltaPString += ' ' + str(arg) + ' ' + str(pointIndex)
					
					deltaPString += ' ' + str(len(deltasP1))
					middleDeltas.append(deltaPString)
					middleDeltas.append('DELTAP2[ ]')

				if deltasP3:
					for i in range(len(deltasP3)):
						relativeSize = deltasP3[i]
						arg = ((relativeSize -32) << 4 ) + stepToSelector[step]
						deltaPString += ' ' + str(arg) + ' ' + str(pointIndex)
					
					deltaPString += ' ' + str(len(deltasP1))
					middleDeltas.append(deltaPString)
					middleDeltas.append('DELTAP3[ ]')

				if TTHCommand['code'] == 'mdeltah':
					x_instructions.extend(middleDeltas)
				elif TTHCommand['code'] == 'mdeltav':
					y_instructions.extend(middleDeltas)

				elif TTHCommand['code'] == 'fdeltah':
					finalDeltasH.extend(middleDeltas)
				elif TTHCommand['code'] == 'fdeltav':
					finalDeltasV.extend(middleDeltas)

		##############################	
		assembly.extend(x_instructions)
		assembly.extend(y_instructions)

		assembly.extend(['IUP[0]', 'IUP[1]'])
		assembly.append('SVTCA[1]')
		assembly.extend(finalDeltasH)
		assembly.append('SVTCA[0]')
		assembly.extend(finalDeltasV)
		g.lib['com.robofont.robohint.assembly'] = assembly

	def getGlyphIndexByName(self, glyphName):
		try:
			return self.indexOfGlyphNames[glyphName]
		except:
			return None

	def loadFaceGlyph(self, glyphName, size):
		if self.face == None:
			return
		self.face.set_pixel_sizes(int(size), int(size))
		g_index = self.getGlyphIndexByName(glyphName)
		if self.bitmapPreviewSelection == 'Monochrome':
			self.face.load_glyph(g_index, freetype.FT_LOAD_RENDER |
    	                    freetype.FT_LOAD_TARGET_MONO )
		elif self.bitmapPreviewSelection == 'Grayscale':
			self.face.load_glyph(g_index, freetype.FT_LOAD_RENDER |
							freetype.FT_LOAD_TARGET_NORMAL)
		elif self.bitmapPreviewSelection == 'Subpixel':
			self.face.load_glyph(g_index, freetype.FT_LOAD_RENDER |
                       freetype.FT_LOAD_TARGET_LCD )
		else:
			self.face.load_glyph(g_index)

		self.adaptedOutline_points = []
		for i in range(len(self.face.glyph.outline.points)):
			self.adaptedOutline_points.append( (int( self.pitch*self.face.glyph.outline.points[i][0]/64), int( self.pitch*self.face.glyph.outline.points[i][1]/64  )) )

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

		for zone in self.FL_Windows.topZonesList:
			y_start = int(zone['Position'])
			y_end = int(zone['Width'])
			pathZone = NSBezierPath.bezierPath()
			pathZone.moveToPoint_((-5000, y_start))
			pathZone.lineToPoint_((5000, y_start))
			pathZone.lineToPoint_((5000, y_start+y_end))
			pathZone.lineToPoint_((-5000, y_start+y_end))
			pathZone.closePath
			NSColor.colorWithRed_green_blue_alpha_(0/255, 180/255, 50/255, .2).set()
			pathZone.fill()	
		for zone in self.FL_Windows.bottomZonesList:
			y_start = int(zone['Position'])
			y_end = int(zone['Width'])
			pathZone = NSBezierPath.bezierPath()
			pathZone.moveToPoint_((-5000, y_start))
			pathZone.lineToPoint_((5000, y_start))
			pathZone.lineToPoint_((5000, y_start-y_end))
			pathZone.lineToPoint_((-5000, y_start-y_end))
			pathZone.closePath
			NSColor.colorWithRed_green_blue_alpha_(0/255, 180/255, 50/255, .2).set()
			pathZone.fill()	

	def drawOutline(self, scale, face):
		#print outline.contours
		if len(face.glyph.outline.contours) == 0:
			return

		pathContour = NSBezierPath.bezierPath()
		start, end = 0, 0		
		for c_index in range(len(face.glyph.outline.contours)):
			end    = face.glyph.outline.contours[c_index]
			points = self.adaptedOutline_points[start:end+1] 
			points.append(points[0])
			tags   = face.glyph.outline.tags[start:end+1]
			tags.append(tags[0])

			segments = [ [points[0],], ]

			for j in range(1, len(points) ):
				segments[-1].append(points[j])
				if tags[j] & (1 << 0) and j < (len(points)-1):
					segments.append( [points[j],] )
			pathContour.moveToPoint_((points[0][0], points[0][1]))
			for segment in segments:
				if len(segment) == 2:
					pathContour.lineToPoint_(segment[1])
				else:
					onCurve = segment[0]
					for i in range(1,len(segment)-2):
						A,B = segment[i], segment[i+1]
						nextOn = ((A[0]+B[0])/2.0, (A[1]+B[1])/2.0)
						antenne1 = ((onCurve[0] + 2 * A[0]) / 3.0 , (onCurve[1] + 2 * A[1]) / 3.0)
						antenne2 = ((nextOn[0] + 2 * A[0]) / 3.0 , (nextOn[1] + 2 * A[1]) / 3.0)
						pathContour.curveToPoint_controlPoint1_controlPoint2_(nextOn, antenne1, antenne2)
						onCurve = nextOn
					nextOn = segment[-1]
					A = segment[-2]
					antenne1 = ((onCurve[0] + 2 * A[0]) / 3.0 , (onCurve[1] + 2 * A[1]) / 3.0)
					antenne2 = ((nextOn[0] + 2 * A[0]) / 3.0 , (nextOn[1] + 2 * A[1]) / 3.0)
					pathContour.curveToPoint_controlPoint1_controlPoint2_(nextOn, antenne1, antenne2)


			start = end+1

			NSColor.colorWithRed_green_blue_alpha_(255/255, 75/255, 240/255, 1).set()
			pathContour.setLineWidth_(scale*2)
			pathContour.stroke()

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
			for contour in self.g:
				for point in contour.points:
					if point.naked().uniqueID == pointID:
						x = point.x
						y = point.y
		elif pointID == 'lsb':
			x, y = 0, 0
		elif pointID == 'rsb':
			x, y = self.g.width, 0

		self.drawArrowAtPoint(scale, 10, angle, x, y)
		self.drawArrowAtPoint(scale, 10, angle+180, x, y)

		# compute x, y
		if cmdIndex not in self.commandLabelPos:
		    self.commandLabelPos[cmdIndex] = (x + 10, y - 10)

		self.drawTextAtPoint('A', x + 10, y - 10, NSColor.blueColor())

	def drawLink(self, scale, startPoint, endPoint, stemName, cmdIndex):
	 	
	 	start_end_diff = difference(startPoint, endPoint)
	 	dx, dy = start_end_diff[0]/2, start_end_diff[1]/2
	 	angle = getAngle((startPoint[0], startPoint[1]), (endPoint[0], endPoint[1])) + math.radians(90)
	 	offcurve1 = (startPoint[0] - dx + math.cos(angle)*10, startPoint[1] - dy + math.sin(angle)*10)

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
	 	path.curveToPoint_controlPoint1_controlPoint2_((endPoint_x,  endPoint_y), (offcurve1), (offcurve1) )
	 
		NSColor.colorWithRed_green_blue_alpha_(0/255, 0/255, 0/255, 1).set()
		path.setLineWidth_(scale)
		pathArrow.fill()
		path.stroke()

		# compute x, y
		if cmdIndex not in self.commandLabelPos:
		    self.commandLabelPos[cmdIndex] = (offcurve1[0], offcurve1[1])

		if stemName == None:
			self.drawTextAtPoint('S', offcurve1[0], offcurve1[1], NSColor.blackColor())
		else:
			self.drawTextAtPoint(stemName, offcurve1[0], offcurve1[1], NSColor.blackColor())


	def drawDoubleLink(self, scale, startPoint, endPoint, stemName, cmdIndex):
	 	
	 	start_end_diff = difference(endPoint, startPoint)
	 	dx, dy = -start_end_diff[1]/5, start_end_diff[0]/5
	 	offcurve1 = (startPoint[0] + dx, startPoint[1] + dy)
		offcurve2 = (endPoint[0] + dx, endPoint[1] + dy)

		path = NSBezierPath.bezierPath()
	 	path.moveToPoint_((startPoint[0], startPoint[1]))
	 	path.curveToPoint_controlPoint1_controlPoint2_((endPoint[0],  endPoint[1]), (offcurve1), (offcurve2) )

		NSColor.colorWithRed_green_blue_alpha_(0/255, 0/255, 215/255, 1).set()
		path.setLineWidth_(scale)
		path.stroke()

		# compute x, y
		if cmdIndex not in self.commandLabelPos:
		    self.commandLabelPos[cmdIndex] = ((offcurve1[0] + offcurve2[0])/2, (offcurve1[1] + offcurve2[1])/2 )

		if stemName == None:
			self.drawTextAtPoint('D', (offcurve1[0] + offcurve2[0])/2, (offcurve1[1] + offcurve2[1])/2, NSColor.blueColor())
		else:
			self.drawTextAtPoint(stemName, (offcurve1[0] + offcurve2[0])/2, (offcurve1[1] + offcurve2[1])/2, NSColor.blueColor())

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
	 	path.curveToPoint_controlPoint1_controlPoint2_((middlePoint[0],  middlePoint[1]), (center1), (center1) )
	 	path.curveToPoint_controlPoint1_controlPoint2_((endPoint[0],  endPoint[1]), (center2), (center2) )
	 
		NSColor.colorWithRed_green_blue_alpha_(0/255, 255/255, 0/255, 1).set()
		path.setLineWidth_(scale)
		path.stroke()

		# compute x, y
		if cmdIndex not in self.commandLabelPos:
		    self.commandLabelPos[cmdIndex] = (middlePoint[0] + 10*scale, middlePoint[1] - 10*scale)

		self.drawTextAtPoint('I', middlePoint[0] + 10*scale, middlePoint[1] - 10*scale, NSColor.greenColor())

	def drawDelta(self, scale, point, value):

		path = NSBezierPath.bezierPath()
	 	path.moveToPoint_((point[0], point[1]))
	 	path.lineToPoint_((point[0]+ (value[0]/8)*self.pitch, point[1] + (value[1]/8)*self.pitch))

	 	NSColor.colorWithRed_green_blue_alpha_(255/255, 128/255, 0/255, 1).set()
		path.setLineWidth_(scale)
		path.stroke()

	def drawSideBearings(self, scale, face):
		if len(face.glyph.outline.contours) == 0:
			return

		xPos = self.pitch*face.glyph.advance.x/64
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


	def drawBitmapMono(self, pitch, advance, height, alpha, face):
		if face == None:
			return
		glyph = face.glyph
		bm = glyph.bitmap
		numBytes = bm.rows * bm.pitch
		if numBytes == 0:
			return
		buf = allocateBuffer(numBytes)
		ftBuffer = bm._FT_Bitmap.buffer
		for i in range(numBytes):
			buf[i] = ftBuffer[i]

		#provider = Quartz.CGDataProviderCreateWithData(None, bm._FT_Bitmap.buffer, numBytes, None)
		provider = Quartz.CGDataProviderCreateWithData(None, buf, numBytes, None)

		colorspace = Quartz.CGColorSpaceCreateDeviceGray()
		cgimg = Quartz.CGImageCreate(
                         bm.width,
                         bm.rows,
                         1, # bit per component
                         1, # size_t bitsPerPixel,
                         bm.pitch, # size_t bytesPerRow,
                         colorspace, # CGColorSpaceRef colorspace,
                         Quartz.kCGBitmapByteOrderDefault, # CGBitmapInfo bitmapInfo,
                         provider, # CGDataProviderRef provider,
                         None, # const CGFloat decode[],
                         False, # bool shouldInterpolate,
                         Quartz.kCGRenderingIntentDefault # CGColorRenderingIntent intent
                         )
		destRect = Quartz.CGRectMake(glyph.bitmap_left*pitch + advance, (glyph.bitmap_top-bm.rows)*pitch + height, bm.width*pitch, bm.rows*pitch)
		
		context = NSGraphicsContext.currentContext()
		if alpha < 1:
			Quartz.CGContextSetAlpha(context.graphicsPort(), alpha)
		Quartz.CGContextSetBlendMode(context.graphicsPort(), Quartz.kCGBlendModeDifference)
		Quartz.CGContextSetInterpolationQuality(context.graphicsPort(), Quartz.kCGInterpolationNone)
		Quartz.CGContextDrawImage(context.graphicsPort(),
                               destRect, cgimg )
		Quartz.CGContextSetAlpha(context.graphicsPort(), 1)
		Quartz.CGContextSetBlendMode(context.graphicsPort(), Quartz.kCGBlendModeNormal)

	def drawBitmapGray(self, pitch, advance, height, alpha, face):
		glyph = face.glyph
		bm = glyph.bitmap
		numBytes = bm.rows * bm.pitch
		if numBytes == 0:
			return
		buf = allocateBuffer(numBytes)
		ftBuffer = bm._FT_Bitmap.buffer
		for i in range(numBytes):
			buf[i] = ftBuffer[i]

		provider = Quartz.CGDataProviderCreateWithData(None, buf, numBytes, None)

		colorspace = Quartz.CGColorSpaceCreateDeviceGray()
		cgimg = Quartz.CGImageCreate(
                         bm.width,
                         bm.rows,
                         8, # bit per component
                         8, # size_t bitsPerPixel,
                         bm.pitch, # size_t bytesPerRow,
                         colorspace, # CGColorSpaceRef colorspace,
                         Quartz.kCGBitmapByteOrderDefault, # CGBitmapInfo bitmapInfo,
                         provider, # CGDataProviderRef provider,
                         None, # const CGFloat decode[],
                         False, # bool shouldInterpolate,
                         Quartz.kCGRenderingIntentDefault # CGColorRenderingIntent intent
                         )
		destRect = Quartz.CGRectMake(glyph.bitmap_left*pitch + advance, (glyph.bitmap_top-bm.rows)*pitch + height, bm.width*pitch, bm.rows*pitch)
		
		context = NSGraphicsContext.currentContext()
		if alpha < 1:
			Quartz.CGContextSetAlpha(context.graphicsPort(), alpha)
		Quartz.CGContextSetBlendMode(context.graphicsPort(), Quartz.kCGBlendModeDifference)
		Quartz.CGContextSetInterpolationQuality(context.graphicsPort(), Quartz.kCGInterpolationNone)
		Quartz.CGContextDrawImage(context.graphicsPort(),
                               destRect, cgimg )
		Quartz.CGContextSetAlpha(context.graphicsPort(), 1)
		Quartz.CGContextSetBlendMode(context.graphicsPort(), Quartz.kCGBlendModeNormal)

	def drawBitmapSubPixelColor(self, pitch, advance, height, alpha, face):
		glyph = face.glyph
		bm = glyph.bitmap
		pixelWidth = int(bm.width/3)
		numBytes = 4 * bm.rows * pixelWidth
		if numBytes == 0:
			return
		buf = allocateBuffer(numBytes)
		ftBuffer = bm._FT_Bitmap.buffer
		pos = 0
		for i in range(bm.rows):
			source = bm.pitch * i
			for j in range(pixelWidth):
				ftSub = ftBuffer[source:source+3];
				gray = (1.0 - 0.4) * sum([x*y for x,y in zip([0.3086, 0.6094, 0.0820], ftSub)])
				buf[pos:pos+3] = [int(0.4 * x + gray) for x in ftSub]
				buf[pos+3] = 0
				pos += 4
				source += 3

		provider = Quartz.CGDataProviderCreateWithData(None, buf, numBytes, None)

		colorspace = Quartz.CGColorSpaceCreateDeviceRGB()
		cgimg = Quartz.CGImageCreate(
			 pixelWidth,
                         bm.rows,
                         8, # bit per component
                         32, # size_t bitsPerPixel,
                         4 * pixelWidth, # size_t bytesPerRow,
                         colorspace, # CGColorSpaceRef colorspace,
                         Quartz.kCGImageAlphaNone, # CGBitmapInfo bitmapInfo,
                         #Quartz.kCGBitmapByteOrderDefault, # CGBitmapInfo bitmapInfo,
                         provider, # CGDataProviderRef provider,
                         None, # const CGFloat decode[],
                         False, # bool shouldInterpolate,
                         Quartz.kCGRenderingIntentDefault # CGColorRenderingIntent intent
                         )
		destRect = Quartz.CGRectMake(glyph.bitmap_left*pitch + advance, (glyph.bitmap_top-bm.rows)*pitch + height, pixelWidth*pitch, bm.rows*pitch)
		
		context = NSGraphicsContext.currentContext()
		if alpha < 1:
			Quartz.CGContextSetAlpha(context.graphicsPort(), alpha)
		Quartz.CGContextSetBlendMode(context.graphicsPort(), Quartz.kCGBlendModeDifference)
		Quartz.CGContextSetInterpolationQuality(context.graphicsPort(), Quartz.kCGInterpolationNone)
		Quartz.CGContextDrawImage(context.graphicsPort(), destRect, cgimg )
		Quartz.CGContextSetAlpha(context.graphicsPort(), 1)
		Quartz.CGContextSetBlendMode(context.graphicsPort(), Quartz.kCGBlendModeNormal)

	def drawPreviewWindow(self):
		if self.ready == False:
			return
		if CurrentGlyph() == None:
			return

		self.advance = 10
		startgname = False
		gname = ''
		gnametemp = ''
		count = 0
		for c in self.previewWindow.previewString:
			gname = ''
			count += 1
			if c != '@' and c != '/' and startgname != True:
				unicodeGlyph = ord(c)
				gname = getGlyphNameByUnicode(self.unicodeToNameDict, unicodeGlyph)
			elif c == '@':
				gname = CurrentGlyph().name
			elif c =='/' or c == ' ' :
				if gnametemp in self.fullTempUFO:
					gname = gnametemp
					gnametemp = ''
				if startgname != True:
					startgname = True
				else:
					startgname = False
			elif startgname == True:
				gnametemp += c

			if gname not in self.fullTempUFO:
				continue
			self.loadFaceGlyph(gname, self.PPM_Size)
			if self.bitmapPreviewSelection == 'Monochrome':
				self.drawBitmapMono(1, self.advance, 50, 1, self.face)
			elif self.bitmapPreviewSelection == 'Grayscale':
				self.drawBitmapGray(1, self.advance, 50, 1, self.face)
			elif self.bitmapPreviewSelection == 'Subpixel':
				self.drawBitmapSubPixelColor(1, self.advance, 50, 1, self.face)
			
			self.advance += int(self.face.glyph.advance.x/64)

		self.advance = 10

		for size in range(9, 48, 1):
			gname = CurrentGlyph().name
			sizedpitch = self.UPM/size
			self.loadFaceGlyph(gname, size)
			if self.bitmapPreviewSelection == 'Monochrome':
				self.drawBitmapMono(1, self.advance, 100, 1, self.face)
			elif self.bitmapPreviewSelection == 'Grayscale':
				self.drawBitmapGray(1, self.advance, 100, 1, self.face)
			elif self.bitmapPreviewSelection == 'Subpixel':
				self.drawBitmapSubPixelColor(1, self.advance, 100, 1, self.face)
			
			self.advance += int(self.face.glyph.advance.x/64) + 5


	def drawBackground(self, scale):
		if self.g == None:
			return
		
		self.loadFaceGlyph(CurrentGlyph().name, self.PPM_Size)
		if self.bitmapPreviewSelection == 'Monochrome':
			self.drawBitmapMono(self.pitch, 0, 0, .4, self.face)
		elif self.bitmapPreviewSelection == 'Grayscale':
			self.drawBitmapGray(self.pitch, 0, 0, .4, self.face)
		elif self.bitmapPreviewSelection == 'Subpixel':
			self.drawBitmapSubPixelColor(self.pitch, 0, 0, .4, self.face)

		r = 5*scale
		self.drawDiscAtPoint(r, 0, 0)
		self.drawDiscAtPoint(r, self.g.width, 0)

		self.drawGrid(scale, self.pitch)
		self.drawZones(scale)

		self.drawOutline(scale, self.face)
		self.drawSideBearings(scale, self.face)

	def draw(self, scale):
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
					if cmd_code in ['alignv', 'alignt', 'alignb'] and self.centralWindow.selectedAxis == 'Y':
						self.drawAlign(scale, cmd_pt, angle, cmdIndex)
					elif cmd_code == 'alignh' and self.centralWindow.selectedAxis == 'X':
						self.drawAlign(scale, cmd_pt, angle, cmdIndex)
				elif cmd_code in ['alignv', 'alignt', 'alignb'] and self.centralWindow.selectedAxis == 'Y':
					self.drawAlign(scale, self.pointNameToUniqueID[cmd_pt], angle, cmdIndex)
				elif cmd_code == 'alignh' and self.centralWindow.selectedAxis == 'X':
					self.drawAlign(scale, self.pointNameToUniqueID[cmd_pt], angle, cmdIndex)

			if cmd_code in ['singleh', 'singlev', 'doubleh', 'doublev']:
				if cmd_pt1 == 'lsb':
					startPoint = (0, 0)
				elif cmd_pt1== 'rsb':
					startPoint = (0, self.g.width)
				else:
					startPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt1]]

				if cmd_pt2 == 'lsb':
					endPoint = (0, 0)
				elif cmd_pt2 == 'rsb':
					endPoint = (self.g.width, 0)
				else:
					endPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt2]]

				if cmd_code in ['doubleh', 'doublev']:
					if self.centralWindow.selectedAxis == 'X' and cmd_code == 'doubleh':
						self.drawDoubleLink(scale, startPoint, endPoint, cmd_stem, cmdIndex)
					elif self.centralWindow.selectedAxis == 'Y' and cmd_code == 'doublev':
						self.drawDoubleLink(scale, startPoint, endPoint, cmd_stem, cmdIndex)
				elif self.centralWindow.selectedAxis == 'X' and cmd_code == 'singleh':
					self.drawLink(scale, startPoint, endPoint, cmd_stem, cmdIndex)
				elif self.centralWindow.selectedAxis == 'Y' and cmd_code == 'singlev':
					self.drawLink(scale, startPoint, endPoint, cmd_stem, cmdIndex)

			if cmd_code in ['interpolateh', 'interpolatev']:

				if cmd_pt == 'lsb':
					middlePoint = (0, 0)
				elif cmd_pt== 'rsb':
					middlePoint = (0, self.g.width)
				else:
					middlePoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt]]

				if cmd_pt1 == 'lsb':
					startPoint = (0, 0)
				elif cmd_pt1== 'rsb':
					startPoint = (0, self.g.width)
				else:
					startPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt1]]

				if cmd_pt2 == 'lsb':
					endPoint = (0, 0)
				elif cmd_pt2 == 'rsb':
					endPoint = (self.g.width, 0)
				else:
					endPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt2]]

				if self.centralWindow.selectedAxis == 'X' and cmd_code == 'interpolateh':
					self.drawInterpolate(scale, startPoint, endPoint, middlePoint, cmdIndex)
				elif self.centralWindow.selectedAxis == 'Y' and cmd_code == 'interpolatev':
					self.drawInterpolate(scale, startPoint, endPoint, middlePoint, cmdIndex)

			if cmd_code in ['mdeltah', 'mdeltav', 'fdeltah', 'fdeltav']:

				if cmd_pt == 'lsb':
					point = (0, 0)
				elif cmd_pt== 'rsb':
					point = (self.g.width, 0)
				else:
					point = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[cmd_pt]]

				if cmd_code[-1] == 'h':
					value = (int(c['delta']), 0)
				elif cmd_code[-1] == 'v':
					value = (0, int(c['delta']))
				else:
					value = 0

				if int(self.PPM_Size) in range(int(c['ppm1']), int(c['ppm2'])+1, 1):
					if self.centralWindow.selectedAxis == 'X' and cmd_code in ['mdeltah', 'fdeltah']:
						self.drawDelta(scale, point, value)
					elif self.centralWindow.selectedAxis == 'Y' and cmd_code in ['mdeltav', 'fdeltav']:
						self.drawDelta(scale, point, value)




class centralWindow(object):
	def __init__(self, f, TTHToolInstance):
		self.f = f
		self.TTHToolInstance = TTHToolInstance
		self.wCentral = FloatingWindow((10, 30, 200, 600), "Central", closable = False)

		self.PPMSizesList = ['9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', 
							'21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
							'31', '32', '33', '34', '35', '36', '37', '38', '39', '40',
							'41', '42', '43', '44', '45', '46', '47', '48', '60', '72' ]
		self.axisList = ['X', 'Y']
		self.selectedAxis = 'X'

		self.BitmapPreviewList = ['Monochrome', 'Grayscale', 'Subpixel']

		self.wCentral.PPEMSizeText= TextBox((10, 10, 70, 14), "ppEm Size:", sizeStyle = "small")
		
		self.wCentral.PPEMSizeEditText = EditText((110, 8, 30, 19), sizeStyle = "small", 
                            callback=self.PPEMSizeEditTextCallback)

		self.wCentral.PPEMSizeEditText.set(self.TTHToolInstance.PPM_Size)
		
		self.wCentral.PPEMSizePopUpButton = PopUpButton((150, 10, 40, 14),
                              self.PPMSizesList, sizeStyle = "small",
                              callback=self.PPEMSizePopUpButtonCallback)
		self.wCentral.PPEMSizePopUpButton.set(0)

		self.wCentral.BitmapPreviewText= TextBox((10, 30, 70, 14), "Preview:", sizeStyle = "small")
		self.wCentral.BitmapPreviewPopUpButton = PopUpButton((90, 30, 100, 14),
                              self.BitmapPreviewList, sizeStyle = "small",
                              callback=self.BitmapPreviewPopUpButtonCallback)

		self.wCentral.AxisText= TextBox((10, 50, 70, 14), "Axis:", sizeStyle = "small")
		self.wCentral.AxisPopUpButton = PopUpButton((150, 50, 40, 14),
                              self.axisList, sizeStyle = "small",
                              callback=self.AxisPopUpButtonCallback)

		self.wCentral.ReadTTProgramButton = SquareButton((10, 80, -10, 22), "Read Glyph TT program", sizeStyle = 'small', 
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
		try:
			newValue = int(sender.get())
		except ValueError:
			newValue = 9
			sender.set(9)
		self.TTHToolInstance.PPM_Size = newValue
		self.TTHToolInstance.pitch = int(self.TTHToolInstance.UPM / int(self.TTHToolInstance.PPM_Size))
		self.TTHToolInstance.loadFaceGlyph(self.TTHToolInstance.g.name,  self.TTHToolInstance.PPM_Size)
		UpdateCurrentGlyphView()
		self.TTHToolInstance.previewWindow.view.setNeedsDisplay_(True)

	def PPEMSizePopUpButtonCallback(self, sender):
		if self.TTHToolInstance.g == None:
			return
		self.TTHToolInstance.PPM_Size = self.PPMSizesList[sender.get()]
		self.wCentral.PPEMSizeEditText.set(self.TTHToolInstance.PPM_Size)
		self.TTHToolInstance.pitch = int(self.TTHToolInstance.UPM / int(self.TTHToolInstance.PPM_Size))
		self.TTHToolInstance.loadFaceGlyph(self.TTHToolInstance.g.name, self.TTHToolInstance.PPM_Size)
		UpdateCurrentGlyphView()
		self.TTHToolInstance.previewWindow.view.setNeedsDisplay_(True)

	def BitmapPreviewPopUpButtonCallback(self, sender):
		if self.TTHToolInstance.g == None:
			return
		self.TTHToolInstance.bitmapPreviewSelection = self.BitmapPreviewList[sender.get()]
		self.TTHToolInstance.loadFaceGlyph(self.TTHToolInstance.g.name,  self.TTHToolInstance.PPM_Size)
		UpdateCurrentGlyphView()
		self.TTHToolInstance.previewWindow.view.setNeedsDisplay_(True)

	def AxisPopUpButtonCallback(self, sender):
		self.selectedAxis = self.axisList[sender.get()]
		UpdateCurrentGlyphView()

	def ReadTTProgramButtonCallback(self, sender):
		FLTTProgram = self.TTHToolInstance.readGlyphFLTTProgram(self.TTHToolInstance.g)
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
		self.f = f
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


installTool(TTHTool())
