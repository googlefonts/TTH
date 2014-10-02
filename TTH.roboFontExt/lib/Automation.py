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
	stemsListX_temp = []
	stemsListY_temp = []
	stemsListX = []
	stemsListY = []

	def goodCandidate(a1, a2):
		# True if nearly opposite angles
		return HF.closeAngle(a1, HF.addAngles(a2, 180.0))

	n = len(g_hPoints)
	pairs = [(i1, i2) for i1 in range(n) for i2 in range(n) if i1 < i2]
	for (i1, i2) in pairs:
		source_hPoint = g_hPoints[i1]
		target_hPoint = g_hPoints[i2]
		sourcePoint, _, _, _, _, angleIn_source, angleOut_source = source_hPoint
		targetPoint, _, _, _, _, angleIn_target, angleOut_target = target_hPoint

		goodAngle = None
		if goodCandidate(angleIn_source, angleIn_target):
			goodAngle = angleIn_source
		if goodCandidate(angleOut_source, angleOut_target):
			goodAngle = angleOut_source # so of both in and out are good, we keep only one, namely 'out'
		if goodAngle == None: continue
		if hasSomeWhite(sourcePoint, targetPoint, g, maxStemX, maxStemY): continue
		dx, dy = HF.absoluteDiff(sourcePoint, targetPoint)
		c_distance = ( HF.roundbase(dx, roundFactor_Stems), HF.roundbase(dy, roundFactor_Stems) )
		hypoth = HF.distance(sourcePoint, targetPoint)
		stem = (sourcePoint, targetPoint, c_distance)
		## if they are horizontal, treat the stem on the Y axis
		if HF.isHorizontal(goodAngle):
			yBound = minStemY*(1.0-roundFactor_Stems/100.0), maxStemY*(1.0+roundFactor_Stems/100.0)
			if HF.inInterval(c_distance[1], yBound) and HF.inInterval(hypoth, yBound):
				stemsListY_temp.append((hypoth, stem))

		## if they are vertical, treat the stem on the X axis
		if HF.isVertical(goodAngle): # the angle is already sheared to counter italic
			xBound = minStemX*(1.0-roundFactor_Stems/100.0), maxStemX*(1.0+roundFactor_Stems/100.0)
			if HF.inInterval(c_distance[0], xBound) and HF.inInterval(hypoth, xBound):
				stemsListX_temp.append((hypoth, stem))
		## Here, the angle of the stem is more diagonal
		# ... do something here with diagonal

	# avoid duplicates, filters temporary stems
	stemsListY_temp.sort() # sort by stem length (hypoth)
	stemsListX_temp.sort()
	yList = []
	for (hypoth, stem) in stemsListY_temp:
		sourceAbsent = not HF.exists(yList, lambda y: HF.approxEqual(stem[0].y, y, 0.025))
		targetAbsent = not HF.exists(yList, lambda y: HF.approxEqual(stem[1].y, y, 0.025))
		if sourceAbsent or targetAbsent:
			stemsListY.append(stem)
		if sourceAbsent:
			yList.append(stem[0].y)
		if targetAbsent:
			yList.append(stem[1].y)

	xList = []
	for (hypoth, stem) in stemsListX_temp:
		shearedSourceX, _ = HF.sheared(stem[0], italicAngle)
		shearedTargetX, _ = HF.sheared(stem[1], italicAngle)
		sourceAbsent = not HF.exists(xList, lambda x: HF.approxEqual(shearedSourceX, x, 0.025))
		targetAbsent = not HF.exists(xList, lambda x: HF.approxEqual(shearedTargetX, x, 0.025))
		if sourceAbsent or targetAbsent:
			stemsListX.append(stem)
		if sourceAbsent:
			xList.append(shearedSourceX)
		if targetAbsent:
			xList.append(shearedTargetX)
	
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
			capHeightZone = (font["H"].box[3], -font["O"].box[1])
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
			detectedWidth = HF.absoluteDiff(stem[0], stem[1])[1]
			self.addStem(stem[0], stem[1], detectedWidth, False)
		for stem in  g_stemsListX:
			detectedWidth = HF.absoluteDiff(stem[0], stem[1])[0]
			self.addStem(stem[0], stem[1], detectedWidth, True)
			

	def addStem(self, p1, p2, width, isHorizontal):
		
		candidatesList = []
		for stemName, stem in self.tthtm.stems.items():
			if stem['horizontal'] != isHorizontal:
				w = int(stem['width'])
				if HF.approxEqual(w, width, .20):
					candidatesList.append((abs(w - width), stemName))

		if candidatesList != []:
			candidatesList.sort()
			stemName = candidatesList[0][1]
			newCommand = {}
			if isHorizontal:
				newCommand['code'] = 'doubleh'
			else:
				newCommand['code'] = 'doublev'
			newCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(p1.x, p1.y)]
			newCommand['point2'] = self.TTHToolInstance.pointCoordinatesToName[(p2.x, p2.y)]
			zonePoint1 = self.isInZone(p1)
			zonePoint2 = self.isInZone(p2)

			if zonePoint1 != None or zonePoint2 != None:
				if newCommand['code'] == 'doubleh':
					newCommand['code'] = 'singleh'
				elif newCommand['code'] == 'doublev':
					newCommand['code'] = 'singlev'

				if zonePoint1 != None:
					newAlign = {}
					if zonePoint1[1]:
						newAlign['code'] = 'alignt'
					else:
						newAlign['code'] = 'alignb'
					newAlign['point'] = self.TTHToolInstance.pointCoordinatesToName[(p1.x, p1.y)]
					newAlign['zone'] = zonePoint1[0]

					if newAlign not in self.TTHToolInstance.glyphTTHCommands:
						self.TTHToolInstance.glyphTTHCommands.append(newAlign)
						ref_point = p1
						siblingsList = self.findSiblingsforPoints_amongst_inAxis(ref_point, self.h_pointList, 'Y')
						for point in siblingsList:
							isTouched = False
							for cmd in self.TTHToolInstance.glyphTTHCommands:
								if 'point' in cmd:
									if cmd['point'] == point:
										isTouched = True
								if 'point1' in cmd:
									if cmd['point1'] == point:
										isTouched = True
								if 'point2' in cmd:
									if cmd['point2'] == point:
										isTouched = True
							newSiblingCommand = {}
							newSiblingCommand['code'] = 'singlev'
							newSiblingCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(ref_point.x, ref_point.y)]
							newSiblingCommand['point2'] = point
							if newSiblingCommand not in self.TTHToolInstance.glyphTTHCommands and newSiblingCommand['point1'] != newSiblingCommand['point2'] and not isTouched:
								self.TTHToolInstance.glyphTTHCommands.append(newSiblingCommand)

				if zonePoint2 != None:
					newCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(p2.x, p2.y)]
					newCommand['point2'] = self.TTHToolInstance.pointCoordinatesToName[(p1.x, p1.y)]
					newAlign = {}
					if zonePoint2[1]:
						newAlign['code'] = 'alignt'
					else:
						newAlign['code'] = 'alignb'
					newAlign['point'] = self.TTHToolInstance.pointCoordinatesToName[(p2.x, p2.y)]
					newAlign['zone'] = zonePoint2[0]
					if newAlign not in self.TTHToolInstance.glyphTTHCommands:
						self.TTHToolInstance.glyphTTHCommands.append(newAlign)
						ref_point = p2
						siblingsList = self.findSiblingsforPoints_amongst_inAxis(ref_point, self.h_pointList, 'Y')
						for point in siblingsList:
							isTouched = False
							for cmd in self.TTHToolInstance.glyphTTHCommands:
								if 'point' in cmd:
									if cmd['point'] == point:
										isTouched = True
								if 'point1' in cmd:
									if cmd['point1'] == point:
										isTouched = True
								if 'point2' in cmd:
									if cmd['point2'] == point:
										isTouched = True
							newSiblingCommand = {}
							newSiblingCommand['code'] = 'singlev'
							newSiblingCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(ref_point.x, ref_point.y)]
							newSiblingCommand['point2'] = point
							if newSiblingCommand not in self.TTHToolInstance.glyphTTHCommands and newSiblingCommand['point1'] != newSiblingCommand['point2'] and not isTouched:
								self.TTHToolInstance.glyphTTHCommands.append(newSiblingCommand)


			for command in self.TTHToolInstance.glyphTTHCommands:
				if (isHorizontal and command['code'] == 'alignv') or ( not isHorizontal and command['code'] in ['alignh', 'alignt', 'alignb']):
					if command['point'] == newCommand['point2']:
						if newCommand['code'] == 'doubleh':
							newCommand['code'] = 'singleh'
						elif newCommand['code'] == 'doublev':
							newCommand['code'] = 'singlev'
						newCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(p2.x, p2.y)]
						newCommand['point2'] = self.TTHToolInstance.pointCoordinatesToName[(p1.x, p1.y)]
					elif command['point'] == newCommand['point1']:
						if newCommand['code'] == 'doubleh':
							newCommand['code'] = 'singleh'
						elif newCommand['code'] == 'doublev':
							newCommand['code'] = 'singlev'

			newCommand['stem'] = stemName
			commandExists = False
			for command in self.TTHToolInstance.glyphTTHCommands:
				if (isHorizontal and command['code'] in ['singleh', 'doubleh']) or ( not isHorizontal and command['code'] in ['singlev', 'doublev']) :
					if (command['point1'] == newCommand['point1'] or command['point1'] == newCommand['point2']) and (command['point2'] == newCommand['point1'] or command['point2'] == newCommand['point2']):
						commandExists = True


			if not commandExists:
				self.TTHToolInstance.glyphTTHCommands.append(newCommand)

				if isHorizontal:
					axis = 'X'
					typeList = ['singleh', 'doubleh']
					newSiblingCommandCode = 'singleh'
				else:
					axis = 'Y'
					typeList = ['singlev', 'doublev']
					newSiblingCommandCode = 'singlev'


				if newCommand['code'] in ['singleh', 'singlev']:
					if newCommand['point2'] == self.TTHToolInstance.pointCoordinatesToName[(p1.x, p1.y)]:
						ref_point = p1
					elif newCommand['point2'] == self.TTHToolInstance.pointCoordinatesToName[(p2.x, p2.y)]:
						ref_point = p2
					siblingsList = self.findSiblingsforPoints_amongst_inAxis(ref_point, self.h_pointList, axis)
					for point in siblingsList:
						isTouched = False
						for cmd in self.TTHToolInstance.glyphTTHCommands:
							if 'point' in cmd:
								if cmd['point'] == point:
									isTouched = True
							if 'point1' in cmd:
								if cmd['point1'] == point:
									isTouched = True
							if 'point2' in cmd:
								if cmd['point2'] == point:
									isTouched = True
						newSiblingCommand = {}
						newSiblingCommand['code'] = newSiblingCommandCode
						newSiblingCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(ref_point.x, ref_point.y)]
						newSiblingCommand['point2'] = point
						if newSiblingCommand not in self.TTHToolInstance.glyphTTHCommands and not isTouched:
							self.TTHToolInstance.glyphTTHCommands.append(newSiblingCommand)
				
				if newCommand['code'] in ['doubleh', 'doublev']:
					ref_point = p1
					siblingsList = self.findSiblingsforPoints_amongst_inAxis(ref_point, self.h_pointList, axis)
					for point in siblingsList:
						isTouched = False
						for cmd in self.TTHToolInstance.glyphTTHCommands:
							if 'point' in cmd:
								if cmd['point'] == point:
									isTouched = True
							if 'point1' in cmd:
								if cmd['point1'] == point:
									isTouched = True
							if 'point2' in cmd:
								if cmd['point2'] == point:
									isTouched = True
						newSiblingCommand = {}
						newSiblingCommand['code'] = newSiblingCommandCode
						newSiblingCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(ref_point.x, ref_point.y)]
						newSiblingCommand['point2'] = point
						if newSiblingCommand not in self.TTHToolInstance.glyphTTHCommands and not isTouched:
							self.TTHToolInstance.glyphTTHCommands.append(newSiblingCommand)

					ref_point = p2
					siblingsList = self.findSiblingsforPoints_amongst_inAxis(ref_point, self.h_pointList, axis)
					for point in siblingsList:
						isTouched = False
						for cmd in self.TTHToolInstance.glyphTTHCommands:
							if 'point' in cmd:
								if cmd['point'] == point:
									isTouched = True
							if 'point1' in cmd:
								if cmd['point1'] == point:
									isTouched = True
							if 'point2' in cmd:
								if cmd['point2'] == point:
									isTouched = True
						newSiblingCommand = {}
						newSiblingCommand['code'] = newSiblingCommandCode
						newSiblingCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(ref_point.x, ref_point.y)]
						newSiblingCommand['point2'] = point
						if newSiblingCommand not in self.TTHToolInstance.glyphTTHCommands and not isTouched:
							self.TTHToolInstance.glyphTTHCommands.append(newSiblingCommand)
					


	def hintWidth(self, g):
		pass

	def isInZone(self, point):
		for zoneName, zone in self.tthtm.zones.items():
			if not zone['top']:
				y_start = int(zone['position']) - int(zone['width'])
				y_end = int(zone['position'])
			else:
				y_start = int(zone['position'])
				y_end = int(zone['position']) + int(zone['width'])
			if y_start <=  point.y and point.y <= y_end:
				return (zoneName, zone['top'])
		return None



	def autoAlignToZones(self, g):
		for zoneName, zone in self.tthtm.zones.items():
			if not zone['top']:
				y_start = int(zone['position']) - int(zone['width'])
				y_end = int(zone['position'])
				self.processZone(g, zoneName, False, y_start, y_end)
			else:
				y_start = int(zone['position'])
				y_end = int(zone['position']) + int(zone['width'])
				self.processZone(g, zoneName, True , y_start, y_end)


	def processZone(self, g, zoneName, isTop, y_start, y_end):
		#hPoint = (currentPoint, contour_index, point_index, directionIN, directionOUT, vectorIN, vectorOUT)

		for p in self.h_pointList:
			if y_start <= p[0].y  and p[0].y <= y_end and p[0].type != 'offCurve':
				exists = False
				redundant = False
				for command in self.TTHToolInstance.glyphTTHCommands:
					if command['code'][:5] != 'align':
						continue
					else:
						if command['point'] == self.TTHToolInstance.pointCoordinatesToName[(p[0].x, p[0].y)]:
							exists = True
						try:
							(x, y) = self.TTHToolInstance.pointUniqueIDToCoordinates[command['point']]
						except:
							(x, y) = self.TTHToolInstance.pointNameToCoordinates[command['point']]
						if abs(y - p[0].y) <= .1*abs(y_end-y_start):
							redundant = True
				if not exists and not redundant and ( (HF.isHorizontal_withTolerance(p[5], 45) or HF.isHorizontal_withTolerance(p[6], 45)) and not p[0].smooth):
					newCommand = {}
					newCommand['point'] = self.TTHToolInstance.pointCoordinatesToName[(p[0].x, p[0].y)]
					newCommand['zone'] = zoneName
					if isTop:
						newCommand['code'] = 'alignt'
					else:
						newCommand['code'] = 'alignb'
					self.TTHToolInstance.glyphTTHCommands.append(newCommand)

					siblingsList = self.findSiblingsforPoints_amongst_inAxis(p[0], self.h_pointList, 'Y')
					for point in siblingsList:
						isTouched = False
						for cmd in self.TTHToolInstance.glyphTTHCommands:
							if 'point' in cmd:
								if cmd['point'] == point:
									isTouched = True
							if 'point1' in cmd:
								if cmd['point1'] == point:
									isTouched = True
							if 'point2' in cmd:
								if cmd['point2'] == point:
									isTouched = True
						newSiblingCommand = {}
						newSiblingCommand['code'] = 'singlev'
						newSiblingCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(p[0].x, p[0].y)]
						newSiblingCommand['point2'] = point
						if newSiblingCommand not in self.TTHToolInstance.glyphTTHCommands and not isTouched:
							self.TTHToolInstance.glyphTTHCommands.append(newSiblingCommand)

	def findSiblingsforPoints_amongst_inAxis(self, p, h_pointList, axis):
		p2List = []
		siblingsList = []
		for i in range(len(h_pointList)):
			p2 = self.h_pointList[i]
			if i == 0:
				p2_prev = h_pointList[len(h_pointList)-1]
			else:
				p2_prev = h_pointList[i-1]

			if i == len(h_pointList)-1:
				p2_next = h_pointList[0]
			else:
				p2_next = h_pointList[i+1]
				

			if axis == 'Y':
				condition = (abs(p.y - p2[0].y) <= 2)
			else:
				condition = (abs(p.x - p2[0].x) <= 2)
			if condition:
				if p != p2[0] and p != p2_prev[0] and p != p2_next[0]:
					p2List.append((p2_prev, p2, p2_next))

		for i in range(len(p2List)):
			c_i = p2List[i][1]
			point2 = self.TTHToolInstance.pointCoordinatesToName[(c_i[0].x, c_i[0].y)]

			prev_i = p2List[i][0]
			next_i = p2List[i][2]
			for j in range(len(p2List)):
				c_j = p2List[j][1]
				prev_j = p2List[j][0]
				next_j = p2List[j][2]
				if prev_i == c_j or next_i == c_j or next_j == c_i or prev_j == c_i:
					break
				if c_j == c_i and p2[0] != p:
					if axis == 'X' and (HF.isVertical(c_i[5]) or HF.isVertical(c_i[6])):
						siblingsList.append(point2)
					elif axis == 'Y' and (HF.isHorizontal(c_i[5]) or HF.isHorizontal(c_i[5])):
						siblingsList.append(point2)

		return siblingsList



	def autohint(self, g):
		if self.tthtm.f.info.italicAngle != None:
			self.ital = - self.tthtm.f.info.italicAngle
		else:
			self.ital = 0

		self.h_pointList = make_hPointsList(g, self.ital)

		self.tthtm.g.prepareUndo("AutoHint")
		self.detectStems(g)
		self.autoAlignToZones(g)
		self.hintWidth(g)
		self.TTHToolInstance.updateGlyphProgram()
		if self.tthtm.alwaysRefresh == 1:
			self.TTHToolInstance.refreshGlyph()
		self.tthtm.g.performUndo()
