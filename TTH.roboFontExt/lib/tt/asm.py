from tt import tables
from commons import helperFunctions as HF

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
commandToGroup = dict(sum([[(code, g) for code in group] for g,group in commandGroups], []))

def getCommandGroup(command):
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
			groups[-1][1].append(e)
		else:
			groups.append((curGroup,[e]))
		prevGroup = curGroup
	return groups

def groupDeltas(deltas):
	return groupList(deltas, getDeltaGroup)

def groupCommands(glyphTTHCommands):
	return groupList(glyphTTHCommands, getCommandGroup)

def getAlign(command, pointIndex, regs):
	alignType = command.get('align')
	if alignType == 'round':
		regs.RP0 = regs.RP1 = pointIndex
		return [	tables.autoPush(pointIndex),
				'MDAP[1]' ]
	elif alignType in ['left', 'bottom']:
		regs.RP0 = regs.RP1 = pointIndex
		return [	'RDTG[ ]',
				tables.autoPush(pointIndex),
				'MDAP[1]',
				'RTG[ ]' ]
	elif alignType in ['right', 'top']:
		regs.RP0 = regs.RP1 = pointIndex
		return [	'RUTG[ ]',
				tables.autoPush(pointIndex),
				'MDAP[1]',
				'RTG[ ]' ]
	elif alignType == 'double':
		regs.RP0 = regs.RP1 = pointIndex
		return [	'RTDG[ ]',
				tables.autoPush(pointIndex),
				'MDAP[1]',
				'RTG[ ]' ]
	elif alignType == 'center':
		regs.RP0 = regs.RP1 = pointIndex
		return [	'RTHG[ ]',
				tables.autoPush(pointIndex),
				'MDAP[1]',
				'RTG[ ]' ]
	return []

def processAlignToZone(commandsList, pointNameToIndex, zone_to_cvt, regs):
	Header = [tables.autoPush(0),
			'RCVT[ ]' ]
	IF = ['IF[ ]']
	ELSE = ['ELSE[ ]']
	Footer = ['EIF[ ]']

	for command in commandsList:
		if command.get('active') == 'false':
			continue

		name = command.get('point')
		if name in pointNameToIndex:
			pointIndex = pointNameToIndex[name]
		else:
			print "[TTH ERROR] point {} has no index in the glyph".format(name)

		zoneCV = zone_to_cvt[command.get('zone')]
		IF.extend([
					tables.autoPush(pointIndex),
					'MDAP[1]'])
		ELSE.extend([
					tables.autoPush(pointIndex, zoneCV),
					'MIAP[0]'])
		regs.RP0 = regs.RP1 = pointIndex

	alignToZone = []
	alignToZone.extend(Header)
	alignToZone.extend(IF)
	alignToZone.extend(ELSE)
	alignToZone.extend(Footer)

	regs.y_instructions.extend(alignToZone)

def processAlign(commandsList, pointNameToIndex, regs):
	for command in commandsList:
		if command.get('active') == 'false':
			continue

		name = command.get('point')
		if name in pointNameToIndex:
			pointIndex = pointNameToIndex[name]
		else:
			print "[TTH ERROR] point {} has no index in the glyph".format(name)

		align = getAlign(command, pointIndex, regs)

		if command.get('code') == 'alignh':
			regs.x_instructions.extend(align)
		elif command.get('code') == 'alignv':
			regs.y_instructions.extend(align)

def processDouble(commandsList, pointNameToIndex, stem_to_cvt, regs):
	Header = [ tables.autoPush(0),
			'RS[ ]',
			tables.autoPush(0),
			'EQ[ ]' ]
	IFh = ['IF[ ]']
	IFv = ['IF[ ]']
	Footer = ['EIF[ ]']

	for command in commandsList:
		if command.get('active') == 'false':
			continue

		try:
			point1Index = pointNameToIndex[command.get('point1')]
			point2Index = pointNameToIndex[command.get('point2')]
		except:
			print "[TTH ERROR] command's point has no index in the glyph"

		if 'stem' in command:
			stemCV = stem_to_cvt[command.get('stem')]
			asm = [ tables.autoPush(point2Index, stemCV, point1Index, 4),
					'CALL[ ]' ]
		else:
			asm = [ tables.autoPush(point2Index, point1Index, 3),
					'CALL[ ]' ]
		if command.get('code') == 'doubleh':
			IFh.extend(asm)
		elif command.get('code') == 'doublev':
			IFv.extend(asm)

		regs.RP0 = regs.RP1 = regs.RP2 = None

	if len(IFh) > 1:
		doubleh = []
		doubleh.extend(Header)
		doubleh.extend(IFh)
		doubleh.extend(Footer)
		regs.x_instructions.extend(doubleh)

	if len(IFv) > 1:
		doublev = []
		doublev.extend(Header)
		doublev.extend(IFv)
		doublev.extend(Footer)
		regs.y_instructions.extend(doublev)


