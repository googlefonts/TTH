import tt_tables

RP0 = RP1 = RP2 = None
lsbIndex = 0
rsbIndex = 1
x_instructions = []
y_instructions = []
finalDeltasH = []
finalDeltasV = []

def getCommandGroup(command):
	alignToZone = ['alignt', 'alignb']
	align = ['alignv', 'alignh']
	single = ['singlev', 'singleh']
	double = ['doublev', 'doubleh']
	interpolate = ['interpolatev', 'interpolateh']
	delta = ['mdeltah', 'mdeltav', 'fdeltah', 'fdeltav']

	groups = dict(alignToZone=alignToZone, align=align, single=single, double=double, interpolate=interpolate, delta=delta)

	for key, value in groups.iteritems():
		if command['code'] in value:
			return key
	return None


def getDeltaGroup(delta):
	if delta['mono'] == 'true' and delta['gray'] == 'true':
		if delta['code'][-1:] == 'h':
			return 'MGh'
		elif delta['code'][-1:] == 'v':
			return 'MGv'
	elif delta['mono'] == 'true' and delta['gray'] == 'false':
		if delta['code'][-1:] == 'h':
			return 'Mh'
		elif delta['code'][-1:] == 'v':
			return 'Mv'
	elif delta['mono'] == 'false' and delta['gray'] == 'true':
		if delta['code'][-1:] == 'h':
			return 'Gh'
		elif delta['code'][-1:] == 'v':
			return 'Gv'
	else:
		return None

def groupDeltas(commandsList):
	groupedDeltas = []

	for delta in commandsList:
		if groupedDeltas == []:
			groupedDeltas.append((getDeltaGroup(delta), [delta]))
			continue

		lastGroupIndex = len(groupedDeltas) -1
		lastDeltaIndex = len(groupedDeltas[lastGroupIndex][1])-1

		deltaGroup = getDeltaGroup(delta)
		lastDeltaGroup = getDeltaGroup(groupedDeltas[lastGroupIndex][1][lastDeltaIndex])

		if lastDeltaGroup == deltaGroup:
			groupedDeltas[lastGroupIndex][1].append(delta)
		else:
			groupedDeltas.append((getDeltaGroup(delta),[delta]))

	return groupedDeltas

def groupCommands(glyphTTHCommands):
	groupedCommands = []

	for command in glyphTTHCommands:
		if groupedCommands == []:
			groupedCommands.append((getCommandGroup(command), [command]))
			continue

		lastGroupIndex = len(groupedCommands)-1
		lastCommandIndex = len(groupedCommands[lastGroupIndex][1])-1

		commandGroup = getCommandGroup(command)
		lastCommandGroup = getCommandGroup(groupedCommands[lastGroupIndex][1][lastCommandIndex])

		if lastCommandGroup == commandGroup:
			groupedCommands[lastGroupIndex][1].append(command)
		else:
			groupedCommands.append((getCommandGroup(command),[command]))

	return groupedCommands

def getAlign(command, pointIndex):
	global RP0
	global RP1
	global RP2
	global lsbIndex
	global rsbIndex
	global x_instructions
	global y_instructions

	if command['align'] == 'round':
		align = [
				'PUSHW[ ] ' + str(pointIndex),
				'MDAP[1]'
				]
		RP0 = RP1 = pointIndex

	elif command['align'] in ['left', 'bottom']:
		align = [
				'RDTG[ ]',
				'PUSHW[ ] ' + str(pointIndex),
				'MDAP[1]',
				'RTG[ ]'
				]
		RP0 = RP1 = pointIndex

	elif command['align'] in ['right', 'top']:
		align = [
				'RUTG[ ]',
				'PUSHW[ ] ' + str(pointIndex),
				'MDAP[1]',
				'RTG[ ]'
				]
		RP0 = RP1 = pointIndex

	elif command['align'] == 'double':
		align = [
				'RTDG[ ]',
				'PUSHW[ ] ' + str(pointIndex),
				'MDAP[1]',
				'RTG[ ]'
				]
		RP0 = RP1 = pointIndex

	elif command['align'] == 'center':
		align = [
				'RTHG[ ]',
				'PUSHW[ ] ' + str(pointIndex),
				'MDAP[1]',
				'RTG[ ]'
				]
		RP0 = RP1 = pointIndex

	else:
		align = []

	return align

def processAlignToZone(commandsList, pointNameToIndex):
	global RP0
	global RP1
	global RP2
	global lsbIndex
	global rsbIndex
	global x_instructions
	global y_instructions

	Header = [
				'PUSHW[ ] 0',
				'RCVT[ ]',
				]
	IF = ['IF[ ]']
	ELSE = ['ELSE[ ]']
	Footer = ['EIF[ ]']

	for command in commandsList:
		if command['active'] == 'false':
			continue

		if command['point'] == 'lsb':
			pointIndex = lsbIndex
		elif command['point'] == 'rsb':
			pointIndex = rsbIndex
		else:
			if command['point'] in pointNameToIndex:
				pointIndex = pointNameToIndex[command['point']]
		
		zoneCV = tt_tables.zone_to_cvt[command['zone']]
		IF.extend([
					'PUSHW[ ] ' + str(pointIndex),
					'MDAP[1]'])
		ELSE.extend([
					'PUSHW[ ] ' + str(pointIndex) + ' ' + str(zoneCV),
					'MIAP[0]'])
		RP0 = RP1 = pointIndex

	alignToZone = []
	alignToZone.extend(Header)
	alignToZone.extend(IF)
	alignToZone.extend(ELSE)
	alignToZone.extend(Footer)

	y_instructions.extend(alignToZone)

