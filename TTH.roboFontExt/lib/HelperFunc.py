import math

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


def directionForPairs((p1x, p1y), (p2x, p2y)):
	direction_x = 4
	direction_y = 4
	if p1x < p2x:
		# Direction is RIGHT
		direction_x = 1
	elif p1x > p2x:
		# Direction is LEFT
		direction_x = -1
	else:
		# Direction is NONE
		direction_x = 4

	if p1y < p2y:
		# Direction is UP
		direction_y = 1
	elif p1y > p2y:
		# Direction is DOWN
		direction_y = -1
	else:
		# Direction is NONE
		direction_y = 4
	return (direction_x, direction_y)

def directionForPoints(a,b):
	return directionForPairs((a.x, a.y), (b.x, b.y))

def rotated(point, angle):
	x = point.x
	y = point.y
	angle = (math.radians(angle))
	cosa = math.cos(angle)
	sina = math.sin(angle)
	rotatedPoint_x = int(cosa*x - sina*y)
	rotatedPoint_y = int(sina*x + cosa*y)
	return (rotatedPoint_x, rotatedPoint_y)

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

def absoluteDiffOfPairs(point1, point2):
	return (abs(point1[0] - point2[0]), abs(point1[1] - point2[1]))

def absoluteDiff(point1, point2):
	return (abs(point1.x - point2.x), abs(point1.y - point2.y))

def distanceOfPairs(point1, point2):
	dx, dy = absoluteDiffOfPairs(point1, point2)
	return math.sqrt(dx*dx+dy*dy)

def distance(point1, point2):
	dx, dy = absoluteDiff(point1, point2)
	return math.sqrt(dx*dx+dy*dy)

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

def shearPoint(point, angle):
	r = math.tan(math.radians(angle))
	return (point.x - r*point.y, point.y)

def shearPair((p_x, p_y), angle):
	r = math.tan(math.radians(angle))
	return (p_x - r*p_y, p_y)

def roundbase(x, base):
	return int(base * round(float(x)/base))

###### - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def intervalsIntersect(a, b):
	return (a[1] >= b[0]) and (b[1] >= a[0])

def inInterval(x, i):
	return (i[0] <= x) and (x <= i[1])

def pointToPair(p):
	return p.x, p.y

def scale(s, (x,y)):
	return s*x, s*y

def scalePoint(s, p):
	return scale(s, pointToPair(p))

def add((x1, y1), (x2, y2)):
	return x1+x2, y1+y2

def lerpPoints(t, a, b):
	return add(scalePoint(1.0-t, a), scalePoint(t, b))

def normalized(p):
	l = math.sqrt(p.x*p.x+p.y*p.y)
	if l < 0.01: return (0.0, 0.0)
	return (p.x/l, p.y/l)

def normalizedPair(p):
	l = math.sqrt(p[0]*p[0]+p[1]*p[1])
	if l < 0.01: return (0.0, 0.0)
	return (p[0]/l, p[1]/l)

def negatePair((x,y)):
	return (-x, -y)

def dotOfPairs(p1, p2):
	return(p1[0]*p2[0] + p1[1]*p2[1])

def diffOfPairs(p1, p2):
	return(p1[0]-p2[0], p1[1]-p2[1])

def det2x2(a, b):
	return a[0]*b[1] - a[1]*b[0]
