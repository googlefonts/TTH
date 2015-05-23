
import math
from string import ascii_letters
from models.TTHTool import uniqueInstance as tthTool
from commons import helperFunctions, KMeans
import auto

def autoStems(fm, progressBar):
	font = fm.f

	if font.info.italicAngle != None:
		ital = - font.info.italicAngle
	else:
		ital = 0

	yBound, xBound = fm.stemSizeBounds

	stemsValuesXList = []
	stemsValuesYList = []

	progressBar.set(0)
	progressBar._nsObject.setMaxValue_(len(ascii_letters))
	for name in ascii_letters:
		g = font[name]
		contours = auto.makeContours(g, ital)
		(XStems, YStems) = auto.makeStemsList(g, contours, ital, xBound, yBound, fm.angleTolerance)
		XStems = [stem[2] for stem in XStems]
		YStems = [stem[2] for stem in YStems]
		stemsValuesXList.extend(XStems)
		stemsValuesYList.extend(YStems)
		progressBar.increment(1)

	upm = float(fm.UPM)
	hStems = clusterAndGenStemDicts(upm, stemsValuesXList, isHorizontal=False)
	vStems = clusterAndGenStemDicts(upm, stemsValuesYList, isHorizontal=True)
	return hStems, vStems

def clusterAndGenStemDicts(upm, stemsValuesList, isHorizontal):
	f = math.log(1.0 + 20.0 / 100.0)
	stemsValuesList.sort()
	logs = [math.log(v) for v in stemsValuesList]
	for k in xrange(1,20):
		score, seeds, clusters = KMeans.optimal(logs, k)
		meanBounds = [(seeds[i], min(c), max(c)) for (i,c) in enumerate(clusters)]
		badClusters = [1 for (mu,mi,ma) in meanBounds if mi<mu-f or ma>mu+f]
		if len(badClusters) == 0: break
	stemSnapList = [int(math.exp(s)+0.5) for s in seeds]

	stems = []
	for width in stemSnapList:
		if not isHorizontal:
			name = 'X_' + str(width)
		else:
			name = 'Y_' + str(width)
		roundedStem = helperFunctions.roundbase(width, 20)
		if roundedStem != 0:
			stemPitch = upm/roundedStem
		else:
			stemPitch = upm/width
			# FIXME maybe, here we should juste skip this width and 'continue'?
		px1 = str(0)
		px2 = str(int(2*stemPitch))
		px3 = str(int(3*stemPitch))
		px4 = str(int(4*stemPitch))
		px5 = str(int(5*stemPitch))
		px6 = str(int(6*stemPitch))

		stemDict = {'horizontal': isHorizontal, 'width': width, 'round': {px1: 1, px2: 2, px3: 3, px4: 4, px5: 5, px6: 6} }
		stems.append(stemDict)
		return stems