def processAlign(commandsList, pointNameToIndex):
	global RP0
	global RP1
	global RP2
	global lsbIndex
	global rsbIndex
	global x_instructions
	global y_instructions

	for command in commandsList:
		if command['active'] == 'false':
			continue

		if command['point'] == 'lsb':
			pointIndex = lsbIndex
		elif command['point'] == 'rsb':
			pointIndex = rsbIndex
		else:
			pointIndex = pointNameToIndex[command['point']]

		align = getAlign(command, pointIndex)

		if command['code'] == 'alignh':
			x_instructions.extend(align)
		elif command['code'] == 'alignv':
			y_instructions.extend(align)

def processDouble(commandsList, pointNameToIndex):
	global RP0
	global RP1
	global RP2
	global lsbIndex
	global rsbIndex
	global x_instructions
	global y_instructions

	Header = [
			'PUSHB[ ] 0',
			'RS[ ]',
			'PUSHB[ ] 0',
			'EQ[ ]'
			]
	IFh = ['IF[ ]']
	IFv = ['IF[ ]']
	Footer = ['EIF[ ]']

	for command in commandsList:
		if command['active'] == 'false':
			continue

		if command['point1'] == 'lsb':
			point1Index = lsbIndex
		elif command['point1'] == 'rsb':
			point1Index = rsbIndex
		else:
			point1Index = pointNameToIndex[command['point1']]

		if command['point2'] == 'lsb':
			point2Index = lsbIndex
		elif command['point2'] == 'rsb':
			point2Index = rsbIndex
		else:
			point2Index = pointNameToIndex[command['point2']]

		if 'stem' in command:
			stemCV = tt_tables.stem_to_cvt[command['stem']]
			stem = [
					'PUSHW[ ] ' + str(point2Index) + ' ' +  str(stemCV) + ' ' + str(point1Index) + ' 4',
					'CALL[ ]'
					]
			if command['code'] == 'doubleh':
				IFh.extend(stem)
			elif command['code'] == 'doublev':
				IFv.extend(stem)
		else:
			nostem = [
					'PUSHW[ ] ' + str(point2Index) + ' ' + str(point1Index) + ' 3',
					'CALL[ ]'
					]
			if command['code'] == 'doubleh':
				IFh.extend(nostem)
			elif command['code'] == 'doublev':
				IFv.extend(nostem)

		RP0 = RP1 = RP2 = None

	if len(IFh) > 1:
		doubleh = []
		doubleh.extend(Header)
		doubleh.extend(IFh)
		doubleh.extend(Footer)
		x_instructions.extend(doubleh)

	if len(IFv) > 1:
		doublev = []
		doublev.extend(Header)
		doublev.extend(IFv)
		doublev.extend(Footer)
		y_instructions.extend(doublev)
			

def processInterpolate(commandsList, pointNameToIndex):
	global RP0
	global RP1
	global RP2
	global lsbIndex
	global rsbIndex
	global x_instructions
	global y_instructions

	for command in commandsList:
		if command['active'] == 'false':
			continue

		if command['point1'] == 'lsb':
			point1Index = lsbIndex
		elif command['point1'] == 'rsb':
			point1Index = rsbIndex
		else:
			point1Index = pointNameToIndex[command['point1']]

		if command['point2'] == 'lsb':
			point2Index = lsbIndex
		elif command['point2'] == 'rsb':
			point2Index = rsbIndex
		else:
			point2Index = pointNameToIndex[command['point2']]

		if command['point'] == 'lsb':
			pointIndex = lsbIndex
		elif command['point'] == 'rsb':
			pointIndex = rsbIndex
		else:
			pointIndex = pointNameToIndex[command['point']]

		interpolate = [
						'PUSHW[ ] ' + str(pointIndex) + ' ' + str(point1Index) + ' ' + str(point2Index),
						'SRP1[ ]',
						'SRP2[ ]',
						'IP[ ]'
						]
		RP1 = point2Index
		RP2 = point1Index
		if 'align' in command:
			align = getAlign(command, pointIndex)
			interpolate.extend(align)

		if command['code'] == 'interpolateh':
			x_instructions.extend(interpolate)
		elif command['code'] == 'interpolatev':
			y_instructions.extend(interpolate)


