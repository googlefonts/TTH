import math
import string
import HelperFunc as HF
reload(HF)

def make_hPointsList(g):
	contoursList = []
	hPointsList = []
	for i in range(len(g)):
		pointsList = []
		for j in g[i].points:
			pointsList.append(j)
		contoursList.append(pointsList)

	for contour_index in range(len(contoursList)):
		for point_index in range(len(contoursList[contour_index])):
			currentPoint = contoursList[contour_index][point_index]
			if point_index == 0:
				prevPoint = contoursList[contour_index][len(contoursList[contour_index])-1]
			else:
				prevPoint = contoursList[contour_index][point_index-1]
			if point_index == len(contoursList[contour_index]) -1:
				nextPoint = contoursList[contour_index][0]
			else:
				nextPoint = contoursList[contour_index][point_index+1]
			
			if currentPoint.type != 'offCurve':
				directionIN = HF.direction(prevPoint, currentPoint)
				directionOUT = HF.direction(currentPoint, nextPoint)
				vectorIN = HF.angle(prevPoint, currentPoint)
				vectorOUT = HF.angle(currentPoint, nextPoint)
				
				hPoint = (currentPoint, contour_index, point_index, directionIN, directionOUT, vectorIN, vectorOUT)
				hPointsList.append(hPoint)
	return hPointsList
	
def getColor(point1, point2, g, maxStemX, maxStemY):
	hasSomeBlack = False
	hasSomeWhite = False
	color = ''
	if abs(point2.x - point1.x) < maxStemX or abs(point2.y - point1.y) < maxStemY:
		hypothLength = HF.distance(point1, point2)
		for j in range(1, int(hypothLength), 5):
			cp_x = point1.x + ((j*1.0)/hypothLength)*(point2.x - point1.x)
			cp_y = point1.y + ((j*1.0)/hypothLength)*(point2.y - point1.y) 
			if g.pointInside((cp_x, cp_y)):
				hasSomeBlack = True
			else:
				hasSomeWhite = True
			if hasSomeBlack and hasSomeWhite:
				break

	if hasSomeBlack and hasSomeWhite:	
		color = 'Gray'
	elif hasSomeBlack:
		color = 'Black'
	else:
		color = 'White'
	return color


