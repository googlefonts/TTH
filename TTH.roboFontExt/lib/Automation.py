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
	def __init__(self, on, sh, ina, outa, cont, seg):
		self.pos = on
		self.shearedPos = sh
		self.inAngle = ina
		self.outAngle = outa
		self.inStemY = False
		self.touched = False
		self.cont= cont # contour number
		self.seg = seg # segment number

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
	return HintingData(onPt, shearedOn, angleIn, angleOut, cidx, sidx)

def makeStemsList(g, italicAngle, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems, tolerance):
	stemsListX_temp = []
	stemsListY_temp = []
	def addStemToList(src, tgt, angle, existingStems):
		dx, dy = HF.absoluteDiffOfPairs(src.shearedPos, tgt.shearedPos)
		c_distance = ( HF.roundbase(dx, roundFactor_Stems), HF.roundbase(dy, roundFactor_Stems) )
		hypoth = HF.distanceOfPairs(src.shearedPos, tgt.shearedPos)
		stem = (src, tgt, c_distance)
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
				if HF.closeAngleModulo180_withTolerance(sa, ta, tolerance):
					if hasWhite(wc, src.pos, tgt.pos): break
					addStemToList(src, tgt, sa, existingStems)
	# avoid duplicates, filters temporary stems
	stemsListX_temp.sort() # sort by stem length (hypoth)
	stemsListY_temp.sort()
	stemsListX = []
	stemsListY = []
	references = []
	for (hypoth, stem) in stemsListY_temp:
		sourceAbsent = not HF.exists(references, lambda y: HF.approxEqual(stem[0].pos.y, y, 0.025))
		targetAbsent = not HF.exists(references, lambda y: HF.approxEqual(stem[1].pos.y, y, 0.025))
		if sourceAbsent or targetAbsent:
			stemsListY.append(stem)
		if sourceAbsent:
			references.append(stem[0].pos.y)
		if targetAbsent:
			references.append(stem[1].pos.y)

	references = []
	for (hypoth, stem) in stemsListX_temp:
		sourceAbsent = not HF.exists(references, lambda x: HF.approxEqual(stem[0].shearedPos[0], x, 0.025))
		targetAbsent = not HF.exists(references, lambda x: HF.approxEqual(stem[1].shearedPos[0], x, 0.025))
		if sourceAbsent or targetAbsent:
			stemsListX.append(stem)
		if sourceAbsent:
			references.append(stem[0].shearedPos[0])
		if targetAbsent:
			references.append(stem[1].shearedPos[0])

	return (stemsListX, stemsListY)

### - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def makeGroups(g, ital, X, autoh):
	if X:
		proj = lambda p: p[0]
		ortho_proj = lambda p: p[1]
	else:
		proj = lambda p: p[1]
		ortho_proj = lambda p: p[0]
	contours = []
	for c in g:
		contours.append([])
	byPos = {}
	# make a copy of all contours with hinting data
	# and groups the ON points having the same 'proj' coordinate (sheared X or Y)
	for contseg in contourSegmentIterator(g):
		hd = makeHintingData(g, ital, contseg)
		contours[contseg[0]].append(hd)
		pos = int(round(proj(hd.shearedPos)))

		# fuse zones
		if not X:
			zd = autoh.zoneAt(pos)
			if None != zd: pos = zd[2]

		ptsAtPos = HF.getOrPutDefault(byPos, pos, [])
		ptsAtPos.append((ortho_proj(hd.shearedPos), contseg))

	byPos = [(k, sorted(v)) for (k, v) in byPos.iteritems()]# if len(v) > 1]
	groups = {}
	for pos, pts in byPos:
		components = []
		for _, (cont,seg) in pts:
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
	return (contours,groups)

