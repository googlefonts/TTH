
import math
from string import ascii_letters
from models.TTHTool import uniqueInstance as tthTool
from commons import helperFunctions
import KMeans

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def computeMaxStemOnO(font):
	minStemX = helperFunctions.roundbase(tthtm.minStemX, roundFactor_Stems)
	minStemY = helperFunctions.roundbase(tthtm.minStemY, roundFactor_Stems)
	maxStemX = helperFunctions.roundbase(tthtm.maxStemX, roundFactor_Stems)
	maxStemY = helperFunctions.roundbase(tthtm.maxStemY, roundFactor_Stems)
	xBound = minStemX*(1.0-roundFactor_Stems/100.0), maxStemX*(1.0+roundFactor_Stems/100.0)
	yBound = minStemY*(1.0-roundFactor_Stems/100.0), maxStemY*(1.0+roundFactor_Stems/100.0)
	if font.info.italicAngle != None:
		ital = - font.info.italicAngle
	else:
		ital = 0
	if 'O' not in font:
		print "WARNING: glyph 'O' missing, unable to calculate stems"
		return -1
	g = font['O']
	contours = makeContours(g, ital)
	(O_stemsListX, O_stemsListY) = makeStemsList(g, contours, ital, xBound, yBound, roundFactor_Stems, tthtm.angleTolerance)

	if O_stemsListX == []:
		return 200
	else:
		return int(round(2.0 * max([stem[2] for stem in O_stemsListX])))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class Automation():
	def __init__(self, controller, TTHToolInstance):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm
		self.controller = controller


	def autoStems(self, font, progressBar):
		roundFactor_Stems = 1#self.tthtm.roundFactor_Stems
		roundFactor_Jumps = self.tthtm.roundFactor_Jumps

		minStemX = helperFunctions.roundbase(self.tthtm.minStemX, roundFactor_Stems)
		minStemY = helperFunctions.roundbase(self.tthtm.minStemY, roundFactor_Stems)

		if font.info.italicAngle != None:
			ital = - font.info.italicAngle
		else:
			ital = 0

		maxStemX = maxStemY = computeMaxStemOnO(self.tthtm, font)
		if maxStemX == -1:
			return

		xBound = minStemX*(1.0-roundFactor_Stems/100.0), maxStemX*(1.0+roundFactor_Stems/100.0)
		yBound = minStemY*(1.0-roundFactor_Stems/100.0), maxStemY*(1.0+roundFactor_Stems/100.0)

		stemsValuesXList = []
		stemsValuesYList = []

		progressBar.set(0)
		tick = 100.0/len(ascii_letters)
		for name in ascii_letters:
			g = font[name]
			contours = makeContours(g, ital)
			(XStems, YStems) = makeStemsList(g, contours, ital, xBound, yBound, roundFactor_Stems, self.tthtm.angleTolerance)
			XStems = [stem[2] for stem in XStems]
			YStems = [stem[2] for stem in YStems]
			stemsValuesXList.extend(XStems)
			stemsValuesYList.extend(YStems)
			progressBar.increment(tick)

		self.sortAndStoreValues(stemsValuesXList, roundFactor_Jumps, isHorizontal=False)
		self.sortAndStoreValues(stemsValuesYList, roundFactor_Jumps, isHorizontal=True)

	def sortAndStoreValues(self, stemsValuesList, roundFactor_Jumps, isHorizontal):
		f = math.log(1.0 + 20.0 / 100.0)
		stemsValuesList.sort()
		logs = [math.log(v) for v in stemsValuesList]
		for k in xrange(1,20):
			score, seeds, clusters = KMeans.optimal(logs, k)
			meanBounds = [(seeds[i], min(c), max(c)) for (i,c) in enumerate(clusters)]
			badClusters = [1 for (mu,mi,ma) in meanBounds if mi<mu-f or ma>mu+f]
			if len(badClusters) == 0: break
		stemSnapList = [int(math.exp(s)+0.5) for s in seeds]

		#valuesDict = {}
		#for StemValue in stemsValuesList:
		#	try:
		#		valuesDict[StemValue] += 1
		#	except KeyError:
		#		valuesDict[StemValue] = 1
		#keyValueList = valuesDict.items()
		#keyValueList.sort(lambda (k1,v1),(k2,v2): v2-v1)
		#stemSnapList = [k for k,v in keyValueList[:6]]

		for width in stemSnapList:
			if not isHorizontal:
				name = 'X_' + str(width)
			else:
				name = 'Y_' + str(width)
			roundedStem = helperFunctions.roundbase(width, roundFactor_Jumps)
			if roundedStem != 0:
				stemPitch = float(self.TTHToolInstance.c_fontModel.UPM)/roundedStem
			else:
				stemPitch = float(self.TTHToolInstance.c_fontModel.UPM)/width
				# FIXME maybe, here we should juste skip this width and 'continue'?
			px1 = str(0)
			px2 = str(int(2*stemPitch))
			px3 = str(int(3*stemPitch))
			px4 = str(int(4*stemPitch))
			px5 = str(int(5*stemPitch))
			px6 = str(int(6*stemPitch))

			self.addStem(isHorizontal, name, width, px1, px2, px3, px4, px5, px6)

	def addStem(self, isHorizontal, stemName, width, px1, px2, px3, px4, px5, px6):
		if stemName in self.TTHToolInstance.c_fontModel.stems:
			return
		stemDict = {'horizontal': isHorizontal, 'width': width, 'round': {px1: 1, px2: 2, px3: 3, px4: 4, px5: 5, px6: 6} }
		if isHorizontal:
			self.TTHToolInstance.addStem(stemName, stemDict, self.controller.horizontalStemView)
		else:
			self.TTHToolInstance.addStem(stemName, stemDict, self.controller.verticalStemView)
