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

class Registers(object):
	def __init__(self):
		self.RP0 = None
		self.RP1 = None
		self.RP2 = None
		self.x_instructions = []
		self.y_instructions = []
		self.finalDeltasH = []
		self.finalDeltasV = []

commandGroups = [	('alignToZone', ['alignt', 'alignb']),
				('align',       ['alignv', 'alignh']),
				('single',      ['singlev', 'singleh']),
				('double',      ['doublev', 'doubleh']),
				('interpolate', ['interpolatev', 'interpolateh']),
				('mdelta',      ['mdeltah', 'mdeltav']),
				('fdelta',      ['fdeltah', 'fdeltav']) ]
commandToGroup = dict(sum([[(code, groupName) for code in group] for groupName,group in commandGroups], []))

def getCommandGroup(command):
	# Might throw exception if command's code is unknown
	return commandToGroup[command.get('code')]

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

def processAlign(commandsList, pointNameToIndex, regs):
	for command in commandsList:
		if command.get('active') == 'false':
			continue

		try:
			name = command.get('point') 
			point1 = name
		except:
			print "[TTH ERROR] command's point1 has no index in the glyph"
			print command.attrib
			continue

		code = command.get('code')
		point = command.get('point')
		cmd = {'code':code, 'point':point}

		if 'h' in code:
			regs.x_instructions.append(cmd)
		elif 'v' in code:
			regs.y_instructions.append(cmd)


def processZoneAlign(commandsList, pointNameToIndex, regs):
	for command in commandsList:
		if command.get('active') == 'false':
			continue

		try:
			name = command.get('point') 
			point1 = name
		except:
			print "[TTH ERROR] command's point1 has no index in the glyph"
			print command.attrib
			continue

		code = command.get('code')
		point = command.get('point')
		zone = command.get('zone')
		cmd = {'code':code, 'point':point, 'zone':zone}

		
		regs.y_instructions.append(cmd)

def processLink(commandsList, pointNameToIndex, regs):

	for command in commandsList:
		if command.get('active') == 'false':
			continue

		try:
			name = command.get('point1') 
			point1 = name
		except:
			print "[TTH ERROR] command's point1 has no index in the glyph"
			print command.attrib
			continue

		try:
			name = command.get('point2') 
			point2 = name
		except:
			print "[TTH ERROR] command's point2 has no index in the glyph"
			print command.attrib
			continue

		code = command.get('code')
		#if 'stem' in command:
		if HF.commandHasAttrib(command, 'stem'):
			stem = command.get('stem')
			cmd = {'code':code, 'point1':point1, 'point2':point2, 'stem':stem}

		else:
			cmd = {'code':code, 'point1':point1, 'point2':point2, 'stem':None}


		regs.RP0 = regs.RP1 = regs.RP2 = None

		if 'h' in code:
			regs.x_instructions.append(cmd)
		elif 'v' in code:
			regs.y_instructions.append(cmd)

def processInterpolate(commandsList, pointNameToIndex, regs):
	for command in commandsList:
		if command.get('active') == 'false':
			continue

		try:
			point  = command.get('point')
			point1 = command.get('point1')
			point2 = command.get('point2')
		except:
			print "[TTH ERROR] command's point(s) has no index in the glyph"
			print command.attrib
			continue

		code = command.get('code')
		cmd = {'code':code, 'point':point, 'point1':point1, 'point2':point2}

		if code == 'interpolateh':
			regs.x_instructions.append(cmd)
		elif code == 'interpolatev':
			regs.y_instructions.append(cmd)

def makePointRFNameToIndexDict(fm, gm):
	result = {}
	index = 0
	for contour in gm.RFGlyph:
		for point in contour.points:
			result[gm.hintingNameForPoint(point)] = index
			index += 1

	return result

def calculateInterpolateMove(fm, gm, cmd, movedPoints, horizontal=False):
	csi = gm.csiOfPointName(cmd['point'])
	csi1 = gm.csiOfPointName(cmd['point1'])
	csi2 = gm.csiOfPointName(cmd['point2'])
	p = geom.makePoint(gm.pointOfCSI(csi))
	p1 = geom.makePoint(gm.pointOfCSI(csi1))
	p2 = geom.makePoint(gm.pointOfCSI(csi2))

	pm1 = movedPoints[csi1[0]].get(csi1) # if not found, returns None
	if pm1 is None: # never touched before
		pm1 = movedPoints[csi1[0]][csi1] = PointTouched(p1, zero, p1, csi1)

	pm2 = movedPoints[csi2[0]].get(csi2) # if not found, returns None
	if pm2 is None: # never touched before
		pm2 = movedPoints[csi2[0]][csi2] = PointTouched(p2, zero, p2, csi2)

	pm = movedPoints[csi[0]].get(csi) # if not found, returns None
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
		movedPoints[csi[0]][csi] = PointTouched(p, pMove, p+pMove, csi)
	else:
		movedPoints[csi[0]][csi] = PointTouched(p, zero, p, csi)


