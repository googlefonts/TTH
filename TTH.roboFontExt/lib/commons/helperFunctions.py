import math
from lib.tools.defaults import getDefault, setDefault

def getOrDefault(dico, key, default):
	try:
		return dico[key]
	except:
		return default

def getOrPutDefault(dico, key, default):
	try:
		return dico[key]
	except:
		dico[key] = default
	return default

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

def roundbase(x, base):
	return int(base * round(float(x)/base))

def mean(l):
	return float(sum(l))/float(len(l))

def intervalsIntersect(a, b):
	return (a[1] >= b[0]) and (b[1] >= a[0])

def inInterval(x, i):
	return (i[0] <= x) and (x <= i[1])

def topologicalSort(l, f):
	n = len(l)
	preds = [[] for i in l]
	visited = [False for i in l]
	loop = list(visited) # separate copy of visited
	# build the list of predecessors for each element of |l|
	for i in range(n):
		for j in range(i+1,n):
			(comp, swap) = f(l[i], l[j])
			if not comp:
				continue
			if swap:
				preds[i].append(j)
			else:
				preds[j].append(i)
	result = []
	def visit(i):
		if loop[i]:
			raise Exception("loop")
		if visited[i]:
			return
		loop[i] = True
		for p in preds[i]:
			visit(p)
		loop[i] = False
		visited[i] = True
		result.append(l[i])
	try:
		for i in range(n):
			visit(i)
		return result
	except:
		pass
	print "ERROR: Found a loop in topological sort"
	return l

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

def getOrNone(dico, key):
	try:
		return dico[key]
	except:
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

def checkDrawingPreferences():
	return (getDefault('drawingSegmentType') == 'qcurve')

def checkSegmentType(font):
	try:
		segmentType = font.preferredSegmentType
	except:
		segmentType = font.preferedSegmentType
	return (segmentType == 'qcurve' or segmentType == 'qCurve')

def checkIntSize(size):
		try:
			size = int(size)
		except ValueError:
			size = 9
		if size < 8: return 8
		return size