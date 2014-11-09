import math
import string
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
		self.pos        = on
		self.name       = on.name.split(',')[0]
		self.shearedPos = sh
		self.inAngle    = ina
		self.outAngle   = outa
		self.inStem     = False
		self.touched    = False
		self.group      = None
		self.cont       = cont # contour number
		self.seg        = seg  # segment number
		self.leader     = None # who is my leader? (only leaders take part
		# in hinting commands, each component of a group has exactly one
		# leader)
	def nextOn(self, contours):
		contour = contours[self.cont]
		return contour[(self.seg+1)%len(contour)]
	def prevOn(self, contours):
		return contours[self.cont][self.seg-1]

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

def makeStemsList(g, italicAngle, xBound, yBound, roundFactor_Stems, tolerance, dedup=True):
	stemsListX_temp = []
	stemsListY_temp = []
	def addStemToList(src, tgt, angle0, angle1, existingStems):
		dx, dy = HF.absoluteDiffOfPairs(src.shearedPos, tgt.shearedPos)
		c_distance = ( HF.roundbase(dx, roundFactor_Stems), HF.roundbase(dy, roundFactor_Stems) )
		hypoth = HF.distanceOfPairs(src.shearedPos, tgt.shearedPos)
		## if they are horizontal, treat the stem on the Y axis
		if (HF.isHorizontal_withTolerance(angle0, tolerance) and
			HF.isHorizontal_withTolerance(angle1, tolerance) and
			not existingStems['h'] ) :
			if HF.inInterval(c_distance[1], yBound) and HF.inInterval(hypoth, yBound):
				existingStems['h'] = True
				stemsListY_temp.append((hypoth, (src, tgt, c_distance[1])))
		## if they are vertical, treat the stem on the X axis
		elif(HF.isVertical_withTolerance(angle0, tolerance) and
			HF.isVertical_withTolerance(angle1, tolerance) and
			not existingStems['v'] ) : # the angle is already sheared to counter italic
			if HF.inInterval(c_distance[0], xBound) and HF.inInterval(hypoth, xBound):
				existingStems['v'] = True
				stemsListX_temp.append((hypoth, (src, tgt, c_distance[0])))
		else:
		## Here, the angle of the stem is more diagonal
		# ... do something here with diagonal
			pass

	def hasWhite(wc, source, target):
		if wc[0] == None:
			wc[0] = hasSomeWhite(source, target, g, xBound[1], yBound[1])
		return wc[0]

	hPoints = [makeHintingData(g, italicAngle, contSeg) for contSeg in contourSegmentIterator(g)]
	for gidx, src in enumerate(hPoints):
		for tgt in hPoints[gidx+1:]:
			existingStems = {'h':False, 'v':False, 'd':False}
			wc = [None]
			for sa in (src.inAngle, src.outAngle):
				for ta in (tgt.inAngle, tgt.outAngle):
					if HF.closeAngleModulo180_withTolerance(sa, ta, tolerance):
						if hasWhite(wc, src.pos, tgt.pos): break
						addStemToList(src, tgt, sa, ta, existingStems)
	stemsListX_temp.sort() # sort by stem length (hypoth)
	stemsListY_temp.sort()
	if not dedup: # dedup means de-duplications
		stemsX = [stem for (hypoth, stem) in stemsListX_temp]
		stemsY = [stem for (hypoth, stem) in stemsListY_temp]
		return (stemsX, stemsY)
	# avoid duplicates, filters temporary stems
	stemsLists = ([], [])
	for i, stems in enumerate([stemsListX_temp, stemsListY_temp]):
		references = set()
		for (hypoth, stem) in stems:
			sourceAbsent = not HF.exists(references, lambda y: HF.approxEqual(stem[0].shearedPos[i], y, 0.025))
			targetAbsent = not HF.exists(references, lambda y: HF.approxEqual(stem[1].shearedPos[i], y, 0.025))
			if sourceAbsent or targetAbsent:
				stemsLists[i].append(stem)
			if sourceAbsent: references.add(stem[0].shearedPos[i])
			if targetAbsent: references.add(stem[1].shearedPos[i])
	return stemsLists

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
	angle = 0.0
	if X: angle = 90.0
	# make a copy of all contours with hinting data
	# and groups the ON points having the same 'proj' coordinate (sheared X or Y)
	for contseg in contourSegmentIterator(g):
		hd = makeHintingData(g, ital, contseg)
		contours[contseg[0]].append(hd)
		goodAngle = HF.closeAngleModulo180_withTolerance(hd.inAngle, angle, autoh.tthtm.angleTolerance) \
			or HF.closeAngleModulo180_withTolerance(hd.outAngle, angle, autoh.tthtm.angleTolerance)
		if not goodAngle: continue
		pos = int(round(proj(hd.shearedPos)))
		ptsAtPos = HF.getOrPutDefault(byPos, pos, [])
		ptsAtPos.append((ortho_proj(hd.shearedPos), contseg))

	byPos = [(k, sorted(v)) for (k, v) in byPos.iteritems()]# if len(v) > 1]
	byPos.sort()
	groups = {}
	lastPos = -10000
	for pos, pts in byPos:
		if pos - lastPos < 10:
			pos = lastPos
			components = groups[pos]
		else:
			components = []
			lastPos = pos
		for _, (cont,seg) in pts:
			contours[cont][seg].group = pos
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

