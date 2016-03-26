import math
import itertools
import xml.etree.ElementTree as ET
from commons import helperFunctions as HF
from drawing import geom
import auto

matching_zero = geom.Point()

class SimplePoint(object):
	__slots__ = ('pos', 'name', 'inTangent', 'outTangent')
	def __init__(self, p, n, it=matching_zero, ot=matching_zero):
		self.pos  = p
		self.name = n
		self.inTangent  = it
		self.outTangent = ot
	def fit(self, lo, dim):
		newP = self.pos - lo
		self.pos = 1000.0 * geom.Point(newP.x/dim.x, newP.y/dim.y)

def square(x):
	return x*x

def angleScore(d):
	if d > 1.0000001: print "ERROR : dot product is larger than ONE"
	if d < -0.999: d = -0.999
	return math.exp( - 2.0 * square(d+1.0) )
	#return math.exp(2.0/(d+1.0))
	return (2.0/(d+1.0))

def onScore(p0, p1):
	posDiff = (p1.pos-p0.pos).squaredLength()
	frontAngleMatch = angleScore(p0.inTangent  | p1.inTangent)
	backAngleMatch  = angleScore(p0.outTangent | p1.outTangent)
	return posDiff *(frontAngleMatch + backAngleMatch)

def offScore(p0, p1):
	return (p1.pos - p0.pos).squaredLength()

def indexOfMin(values):
	i = 0
	v = values[1]
	for j, nv in enumerate(values):
		if nv[1] < v:
			v = nv[1]
			i = j
	return i

def matchTwoContours(fromC, toC, table, score):
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

#def permutationsOf(elements):
#	"""Iterates over all permutations of input 'elements'."""
#	n = len(elements)
#	if n <= 1:
#		yield elements
#		return
#	for i in range(n):
#		for perm in permutationsOf(elements[:i]+elements[i+1:]):
#			yield perm+[elements[i]]

def matchTwoGlyphs(fromG, toG):
	nbFromContours, nbToContours = len(fromG), len(toG)

	# A cache of matchings over pairs of contours
	matchings = [[None for t in toG] for f in fromG]

	def getMatching(f, t):
		if matchings[f][t] == None:
			fromC = fromG[f] # fromC = source Contour
			toC   = toG[t]   # toC   = target Contour
			n = len(toC)
			table = [[None for x in xrange(n+1)] for y in fromC]
			permutedMatches = [fix(matchTwoContours(fromC, toC[i:]+toC[:i]+[toC[i]], table, onScore), i, n) for i in xrange(n)]
			i = indexOfMin(permutedMatches)
			matchings[f][t] = permutedMatches[i]
		return matchings[f][t]

	if nbFromContours <= nbToContours:
		bestPerm = range(nbFromContours)
		bestScore = sum(getMatching(i, bestPerm[i])[1] for i in xrange(nbFromContours))
		for perm in itertools.permutations(range(nbToContours), nbFromContours):
			score = 0.0
			badMatch = False
			for i in xrange(nbFromContours):
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
		return [(f, t, matchings[f][t][0]) for (f,t) in enumerate(bestPerm)]
	else:  # nbFromContours > nbToContours
		print "warning, the matching will be partial"
		bestPerm = range(nbToContours)
		bestScore = sum(getMatching(bestPerm[j], j)[1] for j in xrange(nbToContours))
		for perm in itertools.permutations(range(nbFromContours), nbToContours):
			score = 0.0
			badMatch = False
			for j in xrange(nbToContours):
				score = score + getMatching(perm[j], j)[1]
				if score >= bestScore:
					badMatch = True
					break
			if badMatch: continue
			bestScore = score
			bestPerm = perm
		return [(f, t, matchings[f][t][0]) for (t,f) in enumerate(bestPerm)]

class TTHComponent(object):
	def __init__(self, g, idx, offset, scale):
		self.g = g
		self.idx = idx
		self.offset = offset
		self.scale = scale
	def xform(self, p):
		return geom.Point(self.scale[0]*p.x + self.offset[0], self.scale[1]*p.y + self.offset[1])

def numberOfContours(f, g):
	return sum([len(f[c.baseGlyph]) for c in g.components], len(g))