def processInterpolate(commandsList, pointNameToIndex, regs):
	for command in commandsList:
		if command.get('active') == 'false':
			continue

		try:
			pointIndex  = pointNameToIndex[command.get('point')]
			point1Index = pointNameToIndex[command.get('point1')]
			point2Index = pointNameToIndex[command.get('point2')]
		except:
			print "[TTH ERROR] command's point has no index in the glyph"

		interpolate = [
						tables.autoPush(pointIndex, point1Index, point2Index),
						'SRP1[ ]',
						'SRP2[ ]',
						'IP[ ]'
						]
		regs.RP1 = point2Index
		regs.RP2 = point1Index
		if HF.commandHasAttrib(command, 'align'):
			align = getAlign(command, pointIndex, regs)
			interpolate.extend(align)

		if command.get('code') == 'interpolateh':
			regs.x_instructions.extend(interpolate)
		elif command.get('code') == 'interpolatev':
			regs.y_instructions.extend(interpolate)


def processSingle(commandsList, pointNameToIndex, stem_to_cvt, regs):
	for command in commandsList:
		if command.get('active') == 'false':
			continue

		try:
			point1Index = pointNameToIndex[command.get('point1')]
			point2Index = pointNameToIndex[command.get('point2')]
		except:
			print "[TTH ERROR] command's point has no index in the glyph"

		single_RP0 = []
		single_stem = []
		single_round = []
		single_align = []
		align = []

		if regs.RP0 == None:
			single_RP0 = [
							tables.autoPush(point1Index),
							'MDAP[1]'
							]
			regs.RP0 = regs.RP1 = point1Index

		else:
			single_RP0 = [
						tables.autoPush(point1Index),
						'SRP0[ ]'
						]
			regs.RP0 = point1Index

		if HF.commandHasAttrib(command, 'stem'):
			stemCV = stem_to_cvt[command.get('stem')]
			single_stem = [
							tables.autoPush(0),
							'RS[ ]',
							'IF[ ]',
								tables.autoPush(point2Index),
								'MDRP[10000]',
							'ELSE[ ]',
								tables.autoPush(point2Index, stemCV),
								'MIRP[10100]',
							'EIF[ ]'
							]
			regs.RP1 = regs.RP0
			regs.RP2 = point2Index

		elif HF.commandHasAttrib(command, 'round'):
			single_round = [
							tables.autoPush(point2Index),
							'MDRP[11100]'
							]
			regs.RP1 = regs.RP0
			regs.RP2 = point2Index


		elif HF.commandHasAttrib(command, 'align'):
			single_align = [
							tables.autoPush(point2Index),
							'MDRP[10000]',
							]
			regs.RP1 = regs.RP0
			regs.RP2 = point2Index

			if command.get('align') == 'round':
				single_align = [
							tables.autoPush(point2Index),
							'MDRP[10100]'
							]

			align = getAlign(command, point2Index, regs)

		else:
			single_align = [
							tables.autoPush(point2Index),
							'MDRP[10000]'
							]
			regs.RP1 = regs.RP0
			regs.RP2 = point2Index

		singleLink = []
		singleLink.extend(single_RP0)
		singleLink.extend(single_stem)
		singleLink.extend(single_round)
		singleLink.extend(single_align)
		singleLink.extend(align)

		if command.get('code') == 'singleh':
			regs.x_instructions.extend(singleLink)
		elif command.get('code') == 'singlev':
			regs.y_instructions.extend(singleLink)


def processDelta(commandsList, pointNameToIndex, regs):

	groupedDeltas = groupDeltas(commandsList)

	if groupedDeltas == []: return

	# [0] : first (groupName, Commands) pair
	# [1] : Commands
	# [0] : first command in Commands
	middle = groupedDeltas[0][1][0].get('code')[0] == 'm'

	for groupName, commands in groupedDeltas:
		horizontal = commands[0].get('code')[-1] == 'h'
		# sanity check : that all delta have the same type: final/middle, horizontal/vertical
		middlity      = all([(c.get('code')[0]  == 'm') == middle     for c in commands])
		horizontality = all([(c.get('code')[-1] == 'h') == horizontal for c in commands])
		if (not middlity) or (not horizontality):
			print "[TTH ERROR] Commands in delta group have not all the same type"
		# end of sanity check
		if groupName[0:2] == 'MG':
			header, footer = [], []
		elif groupName[0] == 'M':
			header, footer = [
						tables.autoPush(1),
						'RS[ ]',
						tables.autoPush(0),
						'EQ[ ]',
						'IF[ ]',
						], ['EIF[ ]']
		else: # groupName[0] == 'G'
			header, footer = [
						tables.autoPush(1),
						'RS[ ]',
						'IF[ ]',
						], ['EIF[ ]']
		deltaInstructions = \
				header \
				+ sum([processDeltaCommand(c, pointNameToIndex) for c in commands], []) \
				+ footer
		if horizontal:
			if middle:
				regs.x_instructions.extend(deltaInstructions)
			else:
				regs.finalDeltasH.extend(deltaInstructions)
		else:
			if middle:
				regs.y_instructions.extend(deltaInstructions)
			else:
				regs.finalDeltasV.extend(deltaInstructions)


