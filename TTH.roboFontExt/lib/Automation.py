import math
import string


def direction(point1, point2):
	direction_x = 4
	direction_y = 4
	if point1.x < point2.x:
		# Direction is RIGHT
		direction_x = 1
	elif point1.x > point2.x:
		# Direction is LEFT
		direction_x = -1
	else:
		# Direction is NONE
		direction_x = 4
		
	if point1.y < point2.y:
		# Direction is UP
		direction_y = 1
	elif point1.y > point2.y:
		# Direction is DOWN
		direction_y = -1
	else:
		# Direction is NONE
		direction_y = 4
	return (direction_x, direction_y)


def rotated(point, angle):
	x = point.x
	y = point.y
	angle = (math.radians(angle))
	cosa = math.cos(angle)
	sina = math.sin(angle)
	rotatedPoint_x = int(cosa*x - sina*y)
	rotatedPoint_y = int(sina*x + cosa*y)
	return (rotatedPoint_x, rotatedPoint_y)
	
	
def angle(point1, point2):
	return math.atan2(point2.y - point1.y, point2.x - point1.x) / math.pi * 180
	
def shearFactor(angle):
	# find the shearFactor r with a given angle
	r = math.tan(math.radians(angle))
	return r

def absoluteDiff(point1, point2):
	return (abs(point1.x - point2.x), abs(point1.y - point2.y))
	
def distance(point1, point2):
	dx, dy = absoluteDiff(point1, point2)
	return math.sqrt(dx*dx+dy*dy)
	
def closeAngle(angle1, angle2):
	diff = angle1 - angle2
	while diff >= 90:
		diff -= 180
	while diff < -90:
		diff += 180
	return (abs(diff)<5)

def approxEqual(a1, a2):
	a_max = max(abs(a1), abs(a2))
	return ( abs(a1 - a2) <= .10*a_max )

def opposite(direction1, direction2):
	isOpposite = False
	LR1 = direction1[0]
	UD1 = direction1[1]
	LR2 = direction2[0]
	UD2 = direction2[1]
	if LR1 + LR2 == 0:
		isOpposite = True
	if UD1 + UD2 == 0:
		isOpposite = True
	return isOpposite
	
def isVertical(vector):
	vector = abs(vector)
	if ((65 < vector) and (vector < 115)):
		return True
	else:
		return False
	
def isHorizontal(vector):
	vector = abs(vector)
	if ((0 <= vector) and (vector <= 45)) or ((135 <= vector) and (vector <= 180)):
		return True
	else:
		return False

#True si il existe un element de la liste l pour lequel la fonction p renvoi True (on dit que le predicat p est vrai sur cet element)
def exists(l, p):
	for e in l:
		if p(e):
			return True
	return False

def sheared(point, angle):
	r = shearFactor(angle)
	return (point.x + r*point.y, point.y)

def roundbase(x, base):
	return int(base * round(float(x)/base))
	
def compare((k1,v1),(k2,v2)):
	return v2 - v1

###### - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


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
				directionIN = direction(prevPoint, currentPoint)
				directionOUT = direction(currentPoint, nextPoint)
				vectorIN = angle(prevPoint, currentPoint)
				vectorOUT = angle(currentPoint, nextPoint)
				
				hPoint = (currentPoint, contour_index, point_index, directionIN, directionOUT, vectorIN, vectorOUT)
				hPointsList.append(hPoint)
	return hPointsList
	
