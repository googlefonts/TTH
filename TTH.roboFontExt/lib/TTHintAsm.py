import tt_tables

class Registers(object):
	def __init__(self):
		self.RP0 = None
		self.RP1 = None
		self.RP2 = None
		self.lsbIndex = 0
		self.rsbIndex = 1
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
	return commandToGroup[command['code']]

def getDeltaGroup(delta):
	group = ''
	if delta['mono'] == 'true': group += 'M'
	if delta['gray'] == 'true': group += 'G'
	if len(group) == 0:
		return None
	return (group + delta['code'][-1])

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
	alignType = command['align']
	if alignType == 'round':
		regs.RP0 = regs.RP1 = pointIndex
		return [	tt_tables.autoPush(pointIndex),
				'MDAP[1]' ]
	elif alignType in ['left', 'bottom']:
		regs.RP0 = regs.RP1 = pointIndex
		return [	'RDTG[ ]',
				tt_tables.autoPush(pointIndex),
				'MDAP[1]',
				'RTG[ ]' ]
	elif alignType in ['right', 'top']:
		regs.RP0 = regs.RP1 = pointIndex
		return [	'RUTG[ ]',
				tt_tables.autoPush(pointIndex),
				'MDAP[1]',
				'RTG[ ]' ]
	elif alignType == 'double':
		regs.RP0 = regs.RP1 = pointIndex
		return [	'RTDG[ ]',
				tt_tables.autoPush(pointIndex),
				'MDAP[1]',
				'RTG[ ]' ]
	elif alignType == 'center':
		regs.RP0 = regs.RP1 = pointIndex
		return [	'RTHG[ ]',
				tt_tables.autoPush(pointIndex),
				'MDAP[1]',
				'RTG[ ]' ]
	return []

