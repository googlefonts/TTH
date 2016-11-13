from commons import helperFunctions as HF
from drawing import geom

zero = geom.Point(0,0)

class PointTouched(object):
	def __init__(self, orig=zero, move=zero, newpos=zero, csi=(0,0,0)):
		self.originalPos = orig
		self.move     = move
		self.point = newpos
		self.csi = csi
	def output(self):
		print "<<'org':{}, 'move':{}, 'point':{}, 'csi':{}>>".format(self.originalPos, self.move, self.point, self.csi)

def savePointTouched(regs, axis, pName, csi, pt):
	if pName in ['lsb', 'rsb']:
		regs.setMovedSideBearing(pName, pt)
	else:
		regs.movedPoints[axis][csi[0]][csi] = pt

class Registers(object):
	def __init__(self, fm, gm):
		self.fm = fm
		self.gm = gm
		self.movedPoints = None
		self.movedSideBearings = {'lsb':None, 'rsb':None}
		self.RP0 = None
		self.RP1 = None
		self.RP2 = None
		self.x_instructions = []
		self.y_instructions = []
		self.finalDeltasH = []
		self.finalDeltasV = []
	def setMovedSideBearing(self, name, pt):
		if name in self.movedSideBearings:
			self.movedSideBearings[name] = pt
	def getMovedSideBearing(self, name):
		return self.movedSideBearings.get(name)
	def initMovedSideBearing(self, name):
		p = self.gm.positionForPointName(name)
		msb = PointTouched(p, zero, p, None)
		self.movedSideBearings[name] = msb
		return self.movedSideBearings[name]

commandGroups = [	('alignToZone', ['alignt', 'alignb']),
				('align',       ['alignv', 'alignh']),
				('single',      ['singlev', 'singleh']),
				('double',      ['doublev', 'doubleh']),
				('diagonal',    ['singlediagonal', 'doublediagonal']),
				('interpolate', ['interpolatev', 'interpolateh']),
				('mdelta',      ['mdeltah', 'mdeltav']),
				('fdelta',      ['fdeltah', 'fdeltav']) ]
commandToGroup = dict(sum([[(code, groupName) for code in group] for groupName,group in commandGroups], []))

def getCommandGroup(command):
	# Might throw exception if command's code is unknown
	return commandToGroup.get(command.get('code'), 'pass')

def getDeltaGroup(delta):
	group = ''
	if delta.get('mono') == 'true': group += 'M'
	if delta.get('gray') == 'true': group += 'G'
	if len(group) == 0:
		return None
	return (group + delta.get('code')[-1])

def groupList(l, classifier):
	groups = []
	prevGroup = None
	for e in l:
		curGroup = classifier(e)
		if curGroup == None: continue
		if prevGroup == curGroup:
			# append element |e| to the group that is already at the end of |groups|
			groups[-1][1].append(e)
		else:
			# append element |e| to a new group appended to |groups|
			groups.append((curGroup,[e]))
		prevGroup = curGroup
	return groups

def groupDeltas(deltas):
	return groupList(deltas, getDeltaGroup)

def groupCommands(glyphAWCommands):
	return groupList(glyphAWCommands, getCommandGroup)

def makePointRFNameToIndexDict(fm, gm):
	result = {}
	index = 0
	for contour in gm.RFGlyph:
		for point in contour.points:
			result[gm.hintingNameForPoint(point)] = index
			index += 1

	return result

