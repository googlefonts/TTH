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
			if int(unicodeGlyph, 16) not in unicodeToNameDict.keys():
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

	def becomeActive(self):
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
		self.pointNameToUniqueID = self.makePointNameToUniqueIDDict(self.g)
		self.pointUniqueIDToCoordinates = self.makePointUniqueIDToCoordinatesDict(self.g)
		self.generateMiniTempFont()
		self.face = freetype.Face(self.fulltempfontpath)
		self.ready = True

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

		if 'com.robofont.robohint.cvt ' in CurrentFont().lib.keys():
			tempFont.lib['com.robofont.robohint.cvt '] = CurrentFont().lib['com.robofont.robohint.cvt ']
		if 'com.robofont.robohint.prep' in CurrentFont().lib.keys():
			tempFont.lib['com.robofont.robohint.prep'] = CurrentFont().lib['com.robofont.robohint.prep']
		if 'com.robofont.robohint.fpgm' in CurrentFont().lib.keys():
			tempFont.lib['com.robofont.robohint.fpgm'] = CurrentFont().lib['com.robofont.robohint.fpgm']
		

		tempFont.newGlyph(self.g.name)
		tempFont[self.g.name] = tempGlyph
		if 'com.robofont.robohint.assembly' in self.g.lib.keys():
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
		if 'com.fontlab.ttprogram' not in g.lib.keys():
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

				if 'stem' in TTHCommand.keys():
					stemCV = tt_tables.stem_to_cvt[TTHCommand['stem']]
					double = [
							'PUSHW[ ] ' + str(point2Index) + ' ' +  str(stemCV) + ' ' + str(point1Index) + ' 4',
          					'CALL[ ]'
							]
				elif 'round' in TTHCommand.keys():
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
				if 'align' in TTHCommand.keys():
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

				if 'stem' in TTHCommand.keys():
					stemCV = tt_tables.stem_to_cvt[TTHCommand['stem']]
					singleLink2 = [
									'PUSHW[ ] ' + str(point2Index) + ' ' + str(stemCV),
									'MIRP[10100]'
									]
					RP1 = RP0 = RP2 = point2Index
					if point2UniqueID not in touchedPoints:
						touchedPoints.append(point2UniqueID)

				elif 'round' in TTHCommand.keys():
					singleLink2 = [
									'PUSHW[ ] ' + str(point2Index),
									'MDRP[11100]'
									]
					RP1 = RP0 = RP2 = point2Index
					if point2UniqueID not in touchedPoints:
						touchedPoints.append(point2UniqueID)

				elif 'align' in TTHCommand.keys():
					if TTHCommand['align'] == 'round':
						singleLink2 = [
										'PUSHW[ ] ' + str(point2Index),
										'MDRP[10100]'
										]
						RP1 = RP0 = RP2 = point2Index
						if point2UniqueID not in touchedPoints:
							touchedPoints.append(point2UniqueID)
				else:
					singleLink2 = [
									'PUSHW[ ] ' + str(point2Index),
									'MDRP[10000]'
									]
					RP1 = RP0 = RP2 = point2Index
					if point2UniqueID not in touchedPoints:
						touchedPoints.append(point2UniqueID)

				singleLink.extend(singleLink2)

				if TTHCommand['code'] == 'singleh':
					x_instructions.extend(singleLink)
				elif TTHCommand['code'] == 'singlev':
					y_instructions.extend(singleLink)

		##############################	
		assembly.extend(x_instructions)
		assembly.extend(y_instructions)

		assembly.extend(['IUP[0]', 'IUP[1]'])
		g.lib['com.robofont.robohint.assembly'] = assembly

	def getGlyphIndexByName(self, glyphName):
		try:
			return self.indexOfGlyphNames[glyphName]
		except:
			return None

	def loadFaceGlyph(self, glyphName):
		if self.face == None:
			return
		self.face.set_pixel_sizes(int(self.PPM_Size), int(self.PPM_Size))
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
			pathX = NSBezierPath.bezierPath()
			pathX.moveToPoint_((-5000, yPos))
			pathX.lineToPoint_((5000, yPos))
			NSColor.colorWithRed_green_blue_alpha_(0, 0, 0, 0.1).set()
			pathX.setLineWidth_(scale)
			pathX.stroke()
		for yPos in range(0, -5000, -int(pitch)):
			pathX = NSBezierPath.bezierPath()
			pathX.moveToPoint_((-5000, yPos))
			pathX.lineToPoint_((5000, yPos))
			NSColor.colorWithRed_green_blue_alpha_(0, 0, 0, 0.1).set()
			pathX.setLineWidth_(scale)
			pathX.stroke()

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

			NSColor.colorWithRed_green_blue_alpha_(255/255, 75/255, 240/255, .5).set()
			pathContour.setLineWidth_(scale*2)
			pathContour.stroke()

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

		NSColor.colorWithRed_green_blue_alpha_(0/255, 180/255, 50/255, 1).set()
		pathArrow.setLineWidth_(scale)
		pathArrow.fill()
		NSColor.colorWithRed_green_blue_alpha_(1, 1, 1, .5).set()
		pathArrow.stroke()

	def drawDiscAtPoint(self, r, x, y):
		NSColor.colorWithRed_green_blue_alpha_(1, 0, 0, 1).set()
		NSBezierPath.bezierPathWithOvalInRect_(((x-r, y-r), (r*2, r*2))).fill()

	def drawAlign(self, scale, pointID, angle):

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

	def drawLink(self, scale, startPoint, endPoint):
	 	
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

	def drawDoubleLink(self, scale, startPoint, endPoint):
	 	
	 	start_end_diff = difference(endPoint, startPoint)
	 	dx, dy = -start_end_diff[1]/5, start_end_diff[0]/5
	 	offcurve1 = (startPoint[0] + dx, startPoint[1] + dy)
		offcurve2 = (endPoint[0] + dx, endPoint[1] + dy)

		path = NSBezierPath.bezierPath()
	 	path.moveToPoint_((startPoint[0], startPoint[1]))
	 	path.curveToPoint_controlPoint1_controlPoint2_((endPoint[0],  endPoint[1]), (offcurve1), (offcurve2) )

	 
		NSColor.colorWithRed_green_blue_alpha_(0/255, 215/255, 0/255, 1).set()
		path.setLineWidth_(scale)
		path.stroke()

	def drawInterpolate(self, scale, startPoint, endPoint, middlePoint):

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
	 
		NSColor.colorWithRed_green_blue_alpha_(255/255, 0/255, 0/255, 1).set()
		path.setLineWidth_(scale)
		path.stroke()

	def drawBitmapMono(self, pitch, advance, height, alpha, face):
		if face == None:
			return
		pyBuffer = face.glyph.bitmap.buffer
		if len(pyBuffer) == 0:
			return

		colorspace = Quartz.CGColorSpaceCreateDeviceGray()
		buf = allocateBuffer(len(pyBuffer))
		for i in range(len(pyBuffer)):
			buf[i] = pyBuffer[i]^255

		provider = Quartz.CGDataProviderCreateWithData(None, buf, face.glyph.bitmap.rows*face.glyph.bitmap.pitch, None)

		cgimg = Quartz.CGImageCreate(
                         face.glyph.bitmap.width,
                         face.glyph.bitmap.rows,
                         1, # bit per component
                         1, # size_t bitsPerPixel,
                         face.glyph.bitmap.pitch, # size_t bytesPerRow,
                         colorspace, # CGColorSpaceRef colorspace,
                         Quartz.kCGBitmapByteOrderDefault, # CGBitmapInfo bitmapInfo,
                         provider, # CGDataProviderRef provider,
                         None, # const CGFloat decode[],
                         False, # bool shouldInterpolate,
                         Quartz.kCGRenderingIntentDefault # CGColorRenderingIntent intent
                         )
		destRect = Quartz.CGRectMake(face.glyph.bitmap_left*pitch + advance, (face.glyph.bitmap_top-face.glyph.bitmap.rows)*pitch + height, face.glyph.bitmap.width*pitch, face.glyph.bitmap.rows*pitch)
		
		context = NSGraphicsContext.currentContext()
		if alpha < 1:
			Quartz.CGContextSetAlpha(context.graphicsPort(), alpha)
		Quartz.CGContextSetBlendMode(context.graphicsPort(), Quartz.kCGBlendModeMultiply)
		Quartz.CGContextSetInterpolationQuality(context.graphicsPort(), Quartz.kCGInterpolationNone)
		Quartz.CGContextDrawImage(context.graphicsPort(),
                               destRect, cgimg )
		Quartz.CGContextSetAlpha(context.graphicsPort(), 1)
		Quartz.CGContextSetBlendMode(context.graphicsPort(), Quartz.kCGBlendModeNormal)

	def drawBitmapGray(self, pitch, advance, height, alpha, face):
		pyBuffer = face.glyph.bitmap.buffer
		if len(pyBuffer) == 0:
			return

		colorspace = Quartz.CGColorSpaceCreateDeviceGray()
		buf = allocateBuffer(len(pyBuffer))
		for i in range(len(pyBuffer)):
			buf[i] = 255 - pyBuffer[i]

		provider = Quartz.CGDataProviderCreateWithData(None, buf, face.glyph.bitmap.rows*face.glyph.bitmap.pitch, None)

		cgimg = Quartz.CGImageCreate(
                         face.glyph.bitmap.width,
                         face.glyph.bitmap.rows,
                         8, # bit per component
                         8, # size_t bitsPerPixel,
                         face.glyph.bitmap.pitch, # size_t bytesPerRow,
                         colorspace, # CGColorSpaceRef colorspace,
                         Quartz.kCGBitmapByteOrderDefault, # CGBitmapInfo bitmapInfo,
                         provider, # CGDataProviderRef provider,
                         None, # const CGFloat decode[],
                         False, # bool shouldInterpolate,
                         Quartz.kCGRenderingIntentDefault # CGColorRenderingIntent intent
                         )
		destRect = Quartz.CGRectMake(face.glyph.bitmap_left*pitch + advance, (face.glyph.bitmap_top-face.glyph.bitmap.rows)*pitch + height, face.glyph.bitmap.width*pitch, face.glyph.bitmap.rows*pitch)
		
		context = NSGraphicsContext.currentContext()
		if alpha < 1:
			Quartz.CGContextSetAlpha(context.graphicsPort(), alpha)
		Quartz.CGContextSetBlendMode(context.graphicsPort(), Quartz.kCGBlendModeMultiply)
		Quartz.CGContextSetInterpolationQuality(context.graphicsPort(), Quartz.kCGInterpolationNone)
		Quartz.CGContextDrawImage(context.graphicsPort(),
                               destRect, cgimg )
		Quartz.CGContextSetAlpha(context.graphicsPort(), 1)
		Quartz.CGContextSetBlendMode(context.graphicsPort(), Quartz.kCGBlendModeNormal)

	def drawBitmapSubPixelColor(self, pitch, advance, height, alpha, face):
		pyBuffer = face.glyph.bitmap.buffer
		if len(pyBuffer) == 0:
			return
		data = []
		for i in range(face.glyph.bitmap.rows):
			data.append(pyBuffer[i*face.glyph.bitmap.pitch:i*face.glyph.bitmap.pitch+face.glyph.bitmap.width])
		
		row_len = len(data[0])
		rect = NSMakeRect(face.glyph.bitmap_left * pitch + advance,
			face.glyph.bitmap_top * pitch - pitch + height,
			pitch, pitch)
		for row_index in range(len(data)):
			for pix_index in range(0, row_len, 3):
				red = 255 - data[row_index][pix_index]
				green = 255 - data[row_index][pix_index+1]
				blue = 255 - data[row_index][pix_index+2]
				gray = red * 0.3086 + green * 0.6094 + blue * 0.0820
				s = 0.4
				red = (red * s + gray * (1-s)) / 255
				green = (green * s + gray * (1-s)) / 255
				blue = (blue * s + gray * (1-s)) / 255
				NSColor.colorWithRed_green_blue_alpha_(red, green, blue, alpha).set()
				NSBezierPath.fillRect_(rect)
				rect.origin.x += pitch
			rect.origin.x -= int(row_len / 3) * pitch # on rembobine
			rect.origin.y -= pitch

	def drawPreview(self):
		if self.ready == False:
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
				if gnametemp in self.fullTempUFO.keys():
					gname = gnametemp
					gnametemp = ''
				if startgname != True:
					startgname = True
				else:
					startgname = False
			elif startgname == True:
				gnametemp += c

			if gname not in self.fullTempUFO.keys():
				continue
			self.loadFaceGlyph(gname)
			if self.bitmapPreviewSelection == 'Monochrome':
				self.drawBitmapMono(1, self.advance, 50, 1, self.face)
			elif self.bitmapPreviewSelection == 'Grayscale':
				self.drawBitmapGray(1, self.advance, 50, 1, self.face)
			elif self.bitmapPreviewSelection == 'Subpixel':
				self.drawBitmapSubPixelColor(1, self.advance, 50, 1, self.face)
			
			self.advance += self.f[gname].width/self.pitch


	def drawBackground(self, scale):
		if self.g == None:
			return
		
		self.loadFaceGlyph(CurrentGlyph().name)
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

	def draw(self, scale):
		for c in self.glyphTTHCommands:
			if c['code'] == 'alignh':
				if c['point'] == 'lsb' or c['point'] == 'rsb':
					self.drawAlign(scale, c['point'], 180)
				else:
					self.drawAlign(scale, self.pointNameToUniqueID[c['point']], 180)
			if c['code'] == 'alignv' or c['code'] == 'alignt' or c['code'] == 'alignb' :
				if c['point'] == 'lsb' or c['point'] == 'rsb':
					self.drawAlign(scale, c['point'], 90)
				else:
					self.drawAlign(scale, self.pointNameToUniqueID[c['point']], 90)

			if c['code'] == 'singleh' or c['code'] == 'singlev':
				if c['point1'] == 'lsb':
					startPoint = (0, 0)
				elif c['point1']== 'rsb':
					startPoint = (0, self.g.width)
				else:
					startPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[c['point1']]]

				if c['point2'] == 'lsb':
					endPoint = (0, 0)
				elif c['point2'] == 'rsb':
					endPoint = (self.g.width, 0)
				else:
					endPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[c['point2']]]

				self.drawLink(scale, startPoint, endPoint)

			if c['code'] == 'doubleh' or c['code'] == 'doublev':
				if c['point1'] == 'lsb':
					startPoint = (0, 0)
				elif c['point1']== 'rsb':
					startPoint = (0, self.g.width)
				else:
					startPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[c['point1']]]

				if c['point2'] == 'lsb':
					endPoint = (0, 0)
				elif c['point2'] == 'rsb':
					endPoint = (self.g.width, 0)
				else:
					endPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[c['point2']]]
				self.drawDoubleLink(scale, startPoint, endPoint)

			if c['code'] == 'interpolateh' or c['code'] == 'interpolatev':

				if c['point'] == 'lsb':
					middlePoint = (0, 0)
				elif c['point']== 'rsb':
					middlePoint = (0, self.g.width)
				else:
					middlePoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[c['point']]]

				if c['point1'] == 'lsb':
					startPoint = (0, 0)
				elif c['point1']== 'rsb':
					startPoint = (0, self.g.width)
				else:
					startPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[c['point1']]]

				if c['point2'] == 'lsb':
					endPoint = (0, 0)
				elif c['point2'] == 'rsb':
					endPoint = (self.g.width, 0)
				else:
					endPoint = self.pointUniqueIDToCoordinates[self.pointNameToUniqueID[c['point2']]]

				self.drawInterpolate(scale, startPoint, endPoint, middlePoint)



