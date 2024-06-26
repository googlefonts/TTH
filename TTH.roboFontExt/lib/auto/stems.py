
from collections import deque
import math
from string import ascii_letters
from models.TTHTool import uniqueInstance as tthTool
from commons import helperFunctions, KMeans
from drawing import geom
import auto

def autoStems(fm, progressBar):
	font = fm.f
	# test if quadratic or cubic font
	fontIsQuad = helperFunctions.fontIsQuadratic(font)

	if font.info.italicAngle != None:
		ital = - font.info.italicAngle
	else:
		ital = 0

	yBound, xBound = fm.stemSizeBounds

	stemsValuesX = []
	stemsValuesY = []

	progressBar.set(0)
	progressBar._nsObject.setMaxValue_(len(ascii_letters))
	for name in ascii_letters:
		g = font[name]
		noName, contours = auto.makeContours(g, ital)
		(XStems, YStems) = makeStemsList(g, contours, ital, xBound, yBound, fm.angleTolerance, fontIsQuad, False)
		XStems = [stem[2] for stem in XStems]
		YStems = [stem[2] for stem in YStems]
		stemsValuesX.extend(XStems)
		stemsValuesY.extend(YStems)
		progressBar.increment(1)

	upm = float(fm.UPM)
	vStems = clusterAndGenStemDicts(upm, stemsValuesX, isHorizontal=False)
	hStems = clusterAndGenStemDicts(upm, stemsValuesY, isHorizontal=True)
	return hStems, vStems

def clusterAndGenStemDicts(upm, stemsValues, isHorizontal):
	if not stemsValues: return {}
	f = math.log(1.0 + 20.0 / 100.0)
	logs = [math.log(v) for v in stemsValues]
	for k in xrange(1,20):
		score, seeds, clusters = KMeans.optimal(logs, k)
		meanBounds = [(seeds[i], min(c), max(c)) for (i,c) in enumerate(clusters)]
		badClusters = [1 for (mu,mi,ma) in meanBounds if mi<mu-f or ma>mu+f]
		if len(badClusters) == 0: break
	stemSnapList = [int(math.exp(s)+0.5) for s in seeds]

	stems = {}
	for width in stemSnapList:
		if isHorizontal:
			name = 'Y_' + str(width)
		else:
			name = 'X_' + str(width)
		roundedStem = helperFunctions.roundbase(width, 20)
		if roundedStem != 0:
			stemPitch = upm/roundedStem
		else:
			stemPitch = upm/max(1,width)
			# FIXME maybe, here we should juste skip this width and 'continue'?
		px1 = str(0)
		px2 = str(int(2*stemPitch))
		px3 = str(int(3*stemPitch))
		px4 = str(int(4*stemPitch))
		px5 = str(int(5*stemPitch))
		px6 = str(int(6*stemPitch))

		stemDict = {'horizontal': isHorizontal, 'width': width, 'round': {px1: 1, px2: 2, px3: 3, px4: 4, px5: 5, px6: 6}, 'targetWidth': width }
		stems[name] = stemDict
	return stems

def hasSomeWhite(point1, point2, g, maxStemX, maxStemY):
	dif = (point1 - point2).absolute()
	if dif.x > maxStemX and dif.y > maxStemY:
		return True # too far away, assume there is white in between
	hypothLength = dif.length() / 5.0
	queue = deque()
	queue.append((0, int(math.ceil(hypothLength))))
	while len(queue) > 0:
		(left, right) = queue.popleft()
		mid = int((left+right)/2)
		p = geom.lerp(mid/hypothLength, point1, point2)
		# for some reason (in RF) we can't pass 'p' directly, although it implements __getitem__
		if g.pointInside((p.x, p.y)):
			if mid  - left > 1: queue.append((left, mid))
			if right - mid > 1: queue.append((mid, right))
		else:
			return True
	return False

