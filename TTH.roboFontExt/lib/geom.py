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
			print "ERROR ON INDEX", i
			assert(False)
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

def makePoint(p): # used when 'p' is a RoboFab point
	return Point(p.x, p.y)

def lerp(t, a, b):
	return (t * b) + ((1.0 - t) * a)

def det2x2(a, b):
	return a.x * b.y - a.y * b.x

def splitQuadratic(t, quadBez):
	"""Splits a quadratic Bezier into two quadratic Bezier at the given parameter t.

	Uses de Casteljau algorithm."""
	a0 = lerp(t, quadBez[0], quadBez[1])
	a1 = lerp(t, quadBez[1], quadBez[2])
	c0 = lerp(t, a0, a1)
	return (quadBez[0], a0, c0), (c0, a1, quadBez[2])

def quadraticPointAtParam(t, quadBez):
	"""Splits a quadratic Bezier into two quadratic Bezier at the given parameter t.

	Uses de Casteljau algorithm."""
	a0 = lerp(t, quadBez[0], quadBez[1])
	a1 = lerp(t, quadBez[1], quadBez[2])
	return lerp(t, a0, a1)

eps = 1.0e-5

def solveQuadratic(a, b, c):
	if abs(a) < eps:
		if abs(b) < eps: return []
		return [- c / b]
	disc = b * b - 4.0 * a * c
	if disc < 0.0: return []
	if disc < eps:
		t = - b / (2.0 * a)
		return [t, t]
	disc = math.sqrt(disc)
	root1 = ( - b - disc ) / (2.0 * a)
	root2 = ( - b + disc ) / (2.0 * a)
	if root2 < root1:
		return [root2, root1]
	return [root1, root2]

def quadBezierToPolynomial((a, b, c)):
	return (a+c-b), (b-(2*a)), a

def quadBezierHitsLine(quad, (n, d)):
	# lineq = (Point(nx, ny), d) --> nx*x+ny*y+d = 0
	a,b,c = quadBezierToPolynomial(quad)
	a = a | n
	b = b | n
	c = (c | n) + d
	return [(r, quadraticPointAtParam(r, quad)) for r in [r for r in solveQuadratic(a, b, c) if r > -eps and r < 1.0+eps]]