def calculateAlignMove(fm, gm, cmd, movedPoints, horizontal=False):
	if cmd['point'] in ['lsb', 'rsb']: return
	csi = gm.csiOfPointName(cmd['point'])
	p = geom.makePoint(gm.pointOfCSI(csi))
	pm = movedPoints[csi[0]].get(csi) # if not found, returns None
	if pm is None: # never touched before
		movedPoints[csi[0]][csi] = PointTouched(p, zero, p, csi)
	# else: # nothing to do

def calculateAlignZoneMove(fm, gm, cmd, movedPoints):
	cmdZone = cmd['zone']
	fmZones = fm.zones
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

	csi = gm.csiOfPointName(cmd['point'])
	p = geom.makePoint(gm.pointOfCSI(csi))

	pm = movedPoints[csi[0]].get(csi) # if not found, returns None
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
	movedPoints[csi[0]][csi] = pT

def calculateLinkMove(fm, gm, cmd, movedPoints, horizontal=False, double=False):
	if horizontal:
		fmStems = fm.horizontalStems
	else:
		fmStems = fm.verticalStems

	cmdStem = cmd['stem']
	if cmdStem in fmStems:
		try:
			fontStem = fmStems[cmdStem]
			width = fontStem['width']
			value = fontStem['targetWidth']
			distance = int(value)
		except: return

		if cmd['point1'] == 'lsb':
			csi1 = None
			p1 = geom.Point(0, 0)
		elif cmd['point1'] == 'rsb':
			csi1 = None
			p1 = geom.Point(gm.RFGlyph.width, 0)
		else:
			csi1 = gm.csiOfPointName(cmd['point1'])
			p1 = geom.makePoint(gm.pointOfCSI(csi1))

		if cmd['point2'] == 'lsb':
			csi2 = None
			p2 = geom.Point(0, 0)
		elif cmd['point2'] == 'rsb':
			csi2 = None
			p2 = geom.Point(gm.RFGlyph.width, 0)
		else:
			csi2 = gm.csiOfPointName(cmd['point2'])
			p2 = geom.makePoint(gm.pointOfCSI(csi2))

		axis = 0
		if horizontal: axis = 1
		originalDistance = abs(p2[axis] - p1[axis])
		oneBeforeTwo = p1[axis] < p2[axis]
		delta = distance - originalDistance

		if double:
			p1Move = geom.Point(int(round(-delta*0.3)), 0)
			p2Move = geom.Point(int(round(+delta*0.7)), 0)
		else:
			p1Move = geom.Point(0, 0)
			p2Move = geom.Point(int(round(delta)), 0)
			
		if not oneBeforeTwo:
			p1Move = p1Move.opposite()
			p2Move = p2Move.opposite()

		if horizontal:
			p1Move = p1Move.swapAxes()
			p2Move = p2Move.swapAxes()

	elif cmdStem == None:
		if cmd['point1'] == 'lsb':
			csi1 = None
			p1 = geom.Point(0, 0)
		elif cmd['point1'] == 'rsb':
			csi1 = None
			p1 = geom.Point(gm.RFGlyph.width, 0)
		else:
			csi1 = gm.csiOfPointName(cmd['point1'])
			p1 = geom.makePoint(gm.pointOfCSI(csi1))

		if cmd['point2'] == 'lsb':
			csi2 = None
			p2 = geom.Point(0, 0)
		elif cmd['point2'] == 'rsb':
			csi2 = None
			p2 = geom.Point(gm.RFGlyph.width, 0)
		else:
			csi2 = gm.csiOfPointName(cmd['point2'])
			p2 = geom.makePoint(gm.pointOfCSI(csi2))

		p1Move = zero
		p2Move = zero
	else:
		print "BUGGY LINK COMMAND"
		return

	if not double:
		try:
			p1m = movedPoints[csi1[0]].get(csi1)
		except:
			p1m = None
		if p1m != None:
			p2Move = p2Move + p1m.move
		try:
			if csi2 in movedPoints[csi2[0]]:
				print "BUGGY SINGLE LINK COMMAND : Pt2 has already moved"
				return
		except:
			pass
	try:
		p1m = movedPoints[csi1[0]].get(csi1) # if not found, returns None
	except:
		p1m = None
	if p1m is None: # never touched before
		pT1 = PointTouched(p1, p1Move, p1+p1Move, csi1)
	else:
		pT1 = PointTouched(p1, p1m.move+p1Move, p1m.point+p1Move, csi1)
	try:
		movedPoints[csi1[0]][csi1] = pT1
	except:
		pass
	try:
		p2m = movedPoints[csi2[0]].get(csi2) # if not found, returns None
	except:
		p2m = None
	if p2m is None: # never touched before
		pT2 = PointTouched(p2, p2Move, p2+p2Move, csi2)
	else:
		pT2 = PointTouched(p2, p2m.move+p2Move, p2m.point+p2Move, csi2)
		print "WEIRD"
	try:
		movedPoints[csi2[0]][csi2] = pT2
	except:
		pass

