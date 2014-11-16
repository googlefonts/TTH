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

###### - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def intervalsIntersect(a, b):
	return (a[1] >= b[0]) and (b[1] >= a[0])

def inInterval(x, i):
	return (i[0] <= x) and (x <= i[1])
