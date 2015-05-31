
from commons import helperFunctions as HF

FL_tth_key = "com.fontlab.v2.tth"
SP_tth_key = "com.sansplomb.tth"

def modifiesLSBOrRSB(cmd):
	code = cmd.get('code')
	targets = ['lsb', 'rsb']
	if code in ['alignh', 'alignv', 'alignt', 'alignb']:
		return cmd.get('point') in targets
	elif code in ['mdeltav', 'mdeltah', 'fdeltav', 'fdeltah']:
		return cmd.get('point') in targets
	elif code in ['singlev', 'singleh']:
		return cmd.get('point2') in targets
	elif code in ['doublev', 'doubleh']:
		return (cmd.get('point1') in targets) or (cmd.get('point2') in targets)
	elif code in ['interpolatev', 'interpolateh']:
		return cmd.get('point') in targets
	else:
		return False

def compare(A, B):
	A_isMiddleDelta = A.get('code') in ['mdeltah', 'mdeltav']
	B_isMiddleDelta = B.get('code') in ['mdeltah', 'mdeltav']
	A_isFinalDelta  = A.get('code') in ['fdeltah', 'fdeltav']
	B_isFinalDelta  = B.get('code') in ['fdeltah', 'fdeltav']
	ba = (True, True)
	ab = (True, False)
	dontcare = (False, False)

	if ((A_isMiddleDelta and B_isMiddleDelta) and (A.get('point') == B.get('point'))) \
	or (A_isFinalDelta and B_isFinalDelta):
		# Two middle deltas on the same point
		# OR two final deltas: we group deltas with same type together
		if A.get('mono') == 'true': Avalue = 2
		else: Avalue = 0
		if A.get('gray') == 'true': Avalue += 1
		if B.get('mono') == 'true': Bvalue = 2
		else: Bvalue = 0
		if B.get('gray') == 'true': Bvalue += 1
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
		cKeys = [k for k in keys if HF.commandHasAttrib(c, k)]
		n = len(cKeys)
		if n == 1: # Align, MiddleDelta, FinalDelta
			target.append(c.get('point'))
			sources.append([c.get('point')])
		elif n == 2: # SingleLink
			target.append(c.get('point2'))
			sources.append([c.get('point1')])
		elif n == 3: # Interpolate
			target.append(c.get('point'))
			sources.append([c.get('point1'), c.get('point2')])
		else:
			print "[WARNING] Command has a problem!"
			target.append(None)
			sources.append([])

	AbeforeB = (target[0] != None) and (target[0] in sources[1])
	BbeforeA = (target[1] != None) and (target[1] in sources[0])
	if AbeforeB and BbeforeA:
		A_isAlign       = A.get('code') in ['alignh', 'alignv']
		B_isAlign       = B.get('code') in ['alignh', 'alignv']
		if A_isAlign and B_isMiddleDelta: # special case
			return ab
		elif B_isAlign and A_isMiddleDelta : # symmetrical special case
			return ba
		else:
			#print "COMPARE_LOOP",A,B
			raise Exception("loop")
	if   AbeforeB: return ab
	elif BbeforeA: return ba
	else: return dontcare

def sort(cmds):
	x, ytb, y, fdeltah, fdeltav = [], [], [], [], []
	for c in cmds:
		code = c.get('code')
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