def interpolate(fm, gm, movedPoints, actual, horizontal=False):
	axis = 0
	if horizontal:
		axis = 1
	for cidx, c in enumerate(gm.RFGlyph):
		touchedInContour = movedPoints[cidx].values()
		touchedInContour.sort(key=lambda pt:pt.csi)
		for pt in touchedInContour:
			if actual:
				gm.pointOfCSI(pt.csi).move(pt.move)
			else:
				gm.pPointOfCSI(pt.csi).move(pt.move)
	
		nbTouched = len(touchedInContour)
		if nbTouched == 0: continue
		if nbTouched == 1:
			trans = touchedInContour[0].move
			for sidx, s in enumerate(c):
				for (idx, p) in enumerate(s.points):
					csi = cidx, sidx, idx
					if csi == touchedInContour[0].csi:
						continue
					if actual:
						gm.pointOfCSI(csi).move(trans)
					else:
						gm.pPointOfCSI(csi).move(trans)
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
			csi = gm.increaseSI(srcTouched.csi, True)
			#srcTouched.output()
			#dstTouched.output()
			while csi != dstTouched.csi:
				#print csi,
				if actual:
					p = gm.pointOfCSI(csi)
				else:
					p = gm.pPointOfCSI(csi)
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
				csi = gm.increaseSI(csi, True)

def processParametric(fm, gm, actual=False):
	g = gm.RFGlyph
	gm._pg = g.copy()
	
	if g == None:
		return
	sortedCommands = gm.sortedHintingCommands
	if sortedCommands == []:
		return

	regs = Registers()

	groupedCommands = groupCommands(sortedCommands)

	pointNameToIndex = makePointRFNameToIndexDict(fm, gm)
	
	regs.x_instructions = []
	regs.y_instructions = []


	for groupType, commands in groupedCommands:
		if groupType == 'alignToZone':
			processZoneAlign(commands, pointNameToIndex, regs)
		elif groupType == 'align':
			processAlign(commands, pointNameToIndex, regs)	
		elif groupType in ['double', 'single']:
			processLink(commands, pointNameToIndex, regs)
		elif groupType == 'interpolate':
		 	processInterpolate(commands, pointNameToIndex, regs)

	applyParametric(fm, gm, regs.x_instructions, regs.y_instructions, actual)

def applyParametric(fm, gm, vCode, hCode, actual):
	for horiz,codes in ((True, hCode), (False, vCode)):
		movedPoints = [{} for c in gm.RFGlyph] # an empty list for each contour
		for cmd in codes:
			if cmd['code'] in ['alignv', 'alignh']:
				calculateAlignMove(fm, gm, cmd, movedPoints, horizontal=horiz)
			elif cmd['code'] in ['alignt', 'alignb']:
				calculateAlignZoneMove(fm, gm, cmd, movedPoints)
			elif 'stem' in cmd.keys():
				if 'double' in cmd['code']:
					calculateLinkMove(fm, gm, cmd, movedPoints, horizontal=horiz, double=True)
				elif 'single' in cmd['code']:
					calculateLinkMove(fm, gm, cmd, movedPoints, horizontal=horiz, double=False)
			elif cmd['code'] in ['interpolatev', 'interpolateh']:
				calculateInterpolateMove(fm, gm, cmd, movedPoints, horizontal=horiz)

		interpolate(fm, gm, movedPoints, actual, horizontal=horiz)

