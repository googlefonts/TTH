import math
import string
import HelperFunc as HF
reload(HF)

def make_hPointsList(g, italAngle):
	hPointsList = []
	for (contour_index, contour) in enumerate(g):
		contour_pts = contour.points
		nbPts = len(contour_pts)
		for (point_index, currentPoint) in enumerate(contour_pts):
			if currentPoint.type == 'offCurve': continue
			prevPoint = contour_pts[point_index - 1]
			nextPoint = contour_pts[(point_index + 1) % nbPts]

			prev,cur,nex = map(lambda p: HF.sheared(p, italAngle), (prevPoint, currentPoint, nextPoint))
			
			directionIN  = HF.directionForPairs(prev, cur) # useless
			directionOUT = HF.directionForPairs(cur, nex) # useless
			angleIN      = HF.angleOfVectorBetweenPairs(prev, cur)
			angleOUT     = HF.angleOfVectorBetweenPairs(cur, nex)

			hPoint = (currentPoint, contour_index, point_index, directionIN, directionOUT, angleIN, angleOUT)
			hPointsList.append(hPoint)
	return hPointsList
	
def hasSomeWhite(point1, point2, g, maxStemX, maxStemY):
	dif = HF.absoluteDiff(point1, point2)
	if dif[0] < maxStemX or dif[1] < maxStemY:
		hypothLength = HF.distance(point1, point2)
		for j in range(1, int(hypothLength), 5):
			p = HF.lerpPoints(j * 1.0 / hypothLength, point1, point2)
			if not g.pointInside(p):
				return True
		return False
	return True # too far away, assume there is white in between

def getColor(point1, point2, g, maxStemX, maxStemY):
	hasSomeBlack = False
	hasSomeWhite = False
	dif = HF.absoluteDiff(point1, point2)
	if dif[0] < maxStemX or dif[1] < maxStemY:
		hypothLength = HF.distance(point1, point2)
		for j in range(1, int(hypothLength), 5):
			p = HF.lerpPoints(j * 1.0 / hypothLength, point1, point2)
			if g.pointInside(p):
				hasSomeBlack = True
			else:
				hasSomeWhite = True
			if hasSomeBlack and hasSomeWhite:
				break

	if hasSomeBlack and hasSomeWhite:
		return 'Gray'
	elif hasSomeBlack:
		return 'Black'
	else:
		return 'White'

def makeStemsList(f, g_hPoints, g, italicAngle, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems):
	# parameter 'f' is not used. Remove?
	stemsListX_temp = []
	stemsListY_temp = []
	def addStemToList(sourcePoint, targetPoint, angle, existingStems):
		dx, dy = HF.absoluteDiff(sourcePoint, targetPoint)
		c_distance = ( HF.roundbase(dx, roundFactor_Stems), HF.roundbase(dy, roundFactor_Stems) )
		hypoth = HF.distance(sourcePoint, targetPoint)
		stem = (sourcePoint, targetPoint, c_distance)
		## if they are horizontal, treat the stem on the Y axis
		if HF.isHorizontal(angle) and not existingStems['h']:
			yBound = minStemY*(1.0-roundFactor_Stems/100.0), maxStemY*(1.0+roundFactor_Stems/100.0)
			if HF.inInterval(c_distance[1], yBound) and HF.inInterval(hypoth, yBound):
				existingStems['h'] = True
				stemsListY_temp.append((hypoth, stem))
		## if they are vertical, treat the stem on the X axis
		if HF.isVertical(angle) and not existingStems['v']: # the angle is already sheared to counter italic
			xBound = minStemX*(1.0-roundFactor_Stems/100.0), maxStemX*(1.0+roundFactor_Stems/100.0)
			if HF.inInterval(c_distance[0], xBound) and HF.inInterval(hypoth, xBound):
				existingStems['v'] = True
				stemsListX_temp.append((hypoth, stem))
		## Here, the angle of the stem is more diagonal
		# ... do something here with diagonal

	def hasWhite(wc, source, target):
		if wc[0] == None:
			wc[0] = hasSomeWhite(source, target, g, maxStemX, maxStemY)
		return wc[0]

	for (i1, source_hPoint) in enumerate(g_hPoints):
		for target_hPoint in g_hPoints[i1+1:]:
			sourcePoint, _, _, _, _, sia, soa = source_hPoint # sia = Source In Angle
			targetPoint, _, _, _, _, tia, toa = target_hPoint
			existingStems = {'h':False, 'v':False, 'd':False}
			wc = [None]
			for (sa,ta) in [(sia,tia), (soa,toa), (sia,toa), (soa,tia)]:
				if HF.closeAngleModulo180(sa, ta):
					if hasWhite(wc, sourcePoint, targetPoint): break
					addStemToList(sourcePoint, targetPoint, sa, existingStems)
	# avoid duplicates, filters temporary stems
	stemsListY_temp.sort() # sort by stem length (hypoth)
	stemsListX_temp.sort()
	stemsListX = []
	stemsListY = []
	references = []
	for (hypoth, stem) in stemsListY_temp:
		sourceAbsent = not HF.exists(references, lambda y: HF.approxEqual(stem[0].y, y, 0.025))
		targetAbsent = not HF.exists(references, lambda y: HF.approxEqual(stem[1].y, y, 0.025))
		if sourceAbsent and targetAbsent:
			stemsListY.append(stem)
		if sourceAbsent:
			references.append(stem[0].y)
		if targetAbsent:
			references.append(stem[1].y)

	references = []
	for (hypoth, stem) in stemsListX_temp:
		shearedSourceX, _ = HF.sheared(stem[0], italicAngle)
		shearedTargetX, _ = HF.sheared(stem[1], italicAngle)
		sourceAbsent = not HF.exists(references, lambda x: HF.approxEqual(shearedSourceX, x, 0.025))
		targetAbsent = not HF.exists(references, lambda x: HF.approxEqual(shearedTargetX, x, 0.025))
		if sourceAbsent and targetAbsent:
			stemsListX.append(stem)
		if sourceAbsent:
			references.append(shearedSourceX)
		if targetAbsent:
			references.append(shearedTargetX)
	
	return (stemsListX, stemsListY)
	