def processSingle(commandsList, pointNameToIndex):
	global RP0
	global RP1
	global RP2
	global lsbIndex
	global rsbIndex
	global x_instructions
	global y_instructions

	for command in commandsList:
		if command['active'] == 'false':
			continue

		if command['point1'] == 'lsb':
			point1Index = lsbIndex
		elif command['point1'] == 'rsb':
			point1Index = rsbIndex
		else:
			point1Index = pointNameToIndex[command['point1']]

		if command['point2'] == 'lsb':
			point2Index = lsbIndex
		elif command['point2'] == 'rsb':
			point2Index = rsbIndex
		else:
			point2Index = pointNameToIndex[command['point2']]

		single_RP0 = []
		single_stem = []
		single_round = []
		single_align = []
		align = []

		if RP0 == None:
			single_RP0 = [
							'PUSHW[ ] ' + str(point1Index),
							'MDAP[1]'
							]
			RP0 = RP1 = point1Index

		else:
			single_RP0 = [
						'PUSHW[ ] ' + str(point1Index),
						'SRP0[ ]'
						]
			RP0 = point1Index
			
		if 'stem' in command:
			stemCV = tt_tables.stem_to_cvt[command['stem']]
			single_stem = [
							'PUSHB[ ] 0',
							'RS[ ]',
							'IF[ ]',
								'PUSHW[ ] ' + str(point2Index),
								'MDRP[10000]',
							'ELSE[ ]',
								'PUSHW[ ] ' + str(point2Index) + ' ' + str(stemCV),
								'MIRP[10100]',
							'EIF[ ]'
							]
			RP1 = RP0
			RP2 = point2Index

		elif 'round' in command:
			single_round = [
							'PUSHW[ ] ' + str(point2Index),
							'MDRP[11100]'
							]
			RP1 = RP0 
			RP2 = point2Index


		elif 'align' in command:
			single_align = [
							'PUSHW[ ] ' + str(point2Index),
							'MDRP[10000]',
							]
			RP1 = RP0 
			RP2 = point2Index

			if command['align'] == 'round':
				single_align = [
							'PUSHW[ ] ' + str(point2Index),
							'MDRP[10100]'
							]

			align = getAlign(command, point2Index)
				
				
		else:
			single_align = [
							'PUSHW[ ] ' + str(point2Index),
							'MDRP[10000]'
							]
			RP1 = RP0
			RP2 = point2Index

		singleLink = []
		singleLink.extend(single_RP0)
		singleLink.extend(single_stem)
		singleLink.extend(single_round)
		singleLink.extend(single_align)
		singleLink.extend(align)

		if command['code'] == 'singleh':
			x_instructions.extend(singleLink)
		elif command['code'] == 'singlev':
			y_instructions.extend(singleLink)


def processDelta(commandsList, pointNameToIndex):
	global RP0
	global RP1
	global RP2
	global lsbIndex
	global rsbIndex
	global x_instructions
	global y_instructions
	global finalDeltasH
	global finalDeltasV

	groupedDeltas = groupDeltas(commandsList)

	for deltaGroup in groupedDeltas:
		if deltaGroup[0] == 'MGh':
			for command in deltaGroup[1]:
				deltaInstructions = (processDeltaCommand(command, pointNameToIndex))
				if command['code'] == 'mdeltah':
					x_instructions.extend(deltaInstructions)
				elif command['code'] == 'fdeltah':
					finalDeltasH.extend(deltaInstructions)
		elif deltaGroup[0] == 'MGv':
			for command in deltaGroup[1]:
				deltaInstructions = (processDeltaCommand(command, pointNameToIndex))
				if command['code'] == 'mdeltav':
					y_instructions.extend(deltaInstructions)
				elif command['code'] == 'fdeltav':
					finalDeltasV.extend(deltaInstructions)

		elif deltaGroup[0] == 'Mh':
			deltaInstructions = [
						'PUSHB[ ] 1',
						'RS[ ]',
						'PUSHB[ ] 0',
						'EQ[ ]',
						'IF[ ]',
						]
			for command in deltaGroup[1]:
				deltaInstructions.extend(processDeltaCommand(command, pointNameToIndex))
			deltaInstructions.append('EIF[ ]')
			if command['code'] == 'mdeltah':
				x_instructions.extend(deltaInstructions)
			elif command['code'] == 'fdeltah':
				finalDeltasH.extend(deltaInstructions)

		elif deltaGroup[0] == 'Mv':
			deltaInstructions = [
						'PUSHB[ ] 1',
						'RS[ ]',
						'PUSHB[ ] 0',
						'EQ[ ]',
						'IF[ ]',
						]
			for command in deltaGroup[1]:
				deltaInstructions.extend(processDeltaCommand(command, pointNameToIndex))
			deltaInstructions.append('EIF[ ]')
			if command['code'] == 'mdeltav':
				y_instructions.extend(deltaInstructions)
			elif command['code'] == 'fdeltav':
				finalDeltasV.extend(deltaInstructions)

		elif deltaGroup[0] == 'Gh':
			deltaInstructions = [
						'PUSHB[ ] 1',
						'RS[ ]',
						'IF[ ]',
						]
			for command in deltaGroup[1]:
				deltaInstructions.extend(processDeltaCommand(command, pointNameToIndex))
			deltaInstructions.append('EIF[ ]')
			if command['code'] == 'mdeltah':
				x_instructions.extend(deltaInstructions)
			elif command['code'] == 'fdeltah':
				finalDeltasH.extend(deltaInstructions)

		elif deltaGroup[0] == 'Gv':
			deltaInstructions = [
						'PUSHB[ ] 1',
						'RS[ ]',
						'IF[ ]',
						]
			for command in deltaGroup[1]:
				deltaInstructions.extend(processDeltaCommand(command, pointNameToIndex))
			deltaInstructions.append('EIF[ ]')
			if command['code'] == 'mdeltav':
				y_instructions.extend(deltaInstructions)
			elif command['code'] == 'fdeltav':
				finalDeltasV.extend(deltaInstructions)

		else:
			continue

