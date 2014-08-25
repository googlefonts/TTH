from robofab.world import *

# ======================================================================

FL_tth_key = "com.fontlab.v2.tth"

def invertedDictionary( dico ):
	return dict([(v,k) for (k,v) in dico.iteritems()])

def getOrDefault(dico, key, default):
	try:
		return dico[key]
	except:
		return default

def getOrPutDefault(dico, key, default):
	try:
		return dico[key]
	except:
		dico[key] = default
		return default

# ======================================================================

class TTHToolModel():
	def __init__(self):
		self.f = CurrentFont()
		self.g = CurrentGlyph()
		self.UPM = 1000
		self.PPM_Size = 9
		self.pitch = self.UPM/self.PPM_Size
		self.selectedAxis = 'X'
		self.bitmapPreviewSelection = 'Monochrome'

		self.selectedHintingTool = 'Align'
		self.selectedAlignmentTypeAlign = 'round'
		self.selectedAlignmentTypeLink = 'None'
		self.selectedStemX = 'None'
		self.selectedStemY = 'None'
		self.stemsListX = []
		self.stemsListY = []
		self.roundBool = 0
		self.deltaOffset = 0
		self.deltaRange1 = 9
		self.deltaRange2 = 9

		self.textRenderer = None

		self.previewWindowVisible = 0
		self.previewString = ''
		self.previewFrom = 9
		self.previewTo = 48
		self.requiredGlyphsForPartialTempFont = set()
		self.requiredGlyphsForPartialTempFont.add('space')
		self.alwaysRefresh = 1

		tth_lib = getOrPutDefault(self.f.lib, FL_tth_key, {})
		self.zones	= getOrPutDefault(tth_lib, "zones", {})
		self.UITopZones = self.buildUIZonesList(buildTop=True)
		self.UIBottomZones = self.buildUIZonesList(buildTop=False)
		self.stems	= getOrPutDefault(tth_lib, "stems", {})
		self.codeppm	= getOrPutDefault(tth_lib, "codeppm", 48)
		self.alignppm	= getOrPutDefault(tth_lib, "alignppm", 48)
		self.stemsnap	= getOrPutDefault(tth_lib, "stemsnap", 17)

		self.stems = getOrPutDefault(tth_lib, "stems", {})


	def setFont(self, font):
		self.f = font

	def setGlyph(self, glyph):
		self.g = glyph

	def setUPM(self, UPM):
		self.UPM = int(UPM)

	def setSize(self, size):
		self.PPM_Size = int(size)

	def resetFontUPM(self, font):
		if font != None:
			self.UPM = font.info.unitsPerEm
			return self.UPM
		return None

	def resetPitch(self):
		self.resetFontUPM(self.f)
		self.pitch = self.UPM/self.PPM_Size

	def setAxis(self, axis):
		if axis in ['X', 'Y']:
			self.selectedAxis = axis

	def setBitmapPreview(self, preview):
		if preview in ['Monochrome', 'Grayscale', 'Subpixel']:
			self.bitmapPreviewSelection = preview

	def setHintingTool(self, hintingTool):
		if hintingTool in ['Align', 'Single Link', 'Double Link', 'Interpolation', 'Middle Delta', 'Final Delta']:
			self.selectedHintingTool = hintingTool

	def setAlignmentTypeAlign(self, alignmentType):
		if alignmentType in ['round', 'left', 'right', 'center', 'double']:
			self.selectedAlignmentTypeAlign = alignmentType

	def setAlignmentTypeLink(self, alignmentType):
		if alignmentType in ['None', 'round', 'left', 'right', 'center', 'double']:
			self.selectedAlignmentTypeLink = alignmentType

	def setStemX(self, stem):
		self.selectedStemX = str(stem)

	def setStemY(self, stem):
		self.selectedStemY = str(stem)

	def setRoundBool(self, roundBool):
		if roundBool in [0, 1]:
			self.roundBool = roundBool

	def setDeltaOffset(self, offset):
		if offset >= -8 and offset <= 8:
			self.deltaOffset = int(offset)

	def setDeltaRange1(self, value):
		self.deltaRange1 = int(value)

	def setDeltaRange2(self, value):
		self.deltaRange2 = int(value)


	def showPreviewWindow(self, ShowHide):
		if ShowHide == 0:
			self.previewWindowVisible = 0
		elif ShowHide == 1:
			self.previewWindowVisible = 1

	def setPreviewString(self, previewString):
		self.previewString = previewString

	def setAlwaysRefresh(self, valueBool):
		if valueBool in (0, 1):
			self.alwaysRefresh = valueBool

	def setStemsnap(self, value):
		self.stemsnap = int(value)

	def setAlignppm(self, value):
		self.alignppm = int(value)

	def setCodeppm(self, value):
		self.codeppm = int(value)