class centralWindow(object):
	def __init__(self, f, TTHToolInstance):
		self.f = f
		self.TTHToolInstance = TTHToolInstance
		self.wCentral = FloatingWindow((10, 30, 200, 600), "Central", closable = False)

		self.PPMSizesList = ['9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', 
							'21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
							'31', '32', '33', '34', '35', '36', '37', '38', '39', '40',
							'41', '42', '43', '44', '45', '46', '47', '48', '60', '72' ]

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
		self.TTHToolInstance.loadFaceGlyph(self.TTHToolInstance.g.name)
		UpdateCurrentGlyphView()
		self.TTHToolInstance.previewWindow.view.setNeedsDisplay_(True)

	def PPEMSizePopUpButtonCallback(self, sender):
		if self.TTHToolInstance.g == None:
			return
		self.TTHToolInstance.PPM_Size = self.PPMSizesList[sender.get()]
		self.wCentral.PPEMSizeEditText.set(self.TTHToolInstance.PPM_Size)
		self.TTHToolInstance.pitch = int(self.TTHToolInstance.UPM / int(self.TTHToolInstance.PPM_Size))
		self.TTHToolInstance.loadFaceGlyph(self.TTHToolInstance.g.name)
		UpdateCurrentGlyphView()
		self.TTHToolInstance.previewWindow.view.setNeedsDisplay_(True)

	def BitmapPreviewPopUpButtonCallback(self, sender):
		if self.TTHToolInstance.g == None:
			return
		self.TTHToolInstance.bitmapPreviewSelection = self.BitmapPreviewList[sender.get()]
		self.TTHToolInstance.loadFaceGlyph(self.TTHToolInstance.g.name)
		UpdateCurrentGlyphView()
		self.TTHToolInstance.previewWindow.view.setNeedsDisplay_(True)

	def PreviewShowButtonCallback(self, sender):
		self.wCentral.PreviewHideButton.show(True)
		self.wCentral.PreviewShowButton.show(False)

	def PreviewHideButtonCallback(self, sender):
		self.wCentral.PreviewHideButton.show(False)
		self.wCentral.PreviewShowButton.show(True)

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

		self.wPreview = FloatingWindow((210, 600, 600, 200), "Preview", closable = False)
		self.view = preview.PreviewArea.alloc().init_withTTHToolInstance(self.TTHToolInstance)

		self.view.setFrame_(((0, 0), (560, 160)))
		self.wPreview.previewEditText = EditText((10, 10, -10, 22),
										callback=self.previewEditTextCallback)
		self.wPreview.previewScrollview = ScrollView((10, 50, -10, -10),
                                self.view)

		self.wPreview.open()

	def closePreview(self):
		self.wPreview.close()

	def previewEditTextCallback(self, sender):
		self.previewString = sender.get()
		self.view.setNeedsDisplay_(True)


installTool(TTHTool())