def processDeltaCommand(command, pointNameToIndex):
	if command['active'] == 'false':
		return []

	deltaInstructions = []

	if command['point'] == 'lsb':
		pointIndex = lsbIndex
	elif command['point'] == 'rsb':
		pointIndex = rsbIndex
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
	deltaPString = 'PUSHW[ ]'
	if deltasP1:
		for i in range(len(deltasP1)):
			relativeSize = deltasP1[i]
			arg = (relativeSize << 4 ) + tt_tables.stepToSelector[step]
			deltaPString += ' ' + str(arg) + ' ' + str(pointIndex)
		
		deltaPString += ' ' + str(len(deltasP1))
		deltaInstructions.append(deltaPString)
		deltaInstructions.append('DELTAP1[ ]')

	if deltasP2:
		for i in range(len(deltasP2)):
			relativeSize = deltasP2[i]
			arg = ((relativeSize -16) << 4 ) + tt_tables.stepToSelector[step]
			deltaPString += ' ' + str(arg) + ' ' + str(pointIndex)
		
		deltaPString += ' ' + str(len(deltasP2))
		deltaInstructions.append(deltaPString)
		deltaInstructions.append('DELTAP2[ ]')

	if deltasP3:
		for i in range(len(deltasP3)):
			relativeSize = deltasP3[i]
			arg = ((relativeSize -32) << 4 ) + tt_tables.stepToSelector[step]
			deltaPString += ' ' + str(arg) + ' ' + str(pointIndex)
		
		deltaPString += ' ' + str(len(deltasP3))
		deltaInstructions.append(deltaPString)
		deltaInstructions.append('DELTAP3[ ]')


	return deltaInstructions