def makeStemsList(f, g_hPoints, g, italicAngle, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems):
	stemsListX_temp = []
	stemsListY_temp = []
	stemsListX = []
	stemsListY = []

	for source_hPoint in range(len(g_hPoints)):
		for target_hPoint in range(len(g_hPoints)):
			sourcePoint = g_hPoints[source_hPoint][0]
			targetPoint = g_hPoints[target_hPoint][0]
			directionIn_source = g_hPoints[source_hPoint][3]
			directionOut_source = g_hPoints[source_hPoint][4]
			directionIn_target = g_hPoints[target_hPoint][3]
			directionOut_target = g_hPoints[target_hPoint][4]
			angleIn_source =  g_hPoints[source_hPoint][5]
			angleOut_source = g_hPoints[source_hPoint][6]
			angleIn_target =  g_hPoints[target_hPoint][5]
			angleOut_target = g_hPoints[target_hPoint][6]
			if source_hPoint == target_hPoint:
				continue
			if ( ( ( (HF.isHorizontal(angleIn_source) or HF.isHorizontal(angleOut_source)) and (HF.isHorizontal(angleIn_target) or HF.isHorizontal(angleOut_target)) ) or ( (HF.isVertical(angleIn_source) or HF.isVertical(angleOut_source)) and (HF.isVertical(angleIn_target) or HF.isVertical(angleOut_target)) ) )
			or ( ( (HF.isHorizontal(HF.rotatedVector(angleIn_source, italicAngle)) or HF.isHorizontal(HF.rotatedVector(angleOut_source, italicAngle))) and (HF.isHorizontal(HF.rotatedVector(angleIn_target, italicAngle)) or HF.isHorizontal(HF.rotatedVector(angleOut_target, italicAngle))) ) or ( (HF.isVertical(HF.rotatedVector(angleIn_source, italicAngle)) or HF.isVertical(HF.rotatedVector(angleOut_source, italicAngle))) and (HF.isVertical(HF.rotatedVector(angleIn_target, italicAngle)) or HF.isVertical(HF.rotatedVector(angleOut_target, italicAngle))) ) ) ):
				color = getColor(sourcePoint, targetPoint, g, maxStemX, maxStemY)
				if color == 'Black':
					c_distance = HF.absoluteDiff(sourcePoint, targetPoint)
					c_distance = ( HF.roundbase(c_distance[0], roundFactor_Stems), HF.roundbase(c_distance[1], roundFactor_Stems) )
					stem = (sourcePoint, targetPoint, c_distance)
					hypoth = HF.distance(sourcePoint, targetPoint)
					## if Source and Target are almost aligned
					# closeAngle(angleIn_source, angleIn_target) or closeAngle(angleOut_source, angleOut_target) or 
					if HF.closeAngle(angleIn_source, angleOut_target) or HF.closeAngle(angleOut_source, angleIn_target):
						## if Source and Target have opposite direction
						if HF.opposite(directionIn_source, directionIn_target) or HF.opposite(directionIn_source, directionOut_target) or HF.opposite(directionOut_source, directionIn_target):
							
							## if they are horizontal, treat the stem on the Y axis
							if (HF.isHorizontal(angleIn_source) or HF.isHorizontal(angleOut_source)) and (HF.isHorizontal(angleIn_target) or HF.isHorizontal(angleOut_target)):
								yBound = minStemY*(1.0-roundFactor_Stems/100.0), maxStemY*(1.0+roundFactor_Stems/100.0)
								if (yBound[0] < c_distance[1] < yBound[1]) and (yBound[0] <= hypoth <= yBound[1]):
									stemsListY_temp.append(stem)
									
							## if they are vertical, treat the stem on the X axis		
							if ( ((HF.isVertical(angleIn_source) or HF.isVertical(angleOut_source)) and (HF.isVertical(angleIn_target) or HF.isVertical(angleOut_target)))
							or ((HF.isVertical(HF.rotatedVector(angleIn_source, italicAngle)) or HF.isVertical(HF.rotatedVector(angleOut_source, italicAngle))) and (HF.isVertical(HF.rotatedVector(angleIn_target, italicAngle)) or HF.isVertical(HF.rotatedVector(angleOut_target, italicAngle)))) ):
								xBound = minStemX*(1.0-roundFactor_Stems/100.0), maxStemX*(1.0+roundFactor_Stems/100.0)
								if (xBound[0] <= c_distance[0] <= xBound[1]) and (xBound[0] <= hypoth <= xBound[1]):
									stemsListX_temp.append(stem)
	# avoid duplicates, filters temporary stems
	yList = []
	for stem in stemsListY_temp:
		def pred0(y):
			return HF.approxEqual(stem[0].y, y, .025)
		def pred1(y):
			return HF.approxEqual(stem[1].y, y, .025)
		if not HF.exists(yList, pred0) or not HF.exists(yList, pred1):
			stemsListY.append(stem)
			yList.append(stem[0].y)
			yList.append(stem[1].y)

	xList = []
	for stem in stemsListX_temp:
		(preRot0x, preRot0y) = HF.rotated(stem[0], italicAngle)
		(preRot1x, preRot1y) = HF.rotated(stem[1], italicAngle)
		def pred0(x):
			#print preRot0x, x
			return HF.approxEqual(preRot0x, x, 0.025)
		def pred1(x):
			#print preRot1x, x
			return HF.approxEqual(preRot1x, x, 0.025)
		if not HF.exists(xList,pred0) or not HF.exists(xList,pred1):
			stemsListX.append(stem)
			xList.append(preRot0x)
			xList.append(preRot1x)
	
	return (stemsListX, stemsListY)
	
### - - - - - - - - - - -  - - - - - - - - - - - - - - - - - - - - - - 