def prepareGlyph(fm, gm, withOff):
	comps = [TTHComponent(gm,-1,(0,0),(1,1))]
	for idx, comp in enumerate(gm.RFGlyph.components):
		comps.append(TTHComponent(fm.glyphModelForGlyph(fm.f[comp.baseGlyph]), idx, comp.offset, comp.scale))
	onContours = []
	compIndices = []
	offContours = []
	for compo in comps:
		for cidx, contour in enumerate(compo.g.RFGlyph):
			newContour  = []
			contourOffs = []
			contourLen = len(contour)
			for sidx, seg in enumerate(contour):
				onPt = compo.xform(seg.onCurve)
				nextOff = compo.xform(contour[(sidx+1) % contourLen].points[0])
				if len(seg.points) > 1: prevOff = compo.xform(seg[-2])
				else: prevOff = compo.xform(contour[sidx-1].onCurve)
				outTangent = (nextOff-onPt).normalized()
				inTangent  = (onPt-prevOff).normalized()
				name = compo.g.hintingNameForPoint(seg.onCurve)
				newContour.append(SimplePoint(onPt, name, inTangent, outTangent))
				if not withOff: continue
				contourOffs.append([SimplePoint(geom.makePoint(o), compo.g.hintingNameForPoint(o)) for o in seg.offCurve])
			onContours.append(newContour)
			offContours.append(contourOffs)
			compIndices.append(compo.idx)

	xs = sum([[float(p.pos.x) for p in c] for c in onContours], [])
	ys = sum([[float(p.pos.y) for p in c] for c in onContours], [])
	if (len(xs) <= 1) or (len(ys) <= 1):
		return None, None, None
	lo = geom.Point(min(xs), min(ys))
	hi = geom.Point(max(xs), max(ys))
	dim = hi - lo
	if dim.x < 1e-4: dim.x = 1.0
	if dim.y < 1e-4: dim.y = 1.0
	# Rescale the glyph to fit in a square box from (0,0) to (1000,1000)
	for c in onContours:
		for sp in c: sp.fit(lo, dim)
	for c in offContours:
		for offs in c:
			for sp in offs: sp.fit(lo, dim)
	#print len(onContours),"contours"
	return onContours, offContours, compIndices

def getOffMatching(srcCompIdx, srcOffs, tgtCompIdx, tgtOffContour, tgtSeg0, tgtSeg1):
	if srcOffs == []: return {}
	n = len(tgtOffContour)
	i = tgtSeg0
	tgtOffs = []
	while i != tgtSeg1:
		i = (i+1) % n
		tgtOffs.extend(tgtOffContour[i])
	if tgtOffs == []: return {}
	n = len(tgtOffs)
	table = [[None for x in xrange(n)] for y in srcOffs]
	permut, matchQuality = matchTwoContours(srcOffs, tgtOffs, table, offScore)
	return dict(((srcCompIdx,srcOffs[s].name), (tgtCompIdx, tgtOffs[t].name)) for (s,t) in enumerate(permut))

class PointNameMatcher(object):
	def __init__(self, fm0, gm0, fm1, gm1, withOff=False):
		m  = {(-1,'lsb'):(-1,'lsb'), (-1,'rsb'):(-1,'rsb')}
		self._nameMap = m
		srcG, srcOffs, srcCompIdx = prepareGlyph(fm0, gm0, withOff)
		tgtG, tgtOffs, tgtCompIdx = prepareGlyph(fm1, gm1, withOff)
		if srcG == None:
			print "[TTH Warning] glyph {} in font {} has less than one control point".format(gm0.RFGlyph.name, fm0.f.fileName)
			return
		if tgtG == None:
			print "[TTH Warning] glyph {} in font {} has less than one control point".format(gm1.RFGlyph.name, fm1.f.fileName)
			return
		matchings = matchTwoGlyphs(srcG, tgtG)
		if matchings == None: return
		for srcContour, tgtContour, perm in matchings:
			for srcSeg, tgtSeg in enumerate(perm):
				srcCompName = srcCompIdx[srcContour], srcG[srcContour][srcSeg].name
				tgtCompName = tgtCompIdx[tgtContour], tgtG[tgtContour][tgtSeg].name
				m[srcCompName] = tgtCompName
				if not withOff: continue
				m.update(getOffMatching(srcCompIdx[srcContour], srcOffs[srcContour][srcSeg],\
						tgtCompIdx[tgtContour], tgtOffs[tgtContour], perm[srcSeg-1], tgtSeg))
		#for k,v in m.iteritems():
		#	print k,' --> ',v
	def map(self, srcCompName):
		return self._nameMap.get(srcCompName, (None, None))

