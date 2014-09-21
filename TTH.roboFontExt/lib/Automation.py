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

def distance(point1, point2):
	return (abs(point1.x - point2.x), abs(point1.y - point2.y))
	
def hypothenuse(point1, point2):
	return math.sqrt(distance(point1, point2)[0]*distance(point1, point2)[0] + distance(point1, point2)[1]*distance(point1, point2)[1])

def closeAngle(angle1, angle2):
	diff = angle1 - angle2
	while diff >= 90:
		diff -= 180
	while diff < -90:
		diff += 180
	return (abs(diff)<5)

def approxEqual(a1, a2):
	#return abs(a1 - a2) < 10*(abs(a1)/100)
	return ( abs(a1 - a2) <= 10*(abs(a1)/100) )

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
	if ((45 < vector) and (vector < 135)):
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
	
def getColor(point1, point2, g):
	hasSomeBlack = False
	hasSomeWhite = False
	color = ''
	if abs(point2.x - point1.x) < maxStemX or abs(point2.y - point1.y) < maxStemY:
		hypothLength = int(hypothenuse(point1, point2))
		for j in range(1, hypothLength-1):
			cp_x = point1.x + ((j)/hypothLength)*(point2.x - point1.x)
			cp_y = point1.y + ((j)/hypothLength)*(point2.y - point1.y) 
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


def makeStemsList(f, g_hPoints, g, italicAngle, minStemX, minStemY, maxStemX, maxStemY):
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
			color = getColor(sourcePoint, targetPoint, g)
			if color == 'Black':
				c_distance = distance(sourcePoint, targetPoint)
				stem = (sourcePoint, targetPoint, c_distance)
				hypoth = hypothenuse(sourcePoint, targetPoint)
				## if Source and Target are almost aligned
				# closeAngle(angleIn_source, angleIn_target) or closeAngle(angleOut_source, angleOut_target) or 
				if closeAngle(angleIn_source, angleOut_target) or closeAngle(angleOut_source, angleIn_target):
					## if Source and Target have opposite direction
					if opposite(directionIn_source, directionIn_target) or opposite(directionIn_source, directionOut_target) or opposite(directionOut_source, directionIn_target):
						
						## if they are horizontal, treat the stem on the Y axis
						if (isHorizontal(angleIn_source) or isHorizontal(angleOut_source)) and (isHorizontal(angleIn_target) or isHorizontal(angleOut_target)):
							if (minStemY - 20*(minStemY/100) < c_distance[1] < maxStemY + 20*(maxStemY/100)) and (minStemY - 20*(minStemY/100) <= hypoth <= maxStemY + 20*(maxStemY/100)):
								stemsListY_temp.append(stem)
								
						## if they are vertical, treat the stem on the X axis		
						if (isVertical(angleIn_source) or isVertical(angleOut_source)) and (isVertical(angleIn_target) or isVertical(angleOut_target)):
							
							if (minStemX - 20*(minStemX/100) <= c_distance[0] <= maxStemX + 20*(maxStemX/100)) and (minStemX - 20*(minStemX/100)<= hypoth <= maxStemX + 20*(maxStemX/100)):
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


	def autoStems(self, font):
		minStemX = 10
		minStemY = 10
		maxStemX = 400
		maxStemY = 400

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

		g = font['o']
		if not g:
			print "WARNING: glyph 'o' missing"
		o_hPoints = make_hPointsList(g)
		(o_stemsListX, o_stemsListY) = makeStemsList(font, o_hPoints, g, ital, minStemX, minStemY, maxStemX, maxStemY)

		g = font['O']
		if not g:
			print "WARNING: glyph 'O' missing"
		O_hPoints = make_hPointsList(g)
		(O_stemsListX, O_stemsListY) = makeStemsList(font, O_hPoints, g, ital, minStemX, minStemY, maxStemX, maxStemY)

		Xs = []
		for i in O_stemsListX:
			Xs.append(i[2][0])
		maxStemX = max(Xs)
		maxStemY = max(Xs)

		Ys = []
		for i in o_stemsListY:
			Ys.append(i[2][1])
		minStemY = min(Ys)
		minStemX = min(Ys)

		for g in font:
			if g.selected:
				g_hPoints = make_hPointsList(g)
				(self.stemsListX, self.stemsListY) = makeStemsList(font, g_hPoints, g, ital, minStemX, minStemY, maxStemX, maxStemY)
				for stem in self.stemsListX:
					originalStemsXList.append(roundbase(stem[2][0], 16))
				for stem in self.stemsListY:
					originalStemsYList.append(roundbase(stem[2][1], 16))
				
				stemsValuesXList = originalStemsXList
				stemsValuesYList = originalStemsYList
			
		valuesXDict = {}
		for StemXValue in stemsValuesXList:
			try:
				valuesXDict[StemXValue] += 1
			except KeyError:
				valuesXDict[StemXValue] = 1
		
		valuesYDict = {}
		for StemYValue in stemsValuesYList:
			try:
				valuesYDict[StemYValue] += 1
			except KeyError:
				valuesYDict[StemYValue] = 1
		
		keyValueXList = valuesXDict.items()
		keyValueXList.sort(compare)
		keyValueXList = keyValueXList[:12]

		keyValueYList = valuesYDict.items()
		keyValueYList.sort(compare)
		keyValueYList = keyValueYList[:12]
		
		
		for keyValue in keyValueXList:
			stemSnapHList.append(keyValue[0])
		

		for keyValue in keyValueYList:
			stemSnapVList.append(keyValue[0])

		print stemSnapHList
		print stemSnapVList
					


	def autoZones(self, font):
		baselineZone = None
		capHeightZone = None
		xHeightZone = None
		ascenderstZone = None
		decenderstZone = None

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
				decenderstZone = (font["p"].box[1], - (font["g"].box[1] - font["p"].box[1]) )

		if baselineZone != None:
			self.addZone('baseline', 'bottom', baselineZone[0], baselineZone[1])
		if capHeightZone != None:
			self.addZone('cap-height', 'top', capHeightZone[0], capHeightZone[1])
		if xHeightZone != None:
			self.addZone('x-height', 'top', xHeightZone[0], xHeightZone[1])
		if ascenderstZone != None:
			self.addZone('ascenders', 'top', ascenderstZone[0], ascenderstZone[1])
		if decenderstZone != None:
			self.addZone('decenders', 'bottom', decenderstZone[0], decenderstZone[1])


	def addZone(self, zoneName, ID, position, width, delta='0@0'):
		if zoneName in self.tthtm.zones:
			return
		deltaDict = self.TTHToolInstance.deltaDictFromString(delta)

		newZone = {'top': (ID=='top'), 'position': position, 'width': width, 'delta' : deltaDict }
		if ID=='top':
			self.TTHToolInstance.AddZone(zoneName, newZone, self.controller.topZoneView)
		else:
			self.TTHToolInstance.AddZone(zoneName, newZone, self.controller.bottomZoneView)