### - - - - - - - - - - -  - - - - - - - - - - - - - - - - - - - - - - 

class Automation():
	def __init__(self, controller, TTHToolInstance):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm
		self.controller = controller


	def autoStems(self, font, progressBar):
		minStemX = self.tthtm.minStemX
		minStemY = self.tthtm.minStemY
		maxStemX = self.tthtm.maxStemX
		maxStemY = self.tthtm.maxStemY
		roundFactor_Stems = self.tthtm.roundFactor_Stems
		roundFactor_Jumps = self.tthtm.roundFactor_Jumps

		minStemX = HF.roundbase(minStemX, roundFactor_Stems)
		minStemY = HF.roundbase(minStemY, roundFactor_Stems)
		maxStemX = HF.roundbase(maxStemX, roundFactor_Stems)
		maxStemY = HF.roundbase(maxStemY, roundFactor_Stems)


		stemsValuesXList = []
		stemsValuesYList = []
		stemSnapHList = []
		stemSnapVList = []
		roundedStemsXList = []
		roundedStemsYList = []
		originalStemsXList = []
		originalStemsYList = []

		if font.info.italicAngle != None:
			ital = - font.info.italicAngle
		else:
			ital = 0

		g = font['O']
		if not g:
			print "WARNING: glyph 'O' missing"
		O_hPoints = make_hPointsList(g, ital)
		(O_stemsListX, O_stemsListY) = makeStemsList(font, O_hPoints, g, ital, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems)

		Xs = []
		for stem in O_stemsListX:
			Xs.append(stem[2][0])
		maxStemX = max(Xs)
		maxStemY = max(Xs)

		stemsValuesXList = []
		stemsValuesYList = []

		progressBar.set(0)
		tick = 100.0/len(string.ascii_letters)
		for name in string.ascii_letters:
			g = font[name]
			( originalStemsXList, originalStemsYList ) = self.getRoundedStems(font, g, ital, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems)
			stemsValuesXList.extend(originalStemsXList)
			stemsValuesYList.extend(originalStemsYList)
			progressBar.increment(tick)

		self.sortAndStoreValues(stemsValuesXList, False, roundFactor_Jumps)
		self.sortAndStoreValues(stemsValuesYList, True, roundFactor_Jumps)

	def getRoundedStems(self, font, g, ital, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems):
		originalStemsXList = []
		originalStemsYList = []
		g_hPoints = make_hPointsList(g, ital)
		(self.stemsListX, self.stemsListY) = makeStemsList(font, g_hPoints, g, ital, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems)
		for stem in self.stemsListX:
			originalStemsXList.append(stem[2][0])
		for stem in self.stemsListY:
			originalStemsYList.append(stem[2][1])

		return (originalStemsXList, originalStemsYList)
	

	def sortAndStoreValues(self, stemsValuesList, isHorizontal, roundFactor_Jumps):
		valuesDict = {}
		stemSnapList = []
		for StemValue in stemsValuesList:
			try:
				valuesDict[StemValue] += 1
			except KeyError:
				valuesDict[StemValue] = 1
		
		
		keyValueList = valuesDict.items()
		keyValueList.sort(HF.compare)
		keyValueList = keyValueList[:6]

		for keyValue in keyValueList:
			stemSnapList.append(keyValue[0])

		for width in stemSnapList:
			if isHorizontal == False:
				name = 'X_' + str(width)
			else:
				name = 'Y_' + str(width)
			#stemPitch = float(self.tthtm.UPM)/width
			roundedStem = HF.roundbase(width, roundFactor_Jumps)
			if roundedStem !=0:
				stemPitch = float(self.tthtm.UPM)/roundedStem
			else:
				stemPitch = float(self.tthtm.UPM)/width
			#stemPitch = roundbase(float(self.tthtm.UPM)/width, roundFactor_Jumps)
			px1 = str(0)
			px2 = str(int(2*stemPitch))
			#stemPitch = float(self.tthtm.UPM)/roundbase(width, roundFactor_Jumps - 1*int(roundFactor_Jumps/5))
			px3 = str(int(3*stemPitch))
			#stemPitch = float(self.tthtm.UPM)/roundbase(width, roundFactor_Jumps - 2*int(roundFactor_Jumps/5))
			px4 = str(int(4*stemPitch))
			#stemPitch = float(self.tthtm.UPM)/roundbase(width, roundFactor_Jumps - 3*int(roundFactor_Jumps/5))
			px5 = str(int(5*stemPitch))
			#stemPitch = float(self.tthtm.UPM)/roundbase(width, roundFactor_Jumps - 4*int(roundFactor_Jumps/5))
			px6 = str(int(6*stemPitch))

			self.addStem(isHorizontal, name, width, px1, px2, px3, px4, px5, px6)

					
	def addStem(self, isHorizontal, stemName, width, px1, px2, px3, px4, px5, px6):
		if stemName in self.tthtm.stems:
			return
		stemDict = {'horizontal': isHorizontal, 'width': width, 'round': {px1: 1, px2: 2, px3: 3, px4: 4, px5: 5, px6: 6} }
		if isHorizontal:
			self.TTHToolInstance.addStem(stemName, stemDict, self.controller.horizontalStemView)
		else:
			self.TTHToolInstance.addStem(stemName, stemDict, self.controller.verticalStemView)


	def autoZones(self, font):
		baselineZone = None
		capHeightZone = None
		xHeightZone = None
		ascenderstZone = None
		descenderstZone = None

		if "O" in font and "H" in font:
			baselineZone = (0, -font["O"].box[1])
			capHeightZone = (font["H"].box[3], font["O"].box[3] - font["H"].box[3])
		if "o" in font:
			xHeightZone = (font["o"].box[3] + font["o"].box[1], - font["o"].box[1])
		if "f" in font and "l" in font:
			if font["l"].box[3] < font["f"].box[3]:
				ascenderstZone = (font["l"].box[3], font["f"].box[3] - font["l"].box[3])
		if "g" in font and "p" in font:
			if font["p"].box[1] > font["g"].box[1]:
				descenderstZone = (font["p"].box[1], - (font["g"].box[1] - font["p"].box[1]) )

		if baselineZone != None:
			self.addZone('baseline', 'bottom', baselineZone[0], baselineZone[1])
		if capHeightZone != None:
			self.addZone('cap-height', 'top', capHeightZone[0], capHeightZone[1])
		if xHeightZone != None:
			self.addZone('x-height', 'top', xHeightZone[0], xHeightZone[1])
		if ascenderstZone != None:
			self.addZone('ascenders', 'top', ascenderstZone[0], ascenderstZone[1])
		if descenderstZone != None:
			self.addZone('descenders', 'bottom', descenderstZone[0], descenderstZone[1])


	def addZone(self, zoneName, ID, position, width, delta='0@0'):
		if zoneName in self.tthtm.zones:
			return
		deltaDict = self.TTHToolInstance.deltaDictFromString(delta)

		newZone = {'top': (ID=='top'), 'position': position, 'width': width, 'delta' : deltaDict }
		if ID=='top':
			self.TTHToolInstance.AddZone(zoneName, newZone, self.controller.topZoneView)
		else:
			self.TTHToolInstance.AddZone(zoneName, newZone, self.controller.bottomZoneView)

