import math
import string
import sets
import HelperFunc as HF
reload(HF)

def hasSomeWhite(point1, point2, g, maxStemX, maxStemY):
	dif = HF.absoluteDiff(point1, point2)
	if dif[0] > maxStemX and dif[1] > maxStemY:
		return True # too far away, assume there is white in between
	hypothLength = HF.distance(point1, point2)
	for j in range(1, int(hypothLength), 5):
		p = HF.lerpPoints(j * 1.0 / hypothLength, point1, point2)
		if not g.pointInside(p):
			return True
	return False

def buildContourSegmentList(g):
	l = [[(cidx, sidx) for sidx in range(len(g[cidx]))] for cidx in range(len(g))]
	return sum(l, []) # flatten the list of lists

def hintingData(g, ital, (cidx, sidx)):
	"""Compute data relevant to hinting for the ON point in the
	sidx-th segment of the cidx-th contour of glyph 'g'."""
	contour = g[cidx]
	contourLen = len(contour)
	segment = contour[sidx]
	onPt = segment.onCurve
	nextOff = contour[(sidx+1) % contourLen].points[0]
	if len(segment.points) > 1:
		prevOff = segment[-2]
	else:
		prevOff = contour[sidx-1].onCurve
	shearedOn = HF.shearPoint(segment.onCurve, ital)
	angleIn  = HF.angleOfVectorBetweenPairs(HF.shearPoint(prevOff, ital), shearedOn)
	angleOut = HF.angleOfVectorBetweenPairs(shearedOn, HF.shearPoint(nextOff, ital))
	return (onPt, angleIn, angleOut)