def makeStemsList(g, contours, italicAngle, xBound, yBound, tolerance, fontIsQuad, dedup=True):
	stemsListX_temp = []
	stemsListY_temp = []
	minCosine = abs(math.cos(math.radians(tolerance)))
	def addStemToList(src, tgt, c_distance, hypoth, srcTangent, tgtTangent, existingStems, debug):
		#if debug: print "DD"
		# if they are horizontal, treat the stem on the Y axis
		if (abs(srcTangent.x) > minCosine and abs(tgtTangent.x) > minCosine and
			not existingStems['h'] ) :
			if helperFunctions.inInterval(c_distance.y, yBound) and helperFunctions.inInterval(hypoth, yBound):
				existingStems['h'] = True
				stemsListY_temp.append((hypoth, (src, tgt, c_distance.y)))
			return
		#if debug: print "EE"
		# if they are vertical, treat the stem on the X axis
		if (abs(srcTangent.y) > minCosine and abs(tgtTangent.y) > minCosine and
			not existingStems['v'] ) : # the angle is already sheared to counter italic
			if helperFunctions.inInterval(c_distance.x, xBound) and helperFunctions.inInterval(hypoth, xBound):
				existingStems['v'] = True
				stemsListX_temp.append((hypoth, (src, tgt, c_distance.x)))
			return
		## Here, the angle of the stem is more diagonal
		# ... do something here with diagonal
		#if debug: print "FF"
		return

	def hasWhite(wc, source, target):
		if wc[0] == None:
			wc[0] = hasSomeWhite(source.pos, target.pos, g, xBound[1], yBound[1])
		return wc[0]

	contsegs = [contSeg for contSeg in auto.contourSegmentIterator(g)]
	bound = min(xBound[0], yBound[0])-1, max(xBound[1], yBound[1])+1
	# We loop over all pairs of distinct points (ON control points)
	for gidx, (sc, ss) in enumerate(contsegs): # 'sc' = Source Contour, 'sc' = Source Segment
		src = contours[sc][ss] # 'src' = Source Point
		sc_len = len(contours[sc])
		for (tc, ts) in contsegs[gidx+1:]: # 'tc' = Target Contour, 'tc' = Target Segment
			tgt = contours[tc][ts] # 'tgt' = Target Point
			debug = False#ss == 16 and ts == 17
			dif = (src.shearedPos - tgt.shearedPos).absolute()
			c_distance = dif
			hypoth = dif.length()
			#if debug: print "AA"
			if not helperFunctions.inInterval(hypoth, bound): continue

			diff = tgt.pos - src.pos # the vector between the source and the target under consideration

			wc = [None] # 'wc' = White Cache : 'None' means that we don't know if
			# there is some white between source and target. We put it in a list
			# so that 'wc' can be passed as a parameter and the called function
			# (hasWhite()) can modify the only cell in the list.

			if sc == tc: # source and target live on the same contour.
				# if they are neighboring points and are linked with a straight line then wc <- [false]
				# which indicates that there is only black ink between them (no white).
				if ts == ss + 1 and tgt.type == 'line':
					wc[0] = False # False --> no white, so pure black
				elif (ss == 0 and ts == sc_len - 1) and src.type == 'line':
					wc[0] = False
			#f debug: print "wc[0] =", wc[0]
			existingStems = {'h':False, 'v':False, 'd':False}
			# For example, existingStems['h'] = True if we found an horizontal stem between 'src' and 'tgt'
			# 'v' : vertical
			# 'd' : diagonal
			for sa in (src.inTangent, src.outTangent):
				for ta in (tgt.inTangent, tgt.outTangent):
					#if debug: print "BB", geom.det2x2(sa, diff), geom.det2x2(ta, diff), abs(sa | ta)
					if fontIsQuad:
						if ( geom.det2x2(sa, diff) < 0.0 and # test that 'tgt' is on the correct side of tangent 'sa'
						     geom.det2x2(ta, diff) > 0.0 and # test that 'src' is on the correct side of tangent 'ta'
						     abs(sa | ta) > minCosine): # and test that both tangent are almost parallel
							#if debug: print "CC"
							if hasWhite(wc, src, tgt): break
							# OK we found a 'stem'!
							addStemToList(src, tgt, c_distance, hypoth, sa, ta, existingStems, debug)
					else:
						if ( geom.det2x2(sa, diff) > 0.0 and # test that 'tgt' is on the correct side of tangent 'sa'
						     geom.det2x2(ta, diff) < 0.0 and # test that 'src' is on the correct side of tangent 'ta'
						     abs(sa | ta) > minCosine): # and test that both tangent are almost parallel
							#if debug: print "CC"
							if hasWhite(wc, src, tgt): break
							# OK we found a 'stem'!
							addStemToList(src, tgt, c_distance, hypoth, sa, ta, existingStems, debug)

	stemsListX_temp.sort() # sort by stem length (hypoth)
	stemsListY_temp.sort()
	if not dedup: # dedup means de-duplications
		stemsX = [stem[1] for stem in stemsListX_temp]
		stemsY = [stem[1] for stem in stemsListY_temp]
		return (stemsX, stemsY)
	# avoid duplicates, filters temporary stems
	stemsLists = ([], [])
	for i, stems in enumerate([stemsListX_temp, stemsListY_temp]):
		references = set()
		for (hypoth, stem) in stems:
			sourceAbsent = not helperFunctions.exists(references,
							lambda y: helperFunctions.approxEqual(stem[0].shearedPos[i], y, 0.025))
			targetAbsent = not helperFunctions.exists(references,
							lambda y: helperFunctions.approxEqual(stem[1].shearedPos[i], y, 0.025))
			if sourceAbsent or targetAbsent:
				stemsLists[i].append(stem)
			if sourceAbsent: references.add(stem[0].shearedPos[i])
			if targetAbsent: references.add(stem[1].shearedPos[i])
	return stemsLists