class AutoHinting():
	def __init__(self, TTHToolInstance):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm

	def detectStems(self, g):
		minStemX = self.tthtm.minStemX
		minStemY = self.tthtm.minStemY
		maxStemX = self.tthtm.maxStemX
		maxStemY = self.tthtm.maxStemY
		roundFactor_Stems = self.tthtm.roundFactor_Stems
		roundFactor_Jumps = self.tthtm.roundFactor_Jumps

		minStemX = HF.roundbase(minStemX, roundFactor_Stems)
		minStemY = HF.roundbase(minStemY, roundFactor_Stems)
		maxStemX = HF.roundbase(maxStemX, roundFactor_Stems)
		maxStemY = HF.roundbase(maxStemY, roundFactor_Stems)

		font = g.getParent()

		(g_stemsListX, g_stemsListY) = makeStemsList(font, self.h_pointList, g, self.ital, minStemX, minStemY, maxStemX, maxStemY, 10)

		for stem in  g_stemsListY:
			stemName = self.guessStemForDistance(stem[0], stem[1], True)
			self.addDoubleLink(stem[0], stem[1], stemName, True)
		for stem in  g_stemsListX:
			stemName = self.guessStemForDistance(stem[0], stem[1], False)
			self.addDoubleLink(stem[0], stem[1], stemName, False)
			
	def guessStemForDistance(self, p1, p2, isHorizontal):
		candidatesList = []
		for stemName, stem in self.tthtm.stems.items():
			w = int(stem['width'])
			if stem['horizontal'] == isHorizontal and isHorizontal == True:
				detectedWidth = HF.absoluteDiff(p1, p2)[1]
				if abs(w - detectedWidth) <= detectedWidth*0.20:
					candidatesList.append((abs(w - detectedWidth), stemName))
			elif stem['horizontal'] == isHorizontal and isHorizontal == False:
				detectedWidth = HF.absoluteDiff(p1, p2)[0]
				if abs(w - detectedWidth) <= detectedWidth*0.20:
					candidatesList.append((abs(w - detectedWidth), stemName))

		if candidatesList != []:
			candidatesList.sort()
			stemName = candidatesList[0][1]
			return stemName
		else:
			return None

	def addDoubleLink(self, p1, p2, stemName, isHorizontal):
		newCommand = {}
		if isHorizontal:
			newCommand['code'] = 'doublev'
		else:
			newCommand['code'] = 'doubleh'
		newCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(p1.x, p1.y)]
		newCommand['point2'] = self.TTHToolInstance.pointCoordinatesToName[(p2.x, p2.y)]
		if stemName != None:
			newCommand['stem'] = stemName
			if newCommand not in self.TTHToolInstance.glyphTTHCommands:
				self.TTHToolInstance.glyphTTHCommands.append(newCommand)

	def attachLinksToZones(self, g):
		for command in self.TTHToolInstance.glyphTTHCommands:
			if command['code'] == 'doublev':
				p1_uniqueID = self.TTHToolInstance.pointNameToUniqueID[command['point1']]
				p1_y = self.TTHToolInstance.pointUniqueIDToCoordinates[p1_uniqueID][1]
				p2_uniqueID = self.TTHToolInstance.pointNameToUniqueID[command['point2']]
				p2_y = self.TTHToolInstance.pointUniqueIDToCoordinates[p2_uniqueID][1]
				zonePoint1 = self.isInZone(p1_y)
				zonePoint2 = self.isInZone(p2_y)
				if zonePoint1 != None or zonePoint2 != None:
					command['code'] = 'singlev'
					if zonePoint2 != None:
						p2 = command['point2']
						p1 = command['point1']
						command['point1'] = p2
						command['point2'] = p1
						self.addAlign(g, p2_uniqueID, zonePoint2)
					elif zonePoint1 != None:
						self.addAlign(g, p1_uniqueID, zonePoint1)

	def addAlign(self, g, pointName, zonePoint):
		newAlign = {}
		if zonePoint[1] == True:
			newAlign['code'] = 'alignt'
		else:
			newAlign['code'] = 'alignb'
		newAlign['point'] = pointName
		newAlign['zone'] = zonePoint[0]
		self.TTHToolInstance.glyphTTHCommands.append(newAlign)

	def isInZone(self, y):
		for zoneName, zone in self.tthtm.zones.items():
			if not zone['top']:
				y_start = int(zone['position']) - int(zone['width'])
				y_end = int(zone['position'])
			else:
				y_start = int(zone['position'])
				y_end = int(zone['position']) + int(zone['width'])
			if y_start <=  y and y <= y_end:
				return (zoneName, zone['top'])
		return None

	def findSiblings(self, g):
		touchedPoints = self.findTouchedPoints(g)
		touchedPointsNames = []
		for name, _ in touchedPoints:
			touchedPointsNames.append(name)

		for pointName, axis in touchedPoints:
			(p_x, p_y) = self.TTHToolInstance.pointNameToCoordinates[pointName]
			for h_point in self.h_pointList:
				h_pointName = self.TTHToolInstance.pointCoordinatesToName[(h_point[0].x, h_point[0].y)]
				if h_pointName in touchedPointsNames:
					continue
				if axis == 'Y' and abs(h_point[0].y - p_y) <= 2 and h_pointName != pointName and (HF.isHorizontal(h_point[5]) or HF.isHorizontal(h_point[6])):
					newSiblingCommand = {}
					newSiblingCommand['code'] = 'singlev'
					newSiblingCommand['point1'] = pointName
					newSiblingCommand['point2'] = h_pointName
					self.TTHToolInstance.glyphTTHCommands.append(newSiblingCommand)
				if axis == 'X' and abs(HF.sheared(h_point[0], self.ital)[0] - HF.shearedFromCoords((p_x, p_y), self.ital)[0]) <= 2 and h_pointName != pointName and (HF.isVertical(h_point[5]-self.ital) or HF.isVertical(h_point[6]-self.ital)):
					newSiblingCommand = {}
					newSiblingCommand['code'] = 'singleh'
					newSiblingCommand['point1'] = pointName
					newSiblingCommand['point2'] = h_pointName
					self.TTHToolInstance.glyphTTHCommands.append(newSiblingCommand)



	def findTouchedPoints(self, g):
		touchedPoints = []
		for command in self.TTHToolInstance.glyphTTHCommands:
			if command['code'][-1:] in ['t', 'b', 'v']:
				axis = 'Y'
			else:
				axis = 'X'

			if 'point' in command and (command['point'], axis) not in touchedPoints:
				touchedPoints.append((command['point'], axis))
			if 'point1' in command and (command['point1'], axis) not in touchedPoints:
				touchedPoints.append((command['point1'], axis))
			if 'point2' in command and (command['point2'], axis) not in touchedPoints:
				touchedPoints.append((command['point2'], axis))
		return touchedPoints


	def hintWidth(self, g):
		pass


	# def autoAlignToZones(self, g):
	# 	for zoneName, zone in self.tthtm.zones.items():
	# 		if not zone['top']:
	# 			y_start = int(zone['position']) - int(zone['width'])
	# 			y_end = int(zone['position'])
	# 			self.processZone(g, zoneName, False, y_start, y_end)
	# 		else:
	# 			y_start = int(zone['position'])
	# 			y_end = int(zone['position']) + int(zone['width'])
	# 			self.processZone(g, zoneName, True , y_start, y_end)


	# def processZone(self, g, zoneName, isTop, y_start, y_end):
	# 	#hPoint = (currentPoint, contour_index, point_index, directionIN, directionOUT, vectorIN, vectorOUT)

	# 	for p in self.h_pointList:
	# 		if y_start <= p[0].y  and p[0].y <= y_end and p[0].type != 'offCurve':
	# 			exists = False
	# 			redundant = False
	# 			for command in self.TTHToolInstance.glyphTTHCommands:
	# 				if command['code'][:5] != 'align':
	# 					continue
	# 				else:
	# 					if command['point'] == self.TTHToolInstance.pointCoordinatesToName[(p[0].x, p[0].y)]:
	# 						exists = True
	# 					try:
	# 						(x, y) = self.TTHToolInstance.pointUniqueIDToCoordinates[command['point']]
	# 					except:
	# 						(x, y) = self.TTHToolInstance.pointNameToCoordinates[command['point']]
	# 					if abs(y - p[0].y) <= .1*abs(y_end-y_start):
	# 						redundant = True
	# 			if not exists and not redundant and ( (HF.isHorizontal_withTolerance(p[5], 45) or HF.isHorizontal_withTolerance(p[6], 45)) and not p[0].smooth):
	# 				newCommand = {}
	# 				newCommand['point'] = self.TTHToolInstance.pointCoordinatesToName[(p[0].x, p[0].y)]
	# 				newCommand['zone'] = zoneName
	# 				if isTop:
	# 					newCommand['code'] = 'alignt'
	# 				else:
	# 					newCommand['code'] = 'alignb'
	# 				self.TTHToolInstance.glyphTTHCommands.append(newCommand)

	# 				siblingsList = self.findSiblingsforPoint_amongst_inAxis(p[0], self.h_pointList, 'Y')
	# 				for point in siblingsList:
	# 					isTouched = False
	# 					for cmd in self.TTHToolInstance.glyphTTHCommands:
	# 						if 'point' in cmd:
	# 							if cmd['point'] == point:
	# 								isTouched = True
	# 						if 'point1' in cmd:
	# 							if cmd['point1'] == point:
	# 								isTouched = True
	# 						if 'point2' in cmd:
	# 							if cmd['point2'] == point:
	# 								isTouched = True
	# 					newSiblingCommand = {}
	# 					newSiblingCommand['code'] = 'singlev'
	# 					newSiblingCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(p[0].x, p[0].y)]
	# 					newSiblingCommand['point2'] = point
	# 					if newSiblingCommand not in self.TTHToolInstance.glyphTTHCommands and not isTouched:
	# 						self.TTHToolInstance.glyphTTHCommands.append(newSiblingCommand)

	# def findSiblingsforPoint_amongst_inAxis(self, p, h_pointList, axis):
	# 	p2List = []
	# 	siblingsList = []
	# 	for i in range(len(h_pointList)):
	# 		p2 = self.h_pointList[i]
	# 		if i == 0:
	# 			p2_prev = h_pointList[len(h_pointList)-1]
	# 		else:
	# 			p2_prev = h_pointList[i-1]

	# 		if i == len(h_pointList)-1:
	# 			p2_next = h_pointList[0]
	# 		else:
	# 			p2_next = h_pointList[i+1]
				

	# 		if axis == 'Y':
	# 			condition = (abs(p.y - p2[0].y) <= 2)
	# 		else:
	# 			condition = (abs(p.x - p2[0].x) <= 2)
	# 		if condition:
	# 			if p != p2[0] and p != p2_prev[0] and p != p2_next[0]:
	# 				p2List.append((p2_prev, p2, p2_next))

	# 	for i in range(len(p2List)):
	# 		c_i = p2List[i][1]
	# 		point2 = self.TTHToolInstance.pointCoordinatesToName[(c_i[0].x, c_i[0].y)]

	# 		# Find a way to keep only stricly necessary siblings

	# 		# prev_i = p2List[i][0]
	# 		# next_i = p2List[i][2]
	# 		# for j in range(len(p2List)):
	# 		# 	c_j = p2List[j][1]
	# 		# 	prev_j = p2List[j][0]
	# 		# 	next_j = p2List[j][2]
	# 		# 	if prev_i == c_j or next_i == c_j or next_j == c_i or prev_j == c_i:
	# 		# 		break
	# 		# 	if c_j == c_i and p2[0] != p:
	# 		# 		if axis == 'X' and (HF.isVertical(c_i[5]) or HF.isVertical(c_i[6])):
	# 		# 			siblingsList.append(point2)
	# 		# 		elif axis == 'Y' and (HF.isHorizontal(c_i[5]) or HF.isHorizontal(c_i[5])):
	# 		siblingsList.append(point2)

	# 	return siblingsList



	def autohint(self, g):
		if self.tthtm.f.info.italicAngle != None:
			self.ital = - self.tthtm.f.info.italicAngle
		else:
			self.ital = 0
		self.h_pointList = make_hPointsList(g, self.ital)
	
		self.tthtm.setGlyph(g)
		self.TTHToolInstance.resetglyph()
		self.TTHToolInstance.glyphTTHCommands = []
		self.detectStems(g)
		self.attachLinksToZones(g)
		self.findSiblings(g)
		#self.autoAlignToZones(g)
		#self.hintWidth(g)
		
