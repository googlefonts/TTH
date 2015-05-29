import math
from models.TTHTool import uniqueInstance as tthTool
from drawing import geom
import auto

def square(x):
	return x*x

def angleScore(d):
	if d > 1.0000001: print "ERROR : dot product is larger than ONE"
	if d < -0.999: d = -0.999
	return math.exp( - 2.0 * square(d+1.0) )
	#return math.exp(2.0/(d+1.0))
	return (2.0/(d+1.0))

def score(p0, p1):
	posDiff = (p1.pos-p0.pos).squaredLength()
	frontAngleMatch = angleScore(p0.inTangent  | p1.inTangent)
	backAngleMatch  = angleScore(p0.outTangent | p1.outTangent)
	return posDiff *(frontAngleMatch + backAngleMatch)

def indexOfMin(values):
	i = 0
	v = values[1]
	for j, nv in enumerate(values):
		if nv[1] < v:
			v = nv[1]
			i = j
	return i

def matchTwoContours(fromC, toC, table):
	lenFrom = len(fromC)
	lenTo = len(toC)
	# dynamic programming init
	for t in xrange(lenTo):
		table[0][t] = (-1, score(fromC[0], toC[t]))
	# dynamic programming propagation
	for f in xrange(1,lenFrom):
		s = 0
		minVal = table[f-1][0][1]
		for t in xrange(lenTo):
			localScore = score(fromC[f], toC[t])
			newVal = table[f-1][t][1]
			if newVal < minVal:
				minVal = newVal
				s = t
			table[f][t] = (s, minVal + localScore)
	# dynamic programming backtrack
	permut = [indexOfMin(table[lenFrom-1])]
	matchQuality = table[lenFrom-1][permut[0]][1] # lower is better
	for f in range(lenFrom-1, 0, -1):
		permut.append(table[f][permut[-1]][0])
	permut.reverse()
	return permut, matchQuality

def fix((permut,s), i, n):
	return [(x+i) % n for x in permut],s # recover original segment numbers

def permutationsOf(elements):
	"""Iterates over all permutations of input 'elements'."""
	n = len(elements)
	if n <= 1:
		yield elements
		return
	for i in range(n):
		for perm in permutationsOf(elements[:i]+elements[i+1:]):
			yield perm+[elements[i]]

def matchTwoGlyphs(fromG, toG):
	nbContours = len(fromG), len(toG)
	if nbContours[0] != nbContours[1]:
		return None

	# A cache of matchings over pairs of contours
	matchings = [[None for t in toG] for f in fromG]

	def getMatching(f, t):
		if matchings[f][t] == None:
			fromC = fromG[f] # fromC = source Contour
			toC   = toG[t]   # toC   = target Contour
			n = len(toC)
			table = [[None for x in xrange(n+1)] for y in fromC]
			permutedMatches = [fix(matchTwoContours(fromC, toC[i:]+toC[:i]+[toC[i]], table), i, n) for i in xrange(n)]
			i = indexOfMin(permutedMatches)
			matchings[f][t] = permutedMatches[i]
		return matchings[f][t]

	bestPerm = range(nbContours[1])
	bestScore = sum(getMatching(i, bestPerm[i])[1] for i in xrange(nbContours[0]))
	for perm in permutationsOf(range(nbContours[1])):
		score = 0.0
		badMatch = False
		for i in xrange(nbContours[0]):
			score = score + getMatching(i, perm[i])[1]
			if score >= bestScore:
				badMatch = True
				break
		if badMatch: continue
		bestScore = score
		bestPerm = perm
	#for f,t in enumerate(bestPerm):
	#	print "Contour",f,"of source glyph matches contour",t,"of target glyph as follows:"
	#	for i,j in enumerate(matchings[f][t][0]):
	#		sys.stdout.write("{}:{}".format(i,j))
	#		if (i+1) % 4 == 0: sys.stdout.write('\n')
	#		else: sys.stdout.write('\t\t')
	#	print ''
	return [(t, matchings[f][t][0]) for (f,t) in enumerate(bestPerm)]

def prepareGlyph(g):
	contours = auto.makeContours(g, 0.0)
	xs = sum([[p.pos.x for p in c] for c in contours], [])
	ys = sum([[p.pos.x for p in c] for c in contours], [])
	lo = geom.Point(min(xs), min(ys))
	hi = geom.Point(max(xs), max(ys))
	dim = hi - lo
	# Rescale the glyph to fit in a square box from (0,0) to (1000,1000)
	for c in contours:
		for p in c:
			newpos = (p.pos - lo)
			p.pos = geom.Point(newpos.x * 1000.0 / dim.x, newpos.y * 1000.0 / dim.y)
	return contours

