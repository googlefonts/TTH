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
		for t in xrange(lenTo):
			localScore = score(fromC[f], toC[t])
			s = indexOfMin([x[1] for x in table[f-1][0:t+1]])
			table[f].append((s, table[f-1][s][1] + localScore))
	permut = [indexOfMin([x[1] for x in table[lenFrom-1]])]
	matchQuality = table[lenFrom-1][permut[0]][1] # lower is better
	for f in range(lenFrom-1, 0, -1):
		permut.append(table[f][permut[-1]][0])
	permut.reverse()
	return matchQuality, permut

def fix((s,permut), i, n):
	return s,[(x+i) % n for x in permut] # recover original segment numbers

def matchTwoGlyphs(fromG, toG):
	nbContours = len(fromG), len(toG)
	if nbContours[0] != nbContours[1]:
		return None
	for fromC in fromG:
		print "From the contour that starts at", fromC[0].shearedPos
		for toC in toG:
			n = len(toC)
			matchings = [fix(matchTwoContours(fromC, toC[i:]+toC[:i]), i, n) for i in xrange(n)]
			i = indexOfMin([x[0] for x in matchings])
			matchingQuality, permut = matchings[i]
			print matchingQuality
			for i,j in enumerate(permut):
				print "{0}->{1}\t".format(i,j),
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