def processDeltaCommand(command, pointNameToIndex):
	if command.get('active') == 'false':
		return []

	deltaInstructions = []

	try:
		pointIndex = pointNameToIndex[command.get('point')]
	except:
		print "[TTH ERROR] command's point has no index in the glyph"

	ppm1 = int(command.get('ppm1'))
	ppm2 = int(command.get('ppm2'))
	step = int(command.get('delta'))
	nbDelta = 1 + ppm2 - ppm1
	deltasP1 = []
	deltasP2 = []
	deltasP3 = []
	for i in range(nbDelta):
		ppm = ppm1 + i
		relativeSize = ppm - 9
		if 0 <= relativeSize <= 15:
			deltasP1.append(relativeSize)
		elif 16 <= relativeSize <= 31:
			deltasP2.append(relativeSize)
		elif 32 <= relativeSize <= 47:
			deltasP3.append(relativeSize)
		else:
			print 'delta out of range'
	deltaPList = []
	if deltasP1:
		for relativeSize  in deltasP1:
			arg = (relativeSize << 4 ) + tables.stepToSelector[step]
			deltaPList += [arg, pointIndex]
		deltaPList.append(len(deltasP1))
		deltaInstructions.append(tables.autoPush(*deltaPList))
		deltaInstructions.append('DELTAP1[ ]')

	elif deltasP2:
		for relativeSize in deltasP2:
			arg = ((relativeSize -16) << 4 ) + tables.stepToSelector[step]
			deltaPList += [arg, pointIndex]
		deltaPList.append(len(deltasP2))
		deltaInstructions.append(tables.autoPush(*deltaPList))
		deltaInstructions.append('DELTAP2[ ]')

	elif deltasP3:
		for relativeSize in deltasP3:
			arg = ((relativeSize -32) << 4 ) + tables.stepToSelector[step]
			deltaPList += [arg, pointIndex]
		deltaPList.append(len(deltasP3))
		deltaInstructions.append(tables.autoPush(*deltaPList))
		deltaInstructions.append('DELTAP3[ ]')

	return deltaInstructions

def makePointRFNameToIndexDict(gm):
	result = {}
	index = 0
	for contour in gm.RFGlyph:
		for point in contour.points:
			result[gm.hintingNameForPoint(point)] = index
			index += 1
	return result

def writeAssembly(gm, stem_to_cvt, zone_to_cvt):
	g = gm.RFGlyph
	if g == None:
		return

	g.lib[tables.k_glyph_assembly_key] = []
	sortedCommands = gm.sortedHintingCommands
	if sortedCommands == []:
		return

	nbPointsContour = 0
	for contour in g:
		nbPointsContour += len(contour.points)

	regs = Registers()

	pointNameToIndex = makePointRFNameToIndexDict(gm)
	pointNameToIndex['lsb'] = nbPointsContour
	pointNameToIndex['rsb'] = nbPointsContour+1
	regs.x_instructions = ['SVTCA[1]']
	regs.y_instructions = ['SVTCA[0]']

	regs.finalDeltasH = []
	regs.finalDeltasV = []

	groupedCommands = groupCommands(sortedCommands)

	for groupType, commands in groupedCommands:
		if groupType == 'alignToZone':
			processAlignToZone(commands, pointNameToIndex, zone_to_cvt, regs)
		elif groupType == 'align':
			processAlign(commands, pointNameToIndex, regs)
		elif groupType == 'double':
			processDouble(commands, pointNameToIndex, stem_to_cvt, regs)
		elif groupType == 'interpolate':
			processInterpolate(commands, pointNameToIndex, regs)
		elif groupType == 'single':
			processSingle(commands, pointNameToIndex, stem_to_cvt, regs)
		elif groupType == 'mdelta':
			processDelta(commands, pointNameToIndex, regs)
		elif groupType == 'fdelta':
			processDelta(commands, pointNameToIndex, regs)

	assembly = []
	assembly.extend(regs.x_instructions)
	assembly.extend(regs.y_instructions)
	assembly.extend(['IUP[0]', 'IUP[1]'])
	assembly.append('SVTCA[1]')
	assembly.extend(regs.finalDeltasH)
	assembly.append('SVTCA[0]')
	assembly.extend(regs.finalDeltasV)
	g.lib[tables.k_glyph_assembly_key] = assembly
