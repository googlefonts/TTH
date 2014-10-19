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

def contourSegmentIterator(g):
	for cidx, c in enumerate(g):
		for sidx, s in enumerate(c):
			yield (cidx, sidx)

class HintingData(object):
	__slots__ = ('pos', 'shearedPos', 'inAngle', 'outAngle')
	def __init__(self, on, sh, ina, outa):
		self.pos = on
		self.shearedPos = sh
		self.inAngle = ina
		self.outAngle = outa

def makeHintingData(g, ital, (cidx, sidx)):
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
	return HintingData(onPt, shearedOn, angleIn, angleOut)

def makeStemsList(g, italicAngle, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems, tolerance):
	stemsListX_temp = []
	stemsListY_temp = []
	def addStemToList(src, tgt, angle, existingStems):
		dx, dy = HF.absoluteDiffOfPairs(src.shearedPos, tgt.shearedPos)
		c_distance = ( HF.roundbase(dx, roundFactor_Stems), HF.roundbase(dy, roundFactor_Stems) )
		hypoth = HF.distanceOfPairs(src.shearedPos, tgt.shearedPos)
		stem = (src.pos, tgt.pos, c_distance)
		## if they are horizontal, treat the stem on the Y axis
		if HF.isHorizontal_withTolerance(angle, tolerance) and not existingStems['h']:
			yBound = minStemY*(1.0-roundFactor_Stems/100.0), maxStemY*(1.0+roundFactor_Stems/100.0)
			if HF.inInterval(c_distance[1], yBound) and HF.inInterval(hypoth, yBound):
				existingStems['h'] = True
				stemsListY_temp.append((hypoth, stem))
		## if they are vertical, treat the stem on the X axis
		elif HF.isVertical_withTolerance(angle, tolerance) and not existingStems['v']: # the angle is already sheared to counter italic
			xBound = minStemX*(1.0-roundFactor_Stems/100.0), maxStemX*(1.0+roundFactor_Stems/100.0)
			if HF.inInterval(c_distance[0], xBound) and HF.inInterval(hypoth, xBound):
				existingStems['v'] = True
				stemsListX_temp.append((hypoth, stem))
		else:
		## Here, the angle of the stem is more diagonal
		# ... do something here with diagonal
			pass

	def hasWhite(wc, source, target):
		if wc[0] == None:
			wc[0] = hasSomeWhite(source, target, g, maxStemX, maxStemY)
		return wc[0]

	hPoints = [makeHintingData(g, italicAngle, contSeg) for contSeg in contourSegmentIterator(g)]
	for gidx, src in enumerate(hPoints):
		for tgt in hPoints[gidx+1:]:
			existingStems = {'h':False, 'v':False, 'd':False}
			wc = [None]
			for (sa,ta) in [(src.inAngle,tgt.inAngle), (src.outAngle,tgt.outAngle),
					(src.inAngle,tgt.outAngle), (src.outAngle,tgt.inAngle)]:
				if HF.closeAngleModulo180(sa, ta):
					if hasWhite(wc, src.pos, tgt.pos): break
					addStemToList(src, tgt, sa, existingStems)
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

### - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def findGroups(g, ital, horizontal):
	if horizontal:
		proj = lambda p: p.x
	else:
		proj = lambda p: p.y
	contours = [[]] * len(g)
	byPos = {}
	for contseg in contourSegmentIterator(g):
		hd = makeHintingData(g, ital, contseg)
		contours[contseg[0]].append(hd)
		pos = int(round(proj(hd.pos)))
		ptsAtPos = HF.getOrPutDefault(byPos, pos, [])
		ptsAtPos.append(contseg)

	byPos = [(k, v) for (k, v) in byPos.iteritems() if len(v) > 1]
	groups = {}
	for pos, pts in byPos:
		components = []
		for (cont,seg) in pts:
			if components == []:
				components.append([(cont,seg)])
				continue
			lenc = len(contours[cont])
			prevId = cont, (seg+lenc-1) % lenc
			nextId = cont, (seg+1) % lenc
			found = False
			for comp in components:
				if (prevId in comp) or (nextId in comp):
					comp.append((cont,seg))
					found = True
					break
			if not found:
				components.append([(cont,seg)])
		groups[pos] = components
	for pos, comps in groups:
		nbComps = len(comps)
		for i in range(nbComps-1):
			self.addSingleLink()
	return groups

### - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

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
		self.singleLinkCommandName = { False: 'singlev', True:'singleh' }

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

	def addSingleLink(self, p1, p2, isHorizontal):
		command = {}
		command['code'] = self.singleLinkCommandName[isHorizontal]
		command['point1'] = p1
		command['point2'] = p2
		self.TTHToolInstance.glyphTTHCommands.append(command)

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

		hPoints = [(makeHintingData(g, self.ital, contSeg), contSeg) for contSeg in contourSegmentIterator(g)]
		for t_pointName, axis in touchedPoints:
			(p_x, p_y) = self.TTHToolInstance.pointNameToCoordinates[t_pointName]
			for onPt, (cidx, sidx) in hPoints:
				h_pointName = self.TTHToolInstance.pointCoordinatesToName[HF.pointToPair(onPt.pos)]

				# Find prev and next ON points
				contour = g[cidx]
				prev_h_Point = contour[sidx-1].onCurve
				prev_h_PointName = self.TTHToolInstance.pointCoordinatesToName[HF.pointToPair(prev_h_Point)]
				next_h_Point = contour[(sidx+1)%len(contour)].onCurve
				next_h_PointName = self.TTHToolInstance.pointCoordinatesToName[HF.pointToPair(next_h_Point)]

				if (axis == 'X' and h_pointName in touchedPointsNames_X): continue
				if (axis == 'Y' and h_pointName in touchedPointsNames_Y): continue
				if axis == 'Y' and abs(onPt.pos.y - p_y) <= 2 and h_pointName != t_pointName and (HF.isHorizontal_withTolerance(onPt.inAngle, self.tthtm.angleTolerance) or HF.isHorizontal_withTolerance(onPt.outAngle, self.tthtm.angleTolerance)):
					if prev_h_Point.x == p_x or next_h_Point.x == p_x:
						continue
					if (prev_h_Point.x < onPt.pos.x and prev_h_Point.y == onPt.pos.y) or (next_h_Point.x < onPt.pos.x and next_h_Point.y == onPt.pos.y):
						continue
					self.addSingleLink(t_pointName, h_pointName, isHorizontal=False)
				if axis == 'X' and abs(HF.shearPoint(onPt.pos, self.ital)[0] - HF.shearPair((p_x, p_y), self.ital)[0]) <= 2 and h_pointName != t_pointName and (HF.isVertical_withTolerance(onPt.inAngle-self.ital, self.tthtm.angleTolerance) or HF.isVertical_withTolerance(onPt.outAngle-self.ital, self.tthtm.angleTolerance)):
					if prev_h_Point.y == p_y or next_h_Point.y == p_y:
						continue
					if (prev_h_Point.y < onPt.pos.y and prev_h_Point.x == onPt.pos.x) or (next_h_Point.y < onPt.pos.y and next_h_Point.x == onPt.pos.x):
						continue
					self.addSingleLink(t_pointName, h_pointName, isHorizontal=True)

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
		hPoints = [(makeHintingData(g, self.ital, contSeg), contSeg) for contSeg in contourSegmentIterator(g)]

		for onPt, (cidx, sidx) in hPoints:
			contour = g[cidx]
			prev_h_Point = HF.pointToPair(contour[sidx-1].onCurve)
			prev_h_PointName = self.TTHToolInstance.pointCoordinatesToName[prev_h_Point]
			next_h_Point = HF.pointToPair(contour[(sidx+1)%len(contour)].onCurve)
			next_h_PointName = self.TTHToolInstance.pointCoordinatesToName[next_h_Point]

			neighborsAreAlreadyAligned = \
				(prev_h_Point[1] == onPt.pos.y and prev_h_PointName in touchedPointsNames) or \
				(next_h_Point[1] == onPt.pos.y and next_h_PointName in touchedPointsNames)
			angleIsOkay = \
				HF.isHorizontal_withTolerance(onPt.inAngle, self.tthtm.angleTolerance) or \
				HF.isHorizontal_withTolerance(onPt.outAngle, self.tthtm.angleTolerance)

			if neighborsAreAlreadyAligned or (not angleIsOkay): continue

			pointName = self.TTHToolInstance.pointCoordinatesToName[HF.pointToPair(onPt.pos)]
			for (zoneName, isTop, y_start, y_end) in zones:
				if not HF.inInterval(onPt.pos.y, (y_start, y_end)): continue
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
		#self.findSiblings(g)
		findGroups(g, self.ital, horizontal=True)
		findGroups(g, self.ital, horizontal=False)
		self.autoAlignToZones(g)
		#self.hintWidth(g)