def makeStemsList(g, italicAngle, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems, tolerance):
	stemsListX_temp = []
	stemsListY_temp = []
	def addStemToList(sourcePoint, targetPoint, angle, existingStems):
		dx, dy = HF.absoluteDiff(sourcePoint, targetPoint)
		c_distance = ( HF.roundbase(dx, roundFactor_Stems), HF.roundbase(dy, roundFactor_Stems) )
		hypoth = HF.distance(sourcePoint, targetPoint)
		stem = (sourcePoint, targetPoint, c_distance)
		## if they are horizontal, treat the stem on the Y axis
		if HF.isHorizontal_withTolerance(angle, tolerance) and not existingStems['h']:
			yBound = minStemY*(1.0-roundFactor_Stems/100.0), maxStemY*(1.0+roundFactor_Stems/100.0)
			if HF.inInterval(c_distance[1], yBound) and HF.inInterval(hypoth, yBound):
				existingStems['h'] = True
				stemsListY_temp.append((hypoth, stem))
		## if they are vertical, treat the stem on the X axis
		if HF.isVertical_withTolerance(angle, tolerance) and not existingStems['v']: # the angle is already sheared to counter italic
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

	#hPoints = [hintingData(g, italicAngle, contSeg) for contSeg in buildContourSegmentList(g)]
	# We don't use italicAngle anymore because we also treat diagonals
	hPoints = [hintingData(g, 0, contSeg) for contSeg in buildContourSegmentList(g)]
	for gidx, onPt0 in enumerate(hPoints):
		sourcePoint, sia, soa = onPt0 # sia = Source In Angle
		for onPt1 in hPoints[gidx+1:]:
			targetPoint, tia, toa = onPt1
			existingStems = {'h':False, 'v':False, 'd':False}
			wc = [None]
			for (sa,ta) in [(sia,tia), (soa,toa), (sia,toa), (soa,tia)]:
				if HF.closeAngleModulo180(sa, ta):
					if hasWhite(wc, sourcePoint, targetPoint): break
					addStemToList(sourcePoint, targetPoint, sa, existingStems)
	# avoid duplicates, filters temporary stems
	stemsListX_temp.sort() # sort by stem length (hypoth)
	stemsListY_temp.sort()
	stemsListX = []
	stemsListY = []
	references = []
	for (hypoth, stem) in stemsListY_temp:
		sourceAbsent = not HF.exists(references, lambda y: HF.approxEqual(stem[0].y, y, 0.025))
		targetAbsent = not HF.exists(references, lambda y: HF.approxEqual(stem[1].y, y, 0.025))
		if sourceAbsent or targetAbsent:
			stemsListY.append(stem)
		if sourceAbsent:
			references.append(stem[0].y)
		if targetAbsent:
			references.append(stem[1].y)

	references = []
	for (hypoth, stem) in stemsListX_temp:
		shearedSourceX, _ = HF.shearPoint(stem[0], italicAngle)
		shearedTargetX, _ = HF.shearPoint(stem[1], italicAngle)
		sourceAbsent = not HF.exists(references, lambda x: HF.approxEqual(shearedSourceX, x, 0.025))
		targetAbsent = not HF.exists(references, lambda x: HF.approxEqual(shearedTargetX, x, 0.025))
		if sourceAbsent or targetAbsent:
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
		roundFactor_Stems = self.tthtm.roundFactor_Stems
		roundFactor_Jumps = self.tthtm.roundFactor_Jumps

		minStemX = HF.roundbase(self.tthtm.minStemX, roundFactor_Stems)
		minStemY = HF.roundbase(self.tthtm.minStemY, roundFactor_Stems)
		maxStemX = HF.roundbase(self.tthtm.maxStemX, roundFactor_Stems)
		maxStemY = HF.roundbase(self.tthtm.maxStemY, roundFactor_Stems)

		if font.info.italicAngle != None:
			ital = - font.info.italicAngle
		else:
			ital = 0

		if 'O' not in font:
			print "WARNING: glyph 'O' missing, unable to calculate stems"
			return
		g = font['O']
		(O_stemsListX, O_stemsListY) = makeStemsList(g, ital, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems, self.tthtm.angleTolerance)

		maxStemX = maxStemY = max([stem[2][0] for stem in O_stemsListX])

		stemsValuesXList = []
		stemsValuesYList = []

		progressBar.set(0)
		tick = 100.0/len(string.ascii_letters)
		for name in string.ascii_letters:
			g = font[name]
			( XStems, YStems ) = self.getRoundedStems(g, ital, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems)
			stemsValuesXList.extend(XStems)
			stemsValuesYList.extend(YStems)
			progressBar.increment(tick)

		self.sortAndStoreValues(stemsValuesXList, roundFactor_Jumps, isHorizontal=False)
		self.sortAndStoreValues(stemsValuesYList, roundFactor_Jumps, isHorizontal=True)

	def getRoundedStems(self, g, ital, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems):
		(stemsListX, stemsListY) = makeStemsList(g, ital, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems, self.tthtm.angleTolerance)
		originalStemsXList = [stem[2][0] for stem in stemsListX]
		originalStemsYList = [stem[2][1] for stem in stemsListY]
		return (originalStemsXList, originalStemsYList)

	def sortAndStoreValues(self, stemsValuesList, roundFactor_Jumps, isHorizontal):
		valuesDict = {}
		for StemValue in stemsValuesList:
			try:
				valuesDict[StemValue] += 1
			except KeyError:
				valuesDict[StemValue] = 1
		
		
		keyValueList = valuesDict.items()
		keyValueList.sort(lambda (k1,v1),(k2,v2): v2-v1)

		stemSnapList = [k for k,v in keyValueList[:6]]

		for width in stemSnapList:
			if not isHorizontal:
				name = 'X_' + str(width)
			else:
				name = 'Y_' + str(width)
			#stemPitch = float(self.tthtm.UPM)/width
			roundedStem = HF.roundbase(width, roundFactor_Jumps)
			if roundedStem != 0:
				stemPitch = float(self.tthtm.UPM)/roundedStem
			else:
				stemPitch = float(self.tthtm.UPM)/width
				# FIXME maybe, here we should juste skip this width and 'continue'?
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
		ascendersZone = None
		descendersZone = None

		if "O" in font and "H" in font:
			baselineZone = (0, -font["O"].box[1])
			capHeightZone = (font["H"].box[3], font["O"].box[3] - font["H"].box[3])
		if "o" in font:
			xHeightZone = (font["o"].box[3] + font["o"].box[1], - font["o"].box[1])
		if "f" in font and "l" in font:
			if font["l"].box[3] < font["f"].box[3]:
				ascendersZone = (font["l"].box[3], font["f"].box[3] - font["l"].box[3])
			elif font["l"].box[3] == font["f"].box[3]:
				ascendersZone = (font["l"].box[3] + font["o"].box[1] , - font["o"].box[1])
		if "g" in font and "p" in font:
			if font["p"].box[1] > font["g"].box[1]:
				descendersZone = (font["p"].box[1], - (font["g"].box[1] - font["p"].box[1]) )

		if baselineZone != None:
			self.addZone('baseline', 'bottom', baselineZone[0], baselineZone[1])
		if capHeightZone != None:
			self.addZone('cap-height', 'top', capHeightZone[0], capHeightZone[1])
		if xHeightZone != None:
			self.addZone('x-height', 'top', xHeightZone[0], xHeightZone[1])
		if ascendersZone != None:
			self.addZone('ascenders', 'top', ascendersZone[0], ascendersZone[1])
		if descendersZone != None:
			self.addZone('descenders', 'bottom', descendersZone[0], descendersZone[1])


	def addZone(self, zoneName, ID, position, width, delta='0@0'):
		if zoneName in self.tthtm.zones:
			return
		deltaDict = self.TTHToolInstance.deltaDictFromString(delta)

		newZone = {'top': (ID=='top'), 'position': position, 'width': width, 'delta' : deltaDict }
		if ID=='top':
			self.TTHToolInstance.AddZone(zoneName, newZone, self.controller.topZoneView)
		else:
			self.TTHToolInstance.AddZone(zoneName, newZone, self.controller.bottomZoneView)