class PointMatcher(object):
	def __init__(self, g0, g1):
		# g0 and g1 are two objects of class 'Glyph'
		fromG = prepareGlyph(g0)
		toG = prepareGlyph(g1)
		matchings = matchTwoGlyphs(fromG, toG)
		m = {'lsb':'lsb', 'rsb':'rsb'}
		self._map = m
		if matchings == None: return
		for f, (t, perm) in enumerate(matchings):
			for fromSeg, toSeg in enumerate(perm):
				fName = fromG[f][fromSeg].name
				tName = toG[t][toSeg].name
				m[fName] = tName
	def map(self, fName):
		try:
			return self._map[fName]
		except:
			return None

def getCmdPoint(glyph, name):
	if name == 'lsb':
		return geom.Point(0,0)
	if name == 'rsb':
		return geom.Point(glyph.width,0)
	ptDict = glyph.naked().getPointsWithLabel(name)
	pt = None
	for k in ptDict.iterkeys():
		pt = k
		break
	return pt

def transfer(sourceFM, targetFM, progress=None):
	sourceFont = sourceFM.f
	targetFont = targetFM.f
	msg = []
	counter = 0
	for sourceG in sourceFont:
		if sourceG.name in targetFont:
			targetG = targetFont[sourceG.name]
			if len(sourceG) == len(targetG) and len(sourceG) > 0:
				# same number of contours
				transfertHintsBetweenTwoGlyphs(sourceFM, sourceG, targetFM, targetG)
		else:
			msg.append(sourceG.name.join(["Warning: glyph "," not found in target font."]))
		if progress:
			counter += 1
			if counter == 20:
				progress.increment(20)
				counter = 0
	if progress:
		progress.increment(counter)
	if msg:
		print '\n'.join(msg)

def transfertHintsBetweenTwoGlyphs(sourceFM, sourceGlyph, targetFM, targetGlyph):
	pm = PointMatcher(sourceGlyph, targetGlyph)
	hasSGM   = sourceFM.hasGlyphModelForGlyph(sourceGlyph)
	sourceGM = sourceFM.glyphModelForGlyph(sourceGlyph)
	hasTGM   = targetFM.hasGlyphModelForGlyph(targetGlyph)
	targetGM = targetFM.glyphModelForGlyph(targetGlyph)
	inCommands = sourceGM.hintingCommands
	if inCommands == None:
		if hasSGM: sourceFM.delGlyphModelForGlyph(sourceGlyph)
		if hasTGM: targetFM.delGlyphModelForGlyph(targetGlyph)
		return
	AH = auto.hint.AutoHinting(targetFM)
	getWidth = auto.hint.getWidthOfTwoPointsStem
	targetGM.clearCommands(True, True)
	for inCmd in inCommands:
		cmd = dict(inCmd) # copy the commands before modifying it
		#print "===================================="
		#print cmd
		if 'delta' in cmd['code']:
			continue
		for k in ['point', 'point1', 'point2']:
			if k in cmd:
				newName = pm.map(cmd[k])
				cmd[k] = newName
		if 'stem' in cmd: # Find the correct name of the stem in the target font
			isHorizontal = (cmd['code'] == 'singlev')
			src = getCmdPoint(targetGlyph, cmd['point1'])
			tgt = getCmdPoint(targetGlyph, cmd['point2'])
			stemWidth = getWidth(src, tgt, isHorizontal)
			stemName = AH.guessStemForWidth(stemWidth, isHorizontal)
			if stemName != None:
				#print cmd['stem'], "--stem-->", stemName
				cmd['stem'] = stemName
			else:
				del cmd['stem']
		elif 'zone' in cmd: # Find the correct name of the zone in the target font if it exists
			pt = getCmdPoint(targetGlyph, cmd['point'])
			if pt == None:
				continue
			zone = AH.zoneAt(pt.y)
			if zone == None:
				#print "Command '{0}' killed.".format(cmd['code'])
				continue
			else:
				#print cmd['zone'], "--zone-->", zone[0]
				cmd['zone'] = zone[0]
		targetGM.addCommand(cmd, update=False)
	targetGM.compile(targetFM)
	if hasSGM: sourceFM.delGlyphModelForGlyph(sourceGlyph)
	if hasTGM: targetFM.delGlyphModelForGlyph(targetGlyph)
	tthTool.hintingProgramHasChanged(targetFM)