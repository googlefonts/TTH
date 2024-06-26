import math, numpy

def distanceTransform(bmp):
	width = bmp.width
	height = bmp.rows
	pitch = bmp.pitch # bytes per row
	boolArray = numpy.array(bmp.buffer, dtype=bool).reshape((height, pitch*8))
	print boolArray

def commandHasAttrib(cmd, atr):
	return (atr in cmd.attrib)

def delCommandAttrib(cmd, atr):
	if atr in cmd.attrib:
		del cmd.attrib[atr]
	assert (not (commandHasAttrib(cmd, atr)))

def makeListItemToIndexDict(l):
	return dict((e,i) for i,e in enumerate(l))

def getOrPutDefault(dico, key, default):
	try:
		return dico[key]
	except:
		dico[key] = default
	return default

def invertedDictionary(dic):
	return dict([(v,k) for (k,v) in dic.iteritems()])

def partition(l, p):
	yes, no = [], []
	for e in l:
		if p(e): yes.append(e)
		else: no.append(e)
	return (yes, no)

def angleOfVector((vx, vy)):
	return addAngles(math.atan2(vy, vx) / math.pi * 180.0, 0.0)

def angleOfVectorBetweenPoints(point1, point2):
	return angleOfVector((point2.x - point1.x, point2.y - point1.y))

def angleOfVectorBetweenPairs((p1x, p1y), (p2x, p2y)):
	return angleOfVector((p2x - p1x, p2y - p1y))

def addAngles(a, b):
	r = a+b
	while r > 180.0:
		r -= 360.0
	while r <= -180.0:
		r += 360.0
	return r

def closeAngle(angle1, angle2):
	"""True if the angle are close modulo 360 degrees"""
	return abs(addAngles(angle1,  - angle2)) <= 3.0

def closeAngleModulo180_withTolerance(angle1, angle2, tolerance):
	"""True if the angle are close modulo 180 degrees"""
	diff = angle1 - angle2
	while diff >= 90.0:
		diff -= 180.0
	while diff < -90.0:
		diff += 180.0
	return abs(diff) <= tolerance

def approxEqual(a1, a2, factor):
	a_max = max(abs(a1), abs(a2))
	return ( abs(a1 - a2) <= factor*a_max )

def opposite(direction1, direction2):
	if direction1[0] + direction2[0] == 0:
		return True
	if direction1[1] + direction2[1] == 0:
		return True
	return False

def isVertical(angle):
	a = round(addAngles(angle, 0.0))
	return a == 90 or a == -90

def isHorizontal(angle):
	a = round(addAngles(angle, 0.0))
	return a == 0 or a == 180 or a == -180

def isVertical_withTolerance(angle, tolerance):
	a = abs(addAngles(angle, 0.0)) # Now, we know that 0 <= a <= 180.0
	return abs(90.0 - a) <= tolerance

def isHorizontal_withTolerance(angle, tolerance):
	a = abs(addAngles(angle, 0.0)) # Now, we know that 0 <= a <= 180.0
	return (a <= tolerance) or (a >= 180.0 - tolerance)

#True si il existe un element de la liste l pour lequel la fonction p renvoi True (on dit que le predicat p est vrai sur cet element)
def exists(l, p):
	for e in l:
		if p(e):
			return True
	return False

def mean(l):
	return float(sum(l))/float(len(l))

def intervalsIntersect(a, b):
	return (a[1] >= b[0]) and (b[1] >= a[0])

def inInterval(x, i):
	return (i[0] <= x) and (x <= i[1])

def pointsApproxEqual(p_glyph, p_cursor, value):
	return (abs(p_glyph[0] - p_cursor[0]) < value) and (abs(p_glyph[1] - p_cursor[1]) < value)

def pointInCommand(commandPos, p_cursor):
	x = commandPos[0][0]
	y = commandPos[0][1]
	width = commandPos[1][0]
	height = commandPos[1][1]
	return (p_cursor[0] >= (x-width/2) and p_cursor[0] <= (x+width/2) and p_cursor[1] >= (y-height/2) and p_cursor[1] <= (y+height/2))

def find_closest(l, p, point):
	if l == []:
		return None
	candidate = (l[0], distance(l[0], point))
	for e in l:
		if p(e):
			if distance(e, point) < candidate[1]:
				candidate = (e, distance(e, point))
	if p(candidate[0]):
		return candidate[0]
	return None

def find_in_list(l, p):
	for e in l:
		if p(e):
			return e
	return None

def find_in_dict(d, p):
	for k, v in d.iteritems():
		if p(k, v):
			return k
	return None

def getGlyphNameByUnicode(unicodeToNameDict, unicodeChar):
	return unicodeToNameDict[unicodeChar]

def difference(point1, point2):
	return ((point1[0] - point2[0]), (point1[1] - point2[1]))

def distance(point1, point2):
	return math.sqrt((point2[0]-point1[0])*(point2[0]-point1[0]) + (point2[1]-point1[1])*(point2[1]-point1[1]))

def getAngle((x1, y1), (x2, y2)):
	xDiff = x2-x1
	yDiff= y2-y1
	return math.atan2(yDiff, xDiff)

def fontIsQuadratic(font):
	try:
		segmentType = font.preferredSegmentType
	except:
		segmentType = font.preferedSegmentType
	return (segmentType.lower() == 'qcurve')

def roundbase(x, base):
	return int(base * round(float(x)/base))

def topologicalSort(l, f):
	n = len(l)
	preds = [[] for i in l]
	visited = numpy.zeros(n, dtype='bool')
	loop    = numpy.zeros(n, dtype='bool')
	try:
		# build the list of predecessors for each element of |l|
		for i in range(n):
			for j in range(i+1,n):
				(comp, swap) = f(l[i], l[j])
				if not comp: # not comparable
					continue
				if swap:
					preds[i].append(j)
				else:
					preds[j].append(i)
		result = []
		def visit(level,i):
			#print "({},{})".format(level,i),
			#print l[i].attrib
			if loop[i]:
				#print "LOOP",l[i]
				raise Exception("Found a loop in topological sort for command {},{},{}".format(i,l[i].get('code'),l[i].get('point')))
			if visited[i]:
				return
			loop[i] = True
			for p in preds[i]:
				visit(level+1,p)
			loop[i] = False
			visited[i] = True
			result.append(l[i])
		for i in range(n):
			visit(0,i)
		#print "=======================done topo"
		return result
	except Exception as e:
		print "Exception during topological sort:", e
		return l

def deltaDictFromString(s):
	try:
		if s == '0@0': return {}
		listOfLists = [[int(i) for i in reversed(x.split('@'))] for x in s.split(',')]
		for li in listOfLists: li[0] = str(li[0])
		return dict(listOfLists)
	except:
		return {}