def calculateInterpolateMove(regs, cmd, horizontal=False):
	csi  = regs.gm.csiOfPointName(cmd['point'])
	csi1 = regs.gm.csiOfPointName(cmd['point1'])
	csi2 = regs.gm.csiOfPointName(cmd['point2'])
	p =  geom.makePoint(regs.gm.pointOfCSI(csi))
	p1 = geom.makePoint(regs.gm.pointOfCSI(csi1))
	p2 = geom.makePoint(regs.gm.pointOfCSI(csi2))

	axisName = 'x'
	if horizontal: axisName = 'y'

	pm1 = regs.movedPoints[axisName][csi1[0]].get(csi1) # if not found, returns None
	if pm1 is None: # never touched before
		pm1 = regs.movedPoints[axisName][csi1[0]][csi1] = PointTouched(p1, zero, p1, csi1)

	pm2 = regs.movedPoints[axisName][csi2[0]].get(csi2) # if not found, returns None
	if pm2 is None: # never touched before
		pm2 = regs.movedPoints[axisName][csi2[0]][csi2] = PointTouched(p2, zero, p2, csi2)

	pm = regs.movedPoints[axisName][csi[0]].get(csi) # if not found, returns None
	if pm is None: # never touched before
		axis = 0
		if horizontal:
			axis = 1
		w = float(p2[axis] - p1[axis])
		factor = float(p[axis]-p1[axis])/w
		newPos = factor*pm2.point + (1.0-factor)*pm1.point
		delta = int(round(newPos[axis])) - p[axis]
		if horizontal:
			pMove = geom.Point(0, delta)
		else:
			pMove = geom.Point(delta, 0)
		regs.movedPoints[axisName][csi[0]][csi] = PointTouched(p, pMove, p+pMove, csi)
	else:
		regs.movedPoints[axisName][csi[0]][csi] = PointTouched(p, zero, p, csi)


def calculateAlignMove(regs, cmd, horizontal=False):
	pName = cmd['point']
	if pName in ['lsb', 'rsb']:
		pm = regs.getMovedSideBearing(pName)
		if pm == None:
			regs.initMovedSideBearing(pName)
		return
	axisName = 'x'
	if horizontal: axisName = 'y'
	csi = regs.gm.csiOfPointName(pName)
	p = geom.makePoint(regs.gm.pointOfCSI(csi))
	pm = regs.movedPoints[axisName][csi[0]].get(csi) # if not found, returns None
	if pm is None: # never touched before
		regs.movedPoints[axisName][csi[0]][csi] = PointTouched(p, zero, p, csi)
	# else: # nothing to do

def calculateAlignZoneMove(regs, cmd):
	cmdZone = cmd['zone']
	fmZones = regs.fm.zones
	if cmdZone in fmZones:
		try:
			zone = fmZones[cmdZone]
			zoneHeight = int(zone['shift']) + int(zone['position'])
			zonePosition = int(zone['position'])
			zoneWidth = int(zone['width'])
		except: return
	else:
		print "BUG in CALCULATE ALIGN ZONE"
		return

	csi = regs.gm.csiOfPointName(cmd['point'])
	p = geom.makePoint(regs.gm.pointOfCSI(csi))

	pm = regs.movedPoints['y'][csi[0]].get(csi) # if not found, returns None
	if pm is None: # never touched before
		if zone['top'] and zoneHeight <= p.y <= zoneHeight + zoneWidth:
			pMove = geom.Point(0, zoneHeight - p.y + (p.y - zonePosition))
		elif not zone['top'] and zoneHeight - zoneWidth <= p.y <= zoneHeight:
			pMove = geom.Point(0, zoneHeight - p.y + (p.y - zonePosition))
		else:
			pMove = geom.Point(0, zoneHeight - p.y)
		pT = PointTouched(p, pMove, p+pMove, csi)
		#print "@@@@@@@@@@",p,pMove,p+pMove
	else:
		print "ALIGN TO ZONE AFTER POINT HAS ALREADY BEEN MOVED !!!"
		pMove = geom.Point(0, zoneHeight - p.y)
		pT = PointTouched(p, pm.move+pMove, pm.point+pMove, csi)
	regs.movedPoints['y'][csi[0]][csi] = pT

def getCSIAndPosAndTouchedFromPointName(regs, pName, axis):
	if pName in ['lsb', 'rsb']:
		return None, regs.gm.positionForPointName(pName), regs.getMovedSideBearing(pName)
	else:
		csi = regs.gm.csiOfPointName(pName)
		return csi, geom.makePoint(regs.gm.pointOfCSI(csi)), regs.movedPoints[axis][csi[0]].get(csi)

