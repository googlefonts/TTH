
from commons import helperFunctions as HF

def compare(A, B):
	#A_isSingleLink  = A['code'] in ['singleh', 'singlev']
	#B_isSingleLink  = B['code'] in ['singleh', 'singlev']
	#A_isInterpolate = A['code'] in ['interpolateh', 'interpolatev']
	#B_isInterpolate = B['code'] in ['interpolateh', 'interpolatev']
	A_isMiddleDelta = A['code'] in ['mdeltah', 'mdeltav']
	B_isMiddleDelta = B['code'] in ['mdeltah', 'mdeltav']
	A_isFinalDelta  = A['code'] in ['fdeltah', 'fdeltav']
	B_isFinalDelta  = B['code'] in ['fdeltah', 'fdeltav']

	if ((A_isMiddleDelta and B_isMiddleDelta) and (A['point'] == B['point'])) \
	or (A_isFinalDelta and B_isFinalDelta):
		if A['mono'] == 'true': Avalue = 2
		else: Avalue = 0
		if A['gray'] == 'true': Avalue += 1
		if B['mono'] == 'true': Bvalue = 2
		else: Bvalue = 0
		if B['gray'] == 'true': Bvalue += 1
		if Avalue < Bvalue:   return (True, True) # order == B->A
		elif Avalue > Bvalue: return (True, False) # order == A->B
		else: return (False, False)
	elif A_isFinalDelta:
		return (True, True) # order == B->A
	elif B_isFinalDelta:
		return (True, False) # order == A->B

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
			return (True, False) # order == A->B
		elif A_isMiddleDelta and B_isAlign: # special
			return (True, True) # order == B->A
		else:
			print "COMPARE_LOOP",A,B
			raise Exception("loop")
	if   AbeforeB: return (True, False)
	elif BbeforeA: return (True, True)
	else: return (False, False)

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

