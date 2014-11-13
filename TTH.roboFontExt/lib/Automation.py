import math
import string
import weakref
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
	def __init__(self, on, sh, ina, outa, cont, seg, weight):
		self.pos        = on
		self.name       = on.name.split(',')[0]
		self.shearedPos = sh
		self.inAngle    = ina
		self.outAngle   = outa
		self.cont       = cont # contour number
		self.seg        = seg  # segment number
		# the following change when we switch from X- to Y-autohinting
		self.weight2D   = weight
		self.weight     = weight
		self.touched    = False
		self.alignment  = None
		self.leader     = None # who is my leader? (only leaders take part
		# in hinting commands, each component of a alignment has exactly one
		# leader)
	def reset(self):
		self.weight     = 0.0
		self.touched    = False
		self.alignment  = None
		self.leader     = None
	def nextOn(self, contours):
		contour = contours[self.cont]
		return contour[(self.seg+1)%len(contour)]
	def prevOn(self, contours):
		return contours[self.cont][self.seg-1]

def makeHintingData(g, ital, (cidx, sidx), computeWeight=False):
	"""Compute data relevant to hinting for the ON point in the
	sidx-th segment of the cidx-th contour of glyph 'g'."""
	contour = g[cidx]
	contourLen = len(contour)
	segment = contour[sidx]
	onPt = segment.onCurve
	nextOff = contour[(sidx+1) % contourLen].points[0]
	nextOn = contour[(sidx+1) % contourLen].onCurve
	prevOn = contour[sidx-1].onCurve
	if len(segment.points) > 1:
		prevOff = segment[-2]
	else:
		prevOff = prevOn
	if computeWeight:
		weightX = abs(nextOn.x - onPt.x) + abs(prevOn.x - onPt.x)
		weightY = abs(nextOn.y - onPt.y) + abs(prevOn.y - onPt.y)
		weight = (weightX, weightY)
	else:
		weight = None
	shearedOn = HF.shearPoint(segment.onCurve, ital)
	angleIn  = HF.angleOfVectorBetweenPairs(HF.shearPoint(prevOff, ital), shearedOn)
	angleOut = HF.angleOfVectorBetweenPairs(shearedOn, HF.shearPoint(nextOff, ital))
	return HintingData(onPt, shearedOn, angleIn, angleOut, cidx, sidx, weight)

def makeContours(g, ital):
	contours = []
	for c in g:
		contours.append([])
	# make a copy of all contours with hinting data
	for contseg in contourSegmentIterator(g):
		hd = makeHintingData(g, ital, contseg, computeWeight=True)
		contours[contseg[0]].append(hd)
	return contours