def processAlignToZone(commandsList, pointNameToIndex, zone_to_cvt, regs):
	Header = [	tt_tables.autoPush(0),
				'RCVT[ ]' ]
	IF = ['IF[ ]']
	ELSE = ['ELSE[ ]']
	Footer = ['EIF[ ]']

	for command in commandsList:
		if command['active'] == 'false':
			continue

		if command['point'] == 'lsb':
			pointIndex = regs.lsbIndex
		elif command['point'] == 'rsb':
			pointIndex = regs.rsbIndex
		else:
			if command['point'] in pointNameToIndex:
				pointIndex = pointNameToIndex[command['point']]
		
		zoneCV = zone_to_cvt[command['zone']]
		IF.extend([
					tt_tables.autoPush(pointIndex),
					'MDAP[1]'])
		ELSE.extend([
					tt_tables.autoPush(pointIndex, zoneCV),
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
		if command['active'] == 'false':
			continue

		if command['point'] == 'lsb':
			pointIndex = regs.lsbIndex
		elif command['point'] == 'rsb':
			pointIndex = regs.rsbIndex
		else:
			pointIndex = pointNameToIndex[command['point']]

		align = getAlign(command, pointIndex)

		if command['code'] == 'alignh':
			regs.x_instructions.extend(align)
		elif command['code'] == 'alignv':
			regs.y_instructions.extend(align)

def processDouble(commandsList, pointNameToIndex, stem_to_cvt, regs):
	Header = [ tt_tables.autoPush(0),
			'RS[ ]',
			tt_tables.autoPush(0),
			'EQ[ ]' ]
	IFh = ['IF[ ]']
	IFv = ['IF[ ]']
	Footer = ['EIF[ ]']

	for command in commandsList:
		if command['active'] == 'false':
			continue

		if command['point1'] == 'lsb':
			point1Index = regs.lsbIndex
		elif command['point1'] == 'rsb':
			point1Index = regs.rsbIndex
		else:
			point1Index = pointNameToIndex[command['point1']]

		if command['point2'] == 'lsb':
			point2Index = regs.lsbIndex
		elif command['point2'] == 'rsb':
			point2Index = regs.rsbIndex
		else:
			point2Index = pointNameToIndex[command['point2']]

		if 'stem' in command:
			stemCV = stem_to_cvt[command['stem']]
			stem = [
					tt_tables.autoPush(pointIndex, stemCV, point1Index, 4),
					'CALL[ ]'
					]
			if command['code'] == 'doubleh':
				IFh.extend(stem)
			elif command['code'] == 'doublev':
				IFv.extend(stem)
		else:
			nostem = [
					tt_tables.autoPush(point2Index, point1Index, 3),
					'CALL[ ]'
					]
			if command['code'] == 'doubleh':
				IFh.extend(nostem)
			elif command['code'] == 'doublev':
				IFv.extend(nostem)

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
		if command['active'] == 'false':
			continue

		if command['point1'] == 'lsb':
			point1Index = regs.lsbIndex
		elif command['point1'] == 'rsb':
			point1Index = regs.rsbIndex
		else:
			point1Index = pointNameToIndex[command['point1']]

		if command['point2'] == 'lsb':
			point2Index = regs.lsbIndex
		elif command['point2'] == 'rsb':
			point2Index = regs.rsbIndex
		else:
			point2Index = pointNameToIndex[command['point2']]

		if command['point'] == 'lsb':
			pointIndex = regs.lsbIndex
		elif command['point'] == 'rsb':
			pointIndex = regs.rsbIndex
		else:
			pointIndex = pointNameToIndex[command['point']]

		interpolate = [
						tt_tables.autoPush(pointIndex, point1Index, point2Index),
						'Sregs.RP1[ ]',
						'Sregs.RP2[ ]',
						'IP[ ]'
						]
		regs.RP1 = point2Index
		regs.RP2 = point1Index
		if 'align' in command:
			align = getAlign(command, pointIndex)
			interpolate.extend(align)

		if command['code'] == 'interpolateh':
			regs.x_instructions.extend(interpolate)
		elif command['code'] == 'interpolatev':
			regs.y_instructions.extend(interpolate)


def processSingle(commandsList, pointNameToIndex, stem_to_cvt, regs):
	for command in commandsList:
		if command['active'] == 'false':
			continue

		if command['point1'] == 'lsb':
			point1Index = regs.lsbIndex
		elif command['point1'] == 'rsb':
			point1Index = regs.rsbIndex
		else:
			point1Index = pointNameToIndex[command['point1']]

		if command['point2'] == 'lsb':
			point2Index = regs.lsbIndex
		elif command['point2'] == 'rsb':
			point2Index = regs.rsbIndex
		else:
			point2Index = pointNameToIndex[command['point2']]

		single_regs.RP0 = []
		single_stem = []
		single_round = []
		single_align = []
		align = []

		if regs.RP0 == None:
			single_regs.RP0 = [
							tt_tables.autoPush(point1Index),
							'MDAP[1]'
							]
			regs.RP0 = regs.RP1 = point1Index

		else:
			single_regs.RP0 = [
						tt_tables.autoPush(point1Index),
						'Sregs.RP0[ ]'
						]
			regs.RP0 = point1Index
			
		if 'stem' in command:
			stemCV = stem_to_cvt[command['stem']]
			single_stem = [
							tt_tables.autoPush(0),
							'RS[ ]',
							'IF[ ]',
								tt_tables.autoPush(point2Index),
								'MDRP[10000]',
							'ELSE[ ]',
								tt_tables.autoPush(point2Index, stemCV),
								'MIRP[10100]',
							'EIF[ ]'
							]
			regs.RP1 = regs.RP0
			regs.RP2 = point2Index

		elif 'round' in command:
			single_round = [
							tt_tables.autoPush(point2Index),
							'MDRP[11100]'
							]
			regs.RP1 = regs.RP0 
			regs.RP2 = point2Index


		elif 'align' in command:
			single_align = [
							tt_tables.autoPush(point2Index),
							'MDRP[10000]',
							]
			regs.RP1 = regs.RP0 
			regs.RP2 = point2Index

			if command['align'] == 'round':
				single_align = [
							tt_tables.autoPush(point2Index),
							'MDRP[10100]'
							]

			align = getAlign(command, point2Index)
				
				
		else:
			single_align = [
							tt_tables.autoPush(point2Index),
							'MDRP[10000]'
							]
			regs.RP1 = regs.RP0
			regs.RP2 = point2Index

		singleLink = []
		singleLink.extend(single_regs.RP0)
		singleLink.extend(single_stem)
		singleLink.extend(single_round)
		singleLink.extend(single_align)
		singleLink.extend(align)

		if command['code'] == 'singleh':
			regs.x_instructions.extend(singleLink)
		elif command['code'] == 'singlev':
			regs.y_instructions.extend(singleLink)


def processDelta(commandsList, pointNameToIndex, regs):
	groupedDeltas = groupDeltas(commandsList)

	for deltaGroup in groupedDeltas:
		if deltaGroup[0] == 'MGh':
			for command in deltaGroup[1]:
				deltaInstructions = (processDeltaCommand(command, pointNameToIndex))
				if command['code'] == 'mdeltah':
					regs.x_instructions.extend(deltaInstructions)
				elif command['code'] == 'fdeltah':
					regs.finalDeltasH.extend(deltaInstructions)
		elif deltaGroup[0] == 'MGv':
			for command in deltaGroup[1]:
				deltaInstructions = (processDeltaCommand(command, pointNameToIndex))
				if command['code'] == 'mdeltav':
					regs.y_instructions.extend(deltaInstructions)
				elif command['code'] == 'fdeltav':
					regs.finalDeltasV.extend(deltaInstructions)

		elif deltaGroup[0] == 'Mh':
			deltaInstructions = [
						tt_tables.autoPush(1),
						'RS[ ]',
						tt_tables.autoPush(0),
						'EQ[ ]',
						'IF[ ]',
						]
			for command in deltaGroup[1]:
				deltaInstructions.extend(processDeltaCommand(command, pointNameToIndex))
			deltaInstructions.append('EIF[ ]')
			if command['code'] == 'mdeltah':
				regs.x_instructions.extend(deltaInstructions)
			elif command['code'] == 'fdeltah':
				regs.finalDeltasH.extend(deltaInstructions)

		elif deltaGroup[0] == 'Mv':
			deltaInstructions = [
						tt_tables.autoPush(1),
						'RS[ ]',
						tt_tables.autoPush(0),
						'EQ[ ]',
						'IF[ ]',
						]
			for command in deltaGroup[1]:
				deltaInstructions.extend(processDeltaCommand(command, pointNameToIndex))
			deltaInstructions.append('EIF[ ]')
			if command['code'] == 'mdeltav':
				regs.y_instructions.extend(deltaInstructions)
			elif command['code'] == 'fdeltav':
				regs.finalDeltasV.extend(deltaInstructions)

		elif deltaGroup[0] == 'Gh':
			deltaInstructions = [
						tt_tables.autoPush(1),
						'RS[ ]',
						'IF[ ]',
						]
			for command in deltaGroup[1]:
				deltaInstructions.extend(processDeltaCommand(command, pointNameToIndex))
			deltaInstructions.append('EIF[ ]')
			if command['code'] == 'mdeltah':
				regs.x_instructions.extend(deltaInstructions)
			elif command['code'] == 'fdeltah':
				regs.finalDeltasH.extend(deltaInstructions)

		elif deltaGroup[0] == 'Gv':
			deltaInstructions = [
						tt_tables.autoPush(1),
						'RS[ ]',
						'IF[ ]',
						]
			for command in deltaGroup[1]:
				deltaInstructions.extend(processDeltaCommand(command, pointNameToIndex))
			deltaInstructions.append('EIF[ ]')
			if command['code'] == 'mdeltav':
				regs.y_instructions.extend(deltaInstructions)
			elif command['code'] == 'fdeltav':
				regs.finalDeltasV.extend(deltaInstructions)

		else:
			continue


def processDeltaCommand(command, pointNameToIndex):
	try:
		return _processDeltaCommand(command, pointNameToIndex)
	except:
		return []

def _processDeltaCommand(command, pointNameToIndex):
	if command['active'] == 'false':
		return []

	deltaInstructions = []

	if command['point'] == 'lsb':
		pointIndex = regs.lsbIndex
	elif command['point'] == 'rsb':
		pointIndex = regs.rsbIndex
	else:
		pointIndex = pointNameToIndex[command['point']]

	ppm1 = command['ppm1']
	ppm2 = command['ppm2']
	step = int(command['delta'])
	nbDelta = 1 + int(ppm2) - int(ppm1)
	deltasP1 = []
	deltasP2 = []
	deltasP3 = []
	for i in range(nbDelta):
		ppm = int(ppm1) + i
		relativeSize = int(ppm) - 9
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
		for i in range(len(deltasP1)):
			relativeSize = deltasP1[i]
			arg = (relativeSize << 4 ) + tt_tables.stepToSelector[step]
			deltaPList.append(arg, pointIndex)
		
		deltaPList.append(len(deltasP1))

		deltaInstructions.append(tt_tables.autoPush(deltaPList))
		deltaInstructions.append('DELTAP1[ ]')

	elif deltasP2:
		for i in range(len(deltasP2)):
			relativeSize = deltasP2[i]
			arg = ((relativeSize -16) << 4 ) + tt_tables.stepToSelector[step]
			deltaPList.append(arg, pointIndex)
		
		deltaPList.append(len(deltasP2))
		deltaInstructions.append(tt_tables.autoPush(deltaPList))
		deltaInstructions.append('DELTAP2[ ]')

	elif deltasP3:
		for i in range(len(deltasP3)):
			relativeSize = deltasP3[i]
			arg = ((relativeSize -32) << 4 ) + tt_tables.stepToSelector[step]
			deltaPList.append(arg, pointIndex)
		
		deltaPList.append(len(deltasP3))
		deltaInstructions.append(tt_tables.autoPush(deltaPList))
		deltaInstructions.append('DELTAP3[ ]')


	return deltaInstructions

def writeAssembly(g, glyphTTHCommands, pointNameToIndex, regs):

	if g == None:
		return

	assembly = []

	g.lib['com.robofont.robohint.assembly'] = []
	if glyphTTHCommands == []:
		return

	nbPointsContour = 0
	for contour in g:
		nbPointsContour += len(contour.points)

	regs.lsbIndex = nbPointsContour
	regs.rsbIndex = nbPointsContour+1
	regs.x_instructions = ['SVTCA[1]']
	regs.y_instructions = ['SVTCA[0]']
	
	regs.finalDeltasH = []
	regs.finalDeltasV = []

	groupedCommands = groupCommands(glyphTTHCommands)

	for groupType, commands in groupedCommands:
		if groupType == 'alignToZone':
			processAlignToZone(commands, pointNameToIndex)
		elif groupType == 'align':
			processAlign(commands, pointNameToIndex)
		elif groupType == 'double':
			processDouble(commands, pointNameToIndex)
		elif groupType == 'interpolate':
			processInterpolate(commands, pointNameToIndex)
		elif groupType == 'single':
			processSingle(commands, pointNameToIndex)
		elif groupType == 'mdelta':
			processDelta(commands, pointNameToIndex)
		elif groupType == 'fdelta':
			processDelta(commands, pointNameToIndex)

	##############################	
	# if TTHToolInstance.c_fontModel.deactivateStemWhenGrayScale == True:
	# 	assembly.extend([
	# 				'PUSHB[ ] 10',
	# 				'CALL[ ]',
	# 				'DUP[ ]',
	# 				'PUSHB[ ] 0',
	# 				'SWAP[ ]',
	# 				'WS[ ]',
	# 				'PUSHB[ ] 1',
	# 				'SWAP[ ]',
	# 				'WS[ ]',
	# 					])
	# else:
	# 	assembly.extend([
	# 				'PUSHB[ ] 0',
	# 				'PUSHB[ ] 0',
	# 				'WS[ ]',
	# 				'PUSHB[ ] 10',
	# 				'CALL[ ]',
	# 				'PUSHB[ ] 1',
	# 				'SWAP[ ]',
	# 				'WS[ ]',
	# 				])

	assembly.extend(regs.x_instructions)
	assembly.extend(regs.y_instructions)
	assembly.extend(['IUP[0]', 'IUP[1]'])
	assembly.append('SVTCA[1]')
	assembly.extend(regs.finalDeltasH)
	assembly.append('SVTCA[0]')
	assembly.extend(regs.finalDeltasV)
	g.lib['com.robofont.robohint.assembly'] = assembly
	regs.RP0 = regs.RP1 = regs.RP2 = None
	regs.lsbIndex = 0
	regs.rsbIndex = 1
	regs.x_instructions = []
	regs.y_instructions = []
	regs.finalDeltasH = []
	regs.finalDeltasV = []
