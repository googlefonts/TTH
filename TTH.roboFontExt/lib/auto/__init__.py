
from drawing import geom

def contourSegmentIterator(g):
	for cidx, c in enumerate(g):
		for sidx, s in enumerate(c):
			yield (cidx, sidx)

class HintingData(object):
	def __init__(self, on, typ, name, sh, ina, outa, cont, seg, weight):
		self.pos        = on
		self.type       = typ
		self.name       = name
		self.shearedPos = sh
		self.inTangent  = ina
		self.outTangent = outa
		self.cont       = cont # contour number
		self.seg        = seg  # segment number
		# the following change when we switch from X- to Y-autohinting
		self.weight2D   = weight # a 2D vector
		self.weight     = weight
		self.touched    = False
		self.alignment  = None
		self.leader     = None # who is my leader? (only leaders take part
		# in hinting commands, each connected component of an alignment has
		# exactly one leader)
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
	onPt = geom.makePoint(segment.onCurve)
	if segment.onCurve.name != None:
		#name = segment.onCurve.name.split(',')[0]
		name = segment.onCurve.name
	else:
		print "WARNING ERROR: a segment's onCurve point has no name"
		name = "noname"
	nextOff = geom.makePoint(contour[(sidx+1) % contourLen].points[0])
	nextOn = geom.makePoint(contour[(sidx+1) % contourLen].onCurve)
	prevOn = geom.makePoint(contour[sidx-1].onCurve)
	if len(segment.points) > 1:
		prevOff = segment[-2]
	else:
		prevOff = prevOn
	prevOn = prevOn.sheared(ital)
	nextOn = nextOn.sheared(ital)
	shearedOn = onPt.sheared(ital)
	if computeWeight:
		weight = (nextOn - shearedOn).absolute() + (prevOn - shearedOn).absolute()
	else:
		weight = None
	nextOff = (nextOff-onPt).normalized()
	prevOff = (onPt-prevOff).normalized()
	return HintingData(onPt, segment.type, name, shearedOn, prevOff, nextOff, cidx, sidx, weight)

def makeContours(g, ital):
	contours = [[] for c in g]
	# make a copy of all contours with hinting data
	for contseg in contourSegmentIterator(g):
		hd = makeHintingData(g, ital, contseg, computeWeight=True)
		contours[contseg[0]].append(hd)
	return contours

