import Automation
import geom
import math
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
	v = values[0]
	for j, nv in enumerate(values):
		if nv < v:
			v = nv
			i = j
	return i

def matchTwoContours(fromC, toC):
	lenFrom = len(fromC)
	lenTo = len(toC)
	table = [[] for _ in range(lenFrom)]
	for t in xrange(lenTo):
		table[0].append((-1, score(fromC[0], toC[t])))
	for f in xrange(1,lenFrom):
		s = 0
		minVal = table[f-1][0][1]
		for t in xrange(lenTo):
			localScore = score(fromC[f], toC[t])
			newVal = table[f-1][t][1]
			if newVal < minVal:
				minVal = newVal
				s = t
			table[f].append((s, minVal + localScore))
	permut = [indexOfMin([x[1] for x in table[lenFrom-1]])]
	matchQuality = table[lenFrom-1][permut[0]][1] # lower is better
	for f in range(lenFrom-1, 0, -1):
		permut.append(table[f][permut[-1]][0])
	permut.reverse()
	return matchQuality, permut

def fix((s,permut), i, n):
	return s,[(x+i) % n for x in permut] # recover original segment numbers

def all_perms(elements):
	n = len(elements)
	if n <= 1:
		yield elements
	else:
		for perm in all_perms(elements[1:]):
			for i in range(n):
				# nb elements[0:1] works in both string and list contexts
				yield perm[:i] + elements[0:1] + perm[i:]

def matchTwoGlyphs(fromG, toG):
	nbContours = len(fromG), len(toG)
	if nbContours[0] != nbContours[1]:
		return None
	matchings = [[] for f in fromG]
	for f,fromC in enumerate(fromG):
		for toC in toG:
			n = len(toC)
			permutedMatches = [fix(matchTwoContours(fromC, toC[i:]+toC[:i]), i, n) for i in xrange(n)]
			i = indexOfMin([x[0] for x in permutedMatches])
			matchings[f].append(permutedMatches[i])
	bestScore = None
	bestPerm = []
	for perm in all_perms(range(len(toG))):
		score = sum(matchings[i][perm[i]][0] for i in xrange(nbContours[0]))
		if (bestScore == None) or (bestScore > score):
			bestScore = score
			bestPerm = perm
	for f,t in enumerate(bestPerm):
		print "Contour",f,"of source glyph matches contour",t,"of target glyph as follows:"
		for i,j in enumerate(matchings[f][t][1]):
			print "{}:{}\t\t".format(i,j),
		print ''

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
	print "\nFrom", fonts[0].fileName, "\nto  ", fonts[1].fileName
	matchTwoGlyphs(g0, g1)

go()