def writeAssembly(TTHToolInstance, g, glyphTTHCommands, pointNameToUniqueID, pointNameToIndex):

	if g == None:
		return

	assembly = []
	global RP0
	global RP1
	global RP2
	global lsbIndex
	global rsbIndex
	global x_instructions
	global y_instructions
	global finalDeltasH
	global finalDeltasV

	g.lib['com.robofont.robohint.assembly'] = []
	if glyphTTHCommands == []:
		return

	nbPointsContour = 0
	for contour in g:
		nbPointsContour += len(contour.points)

	lsbIndex = nbPointsContour
	rsbIndex = nbPointsContour+1
	x_instructions = ['SVTCA[1]']
	y_instructions = ['SVTCA[0]']
	
	finalDeltasH = []
	finalDeltasV = []

	groupedCommands = groupCommands(glyphTTHCommands)

	for group in groupedCommands:
		if group[0] == 'alignToZone':
			processAlignToZone(group[1], pointNameToIndex)
		elif group[0] == 'align':
			processAlign(group[1], pointNameToIndex)
		elif group[0] == 'double':
			processDouble(group[1], pointNameToIndex)
		elif group[0] == 'interpolate':
			processInterpolate(group[1], pointNameToIndex)
		elif group[0] == 'single':
			processSingle(group[1], pointNameToIndex)
		elif group[0] == 'delta':
			processDelta(group[1], pointNameToIndex)

	# for TTHCommand in glyphTTHCommands:
	# 	if TTHCommand['active'] == 'false':
	# 		continue

	# 	if 'point'in TTHCommand:
	# 		if TTHCommand['point'] not in pointNameToUniqueID and TTHCommand['point'] not in ['lsb', 'rsb']:
	# 			print 'problem with point', TTHCommand['point'], 'in glyph', g.name
	# 			#glyphTTHCommands.remove(TTHCommand)
	# 			continue
	# 	if 'point1' in TTHCommand:
	# 		if TTHCommand['point1'] not in pointNameToUniqueID and TTHCommand['point1'] not in ['lsb', 'rsb']:
	# 			print 'problem with point', TTHCommand['point1'], 'in glyph', g.name
	# 			#glyphTTHCommands.remove(TTHCommand)
	# 			continue
	# 	if 'point2' in TTHCommand:
	# 		if TTHCommand['point2'] not in pointNameToUniqueID and TTHCommand['point2'] not in ['lsb', 'rsb']:
	# 			print 'problem with point', TTHCommand['point2'], 'in glyph', g.name
	# 			#glyphTTHCommands.remove(TTHCommand)
	# 			continue

		# if TTHCommand['code'] in ['alignt', 'alignb']:
		# 	if TTHCommand['point'] == 'lsb':
		# 		pointIndex = lsbIndex
		# 	elif TTHCommand['point'] == 'rsb':
		# 		pointIndex = rsbIndex
		# 	else:
		# 		if TTHCommand['point'] in pointNameToIndex:
		# 			pointIndex = pointNameToIndex[TTHCommand['point']]
			
		# 	if 'zone' in TTHCommand:
		# 		zoneCV = tt_tables.zone_to_cvt[TTHCommand['zone']]
		# 		alignToZone = [
		# 				'PUSHW[ ] 0',
		# 				'RCVT[ ]',
		# 				'IF[ ]',
		# 				'PUSHW[ ] ' + str(pointIndex),
		# 				'MDAP[1]',
		# 				'ELSE[ ]',
		# 				'PUSHW[ ] ' + str(pointIndex) + ' ' + str(zoneCV),
		# 				'MIAP[0]',
		# 				'EIF[ ]'
		# 				]
		# 		y_instructions.extend(alignToZone)

		# if TTHCommand['code'] == 'alignh' or TTHCommand['code'] == 'alignv':
		# 	if TTHCommand['point'] == 'lsb':
		# 		pointIndex = lsbIndex
		# 	elif TTHCommand['point'] == 'rsb':
		# 		pointIndex = rsbIndex
		# 	else:
		# 		pointUniqueID = pointNameToUniqueID[TTHCommand['point']]
		# 		pointIndex = pointNameToIndex[TTHCommand['point']]

		# 		if pointUniqueID not in touchedPoints:
		# 				touchedPoints.append(pointUniqueID)

		# 	RP0 = pointIndex
		# 	RP1 = pointIndex

		# 	if 'align' in TTHCommand:

		# 		if TTHCommand['align'] == 'round':
		# 			align = [
		# 					'PUSHW[ ] ' + str(pointIndex),
		# 					'MDAP[1]'
		# 					]
		# 		elif TTHCommand['align'] == 'left' or TTHCommand['align'] == 'bottom':
		# 			align = [
		# 					'RDTG[ ]',
		# 					'PUSHW[ ] ' + str(pointIndex),
		# 					'MDAP[1]',
		# 					'RTG[ ]'
		# 					]
		# 		elif TTHCommand['align'] == 'right' or TTHCommand['align'] == 'top':
		# 			align = [
		# 					'RUTG[ ]',
		# 					'PUSHW[ ] ' + str(pointIndex),
		# 					'MDAP[1]',
		# 					'RTG[ ]'
		# 					]
		# 		elif TTHCommand['align'] == 'double':
		# 			align = [
		# 					'RTDG[ ]',
		# 					'PUSHW[ ] ' + str(pointIndex),
		# 					'MDAP[1]',
		# 					'RTG[ ]'
		# 					]
		# 		elif TTHCommand['align'] == 'center':
		# 			align = [
		# 					'RTHG[ ]',
		# 					'PUSHW[ ] ' + str(pointIndex),
		# 					'MDAP[1]',
		# 					'RTG[ ]'
		# 					]
		# 		if TTHCommand['code'] == 'alignh':
		# 			x_instructions.extend(align)
		# 		elif TTHCommand['code'] == 'alignv':
		# 			y_instructions.extend(align)


		# if TTHCommand['code'] == 'doubleh' or TTHCommand['code'] == 'doublev':
		# 	if TTHCommand['point1'] == 'lsb':
		# 		point1Index = lsbIndex
		# 	elif TTHCommand['point1'] == 'rsb':
		# 		point1Index = rsbIndex
		# 	else:
		# 		point1UniqueID = pointNameToUniqueID[TTHCommand['point1']]
		# 		point1Index = pointNameToIndex[TTHCommand['point1']]
		# 		if point1UniqueID not in touchedPoints:
		# 				touchedPoints.append(point1UniqueID)

		# 	if TTHCommand['point2'] == 'lsb':
		# 		point2Index = lsbIndex
		# 	elif TTHCommand['point2'] == 'rsb':
		# 		point2Index = rsbIndex
		# 	else:
		# 		point2UniqueID = pointNameToUniqueID[TTHCommand['point2']]
		# 		point2Index = pointNameToIndex[TTHCommand['point2']]
		# 		if point2UniqueID not in touchedPoints:
		# 				touchedPoints.append(point2UniqueID)

		# 	if 'stem' in TTHCommand:
		# 		if TTHCommand['stem'] in tt_tables.stem_to_cvt:
		# 			stemCV = tt_tables.stem_to_cvt[TTHCommand['stem']]
		# 			double = [
		# 					'PUSHB[ ] 0',
		# 					'RS[ ]',
		# 					'PUSHB[ ] 0',
		# 					'EQ[ ]',
		# 					'IF[ ]',
		# 						'PUSHW[ ] ' + str(point2Index) + ' ' +  str(stemCV) + ' ' + str(point1Index) + ' 4',
		# 						'CALL[ ]',
		# 					'EIF[ ]',
		# 					]
		# 	else:
		# 		double = [
		# 				'PUSHB[ ] 0',
		# 				'RS[ ]',
		# 				'PUSHB[ ] 0',
		# 				'EQ[ ]',
		# 				'IF[ ]',
		# 					'PUSHW[ ] ' + str(point2Index) + ' ' + str(point1Index) + ' 3',
		# 					'CALL[ ]',
		# 				'EIF[ ]',
		# 				]
		# 	if TTHCommand['code'] == 'doubleh':
		# 		x_instructions.extend(double)
		# 	elif TTHCommand['code'] == 'doublev':
		# 		y_instructions.extend(double)


		# if TTHCommand['code'] == 'interpolateh' or TTHCommand['code'] == 'interpolatev':

		# 	if TTHCommand['point1'] == 'lsb':
		# 		point1Index = lsbIndex
		# 	elif TTHCommand['point1'] == 'rsb':
		# 		point1Index = rsbIndex
		# 	else:
		# 		point1UniqueID = pointNameToUniqueID[TTHCommand['point1']]
		# 		point1Index = pointNameToIndex[TTHCommand['point1']]
		# 		if point1UniqueID not in touchedPoints:
		# 				touchedPoints.append(point1UniqueID)

		# 	if TTHCommand['point2'] == 'lsb':
		# 		point2Index = lsbIndex
		# 	elif TTHCommand['point2'] == 'rsb':
		# 		point2Index = rsbIndex
		# 	else:
		# 		point2UniqueID = pointNameToUniqueID[TTHCommand['point2']]
		# 		point2Index = pointNameToIndex[TTHCommand['point2']]
		# 		if point2UniqueID not in touchedPoints:
		# 				touchedPoints.append(point2UniqueID)

		# 	if TTHCommand['point'] == 'lsb':
		# 		pointIndex = lsbIndex
		# 	elif TTHCommand['point'] == 'rsb':
		# 		pointIndex = rsbIndex
		# 	else:
		# 		pointUniqueID = pointNameToUniqueID[TTHCommand['point']]
		# 		pointIndex = pointNameToIndex[TTHCommand['point']]
		# 		if pointUniqueID not in touchedPoints:
		# 				touchedPoints.append(pointUniqueID)

		# 	interpolate = [
		# 					'PUSHW[ ] ' + str(pointIndex) + ' ' + str(point1Index) + ' ' + str(point2Index),
		# 					'SRP1[ ]',
		# 					'SRP2[ ]',
		# 					'IP[ ]'
		# 					]
		# 	if 'align' in TTHCommand:
		# 		if TTHCommand['align'] == 'round':
		# 			align = [
		# 					'PUSHW[ ] ' + str(pointIndex),
		# 					'MDAP[1]'
		# 					]
		# 		elif TTHCommand['align'] == 'left' or TTHCommand['align'] == 'bottom':
		# 			align = [
		# 					'RDTG[ ]',
		# 					'PUSHW[ ] ' + str(pointIndex),
		# 					'MDAP[1]',
		# 					'RTG[ ]'
		# 					]
		# 		elif TTHCommand['align'] == 'right' or TTHCommand['align'] == 'top':
		# 			align = [
		# 					'RUTG[ ]',
		# 					'PUSHW[ ] ' + str(pointIndex),
		# 					'MDAP[1]',
		# 					'RTG[ ]'
		# 					]
		# 		elif TTHCommand['align'] == 'double':
		# 			align = [
		# 					'RTDG[ ]',
		# 					'PUSHW[ ] ' + str(pointIndex),
		# 					'MDAP[1]',
		# 					'RTG[ ]'
		# 					]
		# 		elif TTHCommand['align'] == 'center':
		# 			align = [
		# 					'RTHG[ ]',
		# 					'PUSHW[ ] ' + str(pointIndex),
		# 					'MDAP[1]',
		# 					'RTG[ ]'
		# 					]
		# 	else:
		# 		align = []
		# 	interpolate.extend(align)

		# 	if TTHCommand['code'] == 'interpolateh':
		# 		x_instructions.extend(interpolate)
		# 	elif TTHCommand['code'] == 'interpolatev':
		# 		y_instructions.extend(interpolate)


		# if TTHCommand['code'] == 'singleh' or TTHCommand['code'] == 'singlev':

		# 	if TTHCommand['point1'] == 'lsb':
		# 		point1Index = lsbIndex
		# 	elif TTHCommand['point1'] == 'rsb':
		# 		point1Index = rsbIndex
		# 	else:
		# 		point1UniqueID = pointNameToUniqueID[TTHCommand['point1']]
		# 		point1Index = pointNameToIndex[TTHCommand['point1']]

		# 	if TTHCommand['point2'] == 'lsb':
		# 		point2Index = lsbIndex
		# 	elif TTHCommand['point2'] == 'rsb':
		# 		point2Index = rsbIndex
		# 	else:
		# 		point2UniqueID = pointNameToUniqueID[TTHCommand['point2']]
		# 		point2Index = pointNameToIndex[TTHCommand['point2']]

		# 	singleLink = []
		# 	if RP0 == None or point1UniqueID not in touchedPoints:
		# 		singleLink = [
		# 						'PUSHW[ ] ' + str(point1Index),
		# 						'MDAP[1]'
		# 						]
		# 		RP0 = point1Index
		# 		RP1 = point1Index
		# 		touchedPoints.append(point1UniqueID)

		# 	else:
		# 		singleLink = [
		# 						'PUSHW[ ] ' + str(point1Index),
		# 						'SRP0[ ]',
		# 						]
		# 		RP0 = point1Index
		# 		if point1UniqueID not in touchedPoints:
		# 			touchedPoints.append(point1UniqueID)

		# 	singleLink2 = []
		# 	singleLink3 = []
		# 	singleLink4 = []
		# 	align2 = []
		# 	if 'stem' in TTHCommand:
		# 		stemCV = tt_tables.stem_to_cvt[TTHCommand['stem']]
		# 		singleLink2 = [
		# 						'PUSHB[ ] 0',
		# 						'RS[ ]',
		# 						'IF[ ]',
		# 							'PUSHW[ ] ' + str(point2Index),
		# 							'MDRP[10000]',
		# 						'ELSE[ ]',
		# 							'PUSHW[ ] ' + str(point2Index) + ' ' + str(stemCV),
		# 							'MIRP[10100]',
		# 						'EIF[ ]'
		# 						]
		# 		RP1 = RP0 = RP2 = point2Index
		# 		if point2UniqueID not in touchedPoints:
		# 			touchedPoints.append(point2UniqueID)

		# 	if 'round' in TTHCommand:
		# 		singleLink3 = [
		# 						'PUSHW[ ] ' + str(point2Index),
		# 						'MDRP[11100]'
		# 						]
		# 		RP1 = RP0 = RP2 = point2Index
		# 		if point2UniqueID not in touchedPoints:
		# 			touchedPoints.append(point2UniqueID)

		# 	if 'align' in TTHCommand:
		# 		singleLink4 = [
		# 						'PUSHW[ ] ' + str(point2Index),
		# 						'MDRP[10000]',
		# 						]
		# 		if TTHCommand['align'] == 'round':
		# 			singleLink4 = [
		# 						'PUSHW[ ] ' + str(point2Index),
		# 						'MDRP[10100]'
		# 						]
		# 			align2 = [
		# 							'PUSHW[ ] ' + str(point2Index),
		# 							'MDAP[1]'
		# 							]
		# 			RP1 = RP0 = RP2 = point2Index
		# 			if point2UniqueID not in touchedPoints:
		# 				touchedPoints.append(point2UniqueID)

		# 		elif TTHCommand['align'] in ['left', 'bottom']:
		# 			align2 = [		
		# 							'RDTG[ ]',
		# 							'PUSHW[ ] ' + str(point2Index),
		# 							'MDAP[1]',
		# 							'RTG[]'
		# 							]
		# 			RP1 = RP0 = RP2 = point2Index
		# 			if point2UniqueID not in touchedPoints:
		# 				touchedPoints.append(point2UniqueID)

		# 		elif TTHCommand['align'] in ['right', 'top']:
		# 			align2 = [		
		# 							'RUTG[ ]',
		# 							'PUSHW[ ] ' + str(point2Index),
		# 							'MDAP[1]',
		# 							'RTG[]'
		# 							]
		# 			RP1 = RP0 = RP2 = point2Index
		# 			if point2UniqueID not in touchedPoints:
		# 				touchedPoints.append(point2UniqueID)

		# 		elif TTHCommand['align'] == 'double':
		# 			align2 = [		
		# 							'RTDG[ ]',
		# 							'PUSHW[ ] ' + str(point2Index),
		# 							'MDAP[1]',
		# 							'RTG[]'
		# 							]
		# 			RP1 = RP0 = RP2 = point2Index
		# 			if point2UniqueID not in touchedPoints:
		# 				touchedPoints.append(point2UniqueID)

		# 		elif TTHCommand['align'] == 'center':
		# 			align2 = [		
		# 							'RTHG[ ]',
		# 							'PUSHW[ ] ' + str(point2Index),
		# 							'MDAP[1]',
		# 							'RTG[]'
		# 							]
		# 			RP1 = RP0 = RP2 = point2Index
		# 			if point2UniqueID not in touchedPoints:
		# 				touchedPoints.append(point2UniqueID)

		# 		else:
		# 			align2 = []

					
		# 	else:
		# 		singleLink4 = [
		# 						'PUSHW[ ] ' + str(point2Index),
		# 						'MDRP[10000]'
		# 						]
		# 		RP1 = RP0 = RP2 = point2Index
		# 		if point2UniqueID not in touchedPoints:
		# 			touchedPoints.append(point2UniqueID)

		# 	singleLink.extend(singleLink2)
		# 	singleLink.extend(singleLink3)
		# 	singleLink.extend(singleLink4)
		# 	singleLink.extend(align2)

		# 	if TTHCommand['code'] == 'singleh':
		# 		x_instructions.extend(singleLink)
		# 	elif TTHCommand['code'] == 'singlev':
		# 		y_instructions.extend(singleLink)


		# deltaNoCondition = False
		# if TTHCommand['code'] in ['mdeltah', 'mdeltav', 'fdeltah', 'fdeltav']:
		# 	if TTHCommand['gray'] == 'true' and TTHCommand['mono'] == 'true':
		# 		middleDeltas = []
		# 		deltaNoCondition = True
		# 	elif TTHCommand['gray'] == 'false' and TTHCommand['mono'] == 'true':
		# 		middleDeltas = [
		# 					'PUSHB[ ] 1',
		# 					'RS[ ]',
		# 					'PUSHB[ ] 0',
		# 					'EQ[ ]',
		# 					'IF[ ]',
		# 					]
		# 	elif TTHCommand['gray'] == 'true' and TTHCommand['mono'] == 'false':
		# 		middleDeltas = [
		# 					'PUSHB[ ] 1',
		# 					'RS[ ]',
		# 					'IF[ ]',
		# 					]
		# 	else:
		# 		continue

		# 	if TTHCommand['point'] == 'lsb':
		# 		pointIndex = lsbIndex
		# 	elif TTHCommand['point'] == 'rsb':
		# 		pointIndex = rsbIndex
		# 	else:
		# 		pointUniqueID = pointNameToUniqueID[TTHCommand['point']]
		# 		pointIndex = pointNameToIndex[TTHCommand['point']]
		# 		if pointUniqueID not in touchedPoints:
		# 				touchedPoints.append(pointUniqueID)

		# 	ppm1 = TTHCommand['ppm1']
		# 	ppm2 = TTHCommand['ppm2']
		# 	step = int(TTHCommand['delta'])
		# 	nbDelta = 1 + int(ppm2) - int(ppm1)
		# 	deltasP1 = []
		# 	deltasP2 = []
		# 	deltasP3 = []
		# 	for i in range(nbDelta):
		# 		ppm = int(ppm1) + i
		# 		relativeSize = int(ppm) - 9
		# 		if 0 <= relativeSize <= 15:
		# 			deltasP1.append(relativeSize)
		# 		elif 16 <= relativeSize <= 31:
		# 			deltasP2.append(relativeSize)
		# 		elif 32 <= relativeSize <= 47:
		# 			deltasP3.append(relativeSize)
		# 		else:
		# 			print 'delta out of range'
		# 	deltaPString = 'PUSHW[ ]'
		# 	if deltasP1:
		# 		for i in range(len(deltasP1)):
		# 			relativeSize = deltasP1[i]
		# 			arg = (relativeSize << 4 ) + tt_tables.stepToSelector[step]
		# 			deltaPString += ' ' + str(arg) + ' ' + str(pointIndex)
				
		# 		deltaPString += ' ' + str(len(deltasP1))
		# 		middleDeltas.append(deltaPString)
		# 		middleDeltas.append('DELTAP1[ ]')

		# 	if deltasP2:
		# 		for i in range(len(deltasP2)):
		# 			relativeSize = deltasP2[i]
		# 			arg = ((relativeSize -16) << 4 ) + tt_tables.stepToSelector[step]
		# 			deltaPString += ' ' + str(arg) + ' ' + str(pointIndex)
				
		# 		deltaPString += ' ' + str(len(deltasP2))
		# 		middleDeltas.append(deltaPString)
		# 		middleDeltas.append('DELTAP2[ ]')

		# 	if deltasP3:
		# 		for i in range(len(deltasP3)):
		# 			relativeSize = deltasP3[i]
		# 			arg = ((relativeSize -32) << 4 ) + tt_tables.stepToSelector[step]
		# 			deltaPString += ' ' + str(arg) + ' ' + str(pointIndex)
				
		# 		deltaPString += ' ' + str(len(deltasP3))
		# 		middleDeltas.append(deltaPString)
		# 		middleDeltas.append('DELTAP3[ ]')
			
		# 	if not deltaNoCondition:
		# 		middleDeltas.append('EIF[ ]')

		# 	if TTHCommand['code'] == 'mdeltah':
		# 		x_instructions.extend(middleDeltas)
		# 	elif TTHCommand['code'] == 'mdeltav':
		# 		y_instructions.extend(middleDeltas)

		# 	elif TTHCommand['code'] == 'fdeltah':
		# 		finalDeltasH.extend(middleDeltas)
		# 	elif TTHCommand['code'] == 'fdeltav':
		# 		finalDeltasV.extend(middleDeltas)

	##############################	
	if TTHToolInstance.c_fontModel.deactivateStemWhenGrayScale == True:
		assembly.extend([
					'PUSHB[ ] 10',
					'CALL[ ]',
					'DUP[ ]',
					'PUSHB[ ] 0',
					'SWAP[ ]',
					'WS[ ]',
					'PUSHB[ ] 1',
					'SWAP[ ]',
					'WS[ ]',
						])
	else:
		assembly.extend([
					'PUSHB[ ] 0',
					'PUSHB[ ] 0',
					'WS[ ]',
					'PUSHB[ ] 10',
					'CALL[ ]',
					'PUSHB[ ] 1',
					'SWAP[ ]',
					'WS[ ]',
					])

	assembly.extend(x_instructions)
	assembly.extend(y_instructions)
	assembly.extend(['IUP[0]', 'IUP[1]'])
	assembly.append('SVTCA[1]')
	assembly.extend(finalDeltasH)
	assembly.append('SVTCA[0]')
	assembly.extend(finalDeltasV)
	g.lib['com.robofont.robohint.assembly'] = assembly
	RP0 = RP1 = RP2 = None
	lsbIndex = 0
	rsbIndex = 1
	x_instructions = []
	y_instructions = []
	finalDeltasH = []
	finalDeltasV = []