def calculateLinkMove(regs, cmd, horizontal=False, double=False, diagonal=False):
	hStems = regs.fm.horizontalStems
	vStems = regs.fm.verticalStems
	if not diagonal:
		if horizontal: vStems = {}
		else: hStems = {}

	# Get the original point positions
	axis = 0
	axisName = 'x'
	if horizontal:
		axis = 1
		axisName = 'y'
	p1Name = cmd['point1']
	p2Name = cmd['point2']
	csi1, p1, p1m = getCSIAndPosAndTouchedFromPointName(regs, p1Name, axisName)
	#print "Point 1: ", p1Name, csi1, p1, p1m
	csi2, p2, p2m = getCSIAndPosAndTouchedFromPointName(regs, p2Name, axisName)
	#print "Point 2: ", p2Name, csi2, p2, p2m

	cmdStem = cmd.get('stem')
	if (cmdStem in hStems) or (cmdStem in vStems):
		try:
			if cmdStem in hStems:
				fontStem = hStems[cmdStem]
			else:
				fontStem = vStems[cmdStem]
			#width = fontStem['width']
			value = fontStem['targetWidth']
			distance = int(value)
		except: return

		if diagonal:
			dp = p2 - p1
			ndp = dp.normalized()
			originalDistance = dp.length()
			delta = distance - originalDistance
			if double:
				p1Move = (delta*(-0.5))*ndp
				p2Move = (delta*(+0.5))*ndp
			else:
				p1Move = zero
				p2Move = delta * ndp
			p1Move = p1Move.projectOnAxis(axis)
			p2Move = p2Move.projectOnAxis(axis)
		else:
			originalDistance = abs(p2[axis] - p1[axis])
			delta = distance - originalDistance
			if double:
				p1Move = geom.Point(int(round(-delta*0.4)), 0)
				p2Move = geom.Point(int(round(+delta*0.6)), 0)
			else:
				p1Move = geom.Point(0, 0)
				p2Move = geom.Point(int(round(delta)), 0)
				oneBeforeTwo = p1[axis] < p2[axis]
				if not oneBeforeTwo:
					p1Move = p1Move.opposite()
					p2Move = p2Move.opposite()
				if horizontal:
					p1Move = p1Move.swapAxes()
					p2Move = p2Move.swapAxes()

	elif cmdStem == None:
		p1Move = zero
		p2Move = zero
	else:
		print "BUGGY LINK COMMAND"
		return

	if not double:
		if p1m != None:
			p2Move = p2Move + p1m.move
		if p2m != None:
			print "BUGGY SINGLE LINK COMMAND : Pt2 has already moved"
			return
	if p1m is None: # never touched before
		pT1 = PointTouched(p1, p1Move, p1+p1Move, csi1)
	else:
		pT1 = PointTouched(p1, p1m.move+p1Move, p1m.point+p1Move, csi1)
	savePointTouched(regs, axisName, p1Name, csi1, pT1)
	if p2m is None: # never touched before
		pT2 = PointTouched(p2, p2Move, p2+p2Move, csi2)
	else:
		pT2 = PointTouched(p2, p2m.move+p2Move, p2m.point+p2Move, csi2)
		print "WEIRD"
	savePointTouched(regs, axisName, p2Name, csi2, pT2)

