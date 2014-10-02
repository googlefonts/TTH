import math

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
	
def absoluteDiff(point1, point2):
	return (abs(point1.x - point2.x), abs(point1.y - point2.y))
	
def distance(point1, point2):
	dx, dy = absoluteDiff(point1, point2)
	return math.sqrt(dx*dx+dy*dy)
	
def closeAngle(angle1, angle2):
	diff = angle1 - angle2
	while diff >= 90.0:
		diff -= 180.0
	while diff < -90.0:
		diff += 180.0
	return abs(diff) < 10.0

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
	a = abs(angle)
	return ((85 < a) and (a < 95))

def isHorizontal(angle):
	a = abs(angle)
	return ((0 <= a) and (a <= 10)) or ((170 <= a) and (a <= 180))

def isHorizontal_withTolerance(angle, tolerance):
	a = abs(angle)
	return ((0 <= a) and (a <= tolerance)) or ((180-tolerance <= a) and (a <= 180))

#True si il existe un element de la liste l pour lequel la fonction p renvoi True (on dit que le predicat p est vrai sur cet element)
def exists(l, p):
	for e in l:
		if p(e):
			return True
	return False

def sheared(point, angle):
	r = math.tan(math.radians(angle))
	return (point.x - r*point.y, point.y)

def roundbase(x, base):
	return int(base * round(float(x)/base))
	
def compare((k1,v1),(k2,v2)):
	return v2 - v1

###### - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

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