def computeMaxStemOnO(tthtm, font):
	roundFactor_Stems = tthtm.roundFactor_Stems
	roundFactor_Jumps = tthtm.roundFactor_Jumps
	minStemX = HF.roundbase(tthtm.minStemX, roundFactor_Stems)
	minStemY = HF.roundbase(tthtm.minStemY, roundFactor_Stems)
	maxStemX = HF.roundbase(tthtm.maxStemX, roundFactor_Stems)
	maxStemY = HF.roundbase(tthtm.maxStemY, roundFactor_Stems)
	xBound = minStemX*(1.0-roundFactor_Stems/100.0), maxStemX*(1.0+roundFactor_Stems/100.0)
	yBound = minStemY*(1.0-roundFactor_Stems/100.0), maxStemY*(1.0+roundFactor_Stems/100.0)
	if font.info.italicAngle != None:
		ital = - font.info.italicAngle
	else:
		ital = 0
	if 'O' not in font:
		print "WARNING: glyph 'O' missing, unable to calculate stems"
		return -1
	g = font['O']
	(O_stemsListX, O_stemsListY) = makeStemsList(g, ital, xBound, yBound, roundFactor_Stems, tthtm.angleTolerance)

	if O_stemsListX == None:
		return 250
	else:
		return int(round(2.0 * max([stem[2] for stem in O_stemsListX])))

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

		maxStemX = maxStemY = computeMaxStemOnO(self.tthtm, font)
		if maxStemX == -1:
			return

		xBound = minStemX*(1.0-roundFactor_Stems/100.0), maxStemX*(1.0+roundFactor_Stems/100.0)
		yBound = minStemY*(1.0-roundFactor_Stems/100.0), maxStemY*(1.0+roundFactor_Stems/100.0)

		if font.info.italicAngle != None:
			ital = - font.info.italicAngle
		else:
			ital = 0

		stemsValuesXList = []
		stemsValuesYList = []

		progressBar.set(0)
		tick = 100.0/len(string.ascii_letters)
		for name in string.ascii_letters:
			g = font[name]
			(XStems, YStems) = makeStemsList(g, ital, xBound, yBound, roundFactor_Stems, self.tthtm.angleTolerance)
			XStems = [stem[2] for stem in XStems]
			YStems = [stem[2] for stem in YStems]
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

