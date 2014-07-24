import tt_tables

#def pointIndexFromUniqueID(g, pointUniqueID):
#	pointIndex = 0
#	for contour in g:
#		for point in contour.points:
#			if pointUniqueID == point.naked().uniqueID:
#				return pointIndex
#			pointIndex += 1
#	return None

def writeAssembly(g, glyphTTHCommands, pointNameToUniqueID, pointNameToIndex):
	if g == None:
		return

	nbPointsContour = 0
	for contour in g:
		nbPointsContour += len(contour.points)

	lsbIndex = nbPointsContour
	rsbIndex = nbPointsContour+1

	assembly = []
	g.lib['com.robofont.robohint.assembly'] = []
	x_instructions = ['SVTCA[1]']
	y_instructions = ['SVTCA[0]']
	RP0 = RP1 = RP2 = None
	pointUniqueID = None
	point1UniqueID = None
	point2UniqueID = None
	touchedPoints = []
	finalDeltasH = []
	finalDeltasV = []

	for TTHCommand in glyphTTHCommands:
		if TTHCommand['code'] == 'alignt' or TTHCommand['code'] == 'alignb':
			if TTHCommand['point'] == 'lsb':
				pointIndex = lsbIndex
			elif TTHCommand['point'] == 'rsb':
				pointIndex = rsbIndex
			else:
				pointUniqueID = pointNameToUniqueID[TTHCommand['point']]
				pointIndex = pointNameToIndex[TTHCommand['point']]
			zoneCV = tt_tables.zone_to_cvt[TTHCommand['zone']]
			alignToZone = [
					'PUSHW[ ] 0',
					'RCVT[ ]',
					'IF[ ]',
					'PUSHW[ ] ' + str(pointIndex),
					'MDAP[1]',
					'ELSE[ ]',
					'PUSHW[ ] ' + str(pointIndex) + ' ' + str(zoneCV),
					'MIAP[0]',
					'EIF[ ]'
					]
			y_instructions.extend(alignToZone)

		if TTHCommand['code'] == 'alignh' or TTHCommand['code'] == 'alignv':
			if TTHCommand['point'] == 'lsb':
				pointIndex = lsbIndex
			elif TTHCommand['point'] == 'rsb':
				pointIndex = rsbIndex
			else:
				pointUniqueID = pointNameToUniqueID[TTHCommand['point']]
				pointIndex = pointNameToIndex[TTHCommand['point']]

				if pointUniqueID not in touchedPoints:
						touchedPoints.append(pointUniqueID)

			RP0 = pointIndex
			RP1 = pointIndex

			if TTHCommand['align'] == 'round':
				align = [
						'PUSHW[ ] ' + str(pointIndex),
						'MDAP[1]'
						]
			elif TTHCommand['align'] == 'left' or TTHCommand['align'] == 'bottom':
				align = [
						'RDTG[ ]',
						'PUSHW[ ] ' + str(pointIndex),
						'MDAP[1]'
						'RTG[ ]'
						]
			elif TTHCommand['align'] == 'right' or TTHCommand['align'] == 'top':
				align = [
						'RUTG[ ]',
						'PUSHW[ ] ' + str(pointIndex),
						'MDAP[1]'
						'RTG[ ]'
						]
			elif TTHCommand['align'] == 'double':
				align = [
						'RTDG[ ]',
						'PUSHW[ ] ' + str(pointIndex),
						'MDAP[1]'
						'RTG[ ]'
						]
			elif TTHCommand['align'] == 'center':
				align = [
						'RTHG[ ]',
						'PUSHW[ ] ' + str(pointIndex),
						'MDAP[1]'
						'RTG[ ]'
						]
			if TTHCommand['code'] == 'alignh':
				x_instructions.extend(align)
			elif TTHCommand['code'] == 'alignv':
				y_instructions.extend(align)


		if TTHCommand['code'] == 'doubleh' or TTHCommand['code'] == 'doublev':
			if TTHCommand['point1'] == 'lsb':
				point1Index = lsbIndex
			elif TTHCommand['point1'] == 'rsb':
				point1Index = rsbIndex
			else:
				point1UniqueID = pointNameToUniqueID[TTHCommand['point1']]
				point1Index = pointNameToIndex[TTHCommand['point1']]
				if point1UniqueID not in touchedPoints:
						touchedPoints.append(point1UniqueID)

			if TTHCommand['point2'] == 'lsb':
				point2Index = lsbIndex
			elif TTHCommand['point2'] == 'rsb':
				point2Index = rsbIndex
			else:
				point2UniqueID = pointNameToUniqueID[TTHCommand['point2']]
				point2Index = pointNameToIndex[TTHCommand['point2']]
				if point2UniqueID not in touchedPoints:
						touchedPoints.append(point2UniqueID)

			if 'stem' in TTHCommand:
				stemCV = tt_tables.stem_to_cvt[TTHCommand['stem']]
				double = [
						'PUSHW[ ] ' + str(point2Index) + ' ' +  str(stemCV) + ' ' + str(point1Index) + ' 4',
					'CALL[ ]'
						]
			elif 'round' in TTHCommand:
				double = [
						'PUSHW[ ] ' + str(point2Index) + ' ' + str(point1Index) + ' 3',
					'CALL[ ]'
						]
			if TTHCommand['code'] == 'doubleh':
				x_instructions.extend(double)
			elif TTHCommand['code'] == 'doublev':
				y_instructions.extend(double)


		if TTHCommand['code'] == 'interpolateh' or TTHCommand['code'] == 'interpolatev':

			if TTHCommand['point1'] == 'lsb':
				point1Index = lsbIndex
			elif TTHCommand['point1'] == 'rsb':
				point1Index = rsbIndex
			else:
				point1UniqueID = pointNameToUniqueID[TTHCommand['point1']]
				point1Index = pointNameToIndex[TTHCommand['point1']]
				if point1UniqueID not in touchedPoints:
						touchedPoints.append(point1UniqueID)

			if TTHCommand['point2'] == 'lsb':
				point2Index = lsbIndex
			elif TTHCommand['point2'] == 'rsb':
				point2Index = rsbIndex
			else:
				point2UniqueID = pointNameToUniqueID[TTHCommand['point2']]
				point2Index = pointNameToIndex[TTHCommand['point2']]
				if point2UniqueID not in touchedPoints:
						touchedPoints.append(point2UniqueID)

			if TTHCommand['point'] == 'lsb':
				pointIndex = lsbIndex
			elif TTHCommand['point'] == 'rsb':
				pointIndex = rsbIndex
			else:
				pointUniqueID = pointNameToUniqueID[TTHCommand['point']]
				pointIndex = pointNameToIndex[TTHCommand['point']]
				if pointUniqueID not in touchedPoints:
						touchedPoints.append(pointUniqueID)

			interpolate = [
							'PUSHW[ ] ' + str(pointIndex) + ' ' + str(point1Index) + ' ' + str(point2Index),
							'SRP1[ ]',
							'SRP2[ ]',
							'IP[ ]'
							]
			if 'align' in TTHCommand:
				if TTHCommand['align'] == 'round':
					align = [
							'PUSHW[ ] ' + str(pointIndex),
							'MDAP[1]'
							]
				elif TTHCommand['align'] == 'left' or TTHCommand['align'] == 'bottom':
					align = [
							'RDTG[ ]',
							'PUSHW[ ] ' + str(pointIndex),
							'MDAP[1]'
							'RTG[ ]'
							]
				elif TTHCommand['align'] == 'right' or TTHCommand['align'] == 'top':
					align = [
							'RUTG[ ]',
							'PUSHW[ ] ' + str(pointIndex),
							'MDAP[1]'
							'RTG[ ]'
							]
				elif TTHCommand['align'] == 'double':
					align = [
							'RTDG[ ]',
							'PUSHW[ ] ' + str(pointIndex),
							'MDAP[1]'
							'RTG[ ]'
							]
				elif TTHCommand['align'] == 'center':
					align = [
							'RTHG[ ]',
							'PUSHW[ ] ' + str(pointIndex),
							'MDAP[1]'
							'RTG[ ]'
							]
			else:
				align = []
			interpolate.extend(align)

			if TTHCommand['code'] == 'interpolateh':
				x_instructions.extend(interpolate)
			elif TTHCommand['code'] == 'interpolatev':
				y_instructions.extend(interpolate)


		if TTHCommand['code'] == 'singleh' or TTHCommand['code'] == 'singlev':

			if TTHCommand['point1'] == 'lsb':
				point1Index = lsbIndex
			elif TTHCommand['point1'] == 'rsb':
				point1Index = rsbIndex
			else:
				point1UniqueID = pointNameToUniqueID[TTHCommand['point1']]
				point1Index = pointNameToIndex[TTHCommand['point1']]

			if TTHCommand['point2'] == 'lsb':
				point2Index = lsbIndex
			elif TTHCommand['point2'] == 'rsb':
				point2Index = rsbIndex
			else:
				point2UniqueID = pointNameToUniqueID[TTHCommand['point2']]
				point2Index = pointNameToIndex[TTHCommand['point2']]

			singleLink = []
			if RP0 == None or point1UniqueID not in touchedPoints:
				singleLink = [
								'PUSHW[ ] ' + str(point1Index),
								'MDAP[1]'
								]
				RP0 = point1Index
				RP1 = point1Index
				touchedPoints.append(point1UniqueID)

			else:
				singleLink = [
								'PUSHW[ ] ' + str(point1Index),
								'SRP0[ ]',
								]
				RP0 = point1Index
				if point1UniqueID not in touchedPoints:
					touchedPoints.append(point1UniqueID)

			singleLink2 = []
			align2 = []
			if 'stem' in TTHCommand:
				stemCV = tt_tables.stem_to_cvt[TTHCommand['stem']]
				singleLink2 = [
								'PUSHW[ ] ' + str(point2Index) + ' ' + str(stemCV),
								'MIRP[10100]'
								]
				RP1 = RP0 = RP2 = point2Index
				if point2UniqueID not in touchedPoints:
					touchedPoints.append(point2UniqueID)

			elif 'round' in TTHCommand:
				singleLink2 = [
								'PUSHW[ ] ' + str(point2Index),
								'MDRP[11100]'
								]
				RP1 = RP0 = RP2 = point2Index
				if point2UniqueID not in touchedPoints:
					touchedPoints.append(point2UniqueID)

			elif 'align' in TTHCommand:
				singleLink2 = [
								'PUSHW[ ] ' + str(point2Index),
								'MDRP[10000]'
								]
				if TTHCommand['align'] == 'round':
					singleLink2 = [
								'PUSHW[ ] ' + str(point2Index),
								'MDRP[10100]'
								]
					align2 = [
									'PUSHW[ ] ' + str(point2Index),
									'MDAP[1]'
									]
					RP1 = RP0 = RP2 = point2Index
					if point2UniqueID not in touchedPoints:
						touchedPoints.append(point2UniqueID)

				if TTHCommand['align'] in ['left', 'bottom']:
					align2 = [		
									'RDTG[ ]',
									'PUSHW[ ] ' + str(point2Index),
									'MDAP[1]',
									'RTG[]'
									]
					RP1 = RP0 = RP2 = point2Index
					if point2UniqueID not in touchedPoints:
						touchedPoints.append(point2UniqueID)

				if TTHCommand['align'] in ['right', 'top']:
					align2 = [		
									'RUTG[ ]',
									'PUSHW[ ] ' + str(point2Index),
									'MDAP[1]',
									'RTG[]'
									]
					RP1 = RP0 = RP2 = point2Index
					if point2UniqueID not in touchedPoints:
						touchedPoints.append(point2UniqueID)

				elif TTHCommand['align'] == 'double':
					align2 = [		
									'RTDG[ ]',
									'PUSHW[ ] ' + str(point2Index),
									'MDAP[1]',
									'RTG[]'
									]
					RP1 = RP0 = RP2 = point2Index
					if point2UniqueID not in touchedPoints:
						touchedPoints.append(point2UniqueID)

				elif TTHCommand['align'] == 'center':
					align2 = [		
									'RTHG[ ]',
									'PUSHW[ ] ' + str(point2Index),
									'MDAP[1]',
									'RTG[]'
									]
					RP1 = RP0 = RP2 = point2Index
					if point2UniqueID not in touchedPoints:
						touchedPoints.append(point2UniqueID)

				else:
					align2 = []

					
			else:
				singleLink2 = [
								'PUSHW[ ] ' + str(point2Index),
								'MDRP[10000]'
								]
				RP1 = RP0 = RP2 = point2Index
				if point2UniqueID not in touchedPoints:
					touchedPoints.append(point2UniqueID)

			singleLink.extend(singleLink2)
			singleLink.extend(align2)

			if TTHCommand['code'] == 'singleh':
				x_instructions.extend(singleLink)
			elif TTHCommand['code'] == 'singlev':
				y_instructions.extend(singleLink)



		if TTHCommand['code'] in ['mdeltah', 'mdeltav', 'fdeltah', 'fdeltav']:
			middleDeltas = []
			if TTHCommand['point'] == 'lsb':
				pointIndex = lsbIndex
			elif TTHCommand['point'] == 'rsb':
				pointIndex = rsbIndex
			else:
				pointUniqueID = pointNameToUniqueID[TTHCommand['point']]
				pointIndex = pointNameToIndex[TTHCommand['point']]
				if pointUniqueID not in touchedPoints:
						touchedPoints.append(pointUniqueID)

			ppm1 = TTHCommand['ppm1']
			ppm2 = TTHCommand['ppm2']
			step = int(TTHCommand['delta'])
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
				middleDeltas.append(deltaPString)
				middleDeltas.append('DELTAP1[ ]')

			if deltasP2:
				for i in range(len(deltasP2)):
					relativeSize = deltasP2[i]
					arg = ((relativeSize -16) << 4 ) + tt_tables.stepToSelector[step]
					deltaPString += ' ' + str(arg) + ' ' + str(pointIndex)
				
				deltaPString += ' ' + str(len(deltasP1))
				middleDeltas.append(deltaPString)
				middleDeltas.append('DELTAP2[ ]')

			if deltasP3:
				for i in range(len(deltasP3)):
					relativeSize = deltasP3[i]
					arg = ((relativeSize -32) << 4 ) + tt_tables.stepToSelector[step]
					deltaPString += ' ' + str(arg) + ' ' + str(pointIndex)
				
				deltaPString += ' ' + str(len(deltasP1))
				middleDeltas.append(deltaPString)
				middleDeltas.append('DELTAP3[ ]')

			if TTHCommand['code'] == 'mdeltah':
				x_instructions.extend(middleDeltas)
			elif TTHCommand['code'] == 'mdeltav':
				y_instructions.extend(middleDeltas)

			elif TTHCommand['code'] == 'fdeltah':
				finalDeltasH.extend(middleDeltas)
			elif TTHCommand['code'] == 'fdeltav':
				finalDeltasV.extend(middleDeltas)

	##############################	
	assembly.extend(x_instructions)
	assembly.extend(y_instructions)

	assembly.extend(['IUP[0]', 'IUP[1]'])
	assembly.append('SVTCA[1]')
	assembly.extend(finalDeltasH)
	assembly.append('SVTCA[0]')
	assembly.extend(finalDeltasV)
	g.lib['com.robofont.robohint.assembly'] = assembly