def getColor(point1, point2, g, maxStemX, maxStemY):
	hasSomeBlack = False
	hasSomeWhite = False
	color = ''
	if abs(point2.x - point1.x) < maxStemX or abs(point2.y - point1.y) < maxStemY:
		hypothLength = distance(point1, point2)
		for j in range(1, int(hypothLength)):
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
			if ( (isHorizontal(angleIn_source) or isHorizontal(angleOut_source)) and (isHorizontal(angleIn_target) or isHorizontal(angleOut_target)) ) or ( (isVertical(angleIn_source) or isVertical(angleOut_source)) and (isVertical(angleIn_target) or isVertical(angleOut_target)) ):
				color = getColor(sourcePoint, targetPoint, g, maxStemX, maxStemY)
				if color == 'Black':
					c_distance = absoluteDiff(sourcePoint, targetPoint)
					c_distance = ( roundbase(c_distance[0], roundFactor_Stems), roundbase(c_distance[1], roundFactor_Stems) )
					stem = (sourcePoint, targetPoint, c_distance)
					hypoth = distance(sourcePoint, targetPoint)
					## if Source and Target are almost aligned
					# closeAngle(angleIn_source, angleIn_target) or closeAngle(angleOut_source, angleOut_target) or 
					if closeAngle(angleIn_source, angleOut_target) or closeAngle(angleOut_source, angleIn_target):
						## if Source and Target have opposite direction
						if opposite(directionIn_source, directionIn_target) or opposite(directionIn_source, directionOut_target) or opposite(directionOut_source, directionIn_target):
							
							## if they are horizontal, treat the stem on the Y axis
							if (isHorizontal(angleIn_source) or isHorizontal(angleOut_source)) and (isHorizontal(angleIn_target) or isHorizontal(angleOut_target)):
								yBound = minStemY*(1.0-roundFactor_Stems/100.0), maxStemY*(1.0+roundFactor_Stems/100.0)
								if (yBound[0] < c_distance[1] < yBound[1]) and (yBound[0] <= hypoth <= yBound[1]):
									stemsListY_temp.append(stem)
									
							## if they are vertical, treat the stem on the X axis		
							if (isVertical(angleIn_source) or isVertical(angleOut_source)) and (isVertical(angleIn_target) or isVertical(angleOut_target)):
								
								xBound = minStemX*(1.0-roundFactor_Stems/100.0), maxStemX*(1.0+roundFactor_Stems/100.0)
								if (xBound[0] <= c_distance[0] <= xBound[1]) and xBound[0] <= hypoth <= xBound[1]):
									stemsListX_temp.append(stem)
	# avoid duplicates, filters temporary stems
	yList = []
	for stem in stemsListY_temp:
		def pred0(y):
			return approxEqual(stem[0].y, y)
		def pred1(y):
			return approxEqual(stem[1].y, y)
		if not exists(yList, pred0) or not exists(yList, pred1):
			stemsListY.append(stem)
			yList.append(stem[0].y)
			yList.append(stem[1].y)

	xList = []
	for stem in stemsListX_temp:
		(preRot0x, preRot0y) = rotated(stem[0], italicAngle)
		(preRot1x, preRot1y) = rotated(stem[1], italicAngle)
		def pred0(x):
			#print preRot0x, x
			return approxEqual(preRot0x, x)
		def pred1(x):
			#print preRot1x, x
			return approxEqual(preRot1x, x)
		if not exists(xList,pred0) or not exists(xList,pred1):
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
		minStemX = 20
		minStemY = 20
		maxStemX = 400
		maxStemY = 400
		roundFactor_Stems = self.tthtm.roundFactor_Stems
		roundFactor_Jumps = self.tthtm.roundFactor_Jumps

		minStemX = roundbase(minStemX, roundFactor_Stems)
		minStemY = roundbase(minStemY, roundFactor_Stems)
		maxStemX = roundbase(maxStemX, roundFactor_Stems)
		maxStemY = roundbase(maxStemY, roundFactor_Stems)


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

		# g = font['o']
		# if not g:
		# 	print "WARNING: glyph 'o' missing"
		# o_hPoints = make_hPointsList(g)
		# (o_stemsListX, o_stemsListY) = makeStemsList(font, o_hPoints, g, ital, minStemX, minStemY, maxStemX, maxStemY)

		g = font['O']
		if not g:
			print "WARNING: glyph 'O' missing"
		O_hPoints = make_hPointsList(g)
		(O_stemsListX, O_stemsListY) = makeStemsList(font, O_hPoints, g, ital, minStemX, minStemY, maxStemX, maxStemY, roundFactor_Stems)

		Xs = []
		for i in O_stemsListX:
			Xs.append(i[2][0])
		maxStemX = max(Xs)
		maxStemY = max(Xs)

		# Ys = []
		# for i in o_stemsListY:
		# 	Ys.append(i[2][1])
		# minStemY = min(Ys)
		# minStemX = min(Ys)
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
		keyValueList.sort(compare)
		keyValueList = keyValueList[:6]

		for keyValue in keyValueList:
			stemSnapList.append(keyValue[0])

		for width in stemSnapList:
			if isHorizontal == False:
				name = 'X_' + str(width)
			else:
				name = 'Y_' + str(width)
			#stemPitch = float(self.tthtm.UPM)/width
			roundedStem = roundbase(width, roundFactor_Jumps)
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