def printGroups((contours, groups), axis):
	print "Groups for", axis
	for pos, comps in sorted(groups.iteritems(), reverse=True):
		print pos, ":",
		for comp in comps:
			print '{',
			for cont,seg in comp:
				print str(cont)+'.'+str(seg),
			print "}",
		print ""

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
			(XStems, YStems) = makeStemsList(g, ital, minStemX, minStemY, maxStemX, maxStemY, \
					roundFactor_Stems, self.tthtm.angleTolerance)
			XStems = [stem[2][0] for stem in XStems]
			YStems = [stem[2][1] for stem in YStems]
			stemsValuesXList.extend(XStems)
			stemsValuesYList.extend(YStems)
			progressBar.increment(tick)

		self.sortAndStoreValues(stemsValuesXList, roundFactor_Jumps, isHorizontal=False)
		self.sortAndStoreValues(stemsValuesYList, roundFactor_Jumps, isHorizontal=True)

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
				stemPitch = float(self.TTHToolInstance.c_fontModel.UPM)/roundedStem
			else:
				stemPitch = float(self.TTHToolInstance.c_fontModel.UPM)/width
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
		if stemName in self.TTHToolInstance.c_fontModel.stems:
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
		if zoneName in self.TTHToolInstance.c_fontModel.zones:
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
		self.singleLinkCommandName = { False: 'singleh', True:'singlev' }
		self.doubleLinkCommandName = { False: 'doubleh', True:'doublev' }
		self.alignCommandName = { False: 'alignb', True:'alignt' }

	def filterStems(self, stems):
		g_stemsListX, g_stemsListY = stems
		newX, newY = [], []
		for stem in g_stemsListY:
			name = self.guessStemForDistance(stem[0], stem[1], True)
			if None != name:
				newY.append((stem, name))
		for stem in g_stemsListX:
			name = self.guessStemForDistance(stem[0], stem[1], False)
			if None != name:
				newX.append((stem,name))
		return (newX, newY)

	def markStems(self, stems, (contoursY, groupsY)):
		sx, sy = stems
		for (stem, stemName) in sy:
			for i in range(2):
				contoursY[stem[i].cont][stem[i].seg].inStemY = True

	def applyStems(self, stems, contours, isHorizontal):
		for (stem, stemName) in stems:
			src, tgt = stem[0], stem[1]
			hd0 = contours[src.cont][src.seg]
			hd1 = contours[tgt.cont][tgt.seg]
			if hd0.touched and hd1.touched: continue
			if not (hd0.touched or hd1.touched):
				self.addDoubleLink(src, tgt, stemName, isHorizontal)
				hd0.touched = True
				hd1.touched = True
				continue
			if hd0.touched:
				self.addSingleLink(src.pos.name, tgt.pos.name, isHorizontal, stemName)
				hd1.touched = True
			else:
				self.addSingleLink(tgt.pos.name, src.pos.name, isHorizontal, stemName)
				hd0.touched = True

	def guessStemForDistance(self, p1, p2, isHorizontal):
		if isHorizontal:
			detectedWidth = abs(p1.shearedPos[1] - p2.shearedPos[1])
		else:
			detectedWidth = abs(p1.shearedPos[0] - p2.shearedPos[0])
		candidatesList = []
		for stemName, stem in self.TTHToolInstance.c_fontModel.stems.iteritems():
			if stem['horizontal'] != isHorizontal: continue
			w = int(stem['width'])
			if abs(w - detectedWidth) <= detectedWidth*0.25:
				candidatesList.append((abs(w - detectedWidth), stemName))

		if candidatesList != []:
			candidatesList.sort()
			stemName = candidatesList[0][1]
			return stemName
		else:
			return None

	def addSingleLink(self, p1name, p2name, isHorizontal, stemName=""):
		command = {}
		command['code'] = self.singleLinkCommandName[isHorizontal]
		command['point1'] = p1name
		command['point2'] = p2name
		if stemName != "":
			command['stem'] = stemName
		self.TTHToolInstance.glyphTTHCommands.append(command)

	def addDoubleLink(self, p1, p2, stemName, isHorizontal):
		if stemName == None:
			return
		newCommand = {}
		if isHorizontal:
			newCommand['code'] = 'doublev'
		else:
			newCommand['code'] = 'doubleh'
		newCommand['point1'] = p1.pos.name#self.TTHToolInstance.pointCoordinatesToName[(p1.x, p1.y)]
		newCommand['point2'] = p2.pos.name#self.TTHToolInstance.pointCoordinatesToName[(p2.x, p2.y)]
		newCommand['stem'] = stemName
		if newCommand not in self.TTHToolInstance.glyphTTHCommands:
			self.TTHToolInstance.glyphTTHCommands.append(newCommand)

	def addAlign(self, g, pointName, (zoneName, isTopZone, ys, ye)):
		newAlign = {}
		if isTopZone:
			newAlign['code'] = 'alignt'
		else:
			newAlign['code'] = 'alignb'
		newAlign['point'] = pointName
		newAlign['zone'] = zoneName
		self.TTHToolInstance.glyphTTHCommands.append(newAlign)

	def zoneAt(self, y):
		for item in self.TTHToolInstance.c_fontModel.zones.iteritems():
			zd = zoneData(item)
			zoneName, isTop, yStart, yEnd = zd
			if HF.inInterval(y, (yStart, yEnd)):
				return zd

	#def attachLinksToZones(self, g):
	#	for command in self.TTHToolInstance.glyphTTHCommands:
	#		if command['code'] != 'doublev': continue
	#		p1_uniqueID = self.TTHToolInstance.pointNameToUniqueID[command['point1']]
	#		p1_y = self.TTHToolInstance.pointUniqueIDToCoordinates[p1_uniqueID][1]
	#		p2_uniqueID = self.TTHToolInstance.pointNameToUniqueID[command['point2']]
	#		p2_y = self.TTHToolInstance.pointUniqueIDToCoordinates[p2_uniqueID][1]
	#		zonePoint1 = self.zoneAt(p1_y)
	#		zonePoint2 = self.zoneAt(p2_y)
	#		if zonePoint1 == None and zonePoint2 == None: continue
	#		command['code'] = 'singlev'
	#		if zonePoint2 != None:
	#			p2 = command['point2']
	#			p1 = command['point1']
	#			command['point1'] = p2 # swap the points
	#			command['point2'] = p1
	#			self.addAlign(g, p2_uniqueID, zonePoint2)
	#		else: # elif zonePoint1 != None:
	#			self.addAlign(g, p1_uniqueID, zonePoint1)

	#def findSiblings(self, g):
	#	touchedPoints = self.findTouchedPoints(g)
	#	touchedPointsNames_X = []
	#	touchedPointsNames_Y = []
	#	for name, axis in touchedPoints:
	#		if axis == 'X':
	#			touchedPointsNames_X.append(name)
	#		else:
	#			touchedPointsNames_Y.append(name)

	#	hPoints = [(makeHintingData(g, self.ital, contSeg), contSeg) for contSeg in contourSegmentIterator(g)]
	#	for t_pointName, axis in touchedPoints:
	#		(p_x, p_y) = self.TTHToolInstance.pointONNameToContSeg[t_pointName]
	#		for onPt, (cidx, sidx) in hPoints:
	#			h_pointName = self.TTHToolInstance.pointCoordinatesToName[HF.pointToPair(onPt.pos)]

	#			# Find prev and next ON points
	#			contour = g[cidx]
	#			prev_h_Point = contour[sidx-1].onCurve
	#			prev_h_PointName = self.TTHToolInstance.pointCoordinatesToName[HF.pointToPair(prev_h_Point)]
	#			next_h_Point = contour[(sidx+1)%len(contour)].onCurve
	#			next_h_PointName = self.TTHToolInstance.pointCoordinatesToName[HF.pointToPair(next_h_Point)]

	#			if (axis == 'X' and h_pointName in touchedPointsNames_X): continue
	#			if (axis == 'Y' and h_pointName in touchedPointsNames_Y): continue
	#			if axis == 'Y' and abs(onPt.pos.y - p_y) <= 2 and h_pointName != t_pointName and (HF.isHorizontal_withTolerance(onPt.inAngle, self.tthtm.angleTolerance) or HF.isHorizontal_withTolerance(onPt.outAngle, self.tthtm.angleTolerance)):
	#				if prev_h_Point.x == p_x or next_h_Point.x == p_x:
	#					continue
	#				if (prev_h_Point.x < onPt.pos.x and prev_h_Point.y == onPt.pos.y) or (next_h_Point.x < onPt.pos.x and next_h_Point.y == onPt.pos.y):
	#					continue
	#				self.addSingleLink(t_pointName, h_pointName, isHorizontal=False)
	#			if axis == 'X' and abs(HF.shearPoint(onPt.pos, self.ital)[0] - HF.shearPair((p_x, p_y), self.ital)[0]) <= 2 and h_pointName != t_pointName and (HF.isVertical_withTolerance(onPt.inAngle-self.ital, self.tthtm.angleTolerance) or HF.isVertical_withTolerance(onPt.outAngle-self.ital, self.tthtm.angleTolerance)):
	#				if prev_h_Point.y == p_y or next_h_Point.y == p_y:
	#					continue
	#				if (prev_h_Point.y < onPt.pos.y and prev_h_Point.x == onPt.pos.x) or (next_h_Point.y < onPt.pos.y and next_h_Point.x == onPt.pos.x):
	#					continue
	#				self.addSingleLink(t_pointName, h_pointName, isHorizontal=True)

	#def findTouchedPoints(self, g):
	#	touchedPoints = sets.Set()
	#	for command in self.TTHToolInstance.glyphTTHCommands:
	#		axis = 'X'
	#		if command['code'][-1] in ['t', 'b', 'v']:
	#			axis = 'Y'
	#		for n in ('point', 'point1', 'point2'):
	#			if n in command: touchedPoints.add((command[n], axis))
	#	return touchedPoints

	#def hintWidth(self, g):
	#	pass

	#def autoAlignToZones(self, g):

	#	touchedPoints = self.findTouchedPoints(g)
	#	touchedPointsNames = [name for name,axis in touchedPoints if axis == 'Y']

	#	zones = [zoneData(item) for item in self.TTHToolInstance.c_fontModel.zones.iteritems()]
	#	hPoints = [(makeHintingData(g, self.ital, contSeg), contSeg) for contSeg in contourSegmentIterator(g)]

	#	for onPt, (cidx, sidx) in hPoints:
	#		contour = g[cidx]
	#		prev_h_Point = HF.pointToPair(contour[sidx-1].onCurve)
	#		prev_h_PointName = self.TTHToolInstance.pointCoordinatesToName[prev_h_Point]
	#		next_h_Point = HF.pointToPair(contour[(sidx+1)%len(contour)].onCurve)
	#		next_h_PointName = self.TTHToolInstance.pointCoordinatesToName[next_h_Point]

	#		neighborsAreAlreadyAligned = \
	#			(prev_h_Point[1] == onPt.pos.y and prev_h_PointName in touchedPointsNames) or \
	#			(next_h_Point[1] == onPt.pos.y and next_h_PointName in touchedPointsNames)
	#		angleIsOkay = \
	#			HF.isHorizontal_withTolerance(onPt.inAngle, self.tthtm.angleTolerance) or \
	#			HF.isHorizontal_withTolerance(onPt.outAngle, self.tthtm.angleTolerance)

	#		if neighborsAreAlreadyAligned or (not angleIsOkay): continue

	#		pointName = self.TTHToolInstance.pointCoordinatesToName[HF.pointToPair(onPt.pos)]
	#		for (zoneName, isTop, y_start, y_end) in zones:
	#			if not HF.inInterval(onPt.pos.y, (y_start, y_end)): continue
	#			newAlign = {}
	#			if isTop:
	#				newAlign['code'] = 'alignt'
	#			else:
	#				newAlign['code'] = 'alignb'
	#			newAlign['point'] = pointName
	#			newAlign['zone'] = zoneName

	#			if pointName not in touchedPointsNames:
	#				self.TTHToolInstance.glyphTTHCommands.append(newAlign)
	#				touchedPointsNames.append(pointName)

	def handleZones(self, g, (contours, groups)):
		# First, handle groups in zones
		nonZonePositions = []
		for pos, comps in groups.iteritems():
			# are we in a zone?
			zoneInfo = self.zoneAt(pos)
			if None == zoneInfo:
				nonZonePositions.append(pos)
				continue

			leader = None
			for i,comp in enumerate(comps):
				if leader != None: break
				for j, (cont, seg) in enumerate(comp):
					if contours[cont][seg].inStemY:
						leader = i,j
						break
			if leader == None:
				leader = 0,0
			else:
				i,j = leader
				if i > 0: comps[0], comps[i] = comps[i], comps[0]
				if j > 0: comps[0][0], comps[0][j] = comps[0][j], comps[0][0]
			#print "At pos", pos,", leader is", comps[0][0]

			zoneName, isTop, _, _ = zoneInfo
			nbComps = len(comps)
			cont, seg = comps[0][0]
			hd = contours[cont][seg]
			startName = hd.pos.name
			hd.touched = True
			# add align
			self.addAlign(g, startName, zoneInfo)
			# add single links
			self.addLinksInGroup((0,0), comps, contours, True)
		return nonZonePositions

	def addLinksInGroup(self, leader, comps, contours, isHorizontal):
		i,j = leader
		if i > 0: comps[0], comps[i] = comps[i], comps[0]
		if j > 0: comps[0][0], comps[0][j] = comps[0][j], comps[0][0]
		cont, seg = comps[0][0]
		hd = contours[cont][seg]
		startName = hd.pos.name
		for comp in comps[1:]:
			cont, seg = comp[0]
			hd = contours[cont][seg]
			endName = hd.pos.name
			hd.touched = True
			self.addSingleLink(startName, endName, isHorizontal)

	def handleNonZones(self, nonZonePositions, (contours, groups), isHorizontal):
		for pos in nonZonePositions:
			comps = groups[pos]
			# are there touched points at this position?
			leader = None
			for i, comp in enumerate(comps):
				for j, (cont, seg) in enumerate(comp):
					if leader != None: break
					if contours[cont][seg].touched:
						leader = i,j
			if leader != None: self.addLinksInGroup(leader, comps, contours, isHorizontal)

	def autohint(self, g):
		if self.TTHToolInstance.c_fontModel.f.info.italicAngle != None:
			self.ital = - self.TTHToolInstance.c_fontModel.f.info.italicAngle
		else:
			self.ital = 0

		self.TTHToolInstance.resetglyph(g)
		self.TTHToolInstance.glyphTTHCommands = []

		roundFactor_Stems = 1 #self.tthtm.roundFactor_Stems
		minStemX = HF.roundbase(self.tthtm.minStemX, roundFactor_Stems)
		minStemY = HF.roundbase(self.tthtm.minStemY, roundFactor_Stems)
		maxStemX = HF.roundbase(self.tthtm.maxStemX, roundFactor_Stems)
		maxStemY = HF.roundbase(self.tthtm.maxStemY, roundFactor_Stems)

		stems = self.filterStems(makeStemsList(g, self.ital, \
				minStemX, minStemY, maxStemX, maxStemY, \
				roundFactor_Stems, self.tthtm.angleTolerance))

		cgY = makeGroups(g, self.ital, False, self) # for Y auto-hinting
		cgX = makeGroups(g, self.ital, True, self) # for X auto-hinting
		#printGroups(cgX, 'X')
		#printGroups(cgY, 'Y')
		# we mark point in Y groups that have at least one stem attached to them:
		self.markStems(stems, cgY)
		# in each Y, anchor one point in the zone, if there is a zone and put siblings to the other points:
		nonZones = self.handleZones(g, cgY)
		contoursX, groupsX = cgX
		contoursY, groupsY = cgY
		# now we actually insert the stem, as double or single links, in X and Y
		self.applyStems(stems[0], contoursX, False)
		self.applyStems(stems[1], contoursY, True)
		# put siblings in Y, where there is no zone, but maybe some 'touched' points due to the stems
		self.handleNonZones(groupsX.keys(), cgX, isHorizontal=False)
		# put siblings in X, from points that were 'touched' by double-links (in 'applyStems')
		self.handleNonZones(nonZones, cgY, isHorizontal=True)