def zoneData((zoneName, zone)):
	isTop = zone['top']
	if isTop:
		y_start = int(zone['position'])
		y_end = int(zone['position']) + int(zone['width'])
	else:
		y_start = int(zone['position']) - int(zone['width'])
		y_end = int(zone['position'])
	return (zoneName, isTop, y_start, y_end)

class AutoHinting():
	def __init__(self, TTHToolInstance):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm

	def detectStems(self, g):
		roundFactor_Stems = self.tthtm.roundFactor_Stems
		minStemX = HF.roundbase(self.tthtm.minStemX, roundFactor_Stems)
		minStemY = HF.roundbase(self.tthtm.minStemY, roundFactor_Stems)
		maxStemX = HF.roundbase(self.tthtm.maxStemX, roundFactor_Stems)
		maxStemY = HF.roundbase(self.tthtm.maxStemY, roundFactor_Stems)

		(g_stemsListX, g_stemsListY) = makeStemsList(g, self.ital, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems, self.tthtm.angleTolerance)

		for stem in g_stemsListY:
			stemName = self.guessStemForDistance(stem[0], stem[1], True)
			self.addDoubleLink(stem[0], stem[1], stemName, True)
			#self.processDoubleLinks()
		for stem in g_stemsListX:
			stemName = self.guessStemForDistance(stem[0], stem[1], False)
			self.addDoubleLink(stem[0], stem[1], stemName, False)

			
	def guessStemForDistance(self, p1, p2, isHorizontal):
		if isHorizontal:
			detectedWidth = abs(p1.y - p2.y)
		else:
			detectedWidth = abs(p1.x - p2.x)
		candidatesList = []
		for stemName, stem in self.tthtm.stems.iteritems():
			if stem['horizontal'] != isHorizontal: continue
			w = int(stem['width'])
			if abs(w - detectedWidth) <= detectedWidth*0.20:
				candidatesList.append((abs(w - detectedWidth), stemName))

		if candidatesList != []:
			candidatesList.sort()
			stemName = candidatesList[0][1]
			return stemName
		else:
			return None

	def addDoubleLink(self, p1, p2, stemName, isHorizontal):
		if stemName == None:
			return
		newCommand = {}
		if isHorizontal:
			newCommand['code'] = 'doublev'
		else:
			newCommand['code'] = 'doubleh'
		newCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(p1.x, p1.y)]
		newCommand['point2'] = self.TTHToolInstance.pointCoordinatesToName[(p2.x, p2.y)]
		newCommand['stem'] = stemName
		if newCommand not in self.TTHToolInstance.glyphTTHCommands:
			self.TTHToolInstance.glyphTTHCommands.append(newCommand)

	def processDoubleLinks(self):
		for command1 in self.TTHToolInstance.glyphTTHCommands:
			for command2 in self.TTHToolInstance.glyphTTHCommands:
				if command1['code'][-1:] == 'v' and command2['code'][-1] == 'v':
					if command1 != command2 and command1['code'][:6] == 'double' and command2['code'][:6] == 'double':
						if command1['point2'] == command2['point2']:
							command1['code'] = 'singlev'
							command2['code'] = 'singlev'

							c1p1 = command1['point1']
							c1p2 = command1['point2']
							c2p1 = command2['point1']
							c2p2 = command2['point2']
							command1['point1'] = c1p2
							command1['point2'] = c1p1
							command2['point1'] = c2p2
							command2['point2'] = c2p1
							


	def attachLinksToZones(self, g):
		for command in self.TTHToolInstance.glyphTTHCommands:
			if command['code'] != 'doublev': continue
			p1_uniqueID = self.TTHToolInstance.pointNameToUniqueID[command['point1']]
			p1_y = self.TTHToolInstance.pointUniqueIDToCoordinates[p1_uniqueID][1]
			p2_uniqueID = self.TTHToolInstance.pointNameToUniqueID[command['point2']]
			p2_y = self.TTHToolInstance.pointUniqueIDToCoordinates[p2_uniqueID][1]
			zonePoint1 = self.zoneAt(p1_y)
			zonePoint2 = self.zoneAt(p2_y)
			if zonePoint1 == None and zonePoint2 == None: continue
			command['code'] = 'singlev'
			if zonePoint2 != None:
				p2 = command['point2']
				p1 = command['point1']
				command['point1'] = p2 # swap the points
				command['point2'] = p1
				self.addAlign(g, p2_uniqueID, zonePoint2)
			else: # elif zonePoint1 != None:
				self.addAlign(g, p1_uniqueID, zonePoint1)

	def addAlign(self, g, pointName, (zoneName, isTopZone)):
		newAlign = {}
		if isTopZone:
			newAlign['code'] = 'alignt'
		else:
			newAlign['code'] = 'alignb'
		newAlign['point'] = pointName
		newAlign['zone'] = zoneName
		self.TTHToolInstance.glyphTTHCommands.append(newAlign)

	def zoneAt(self, y):
		for item in self.tthtm.zones.iteritems():
			zoneName, isTop, yStart, yEnd = zoneData(item)
			if HF.inInterval(y, (yStart, yEnd)):
				return (zoneName, isTop)
				return None

	def findSiblings(self, g):
		touchedPoints = self.findTouchedPoints(g)
		touchedPointsNames_X = []
		touchedPointsNames_Y = []
		for name, axis in touchedPoints:
			if axis == 'X':
				touchedPointsNames_X.append(name)
			else:
				touchedPointsNames_Y.append(name)

		hPoints = [(hintingData(g, self.ital, contSeg), contSeg) for contSeg in buildContourSegmentList(g)]
		for t_pointName, axis in touchedPoints:
			(p_x, p_y) = self.TTHToolInstance.pointNameToCoordinates[t_pointName]
			for onPt, (cidx, sidx) in hPoints:
				onPoint, angleIn, angleOut = onPt # angleIn = Source In Angle
				h_pointName = self.TTHToolInstance.pointCoordinatesToName[HF.pointToPair(onPoint)]

				# Find prev and next ON points
				contour = g[cidx]
				prev_h_Point = contour[sidx-1].onCurve
				prev_h_PointName = self.TTHToolInstance.pointCoordinatesToName[HF.pointToPair(prev_h_Point)]
				next_h_Point = contour[(sidx+1)%len(contour)].onCurve
				next_h_PointName = self.TTHToolInstance.pointCoordinatesToName[HF.pointToPair(next_h_Point)]

				if (axis == 'X' and h_pointName in touchedPointsNames_X): continue
				if (axis == 'Y' and h_pointName in touchedPointsNames_Y): continue
				if axis == 'Y' and abs(onPoint.y - p_y) <= 2 and h_pointName != t_pointName and (HF.isHorizontal_withTolerance(angleIn, self.tthtm.angleTolerance) or HF.isHorizontal_withTolerance(angleOut, self.tthtm.angleTolerance)):
					if prev_h_Point.x == p_x or next_h_Point.x == p_x:
						continue
					if (prev_h_Point.x < onPoint.x and prev_h_Point.y == onPoint.y) or (next_h_Point.x < onPoint.x and next_h_Point.y == onPoint.y):
						continue
					newSiblingCommand = {}
					newSiblingCommand['code'] = 'singlev'
					newSiblingCommand['point1'] = t_pointName
					newSiblingCommand['point2'] = h_pointName
					self.TTHToolInstance.glyphTTHCommands.append(newSiblingCommand)
				if axis == 'X' and abs(HF.shearPoint(onPoint, self.ital)[0] - HF.shearPair((p_x, p_y), self.ital)[0]) <= 2 and h_pointName != t_pointName and (HF.isVertical_withTolerance(angleIn-self.ital, self.tthtm.angleTolerance) or HF.isVertical_withTolerance(angleOut-self.ital, self.tthtm.angleTolerance)):
					if prev_h_Point.y == p_y or next_h_Point.y == p_y:
						continue
					if (prev_h_Point.y < onPoint.y and prev_h_Point.x == onPoint.x) or (next_h_Point.y < onPoint.y and next_h_Point.x == onPoint.x):
						continue
					newSiblingCommand = {}
					newSiblingCommand['code'] = 'singleh'
					newSiblingCommand['point1'] = t_pointName
					newSiblingCommand['point2'] = h_pointName
					self.TTHToolInstance.glyphTTHCommands.append(newSiblingCommand)

	#def getPrevNextONCurve(self, g, ref_point):
	#	for index_c, c in enumerate(g):
	#		contour_points = c.points
	#		ON_pointsList = []
	#		for index_p, p in enumerate(contour_points):
	#			if p.type != 'offCurve':
	#				ON_pointsList.append(p)
	#		nbPts = len(ON_pointsList)
	#		for index, ON_p in enumerate(ON_pointsList):
	#			prevPoint = ON_pointsList[index - 1]
	#			nextPoint = ON_pointsList[(index + 1) % nbPts]
	#			if ON_p == ref_point:
	#				return (prevPoint, nextPoint)

	#	return (None, None)



	def findTouchedPoints(self, g):
		touchedPoints = sets.Set()
		for command in self.TTHToolInstance.glyphTTHCommands:
			axis = 'X'
			if command['code'][-1] in ['t', 'b', 'v']:
				axis = 'Y'
			for n in ('point', 'point1', 'point2'):
				if n in command: touchedPoints.add((command[n], axis))
		return touchedPoints


	def hintWidth(self, g):
		pass


	def autoAlignToZones(self, g):

		touchedPoints = self.findTouchedPoints(g)
		touchedPointsNames = [name for name,axis in touchedPoints if axis == 'Y']

		zones = [zoneData(item) for item in self.tthtm.zones.iteritems()]
		hPoints = [(hintingData(g, self.ital, contSeg), contSeg) for contSeg in buildContourSegmentList(g)]

		for onPt, (cidx, sidx) in hPoints:
			onPoint, angleIn, angleOut = onPt # angleIn = Source In Angle
			contour = g[cidx]
			prev_h_Point = HF.pointToPair(contour[sidx-1].onCurve)
			prev_h_PointName = self.TTHToolInstance.pointCoordinatesToName[prev_h_Point]
			next_h_Point = HF.pointToPair(contour[(sidx+1)%len(contour)].onCurve)
			next_h_PointName = self.TTHToolInstance.pointCoordinatesToName[next_h_Point]

			neighborsAreAlreadyAligned = \
				(prev_h_Point[1] == onPoint.y and prev_h_PointName in touchedPointsNames) or \
				(next_h_Point[1] == onPoint.y and next_h_PointName in touchedPointsNames)
			angleIsOkay = \
				HF.isHorizontal_withTolerance(angleIn, self.tthtm.angleTolerance) or \
				HF.isHorizontal_withTolerance(angleOut, self.tthtm.angleTolerance)

			if neighborsAreAlreadyAligned or (not angleIsOkay): continue

			pointName = self.TTHToolInstance.pointCoordinatesToName[HF.pointToPair(onPoint)]
			for (zoneName, isTop, y_start, y_end) in zones:
				if not HF.inInterval(onPoint.y, (y_start, y_end)): continue
				newAlign = {}
				if isTop:
					newAlign['code'] = 'alignt'
				else:
					newAlign['code'] = 'alignb'
				newAlign['point'] = pointName
				newAlign['zone'] = zoneName

				if pointName not in touchedPointsNames:
					self.TTHToolInstance.glyphTTHCommands.append(newAlign)
					touchedPointsNames.append(pointName)


	def autohint(self, g):
		if self.tthtm.f.info.italicAngle != None:
			self.ital = - self.tthtm.f.info.italicAngle
		else:
			self.ital = 0

		self.tthtm.setGlyph(g)
		self.TTHToolInstance.resetglyph()
		self.TTHToolInstance.glyphTTHCommands = []
		self.detectStems(g)
		self.attachLinksToZones(g)
		self.findSiblings(g)
		self.autoAlignToZones(g)
		#self.hintWidth(g)
		