def makeStemsList(g, contours, italicAngle, xBound, yBound, roundFactor_Stems, tolerance, dedup=True):
	stemsListX_temp = []
	stemsListY_temp = []
	def addStemToList(src, tgt, c_distance, hypoth, angle0, angle1, existingStems):
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

	contsegs = [contSeg for contSeg in contourSegmentIterator(g)]
	bound = min(xBound[0], yBound[0])-1, max(xBound[1], yBound[1])+1
	for gidx, (sc, ss) in enumerate(contsegs):
		src = contours[sc][ss]
		for (tc, ts) in contsegs[gidx+1:]:
			tgt = contours[tc][ts]
			if (src.cont == tgt.cont) and (abs(src.seg-tgt.seg) == 1): # neighbors can't make a stem
				continue
			dx, dy = HF.absoluteDiffOfPairs(src.shearedPos, tgt.shearedPos)
			c_distance = ( HF.roundbase(dx, roundFactor_Stems), HF.roundbase(dy, roundFactor_Stems) )
			hypoth = HF.distanceOfPairs(src.shearedPos, tgt.shearedPos)
			if not HF.inInterval(hypoth, bound): continue

			wc = [None]
			existingStems = {'h':False, 'v':False, 'd':False}
			for sa in (src.inAngle, src.outAngle):
				for ta in (tgt.inAngle, tgt.outAngle):
					if HF.closeAngleModulo180_withTolerance(sa, ta, tolerance):
						if hasWhite(wc, src.pos, tgt.pos): break
						addStemToList(src, tgt, c_distance, hypoth, sa, ta, existingStems)
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
	contours = makeContours(g, ital)
	(O_stemsListX, O_stemsListY) = makeStemsList(g, contours, ital, xBound, yBound, roundFactor_Stems, tthtm.angleTolerance)

	if O_stemsListX == None:
		return 200
	else:
		return int(round(1.5 * max([stem[2] for stem in O_stemsListX])))

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

		if font.info.italicAngle != None:
			ital = - font.info.italicAngle
		else:
			ital = 0

		maxStemX = maxStemY = computeMaxStemOnO(self.tthtm, font)
		if maxStemX == -1:
			return

		xBound = minStemX*(1.0-roundFactor_Stems/100.0), maxStemX*(1.0+roundFactor_Stems/100.0)
		yBound = minStemY*(1.0-roundFactor_Stems/100.0), maxStemY*(1.0+roundFactor_Stems/100.0)

		stemsValuesXList = []
		stemsValuesYList = []

		progressBar.set(0)
		tick = 100.0/len(string.ascii_letters)
		for name in string.ascii_letters:
			g = font[name]
			contours = makeContours(g, ital)
			(XStems, YStems) = makeStemsList(g, contours, ital, xBound, yBound, roundFactor_Stems, self.tthtm.angleTolerance)
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

### - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class Alignment(object):
	def __init__(self, pos):
		self.components = []
		self.pos = pos
		self.weight = 0.0
		self.zone = None
	def leaderPoint(self, pos, contours):
		cont, seg = self.components[pos][0]
		return contours[cont][seg].leader()
	def findZone(self, contours, autoh):
		for comp in self.components:
			for (cont,seg) in comp:
				pt = contours[cont][seg]
				z = autoh.zoneAt(pt.pos.y)
				if z != None:
					self.zone = z
		return self.zone
	def addPoint(self, cont, seg, contours):
		pt = contours[cont][seg]
		pt.alignment = self.pos
		self.weight += pt.weight
		lenc = len(contours[cont])
		prevId = cont, (seg+lenc-1) % lenc
		nextId = cont, (seg+1) % lenc
		found = False
		for comp in self.components:
			if (prevId in comp) or (nextId in comp):
				comp.append((cont,seg))
				found = True
				break
		if not found:
			self.components.append([(cont,seg)])
	def putLeadersFirst(self, contours):
		leaderComp = None
		maxW = 0.0
		comps = self.components
		for i,comp in enumerate(comps):
			compLeader = None
			localMaxW = 0.0
			for j, (cont, seg) in enumerate(comp):
				pt = contours[cont][seg]
				if pt.weight > localMaxW:
					compLeader = j
					localMaxW = pt.weight
				if pt.weight > maxW: #and compLeader == None:
					leaderComp = i
					maxW = pt.weight
			if compLeader == None: compLeader = 0
			if compLeader > 0: comp[compLeader], comp[0] = comp[0], comp[compLeader]
			l = contours[comp[0][0]][comp[0][1]]
			for c,s in comp: contours[c][s].leader = weakref.ref(l)
		if leaderComp != None and leaderComp > 0:
			comps[0], comps[leaderComp] = comps[leaderComp], comps[0]
		# remaining points have themselve as leader
		for c in contours:
			for s in c:
				if s.leader == None:
					s.leader = weakref.ref(s)
	def addLinks(self, leader, contours, isHorizontal, autoh):
		comps = self.components
		cont, seg = comps[leader][0]
		lead = contours[cont][seg]
		lead.touched = True
		startName = lead.name
		for i, comp in enumerate(comps):
			if i == leader: continue
			cont, seg = comp[0]
			hd = contours[cont][seg]
			if hd.touched: continue
			hd.touched = True
			autoh.addSingleLink(startName, hd.name, isHorizontal, None)

### - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class Group:
	def __init__(self):
		self.alignments = set()
		self.leaderPos = None
		self.bounds = (10000000,-10000000)
	def width(self):
		return self.bounds[1] - self.bounds[0]
	def prepare(self, alignments):
		self.alignments = sorted([alignments[p] for p in self.alignments], key=lambda a:a.weight, reverse=True)
		self.avgPos = 0.5 * (self.bounds[0] + self.bounds[1])
		#print "Prepared alignments:",
		#for a in self.alignments:
		#	print '{'+str(a.pos)+', '+str(a.weight)+'}',
		#print ''
	def sticks(self, l, r):
		if l < self.bounds[0] and self.bounds[1] < r: return True
		if self.bounds[0] < l and r < self.bounds[1]: return True
		return ((l,False) in self.alignments) or ((r,True) in self.alignments)
	def add(self, pos):
		self.alignments.add(pos)
		self.bounds = min(self.bounds[0], pos[0]), max(self.bounds[1], pos[0])

### - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def makeAlignments(ital, contours, X, autoh):
	if X: X = 0
	else: X = 1
	proj = lambda p: p[X]
	ortho_proj = lambda p: p[1-X]
	byPos = {}
	angle = (1-X) * 90.0
	# make a copy of all contours with hinting data and groups the ON points
	# having the same 'proj' coordinate (sheared X or Y)
	for cont, contour in enumerate(contours):
		for seg, hd in enumerate(contour):
			hd.weight = hd.weight2D[1-X]
			goodAngle = HF.closeAngleModulo180_withTolerance(hd.inAngle,  angle, autoh.tthtm.angleTolerance) \
				   or HF.closeAngleModulo180_withTolerance(hd.outAngle, angle, autoh.tthtm.angleTolerance)
			if not goodAngle: continue
			pos = int(round(proj(hd.shearedPos)))
			ptsAtPos = HF.getOrPutDefault(byPos, pos, [])
			ptsAtPos.append((ortho_proj(hd.shearedPos), (cont, seg)))

	byPos = [(k, sorted(v)) for (k, v) in byPos.iteritems()]
	byPos.sort()
	alignments = {}
	lastPos = -100000
	for pos, pts in byPos:
		if pos - lastPos < 10:
			pos = lastPos
			alignment = alignments[pos]
		else:
			alignment = Alignment(pos)
			lastPos = pos
		for _, (cont, seg) in pts:
			alignment.addPoint(cont, seg, contours)
		alignments[pos] = alignment
	return alignments

def printAlignments(alignments, axis):
	print "Alignments for", axis
	for pos, alignment in sorted(alignments.iteritems(), reverse=True):
		print pos, ":",
		for comp in alignment.components:
			print '{',
			for cont,seg in comp:
				print str(cont)+'.'+str(seg),
			print "}",
		print ""

### - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def zoneData((zoneName, zone)):
	isTop = zone['top']
	if isTop:
		y_start = int(zone['position'])
		y_end = int(zone['position']) + int(zone['width'])
	else:
		y_start = int(zone['position']) - int(zone['width'])
		y_end = int(zone['position'])
	return (zoneName, isTop, y_start, y_end)

### - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

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
				newX.append((stem, name))
		return (newX, newY)

	def makeGroups(self, contours, stems, debug=False):
		groups = []
		for stem in stems:
			src = contours[stem[0].cont][stem[0].seg]
			tgt = contours[stem[1].cont][stem[1].seg]
			pos0 = src.alignment
			pos1 = tgt.alignment
			if debug: print "(",pos0, pos1,src.pos,tgt.pos,")"
			if pos0 == None or pos1 == None: continue
			if pos1 < pos0:
				pos0, pos1 = pos1, pos0
				src, tgt = tgt, src
			grp = None
			for c in groups:
				if c.sticks(pos0, pos1):
					grp = c
			if grp == None:
				groups.append(Group())
				grp = groups[-1]
			grp.add((pos0,False))
			grp.add((pos1,True))
		for grp in groups:
			grp.alignments = set([p for (p,x) in grp.alignments])
		groups.sort(key=lambda g: g.bounds[0]+g.bounds[1])
		if debug:
			print "Groups:"
			for grp in groups:
				for p in grp.alignments:
					print p,
				print " >|< "
		return groups

	def findLeftRight(self, groups):
		if len(groups) == 0: return None, None, None, None
		atLeastTwoGroups = (len(groups) >= 2)
		groupWeights = [((i,g), sum([a.weight for a in g.alignments])) for (i, g) in enumerate(groups)]
		#weights = [w (g, w) in groupWeights if w >= threshold]
		(i,lg), w0 = groupWeights[0]
		if atLeastTwoGroups:
			(i1,g1),w1 = groupWeights[1]
			#if w1 > 1.6 * w0 and g1.avgPos < lg.bounds[1]+1.2*lg.width():
			if w1 > 1.6 * w0 and HF.intervalsIntersect(lg.bounds, g1.bounds):
				i,lg = i1,g1
		#----------------
		(j,rg), w0 = groupWeights[-1]
		if atLeastTwoGroups:
			(j1,g1),w1 = groupWeights[-2]
			#if w1 > 1.6 * w0 and g1.avgPos > rg.bounds[0]-1.2*rg.width():
			if w1 > 1.6 * w0 and HF.intervalsIntersect(rg.bounds, g1.bounds):
				j,rg = j1,g1
		if i == j and i > 0: (i,lg),_ = groupWeights[0]
		if i == j and j < len(groups)-1: (j,rg),_ = groupWeights[-1]
		#----------------
		if lg.alignments[0].pos < lg.alignments[1].pos:
			leftmost = 0
		else:
			leftmost = 1
		#----------------
		if rg.alignments[0].pos < rg.alignments[1].pos:
			rightmost = 1
		else:
			rightmost = 0
		#----------------
		ret = i,leftmost, j,rightmost
		#print "findLeftRight returns", ret
		return ret

	def propagate(self, grp, contours, isHorizontal):
		leadAli = grp.alignments[grp.leaderPos]
		lead = leadAli.leaderPoint(0, contours)
		leftAlignments = [a for a in grp.alignments if a.pos < leadAli.pos]
		rightAlignments = [a for a in grp.alignments if a.pos > leadAli.pos]
		leftAlignments.sort(key=lambda a:a.pos, reverse=True)
		rightAlignments.sort(key=lambda a:a.pos, reverse=False)
		leadAli.addLinks(0, contours, isHorizontal, self)
		src = lead
		for ali in leftAlignments:
			tgt = ali.leaderPoint(0, contours)
			if not tgt.touched:
				tgt.touched = True
				stemName = self.guessStemForDistance(src, tgt, isHorizontal)
				self.addSingleLink(src.name, tgt.name, isHorizontal, stemName)
			src = tgt
			ali.addLinks(0, contours, isHorizontal, self)
		src = lead
		for ali in rightAlignments:
			tgt = ali.leaderPoint(0, contours)
			if not tgt.touched:
				tgt.touched = True
				stemName = self.guessStemForDistance(src, tgt, isHorizontal)
				self.addSingleLink(src.name, tgt.name, isHorizontal, stemName)
			src = tgt
			ali.addLinks(0, contours, isHorizontal, self)

	def processGroup_X(self, grp, contours, interpolateIsPossible, bounds):
		if len(grp.alignments) == 1:
			if len(grp.alignments[0].components) == 1:
				return
		# Find a leader position, preferably the position of a nice stem
		if grp.leaderPos == None:
			grp.leaderPos = 0
			for (i, ali) in enumerate(grp.alignments):
				if ali.leaderPoint(0, contours).touched:
					grp.leaderPos = i
					break
		# Find the leader control point in the leader alignment (= the alignment at the leaderPos)
		leadAli = grp.alignments[grp.leaderPos]
		lead = leadAli.leaderPoint(0, contours)
		if (not lead.touched) and interpolateIsPossible:
			# If NO alignment in the group had beed processed yet,
			# then add a starting point by interpolation:
			leftmost, rightmost = bounds
			self.addInterpolate(leftmost, lead, rightmost, False)
		lead.touched = True
		self.propagate(grp, contours, False)

	def processGroup_Y(self, grp, contours, interpolateIsPossible, bounds, findZone):
		zone = None
		if grp.leaderPos == None:
			if not findZone:
				grp.leaderPos = 0
			for (i, ali) in enumerate(grp.alignments):
				if ali.leaderPoint(0, contours).touched:
					grp.leaderPos = i
					break
		if grp.leaderPos == None:
			# Here, it must be the case that findZone == True, so we
			# look for a zone
			findTopMostZone = True
			for pos, ali in enumerate(grp.alignments):
				if ali.zone == None: continue
				if not ali.zone[1]: findTopMostZone = False # bottom zone
				if ((zone == None) or
				   ((    findTopMostZone) and (zone[2] < ali.zone[2])) or
				   ((not findTopMostZone) and (zone[2] > ali.zone[2]))):
					zone = ali.zone
					grp.leaderPos = pos
		if grp.leaderPos == None: # no zone
			return None
		# Find the leader control point in the leader alignment (= the alignment at the leaderPos)
		leadAli = grp.alignments[grp.leaderPos]
		lead = leadAli.leaderPoint(0, contours)
		if not lead.touched:
			if zone != None:
				self.addAlign(lead.name, zone)
				lead.touched = True
			elif interpolateIsPossible:
				# If NO alignment in the group had beed processed yet,
				# then add a starting point by interpolation:
				bottommost, topmost = bounds
				self.addInterpolate(bottommost, lead, topmost, True)
				lead.touched = True
		if not lead.touched: return None
		self.propagate(grp, contours, True)
		return lead

	def guessStemForDistance(self, p1, p2, isHorizontal):
		if isHorizontal:
			detectedWidth = abs(p1.shearedPos[1] - p2.shearedPos[1])
		else:
			detectedWidth = abs(p1.shearedPos[0] - p2.shearedPos[0])
		candidatesList = []
		bestD = 10000000
		bestName = None
		for stemName, stem in self.TTHToolInstance.c_fontModel.stems.iteritems():
			if stem['horizontal'] != isHorizontal: continue
			w = int(stem['width'])
			d = abs(w - detectedWidth)
			if d <= detectedWidth*0.25 and d < bestD:
				bestD = d
				bestName = stemName
		return bestName

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
		#if newCommand not in self.TTHToolInstance.glyphTTHCommands:
		self.TTHToolInstance.glyphTTHCommands.append(newCommand)

	#def addDoubleLink(self, p1, p2, stemName, isHorizontal):
	#	if stemName == None:
	#		return
	#	newCommand = {}
	#	if isHorizontal:
	#		newCommand['code'] = 'doublev'
	#	else:
	#		newCommand['code'] = 'doubleh'
	#	newCommand['point1'] = p1.name
	#	newCommand['point2'] = p2.name
	#	newCommand['stem'] = stemName
	#	#if newCommand not in self.TTHToolInstance.glyphTTHCommands:
	#	self.TTHToolInstance.glyphTTHCommands.append(newCommand)

	def addAlign(self, pointName, (zoneName, isTopZone, ys, ye)):
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

	def autoHintY(self, contours, stems):
		alignments = makeAlignments(self.ital, contours, False, self) # for Y auto-hinting
		#printAlignments(alignments, 'Y')
		for pos, alignment in alignments.iteritems():
			alignment.putLeadersFirst(contours)
			alignment.findZone(contours, self)

		groups = self.makeGroups(contours, stems, debug=False)
		for grp in groups: grp.prepare(alignments)

		bottom = None
		top = None
		for group in groups:
			pt = self.processGroup_Y(group, contours, False, None, findZone=True)
			if pt == None: continue
			if top == None or pt.pos.y > top.pos.y: top = pt
			if bottom == None or pt.pos.y < bottom.pos.y: bottom = pt
		interpolateIsPossible = (top != None) and (bottom != None) and (not (top is bottom))
		bounds = (bottom, top)
		for group in groups:
			self.processGroup_Y(group, contours, interpolateIsPossible, bounds, findZone=False)
		return bottom != None and top != None

	def autoHintX(self, g, contours, stems):
		alignments = makeAlignments(self.ital, contours, True, self) # for X auto-hinting
		#printAlignments(alignments, 'X')
		if len(alignments) == 0: return
		for pos, alignment in alignments.iteritems():
			alignment.putLeadersFirst(contours)
		
		groups = self.makeGroups(contours, stems, debug=False)
		for grp in groups: grp.prepare(alignments)

		# Find the left and right points to be anchored to lsb and rsb.
		leftGrpIdx,lmPos, rightGrpIdx,rmPos = self.findLeftRight(groups)
		if leftGrpIdx == None: return g.name
		leftGroup = groups[leftGrpIdx]
		rightGroup = groups[rightGrpIdx]
		bounds = None
		interpolateIsPossible = False

		# Anchor the rightmost point
		rightmost = rightGroup.alignments[rmPos].leaderPoint(0, contours)
		self.addSingleLink('lsb', rightmost.name, False, None)['round'] = 'true'
		self.addSingleLink(rightmost.name, 'rsb', False, None)['round'] = 'true'
		rightGroup.leaderPos = rmPos
		self.processGroup_X(rightGroup, contours, False, None)

		# Anchor the leftmost point if they live in different groups
		# (If not, then the processGroup will take care of the single link
		#  and interpolation will not be possible)
		if leftGrpIdx != rightGrpIdx:
			interpolateIsPossible = True
			leftmost = leftGroup.alignments[lmPos].leaderPoint(0, contours)
			bounds = leftmost, rightmost
			stemName = self.guessStemForDistance(leftmost, rightmost, False)
			link = self.addSingleLink(rightmost.name, leftmost.name, False, stemName)
			if stemName == None: link['round'] = 'true'
			leftGroup.leaderPos = lmPos
			self.processGroup_X(leftGroup, contours, False, None)

		for grp in groups:
			if grp.leaderPos != None: continue
			self.processGroup_X(grp, contours, interpolateIsPossible, bounds)


	def autohint(self, g, maxStemSize):
		font = self.TTHToolInstance.c_fontModel.f
		if font.info.italicAngle != None:
			self.ital = - font.info.italicAngle
		else:
			self.ital = 0

		if maxStemSize == None:
			maxStemSize = computeMaxStemOnO(self.tthtm, font)
			if maxStemSize == -1:
				maxStemSize = maxStemY = 200
			print "max stem size in X, Y is", maxStemSize

		self.TTHToolInstance.resetglyph(g)
		self.TTHToolInstance.glyphTTHCommands = []

		xBound = self.tthtm.minStemX, maxStemSize
		yBound = self.tthtm.minStemY, maxStemSize

		contours = makeContours(g, self.ital)
		stems = makeStemsList(g, contours, self.ital, xBound, yBound, 1, self.tthtm.angleTolerance, dedup=False)
		rx = self.autoHintX(g, contours, stems[0])
		for c in contours:
			for hd in c:
				hd.reset()
		ry = self.autoHintY(contours, stems[1])
		if not ry: ry = g.name
		else: ry = None
		return rx, ry