# ==================================== Functions for Zones

	def deltaDictFromString(self, s):
		try:
			if s == '0@0':
				return {}
			listOfLists = [[int(i) for i in reversed(x.split('@'))] for x in s.split(',')]
			for i in range(len(listOfLists)):
				listOfLists[i][0] = str(listOfLists[i][0])
			return dict(listOfLists)
		except:
			return {}

	def AddZone(self, name, newZone, zoneView):
		# add the zone in the model
		self.zones[name] = newZone
		self.f.lib[FL_tth_key]["zones"][name] = newZone
		# add the zone in the UI
		uiZone = self.buildUIZoneDict(newZone, name)
		zoneView.box.zones_List.append(uiZone)
		#zoneView.UIZones.append(uiZone)
		if zoneView.ID == 'top':
			self.UITopZones.append(uiZone)
		elif zoneView.ID == 'bottom':
			self.UIBottomZones.append(uiZone)


	def deleteZones(self, selected, zoneView):
		for zoneName in selected:
			try:
				del self.f.lib[FL_tth_key]["zones"][zoneName]
				del self.zones[zoneName]
			except:
				pass
		self.UITopZones = self.buildUIZonesList(buildTop = True)
		self.UIBottomZones = self.buildUIZonesList(buildTop = False)
		zoneView.set(self.buildUIZonesList(buildTop = (zoneView.ID == 'top')))

	def EditZone(self, oldZoneName, zoneName, zoneDict, isTop):
		self.storeZone(zoneName, zoneDict, isTop)
		self.f.lib[FL_tth_key]["zones"] = self.zones
		if oldZoneName != zoneName:
			for g in self.f:
				commands = ttht.readGlyphFLTTProgram(g)
				if commands == None:
					continue
				for command in commands:
					if command['code'] in ['alignt', 'alignb']:
						if command['zone'] == oldZoneName:
							command['zone'] = zoneName
				ttht.writeGlyphFLTTProgram(g)
			dummy = ttht.readGlyphFLTTProgram(self.g) # recover the correct commands list

	def storeZone(self, zoneName, entry, isTop):
		if zoneName not in self.tthtm.zones:
			self.tthtm.zones[zoneName] = {}
		zone = self.tthtm.zones[zoneName]
		zone['top'] = isTop
		if 'Position' in entry:
			zone['position'] = int(entry['Position'])
		else:
			zone['position'] = 0
			entry['Position'] = 0
		if 'Width' in entry:
			zone['width'] = int(entry['Width'])
		else:
			zone['width'] = 0
			entry['Width'] = 0
		if 'Delta' in entry:
			deltaDict = self.deltaDictFromString(entry['Delta'])
			if deltaDict != {}:
				zone['delta'] = deltaDict
			else:
				try:
					del zone['delta']
				except:
					pass
		else:
			zone['delta'] = {'0': 0}
			entry['Delta'] = '0@0'

	def buildUIZoneDict(self, zone, name):
		c_zoneDict = {}
		c_zoneDict['Name'] = name
		c_zoneDict['Position'] = zone['position']
		c_zoneDict['Width'] = zone['width']
		deltaString = ''
		if 'delta' in zone:
			count = 0
			for ppEmSize in zone['delta']:
				delta= str(zone['delta'][str(ppEmSize)]) + '@' + str(ppEmSize)
				deltaString += delta
				if count > 0:
					deltaString += ','
				count += 1
			c_zoneDict['Delta'] = deltaString
		else:
			c_zoneDict['Delta'] = '0@0'
		return c_zoneDict

	def buildUIZonesList(self, buildTop):
		return [self.buildUIZoneDict(zone, name) for name, zone in self.zones.iteritems() if zone['top'] == buildTop]

	# ======================================= Functions for Stems

	def storeStem(self, stemName, entry, horizontal):
		stem = getOrPutDefault(self.stems, stemName, {})
		stem['width'] = getOrDefault(entry, 'Width', 0)
		stem['horizontal'] = horizontal
		# stems round dict
		sr = {}
		stem['round'] = sr
		def addRound(colName, val, col):
			if colName in entry:
				sr[str(entry[colName])] = col
			else:
				print("DOES THAT REALLY HAPPEN!?")
				sr[val] = col
		addRound('1 px', '0', 1)
		addRound('2 px', '12', 2)
		addRound('3 px', '16', 3)
		addRound('4 px', '24', 4)
		addRound('5 px', '32', 5)
		addRound('6 px', '64', 6)

	def buildStemUIDict(self, stem, name):
		c_stemDict = {}
		c_stemDict['Name'] = name
		c_stemDict['Width'] = stem['width']
		invDico = invertedDictionary(stem['round'])
		for i in range(1,7):
			c_stemDict[str(i)+' px'] = getOrDefault(invDico, i, '0')
		return c_stemDict

	def buildStemsUIList(self, horizontal=True):
		return [self.buildStemUIDict(stem, name) for name, stem in self.stems.iteritems() if stem['horizontal'] == horizontal]

	def EditStem(self, oldStemName, newStemName, stemDict, horizontal):
		self.storeStem(newStemName, stemDict, horizontal)
		self.f.lib[FL_tth_key]["stems"] = self.stems

	def deleteStems(self, selected, stemView):
		for name in selected:
			try:
				del self.f.lib[FL_tth_key]["stems"][name]
				del self.stems[name]
			except:
				pass
		stemView.set(self.buildStemsUIList(horizontal=stemView.isHorizontal))

	def addStem(self, name, stemDict, stemView):
		self.stems[name] = stemDict
		self.f.lib[FL_tth_key]["stems"][name] = stemDict
		stemView.box.stemsList.set(self.buildStemsUIList(horizontal=stemView.isHorizontal))
