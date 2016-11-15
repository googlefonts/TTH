
from commons import helperFunctions as HF

#def modifiesLSBOrRSB(cmd):
#	code = cmd.get('code')
#	targets = ['lsb', 'rsb']
#	if code in ['alignh', 'alignv', 'alignt', 'alignb']:
#		return cmd.get('point') in targets
#	elif code in ['mdeltav', 'mdeltah', 'fdeltav', 'fdeltah']:
#		return cmd.get('point') in targets
#	elif code in ['singlev', 'singleh']:
#		return cmd.get('point2') in targets
#	elif code in ['doublev', 'doubleh']:
#		return (cmd.get('point1') in targets) or (cmd.get('point2') in targets)
#	elif code in ['interpolatev', 'interpolateh']:
#		return cmd.get('point') in targets
#	else:
#		return False

middleDeltaCodes = ['mdeltah', 'mdeltav']
finalDeltaCodes  = ['fdeltah', 'fdeltav']

def compare(A, B):
	Acode = A.get('code')
	Bcode = B.get('code')
	A_isMiddleDelta = Acode in middleDeltaCodes
	B_isMiddleDelta = Bcode in middleDeltaCodes
	A_isFinalDelta  = Acode in finalDeltaCodes
	B_isFinalDelta  = Bcode in finalDeltaCodes
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

	# Some code in case we have weird diagonal commands
	A_isVertical = Acode[-1] in ['v','t','b','l']
	B_isVertical = Bcode[-1] in ['v','t','b','l']
	A_isHorizontal = Acode[-1] in ['h','l']
	B_isHorizontal = Bcode[-1] in ['h','l']
	no_diagonal = ('diagonal' not in Acode) and ('diagonal' not in Bcode)
	if no_diagonal:
		if A_isHorizontal and B_isVertical:
			return dontcare
		if B_isHorizontal and A_isVertical:
			return dontcare
	# end of diagonal-handling code

	keys = ['point', 'point1', 'point2']

	debug = False

	sources = [[],[]]
	targets = [[],[]]
	for i, c, vert, horz in [(0, A, A_isVertical, A_isHorizontal), (1, B, B_isVertical, B_isHorizontal)]:
		cKeys = [k for k in keys if HF.commandHasAttrib(c, k)]
		n = len(cKeys)
		if n == 1: # Align, MiddleDelta, FinalDelta
			if vert:
				targets[i].append(c.get('point')+'Y')
				sources[i].append(c.get('point')+'Y')
			if horz:
				targets[i].append(c.get('point')+'X')
				sources[i].append(c.get('point')+'X')
		elif n == 2: # SingleLink
			if vert:
				targets[i].append(c.get('point2')+'Y')
				sources[i].append(c.get('point1')+'Y')
			if horz:
				targets[i].append(c.get('point2')+'X')
				sources[i].append(c.get('point1')+'X')
		elif n == 3: # Interpolate
			if vert:
				targets[i].append(c.get('point')+'Y')
				sources[i].extend([c.get('point1')+'Y', c.get('point2')+'Y'])
			if horz:
				targets[i].append(c.get('point')+'X')
				sources[i].extend([c.get('point1')+'X', c.get('point2')+'X'])
		else:
			print "[WARNING] Command has a problem!\n", c

	AbeforeB = (targets[0] != []) and (len([1 for t in targets[0] if (t in sources[1])]) > 0)
	BbeforeA = (targets[1] != []) and (len([1 for t in targets[1] if (t in sources[0])]) > 0)
	if AbeforeB and BbeforeA:
		A_isAlign       = Acode in ['alignh', 'alignv']
		B_isAlign       = Bcode in ['alignh', 'alignv']
		if A_isAlign and B_isMiddleDelta: # special case
			return ab
		elif B_isAlign and A_isMiddleDelta : # symmetrical special case
			return ba
		else:
			#print "COMPARE_LOOP",A,B
			raise Exception("loop")
	if   AbeforeB:
		if debug:
			print "COMPARE"
			print A.attrib
			print B.attrib
			print "A-->B"
		return ab
	elif BbeforeA:
		if debug:
			print "COMPARE"
			print A.attrib
			print B.attrib
			print "B-->A"
		return ba
	else:
		if debug: print "don't care"
		return dontcare

def sort(cmds):
	has_diagonal = False
	x, ytb, y, fdeltah, fdeltav = [], [], [], [], []
	for c in cmds:
		if c.get('active') == 'false':
			continue
		code = c.get('code')
		if code is None:
			print "[WARNING] Command has a problem!\n", c
			continue
		if 'diagonal' in code:
			has_diagonal = True
			x.append(c)
		elif code == 'fdeltah':
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
	if has_diagonal:
		return sum([HF.topologicalSort(l, compare) for l in [x+y,fdeltah,fdeltav]], ytb)
	else:
		x = HF.topologicalSort(x, compare)
		x.extend(ytb)
		return sum([HF.topologicalSort(l, compare) for l in [y,fdeltah,fdeltav]], x)