def iup(regs, actual, horizontal=False):
	axis = 0
	axisName = 'x'
	if horizontal:
		axis = 1
		axisName = 'y'
	for cidx, c in enumerate(regs.gm.RFGlyph):
		touchedInContour = regs.movedPoints[axisName][cidx].values()
		touchedInContour.sort(key=lambda pt:pt.csi)
		for pt in touchedInContour:
			p = [0.0, 0.0]
			p[axis] = pt.move[axis]
			m = geom.Point(p[0], p[1])
			if actual:
				regs.gm.pointOfCSI(pt.csi).move(m)
			else:
				regs.gm.pPointOfCSI(pt.csi).move(m)

		nbTouched = len(touchedInContour)
		if nbTouched == 0: continue
		if nbTouched == 1:
			trans = touchedInContour[0].move.projectOnAxis(axis)
			for sidx, s in enumerate(c):
				for (idx, p) in enumerate(s.points):
					csi = cidx, sidx, idx
					if csi == touchedInContour[0].csi:
						continue
					if actual:
						regs.gm.pointOfCSI(csi).move(trans)
					else:
						regs.gm.pPointOfCSI(csi).move(trans)
			continue
		# nbTouched >= 2
		for k in range(nbTouched):
			j = (k + 1) % nbTouched
			srcTouched = touchedInContour[k]
			dstTouched = touchedInContour[j]
			leftOldPos  = srcTouched.originalPos[axis]
			leftNewPos  = srcTouched.point[axis]
			rightOldPos = dstTouched.originalPos[axis]
			rightNewPos = dstTouched.point[axis]
			if leftOldPos > rightOldPos:
				leftOldPos, rightOldPos = rightOldPos, leftOldPos
				leftNewPos, rightNewPos = rightNewPos, leftNewPos
			w = float(rightOldPos - leftOldPos)
			csi = regs.gm.increaseSI(srcTouched.csi, True)
			#srcTouched.output()
			#dstTouched.output()
			while csi != dstTouched.csi:
				#print csi,
				if actual:
					p = regs.gm.pointOfCSI(csi)
				else:
					p = regs.gm.pPointOfCSI(csi)
				if axis == 0:
					pos = p.x
				else:
					pos = p.y
				if pos <= leftOldPos:
					delta = leftNewPos-leftOldPos
					#print "bot",
				elif pos >= rightOldPos:
					delta = rightNewPos-rightOldPos
					#print "top",delta,
				else:
					factor = float(pos-leftOldPos)/w
					#print factor,
					newPos = factor*rightNewPos + (1.0-factor)*leftNewPos
					delta = int(round(newPos)) - pos
				if horizontal:
					p.move(geom.Point(0,delta))
				else:
					p.move(geom.Point(delta,0))
				csi = regs.gm.increaseSI(csi, True)
	# Finally, handle LSB and RSB
	lsb = regs.getMovedSideBearing('lsb')
	lVal = 0
	if lsb != None and lsb.point.x != 0:
		lVal = lsb.point.x
		regs.gm.leftMargin = regs.gm.leftMargin - lVal
	rsb = regs.getMovedSideBearing('rsb')
	theGlyph = regs.gm.RFGlyph
	if not actual:
		theGlyph = regs.gm.parametricGlyph
	rVal = theGlyph.width
	if rsb != None:
		rVal = rsb.point.x
	newWidth = rVal - lVal
	if newWidth != theGlyph.width:
		theGlyph.width = newWidth

def processParametric(fm, gm, actual=False):
	g = gm.RFGlyph
	gm._pg = g.copy()

	if g == None:
		return
	sortedCommands = gm.sortedHintingCommands
	if sortedCommands == []:
		return

	regs = Registers(fm, gm)

	applyParametric(regs, actual)

def applyParametric(regs, actual):
	sortedCommands = regs.gm.sortedHintingCommands
	regs.movedPoints = dict((axis, [{} for c in regs.gm.RFGlyph]) # an empty list for each contour
			for axis in ['x', 'y'])
	for scmd in sortedCommands:
			cmd = scmd.attrib
			code = cmd['code']
			#print code,cmd
			if code in ['alignv', 'alignh']:
				calculateAlignMove(regs, cmd, horizontal=(code[-1]=='v'))
			elif code in ['alignt', 'alignb']:
				calculateAlignZoneMove(regs, cmd)
			elif 'doublediagonal' == code:
				calculateLinkMove(regs, cmd, horizontal = True, double = True, diagonal=True)
				calculateLinkMove(regs, cmd, horizontal = False, double = True, diagonal=True)
			elif 'singlediagonal' == code:
				calculateLinkMove(regs, cmd, horizontal = True, double = False, diagonal=True)
				calculateLinkMove(regs, cmd, horizontal = False, double = False, diagonal=True)
			elif 'double' in code:
				calculateLinkMove(regs, cmd, horizontal=(code[-1]=='v'), double=True)
			elif 'single' in code:
				calculateLinkMove(regs, cmd, horizontal=(code[-1]=='v'), double=False)
			elif code in ['interpolatev', 'interpolateh']:
				calculateInterpolateMove(regs, cmd, horizontal=(code[-1]=='v'))

	iup(regs, actual, horizontal=False)
	iup(regs, actual, horizontal=True)

