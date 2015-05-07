import math

class Point(object):
	__slots__ = ('x', 'y')
	def __init__(self, ix=0.0, iy=0.0):
		self.x = ix
		self.y = iy
	def __len__(self): return 2
	def __getitem__(self, i):
		if i == 0:
			return self.x
		elif i == 1:
			return self.y
		else:
			raise IndexError("coordinate index {} out of range [0,1]".format(i))
	def __repr__(self):
		return "({:f},{:f})".format(self.x, self.y)
	def __add__(self, rhs): # rhs = right hand side
		return Point(self.x + rhs.x, self.y + rhs.y)
	def __sub__(self, rhs):
		return Point(self.x - rhs.x, self.y - rhs.y)
	def __or__(self, rhs): # dot product
		return (self.x * rhs.x + self.y * rhs.y)
	def __mul__(self, s): # 's' is a number, not a point
		return Point(s * self.x, s * self.y)
	def __rmul__(self, s): # 's' is a number, not a point
		return Point(s * self.x, s * self.y)

	def opposite(self):
		return Point(-self.x, -self.y)
	def rotateCCW(self):
		return Point(-self.y, self.x)
	def squaredLength(self):
		return self.x * self.x + self.y * self.y
	def length(self):
		return math.sqrt(self.squaredLength())

	def sheared(self, angleInDegree):
		r = math.tan(math.radians(angleInDegree))
		return Point(self.x - r*self.y, self.y)
	def absolute(self):
		return Point(abs(self.x), abs(self.y))
	def normalized(self):
		l = self.length()
		if l < 1e-6: return Point(0.0, 0.0)
		return Point(self.x/l, self.y/l)

class Matrix(object):
	__slots__ = ('_m')
	def __init__(self):
		self._m = ((1.0, 0.0), (0.0, 1.0)) # ROW MAJOR
	def setRotationRadian(self, angle):
		cosa = math.cos(angle)
		sina = math.sin(angle)
		self._m = ((cosa, -sina), (sina, cosa))
	def __mul__(self, m):
		l = self._m
		r = m._m
		result = Matrix()
		result._m = ((	l[0][0] * r[0][0] + l[0][1] * r[1][0],
					l[0][0] * r[0][1] + l[0][1] * r[1][1] ),
				 (	l[1][0] * r[0][0] + l[1][1] * r[1][0],
					l[1][0] * r[0][1] + l[1][1] * r[1][1] ))
		return result
	def mulVec(self, v):
		m = self._m
		return Point(m[0][0]*v.x + m[0][1]*v.y, m[1][0]*v.x + m[1][1]*v.y)

def makePoint(p): # used when 'p' is a RoboFab point
	return Point(p.x, p.y)

def makePointForPair(p):
	return Point(p[0], p[1])

def lerp(t, a, b):
	return (t * b) + ((1.0 - t) * a)

def computeOffMiddlePoint(scale, pos1, pos2, reverse = False):
	#diff = (scale / 25.0) * (pos2 - pos1).rotateCCW()
	diff = (1.0 / 25.0) * (pos2 - pos1).rotateCCW()
	if reverse:
		diff = diff.opposite()
	mid  = 0.5*(pos1 + pos2)
	return mid + diff