def transferHintsBetweenTwoFonts(sourceFM, targetFM, transferDeltas=False, progress=None):
	sourceFont = sourceFM.f
	targetFont = targetFM.f
	msg = []
	counter = 0
	for sourceG in sourceFont:
		if sourceG.name in targetFont:
			targetG = targetFont[sourceG.name]
			numSourceContours = numberOfContours(sourceFM.f, sourceG)
			numTargetContours = numberOfContours(targetFM.f, targetG)
			if numTargetContours == numSourceContours and numSourceContours > 0:
				# same number of contours
				transfertHintsBetweenTwoGlyphs(sourceFM, sourceG, targetFM, targetG, transferDeltas)
				targetG.mark = (1, .5, 0, .5)
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

def transfertHintsBetweenTwoGlyphs(sourceFM, sourceGlyph, targetFM, targetGlyph, transferDeltas=False):
	#try:
		transfertHintsBetweenTwoGlyphs__(sourceFM, sourceGlyph, targetFM, targetGlyph, transferDeltas)
	#except:
	#	print "There was an EXCEPTION RAISED while transfering hints between:"
	#	print sourceFM.f.fileName,":",sourceGlyph.name," and ", targetFM.f.fileName,":",targetGlyph.name

def transfertHintsBetweenTwoGlyphs__(sourceFM, sourceGlyph, targetFM, targetGlyph, transferDeltas=False):
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
	pm = PointNameMatcher(sourceFM, sourceGM, targetFM, targetGM, transferDeltas)
	targetGM.clearCommands(True, True)
	for inCmd in inCommands:
		cmd = ET.Element('ttc')
		cmd.attrib = dict(inCmd.attrib) # copy the commands before modifying it
		#print "===================================="
		#print cmd
		if (not transferDeltas) and ('delta' in cmd.get('code')):
			continue
		bug = False
		for (k,b) in [('point','base'), ('point1','base1'), ('point2','base2')]:
			if HF.commandHasAttrib(cmd, k):
				oldCompName = int(cmd.get(b,'-1')), cmd.get(k)
				newComp, newName = pm.map(oldCompName)
				if (newComp) == None or (newName == None):
					print "[TTH ERROR]", oldCompName, "==>", newComp, newName
					bug = True
					continue
				cmd.set(k, newName)
				if newComp != -1:
					cmd.set(b, str(newComp))
				else:
					HF.delCommandAttrib(cmd, b)
		if bug:
			print "There was an error when transfering hints between:"
			print sourceFM.f.fileName,":",sourceGlyph.name," and ", targetFM.f.fileName,":",targetGlyph.name
			break
		if HF.commandHasAttrib(cmd, 'stem'): # Find the correct name of the stem in the target font
			isHorizontal = (cmd.get('code') == 'singlev')
			src = targetGM.positionForPointName(cmd.get('point1'), targetFM, cmd.get('base1'))
			tgt = targetGM.positionForPointName(cmd.get('point2'), targetFM, cmd.get('base2'))
			stemWidth = getWidth(src, tgt, isHorizontal)
			stemName = AH.guessStemForWidth(stemWidth, isHorizontal)
			if stemName != None:
				#print cmd.get('stem'), "--stem-->", stemName
				cmd.set('stem', stemName)
			else:
				HF.delCommandAttrib(cmd, 'stem')
		elif HF.commandHasAttrib(cmd, 'zone'): # Find the correct name of the zone in the target font if it exists
			pt = targetGM.positionForPointName(cmd.get('point'), targetFM, cmd.get('base'))
			if pt == None: continue
			zone = AH.zoneAt(pt.y)
			if zone == None:
				#print "Command '{0}' killed.".format(cmd.get('code'))
				continue
			else:
				#print cmd.get('zone'), "--zone-->", zone[0]
				cmd.set('zone', zone[0])
		targetGM.addCommand(targetFM, cmd, update=False)
	targetGM.compile(targetFM)
	if hasSGM: sourceFM.delGlyphModelForGlyph(sourceGlyph)
	if hasTGM: targetFM.delGlyphModelForGlyph(targetGlyph)
