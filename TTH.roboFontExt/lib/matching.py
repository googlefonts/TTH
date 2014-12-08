import Automation
import geom
import math
import sys
reload(Automation)

def square(x):
	return x*x

def score(p0, p1):
	posDiff = (p1.pos-p0.pos).squaredLength()
	di = p0.inTangent | p1.inTangent
	do = p0.outTangent | p1.outTangent
	frontAngleMatch = math.exp( - 2.0 * square(di + 1.0) )
	backAngleMatch  = math.exp( - 2.0 * square(do + 1.0) )
	return posDiff * (frontAngleMatch + backAngleMatch)

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
	for t in xrange(lenTo):
		table[0][t] = (-1, score(fromC[0], toC[t]))
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
	permut = [indexOfMin(table[lenFrom-1])]
	matchQuality = table[lenFrom-1][permut[0]][1] # lower is better
	for f in range(lenFrom-1, 0, -1):
		permut.append(table[f][permut[-1]][0])
	permut.reverse()
	return permut, matchQuality

def fix((permut,s), i, n):
	return [(x+i) % n for x in permut],s # recover original segment numbers

def permutationsOf(elements):
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

	matchings = [[None for t in toG] for f in fromG]

	def getMatching(f, t):
		if matchings[f][t] == None:
			fromC = fromG[f]
			toC   = toG[t]
			n = len(toC)
			table = [[None for x in xrange(n)] for y in fromC]
			permutedMatches = [fix(matchTwoContours(fromC, toC[i:]+toC[:i], table), i, n) for i in xrange(n)]
			i = indexOfMin(permutedMatches)
			matchings[f][t] = permutedMatches[i]
		return matchings[f][t]

	bestPerm = range(nbContours[1])
	bestScore = sum(getMatching(i, bestPerm[i])[1] for i in xrange(nbContours[1]))
	for perm in permutationsOf(range(len(toG))):
		score = 0.0
		badMatch = False
		for i in xrange(nbContours[0]):
			score = score + getMatching(i, perm[i])[1]
			if score > bestScore:
				badMatch = True
				break
		if badMatch: continue
		bestScore = score
		bestPerm = perm
	for f,t in enumerate(bestPerm):
		print "Contour",f,"of source glyph matches contour",t,"of target glyph as follows:"
		for i,j in enumerate(matchings[f][t][0]):
			sys.stdout.write("{}:{}".format(i,j))
			if (i+1) % 4 == 0: sys.stdout.write('\n')
			else: sys.stdout.write('\t\t')
		print ''
	return [(t, matchings[f][t][0]) for (f,t) in enumerate(bestPerm)]

def prepareGlyph(g):
	contours = Automation.makeContours(g, 0.0)
	xs = sum([[p.pos.x for p in c] for c in contours], [])
	ys = sum([[p.pos.x for p in c] for c in contours], [])
	lo = geom.Point(min(xs), min(ys))
	hi = geom.Point(max(xs), max(ys))
	dim = hi - lo
	for c in contours:
		for p in c:
			newpos = (p.pos - lo)
			p.pos = geom.Point(newpos.x * 1000.0 / dim.x, newpos.y * 1000.0 / dim.y)
	return contours

def go():
	fonts = []
	for f in AllFonts():
		fonts.append(f)
	c = CurrentGlyph().name
	g0 = prepareGlyph(fonts[0][c])
	g1 = prepareGlyph(fonts[1][c])
	print "---------------------------------------------------------"
	print "From", fonts[0].fileName, "\nto  ", fonts[1].fileName, '\n'
	matchTwoGlyphs(g0, g1)

go()