class Collection:
	def __init__(self):
		self.positions = set()
		self.nicePositions = set()
		self.processedPositions = set()
		self.leaderPos = None
		self.minPos = 10000000
		self.bounds = (10000000,-10000000)
	def covers(self, p):
		return (p in self.positions)
	def add(self, pos, isNice):
		self.minPos = min(self.minPos, pos)
		self.positions.add(pos)
		if isNice:
			self.nicePositions.add(pos)
		self.bounds = min(self.bounds[0], pos), max(self.bounds[1], pos)

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
			#if None != name:
			newX.append((stem, name))
		return (newX, newY)

	def beautifulStem(self, stem, contours):
		hd0 = contours[stem[0].cont][stem[0].seg]
		hd1 = contours[stem[1].cont][stem[1].seg]
		return (HF.closeAngleModulo180_withTolerance(hd0.inAngle, hd0.outAngle, 1.0)
		    and HF.closeAngleModulo180_withTolerance(hd0.inAngle, hd1.inAngle, 1.0)
		    and HF.closeAngleModulo180_withTolerance(hd1.inAngle, hd1.outAngle, 1.0))

	def makeCollections(self, contours, stems):
		collections = []
		for stem, stemName in stems:
			src = contours[stem[0].cont][stem[0].seg]
			tgt = contours[stem[1].cont][stem[1].seg]
			group0 = src.group
			group1 = tgt.group
			beautiful = self.beautifulStem(stem, contours)
			#print "(",group0, group1,src.pos,tgt.pos,")",
			if group0 == None or group1 == None: continue
			coll = None
			for c in collections:
				if c.covers(group0) or c.covers(group1):
					coll = c
			if coll == None:
				collections.append(Collection())
				coll = collections[-1]
			coll.add(group0, beautiful)
			coll.add(group1, beautiful)
		collections.sort(key=lambda c: c.minPos)
		print "Collections:"
		for coll in collections:
			for p in coll.positions:
				print p,
			print " >|< "
		return collections

	def findLeftRight(self, collections):
		nbColls = len(collections)
		#--------------
		i = 0
		while (i<nbColls) and len(collections[i].nicePositions) == 0:
			i += 1
		if i == nbColls: return 0,None, 0,None
		col = collections[i]
		nicePositions = sorted(col.nicePositions)
		#print "Left, positions", col.positions
		#print "Left, nicePositions", nicePositions
		leftmost = None
		l = len(nicePositions)
		if l >= 3:
			leftmost = nicePositions[1]
		elif l >= 1:
			leftmost = nicePositions[0]
		#----------------
		j = nbColls-1
		while (j>=0) and len(collections[j].nicePositions) == 0:
			j -= 1
		col = collections[j]
		nicePositions = sorted(col.nicePositions)
		#print "Right, nicePositions", nicePositions
		rightmost = None
		l = len(nicePositions)
		if l >= 3:
			rightmost = nicePositions[-2]
		elif l >= 1:
			rightmost = nicePositions[-1]
		ret = i,leftmost, j,rightmost
		print "findLeftRight returns", ret
		return ret

	def processCollection(self, coll, groups, contours, interpolatePossible, bounds, isHorizontal):
		remainingPositions = sorted(coll.positions - coll.processedPositions)
		if coll.leaderPos == None:
			if len(coll.nicePositions)>0:
				coll.leaderPos = sorted(coll.nicePositions)[0]
			elif len(coll.processedPositions)>0:
				coll.leaderPos = sorted(coll.processedPositions)[0]
			else:
				coll.leaderPos = remainingPositions.pop()
				self.addLinksInGroup(0, groups[coll.leaderPos], contours, isHorizontal)
		cont,seg = groups[coll.leaderPos][0][0]
		lead = contours[cont][seg].leader
		if len(remainingPositions) == len(coll.positions) and interpolatePossible:
			leftmost, rightmost = bounds
			self.addInterpolate(leftmost, lead, rightmost, isHorizontal)
		lead.touched = True
		while len(remainingPositions)>0:
			pos = remainingPositions.pop()
			coll.processedPositions.add(pos)
			cont,seg = groups[pos][0][0]
			tgt = contours[cont][seg].leader
			stemName = self.guessStemForDistance(lead, tgt, isHorizontal)
			if not tgt.touched:
				tgt.touched = True
				self.addSingleLink(lead.name, tgt.name, isHorizontal, stemName)
			self.addLinksInGroup(0, groups[pos], contours, isHorizontal)

	def markStems(self, stems, contours):
		for (stem, stemName) in stems:
			for i in range(2):
				hd = contours[stem[i].cont][stem[i].seg]
				hd.inStem = True

	def applyStems(self, stems, contours, isHorizontal):
		for (stem, stemName) in stems:
			src, tgt = stem[0], stem[1]
			src = contours[src.cont][src.seg].leader
			tgt = contours[tgt.cont][tgt.seg].leader
			if src.touched and tgt.touched: continue
			if not (src.touched or tgt.touched):
				# self.addDoubleLink(src, tgt, stemName, isHorizontal)
				# src.touched = True
				# tgt.touched = True
				continue
			if src.touched:
				self.addSingleLink(src.name, tgt.name, isHorizontal, stemName)
				tgt.touched = True
			else:
				self.addSingleLink(tgt.name, src.name, isHorizontal, stemName)
				src.touched = True

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

	def addSingleLink(self, p1name, p2name, isHorizontal, stemName):
		command = {}
		command['code'] = self.singleLinkCommandName[isHorizontal]
		command['point1'] = p1name
		command['point2'] = p2name
		if stemName != None:
			command['stem'] = stemName
		self.TTHToolInstance.glyphTTHCommands.append(command)
		return command

	def addInterpolate(self, p1, p, p2, isHorizontal):
		newCommand = {}
		if isHorizontal:
			newCommand['code'] = 'interpolatev'
		else:
			newCommand['code'] = 'interpolateh'
		newCommand['point1'] = p1.name
		newCommand['point2'] = p2.name
		newCommand['point'] = p.name
		newCommand['align'] = 'round'
		if newCommand not in self.TTHToolInstance.glyphTTHCommands:
			self.TTHToolInstance.glyphTTHCommands.append(newCommand)

	def addDoubleLink(self, p1, p2, stemName, isHorizontal):
		if stemName == None:
			return
		newCommand = {}
		if isHorizontal:
			newCommand['code'] = 'doublev'
		else:
			newCommand['code'] = 'doubleh'
		newCommand['point1'] = p1.name#self.TTHToolInstance.pointCoordinatesToName[(p1.x, p1.y)]
		newCommand['point2'] = p2.name#self.TTHToolInstance.pointCoordinatesToName[(p2.x, p2.y)]
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

	def putALeaderFirst(self, comps, contours):
		leaderComp = None
		for i,comp in enumerate(comps):
			compLeader = None
			for j, (cont, seg) in enumerate(comp):
				if contours[cont][seg].inStem and compLeader == None:
					compLeader = j
					if leaderComp == None:
						leaderComp = i
				if compLeader != None: break
			if compLeader == None: compLeader = 0
			if compLeader > 0: comp[compLeader], comp[0] = comp[0], comp[compLeader]
			c0,s0 = comp[0]
			for c,s in comp: contours[c][s].leader = contours[c0][s0]
		if leaderComp != None:
			if leaderComp > 0: comps[0], comps[leaderComp] = comps[leaderComp], comps[0]
		for c in contours:
			for s in c:
				if s.leader == None:
					s.leader = s

	def handleZones(self, g, (contours, groups)):
		# First, handle groups in zones
		nonZonePositions = []
		for pos, comps in groups.iteritems():
			# are we in a zone?
			zoneInfo = self.zoneAt(pos)
			if None == zoneInfo:
				nonZonePositions.append(pos)
				continue
			zoneName, isTop, _, _ = zoneInfo
			nbComps = len(comps)
			cont, seg = comps[0][0]
			hd = contours[cont][seg]
			hd.touched = True
			# add align
			self.addAlign(g, hd.name, zoneInfo)
			# add single links
			self.addLinksInGroup(0, comps, contours, True)
		return nonZonePositions

	def addLinksInGroup(self, leader, comps, contours, isHorizontal):
		cont, seg = comps[0][0]
		startName = contours[cont][seg].name
		for i, comp in enumerate(comps):
			if i == leader: continue
			cont, seg = comp[0]
			hd = contours[cont][seg]
			if hd.touched: continue
			hd.touched = True
			self.addSingleLink(startName, hd.name, isHorizontal, None)

	def handleNonZones(self, nonZonePositions, (contours, groups), isHorizontal):
		for pos in nonZonePositions:
			comps = groups[pos]
			# are there touched points at this position?
			leader = None
			for i, comp in enumerate(comps):
				for j, (cont, seg) in enumerate(comp):
					if leader != None: break
					if contours[cont][seg].touched:
						leader = i#,j
			if leader != None: self.addLinksInGroup(leader, comps, contours, isHorizontal)

	def autoHintY(self, g, stems):
		cg = makeGroups(g, self.ital, False, self) # for Y auto-hinting
		contours, groups = cg
		#printGroups(cg, 'Y')
		# we mark point in Y groups that have at least one stem attached to them:
		self.markStems(stems, contours)
		for pos, comps in groups.iteritems(): self.putALeaderFirst(comps, contours)
		# in each Y, anchor one point in the zone, if there is a zone and put siblings to the other points:
		nonZones = self.handleZones(g, cg)
		# now we actually insert the stems, as double or single links, in Y
		self.applyStems(stems, contours, True)
		# put siblings in Y, where there is no zone, but maybe some 'touched' points due to the stems
		self.handleNonZones(nonZones, cg, isHorizontal=True)

	def autoHintX(self, g, stems):
		cg = makeGroups(g, self.ital, True, self) # for X auto-hinting
		contours, groups = cg
		#printGroups(cg, 'X')
		if len(groups) == 0: return
		# we mark point in X groups that have at least one stem attached to them:
		self.markStems(stems, contours)
		for pos, comps in groups.iteritems(): self.putALeaderFirst(comps, contours)
		
		collections = self.makeCollections(contours, stems)
		lci,lmi, rci,rmi = self.findLeftRight(collections)
		leftColl = collections[lci]
		rightColl = collections[rci]
		bounds = None

		if rmi != None:
			rightColl.leaderPos = rmi
			rightColl.processedPositions.add(rmi)
			cont, seg = groups[rmi][0][0]
			rightmost = contours[cont][seg].leader
			self.addSingleLink('lsb', rightmost.name, False, None)['round'] = 'true'
			self.addSingleLink(rightmost.name, 'rsb', False, None)['round'] = 'true'
			rightmost.touched = True
			self.addLinksInGroup(0, groups[rightmost.group], contours, False)
			self.processCollection(rightColl, groups, contours, False, None, isHorizontal=False)
			if lmi != None and lci != rci:
				leftColl.processedPositions.add(lmi)
				cont, seg = groups[lmi][0][0]
				leftmost = contours[cont][seg].leader
				bounds = leftmost, rightmost
				stemName = self.guessStemForDistance(leftmost, rightmost, False)
				link = self.addSingleLink(rightmost.name, leftmost.name, False, stemName)
				if stemName == None:
					link['round'] = 'true'
				leftmost.touched = True
				self.addLinksInGroup(0, groups[leftmost.group], contours, False)
				leftColl.leaderPos = lmi
				self.processCollection(leftColl, groups, contours, False, None, isHorizontal=False)
		interpolatePossible = (lmi != None) and (rmi != None) and (lci != rci)
		for coll in collections:
			if len(coll.processedPositions) < len(coll.positions):
				self.processCollection(coll, groups, contours, \
						interpolatePossible, bounds, isHorizontal=False)

	def autohint(self, g):
		font = self.TTHToolInstance.c_fontModel.f
		maxStemX = maxStemY = computeMaxStemOnO(self.tthtm, font)
		if font.info.italicAngle != None:
			self.ital = - font.info.italicAngle
		else:
			self.ital = 0

		self.TTHToolInstance.resetglyph(g)
		self.TTHToolInstance.glyphTTHCommands = []

		xBound = self.tthtm.minStemX, maxStemX
		yBound = self.tthtm.minStemY, maxStemY
		print "(minStemX, maxStemX) = ", xBound

		stems = makeStemsList(g, self.ital, xBound, yBound, 1, self.tthtm.angleTolerance, dedup=False)
		stems = self.filterStems(stems)
		self.autoHintX(g, stems[0])
		stems = makeStemsList(g, self.ital, xBound, yBound, 1, self.tthtm.angleTolerance)
		stems = self.filterStems(stems)
		self.autoHintY(g, stems[1])