class Automation():
	def __init__(self, controller, TTHToolInstance):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm
		self.controller = controller


	def autoStems(self, font, progressBar):
		minStemX = self.tthtm.minStemX
		minStemY = self.tthtm.minStemY
		maxStemX = self.tthtm.maxStemX
		maxStemY = self.tthtm.maxStemY
		roundFactor_Stems = self.tthtm.roundFactor_Stems
		roundFactor_Jumps = self.tthtm.roundFactor_Jumps

		minStemX = HF.roundbase(minStemX, roundFactor_Stems)
		minStemY = HF.roundbase(minStemY, roundFactor_Stems)
		maxStemX = HF.roundbase(maxStemX, roundFactor_Stems)
		maxStemY = HF.roundbase(maxStemY, roundFactor_Stems)


		stemsValuesXList = []
		stemsValuesYList = []
		stemSnapHList = []
		stemSnapVList = []
		roundedStemsXList = []
		roundedStemsYList = []
		originalStemsXList = []
		originalStemsYList = []

		if font.info.italicAngle != None:
			ital = - font.info.italicAngle
		else:
			ital = 0

		g = font['O']
		if not g:
			print "WARNING: glyph 'O' missing"
		O_hPoints = make_hPointsList(g)
		(O_stemsListX, O_stemsListY) = makeStemsList(font, O_hPoints, g, ital, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems)

		Xs = []
		for stem in O_stemsListX:
			Xs.append(stem[2][0])
		maxStemX = max(Xs)
		maxStemY = max(Xs)

		stemsValuesXList = []
		stemsValuesYList = []

		progressBar.set(0)
		tick = 100.0/len(string.ascii_letters)
		for name in string.ascii_letters:
			g = font[name]
			( originalStemsXList, originalStemsYList ) = self.getRoundedStems(font, g, ital, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems)
			stemsValuesXList.extend(originalStemsXList)
			stemsValuesYList.extend(originalStemsYList)
			progressBar.increment(tick)

		self.sortAndStoreValues(stemsValuesXList, False, roundFactor_Jumps)
		self.sortAndStoreValues(stemsValuesYList, True, roundFactor_Jumps)

	def getRoundedStems(self, font, g, ital, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems):
		originalStemsXList = []
		originalStemsYList = []
		g_hPoints = make_hPointsList(g)
		(self.stemsListX, self.stemsListY) = makeStemsList(font, g_hPoints, g, ital, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems)
		for stem in self.stemsListX:
			originalStemsXList.append(stem[2][0])
		for stem in self.stemsListY:
			originalStemsYList.append(stem[2][1])

		return (originalStemsXList, originalStemsYList)
	

	def sortAndStoreValues(self, stemsValuesList, isHorizontal, roundFactor_Jumps):
		valuesDict = {}
		stemSnapList = []
		for StemValue in stemsValuesList:
			try:
				valuesDict[StemValue] += 1
			except KeyError:
				valuesDict[StemValue] = 1
		
		
		keyValueList = valuesDict.items()
		keyValueList.sort(HF.compare)
		keyValueList = keyValueList[:6]

		for keyValue in keyValueList:
			stemSnapList.append(keyValue[0])

		for width in stemSnapList:
			if isHorizontal == False:
				name = 'X_' + str(width)
			else:
				name = 'Y_' + str(width)
			#stemPitch = float(self.tthtm.UPM)/width
			roundedStem = HF.roundbase(width, roundFactor_Jumps)
			if roundedStem !=0:
				stemPitch = float(self.tthtm.UPM)/roundedStem
			else:
				stemPitch = float(self.tthtm.UPM)/width
			#stemPitch = roundbase(float(self.tthtm.UPM)/width, roundFactor_Jumps)
			px1 = str(0)
			px2 = str(int(2*stemPitch))
			#stemPitch = float(self.tthtm.UPM)/roundbase(width, roundFactor_Jumps - 1*int(roundFactor_Jumps/5))
			px3 = str(int(3*stemPitch))
			#stemPitch = float(self.tthtm.UPM)/roundbase(width, roundFactor_Jumps - 2*int(roundFactor_Jumps/5))
			px4 = str(int(4*stemPitch))
			#stemPitch = float(self.tthtm.UPM)/roundbase(width, roundFactor_Jumps - 3*int(roundFactor_Jumps/5))
			px5 = str(int(5*stemPitch))
			#stemPitch = float(self.tthtm.UPM)/roundbase(width, roundFactor_Jumps - 4*int(roundFactor_Jumps/5))
			px6 = str(int(6*stemPitch))

			self.addStem(isHorizontal, name, width, px1, px2, px3, px4, px5, px6)

					
	def addStem(self, isHorizontal, stemName, width, px1, px2, px3, px4, px5, px6):
		if stemName in self.tthtm.stems:
			return
		stemDict = {'horizontal': isHorizontal, 'width': width, 'round': {px1: 1, px2: 2, px3: 3, px4: 4, px5: 5, px6: 6} }
		if isHorizontal:
			self.TTHToolInstance.addStem(stemName, stemDict, self.controller.horizontalStemView)
		else:
			self.TTHToolInstance.addStem(stemName, stemDict, self.controller.verticalStemView)


	def autoZones(self, font):
		baselineZone = None
		capHeightZone = None
		xHeightZone = None
		ascenderstZone = None
		descenderstZone = None

		if "O" in font and "H" in font:
			baselineZone = (0, -font["O"].box[1])
			capHeightZone = (font["H"].box[3], -font["O"].box[1])
		if "o" in font:
			xHeightZone = (font["o"].box[3] + font["o"].box[1], - font["o"].box[1])
		if "f" in font and "l" in font:
			if font["l"].box[3] < font["f"].box[3]:
				ascenderstZone = (font["l"].box[3], font["f"].box[3] - font["l"].box[3])
		if "g" in font and "p" in font:
			if font["p"].box[1] > font["g"].box[1]:
				descenderstZone = (font["p"].box[1], - (font["g"].box[1] - font["p"].box[1]) )

		if baselineZone != None:
			self.addZone('baseline', 'bottom', baselineZone[0], baselineZone[1])
		if capHeightZone != None:
			self.addZone('cap-height', 'top', capHeightZone[0], capHeightZone[1])
		if xHeightZone != None:
			self.addZone('x-height', 'top', xHeightZone[0], xHeightZone[1])
		if ascenderstZone != None:
			self.addZone('ascenders', 'top', ascenderstZone[0], ascenderstZone[1])
		if descenderstZone != None:
			self.addZone('descenders', 'bottom', descenderstZone[0], descenderstZone[1])


	def addZone(self, zoneName, ID, position, width, delta='0@0'):
		if zoneName in self.tthtm.zones:
			return
		deltaDict = self.TTHToolInstance.deltaDictFromString(delta)

		newZone = {'top': (ID=='top'), 'position': position, 'width': width, 'delta' : deltaDict }
		if ID=='top':
			self.TTHToolInstance.AddZone(zoneName, newZone, self.controller.topZoneView)
		else:
			self.TTHToolInstance.AddZone(zoneName, newZone, self.controller.bottomZoneView)

