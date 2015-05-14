
from commons import helperFunctions as HF

def compare(A, B):
	A_isMiddleDelta = A['code'] in ['mdeltah', 'mdeltav']
	B_isMiddleDelta = B['code'] in ['mdeltah', 'mdeltav']
	A_isFinalDelta  = A['code'] in ['fdeltah', 'fdeltav']
	B_isFinalDelta  = B['code'] in ['fdeltah', 'fdeltav']
	ba = (True, True)
	ab = (True, False)
	dontcare = (False, False)

	if ((A_isMiddleDelta and B_isMiddleDelta) and (A['point'] == B['point'])) \
	or (A_isFinalDelta and B_isFinalDelta):
		# Two middle deltas on the same point
		# OR two final deltas: we group deltas with same type together
		if A['mono'] == 'true': Avalue = 2
		else: Avalue = 0
		if A['gray'] == 'true': Avalue += 1
		if B['mono'] == 'true': Bvalue = 2
		else: Bvalue = 0
		if B['gray'] == 'true': Bvalue += 1
		if Avalue < Bvalue:   return ba
		elif Avalue > Bvalue: return ab
		else: return dontcare
	elif A_isFinalDelta: # B is NOT final delta, so B goes before A
		return ba
	elif B_isFinalDelta: # A is NOT final delta, so A goes before B
		return ab

	keys = ['point', 'point1', 'point2']
	sources = []
	target = []
	for c in [A,B]:
		cKeys = [k for k in keys if k in c]
		n = len(cKeys)
		if n == 1: # Align, MiddleDelta, FinalDelta
			target.append(c['point'])
			sources.append([c['point']])
		elif n == 2: # SingleLink
			target.append(c['point2'])
			sources.append([c['point1']])
		elif n == 3: # Interpolate
			target.append(c['point'])
			sources.append([c['point1'], c['point2']])
		else:
			print "[WARNING] Command has a problem!"
			target.append(None)
			sources.append([])

	AbeforeB = (target[0] != None) and (target[0] in sources[1])
	BbeforeA = (target[1] != None) and (target[1] in sources[0])
	if AbeforeB and BbeforeA:
		A_isAlign       = A['code'] in ['alignh', 'alignv']
		B_isAlign       = B['code'] in ['alignh', 'alignv']
		if A_isAlign and B_isMiddleDelta: # special case
			return ab
		elif B_isAlign and A_isMiddleDelta : # symmetrical special case
			return ba
		else:
			print "COMPARE_LOOP",A,B
			raise Exception("loop")
	if   AbeforeB: return ab
	elif BbeforeA: return ba
	else: return dontcare

def sort(cmds):
	x, ytb, y, fdeltah, fdeltav = [], [], [], [], []
	for c in cmds:
		code = c['code']
		if code == 'fdeltah':
			fdeltah.append(c)
		elif code == 'fdeltav':
			fdeltav.append(c)
		elif code[-1] in ['h']:
			x.append(c)
		elif code[-1] in ['v']:
			y.append(c)
		elif code[-1] in ['t', 'b']:
			ytb.append(c)
		else:
			y.append(c)
	x = HF.topologicalSort(x, compare)
	x.extend(ytb)
	return sum([HF.topologicalSort(l, compare) for l in [y,fdeltah,fdeltav]], x)