class AutoHinting():
	def __init__(self, TTHToolInstance):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm

	def detectStems(self, g):
		minStemX = self.tthtm.minStemX
		minStemY = self.tthtm.minStemY
		maxStemX = self.tthtm.maxStemX
		maxStemY = self.tthtm.maxStemY
		roundFactor_Stems = self.tthtm.roundFactor_Stems
		roundFactor_Jumps = self.tthtm.roundFactor_Jumps

		minStemX = HF.roundbase(minStemX, roundFactor_Stems)
		minStemY = HF.roundbase(minStemY, roundFactor_Stems)
		maxStemX = HF.roundbase(maxStemX, roundFactor_Stems)
		maxStemY = HF.roundbase(maxStemY, roundFactor_Stems)

		font = g.getParent()

		(g_stemsListX, g_stemsListY) = makeStemsList(font, self.h_pointList, g, self.ital, minStemX, minStemY, maxStemX, maxStemY, 10)

		for stem in  g_stemsListY:
			detectedWidth = HF.absoluteDiff(stem[0], stem[1])[1]
			self.addStem(stem[0], stem[1], detectedWidth, False)
		for stem in  g_stemsListX:
			detectedWidth = HF.absoluteDiff(stem[0], stem[1])[0]
			self.addStem(stem[0], stem[1], detectedWidth, True)
			

	def addStem(self, p1, p2, width, isHorizontal):
		
		candidatesList = []
		for stemName, stem in self.tthtm.stems.items():
			if stem['horizontal'] != isHorizontal:
				w = int(stem['width'])
				if HF.approxEqual(w, width, .20):
					candidatesList.append((abs(w - width), stemName))

		if candidatesList != []:
			candidatesList.sort()
			stemName = candidatesList[0][1]
			newCommand = {}
			#newAlign = {}
			if isHorizontal:
				newCommand['code'] = 'singleh'
				#newAlign['code'] = 'alignh'
			else:
				newCommand['code'] = 'singlev'
				#newAlign['code'] = 'alignv'
			newCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(p1.x, p1.y)]
			newCommand['point2'] = self.TTHToolInstance.pointCoordinatesToName[(p2.x, p2.y)]
			#newAlign['point'] = self.TTHToolInstance.pointCoordinatesToName[(p1.x, p1.y)]
			#newAlign['align'] = 'round'
			for command in self.TTHToolInstance.glyphTTHCommands:
				if command['code'][:5] == 'align':
					if command['point'] == newCommand['point2']:
						newCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(p2.x, p2.y)]
						newCommand['point2'] = self.TTHToolInstance.pointCoordinatesToName[(p1.x, p1.y)]
						#newAlign['point'] = self.TTHToolInstance.pointCoordinatesToName[(p2.x, p2.y)]

			newCommand['stem'] = stemName
			commandExists = False
			alignExists = False
			for command in self.TTHToolInstance.glyphTTHCommands:
				if command['code'][:6] == 'single':
					if (command['point1'] == newCommand['point1'] or command['point1'] == newCommand['point2']) and (command['point2'] == newCommand['point1'] or command['point2'] == newCommand['point2']):
						commandExists = True

			if not commandExists:
				self.TTHToolInstance.glyphTTHCommands.append(newCommand)
				
				for i in range(len(self.h_pointList)):
					p = self.h_pointList[i]
					if i > 0:
						p_prev = self.h_pointList[i-1][0]
					else:
						p_prev = self.h_pointList[len(self.h_pointList)-1][0]
					if i <len(self.h_pointList)-1:
						p_next = self.h_pointList[i+1][0]
					else:
						p_next = self.h_pointList[0][0]

					p_x = p[0].x
					p_y = p[0].y
					p1_x = p1.x
					p1_y = p1.y
					p2_x = p2.x
					p2_y = p2.y
					(p_x, p_y) = HF.rotated(p[0], self.ital)
					if isHorizontal:
						if abs(HF.rotated(p[0], self.ital)[0] - HF.rotated(p2, self.ital)[0]) <= 5 and p[0] != p2 and ( HF.isVertical(HF.rotatedVector(p[5], self.ital)) or HF.isVertical(HF.rotatedVector(p[6], self.ital) ) ) and p2 != p_prev and p2 != p_next:
							newCommand = {}
							newCommand['code'] = 'singleh'
							newCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(p2.x, p2.y)]
							newCommand['point2'] = self.TTHToolInstance.pointCoordinatesToName[(p[0].x, p[0].y)]
							dontLink = False
							for command2 in self.TTHToolInstance.glyphTTHCommands:
								if command2['code'] == 'singleh':
									if command2['point1'] == newCommand['point2'] or command2['point2'] == newCommand['point2']:
										dontLink = True
										break

							if newCommand not in self.TTHToolInstance.glyphTTHCommands and dontLink == False:
								self.TTHToolInstance.glyphTTHCommands.append(newCommand)

						if abs(HF.rotated(p[0], self.ital)[0] - HF.rotated(p1, self.ital)[0]) <= 5 and p[0] != p1 and ( HF.isVertical(HF.rotatedVector(p[5], self.ital)) or HF.isVertical(HF.rotatedVector(p[6], self.ital)) ) and p1 != p_prev and p1 != p_next:
							newCommand = {}
							newCommand['code'] = 'singleh'
							newCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(p1.x, p1.y)]
							newCommand['point2'] = self.TTHToolInstance.pointCoordinatesToName[(p[0].x, p[0].y)]
							dontLink = False
							for command2 in self.TTHToolInstance.glyphTTHCommands:
								if command2['code'] == 'singleh':
									if command2['point1'] == newCommand['point2'] or command2['point2'] == newCommand['point2']:
										dontLink = True
										break

							if newCommand not in self.TTHToolInstance.glyphTTHCommands and dontLink == False:
								self.TTHToolInstance.glyphTTHCommands.append(newCommand)

					else:
						if abs(HF.rotated(p[0], self.ital)[1] - HF.rotated(p2, self.ital)[1]) <= 5 and p[0] != p2 and ( HF.isHorizontal(HF.rotatedVector(p[5], self.ital)) or HF.isHorizontal(HF.rotatedVector(p[6], self.ital)) ) and p2 != p_prev and p2 != p_next:
							newCommand = {}
							newCommand['code'] = 'singlev'
							newCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(p2.x, p2.y)]
							newCommand['point2'] = self.TTHToolInstance.pointCoordinatesToName[(p[0].x, p[0].y)]
							dontLink = False
							for command2 in self.TTHToolInstance.glyphTTHCommands:
								if command2['code'] == 'singlev':
									if command2['point1'] == newCommand['point2'] or command2['point2'] == newCommand['point2']:
										dontLink = True
										break

							if newCommand not in self.TTHToolInstance.glyphTTHCommands and dontLink == False:
								self.TTHToolInstance.glyphTTHCommands.append(newCommand)

						if abs(HF.rotated(p[0], self.ital)[1] - HF.rotated(p1, self.ital)[1]) <= 5 and p[0] != p1 and ( HF.isHorizontal(HF.rotatedVector(p[5], self.ital)) or HF.isHorizontal(HF.rotatedVector(p[6], self.ital)) ) and p1 != p_prev and p1 != p_next:
							newCommand = {}
							newCommand['code'] = 'singlev'
							newCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(p1.x, p1.y)]
							newCommand['point2'] = self.TTHToolInstance.pointCoordinatesToName[(p[0].x, p[0].y)]
							dontLink = False
							for command2 in self.TTHToolInstance.glyphTTHCommands:
								if command2['code'] == 'singlev':
									if command2['point1'] == newCommand['point2'] or command2['point2'] == newCommand['point2']:
										dontLink = True
										break

							if newCommand not in self.TTHToolInstance.glyphTTHCommands and dontLink == False:
								self.TTHToolInstance.glyphTTHCommands.append(newCommand)
					


	def hintWidth(self, g):
		pass



	def autoAlignToZones(self, g):
		for zoneName, zone in self.tthtm.zones.items():
			if not zone['top']:
				y_start = int(zone['position']) - int(zone['width'])
				y_end = int(zone['position'])
				self.processZone(g, zoneName, False, y_start, y_end)
			else:
				y_start = int(zone['position'])
				y_end = int(zone['position']) + int(zone['width'])
				self.processZone(g, zoneName, True , y_start, y_end)


	def processZone(self, g, zoneName, isTop, y_start, y_end):
		#hPoint = (currentPoint, contour_index, point_index, directionIN, directionOUT, vectorIN, vectorOUT)

		for p in self.h_pointList:
			if y_start <= p[0].y  and p[0].y <= y_end and p[0].type != 'offCurve':
				exists = False
				redundant = False
				for command in self.TTHToolInstance.glyphTTHCommands:
					if command['code'][:5] != 'align':
						continue
					else:
						if command['point'] == self.TTHToolInstance.pointCoordinatesToName[(p[0].x, p[0].y)]:
							exists = True
						try:
							(x, y) = self.TTHToolInstance.pointUniqueIDToCoordinates[command['point']]
						except:
							(x, y) = self.TTHToolInstance.pointNameToCoordinates[command['point']]
						if abs(y - p[0].y) <= .1*abs(y_end-y_start):
							redundant = True
				if not exists and not redundant and ( (HF.isHorizontal_byAngle(p[5], 45) or HF.isHorizontal_byAngle(p[6], 45)) ):

					newCommand = {}
					newCommand['point'] = self.TTHToolInstance.pointCoordinatesToName[(p[0].x, p[0].y)]
					newCommand['zone'] = zoneName
					if isTop:
						newCommand['code'] = 'alignt'
					else:
						newCommand['code'] = 'alignb'
					self.TTHToolInstance.glyphTTHCommands.append(newCommand)

					for i in range(len(self.h_pointList)):
						p2 = self.h_pointList[i]
						if i > 0:
							p2_prev = self.h_pointList[i-1][0]
						else:
							p2_prev = self.h_pointList[len(self.h_pointList)-1][0]
						if i <len(self.h_pointList)-1:
							p2_next = self.h_pointList[i+1][0]
						else:
							p2_next = self.h_pointList[0][0]
						if abs(p[0].y - p2[0].y) <= 2 and p != p2 and p[0] != p2_prev and p[0] != p2_next:
							newCommand = {}
							newCommand['code'] = 'singlev'
							newCommand['point1'] = self.TTHToolInstance.pointCoordinatesToName[(p[0].x, p[0].y)]
							newCommand['point2'] = self.TTHToolInstance.pointCoordinatesToName[(p2[0].x, p2[0].y)]
							dontLink = False
							for command2 in self.TTHToolInstance.glyphTTHCommands:
								if command2['code'] == 'alignv':
									if command2['point'] == newCommand['point2']:
										dontLink = True
										break
							if not dontLink:
								self.TTHToolInstance.glyphTTHCommands.append(newCommand)



	def autohint(self, g):
		self.h_pointList = make_hPointsList(g)
		if self.tthtm.f.info.italicAngle != None:
			self.ital = - self.tthtm.f.info.italicAngle
		else:
			self.ital = 0

		self.tthtm.g.prepareUndo("AutoHint")
		self.autoAlignToZones(g)
		self.detectStems(g)
		self.hintWidth(g)
		self.TTHToolInstance.updateGlyphProgram()
		if self.tthtm.alwaysRefresh == 1:
			self.TTHToolInstance.refreshGlyph()
		self.tthtm.g.performUndo()
