#coding=utf-8
from mojo.UI import *
from mojo.events import *
from vanilla import *
from AppKit import *

import tt_tables
import TTHintAsm

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

class ZoneView(object):
	def __init__(self, controller, height, title, ID, UIZones):
		self.lock = False
		self.ID = ID
		self.controller = controller
		self.UIZones = UIZones
		self.zonesTitle = TextBox((10, height-24, -10, 14), title, sizeStyle = "small")
		self.box = Box((10, height, 330, 132))
		# put the title as a sub-widget of the zones window
		controller.wZones.__setattr__(ID + 'ZoneViewTitle', self.zonesTitle)
		# put the box as a sub-widget of the zones window
		controller.wZones.__setattr__(ID + 'ZoneViewBox', self.box)
		box = self.box
		box.zones_List = List((0, 0, -0, 100), self.UIZones,
			columnDescriptions=[{"title": "Name", "editable": True}, {"title": "Position", "editable": True},
					    {"title": "Width", "editable": True}, {"title": "Delta", "editable": True}],
			editCallback = self.UIZones_EditCallBack )
		box.buttonRemoveZone = SquareButton((0, 100, 22, 22), "-", sizeStyle = 'small', callback=self.buttonRemoveZoneCallback)
		box.editTextZoneName = EditText(    (22, 100, 100, 22),				callback=self.editTextZoneDummyCallback)
		box.editTextZonePosition = EditText(    (122, 100, 50, 22),			callback=self.editTextZoneIntegerCallback)
		box.editTextZoneWidth = EditText(    (172, 100, 50, 22),			callback=self.editTextZoneIntegerCallback)
		box.editTextZoneDelta = EditText(    (222, 100, 78, 22),			callback=self.editTextZoneDummyCallback)
		box.buttonAddZone     = SquareButton((-22, 100, 22, 22), u"↵", sizeStyle = 'small', callback=self.buttonAddZoneCallback)

	def set(self, uiZones):
		self.UIZones = uiZones
		self.box.zones_List.setSelection([])
		self.box.zones_List.set(uiZones)

	def UIZones_EditCallBack(self, sender):
		if self.lock or (sender.getSelection() == []):
			return
		self.lock = True
		selection = sender.getSelection()
		sender.setSelection([])
		sel = selection[0]
		try:
			oldZoneName = self.UIZones[sel]['Name']
		except:
			oldZoneName = "" # probably a new zone was created
			print("ERROR SHOULD NEVER HAPPEN in ZoneView.UIZones_EditCallBack")

		zoneDict = sender[sel]

		if 'Name' in zoneDict:
			newZoneName = zoneDict['Name']
		else:
			newZoneName = self.ID + '_' + str(sel)
			sender[sel]['Name'] = newZoneName

		if oldZoneName != newZoneName:
			print("Original zone name = ", oldZoneName, ", new zone name = ", newZoneName)
			if newZoneName in self.controller.zones:
				print("ERROR: Can't use an already existing name.")
				newZoneName = oldZoneName
				sender[sel]['Name'] = newZoneName
				self.lock = False
				return
			else:
				del self.controller.zones[oldZoneName]
		self.UIZones[sel] = sender[sel]
		self.controller.EditZone(oldZoneName, newZoneName, zoneDict, self.ID == 'top')
		self.lock = False

	def buttonRemoveZoneCallback(self, sender):
		UIList = self.box.zones_List
		selection = UIList.getSelection()
		UIList.setSelection([])
		selected = [UIList[i]['Name'] for i in selection]
		self.lock = True
		self.controller.deleteZones(selected, self)
		self.lock = False

	def editTextZoneDummyCallback(self, sender):
		pass

	def editTextZoneIntegerCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def buttonAddZoneCallback(self, sender):
		name = self.box.editTextZoneName.get()
		if name == '' or name in self.controller.zones:
			return
		position = int(self.box.editTextZonePosition.get())
		width = int(self.box.editTextZoneWidth.get())
		delta = self.box.editTextZoneDelta.get()
		deltaDict = self.controller.deltaDictFromString(delta)

		newZone = {'top': (self.ID=='top'), 'position': position, 'width': width }
		if deltaDict == {}:
			newZone['delta'] = deltaDict
		self.box.zones_List.setSelection([])
		self.lock = True
		self.controller.AddZone(name, newZone, self)
		self.box.editTextZoneName.set("")
		self.box.editTextZonePosition.set("")
		self.box.editTextZoneWidth.set("")
		self.box.editTextZoneDelta.set("")
		self.lock = False

# ===========================================================================

class StemView(object):

	def __init__(self, controller, height, title, isHorizontal, stemsList):
		self.lock = False
		self.controller = controller
		self.isHorizontal = isHorizontal
		self.UIStems = stemsList
		titlebox = TextBox((10, height-24, 100, 14), title, sizeStyle = "small")
		box = Box((10, height, 430, 132))
		self.box = box
		prefix = "vertical"
		if self.isHorizontal:
			prefix = "horizontal"
		# put the title as a sub-widget of the zones window
		controller.wStems.__setattr__(prefix + 'StemViewTitle', titlebox)
		# put the box as a sub-widget of the zones window
		controller.wStems.__setattr__(prefix + 'StemViewBox', box)

		box.stemsList = List((0, 0, -0, 100 ), stemsList,
			columnDescriptions=[{"title": "Name", "editable": True}, {"title": "Width", "editable": True},
				{"title": "1 px", "editable": True}, {"title": "2 px", "editable": True},
				{"title": "3 px", "editable": True}, {"title": "4 px", "editable": True},
				{"title": "5 px", "editable": True}, {"title": "6 px", "editable": True}], 
			editCallback = self.stemsList_editCallback)
		box.buttonRemoveStem = SquareButton((0, 100, 22, 22), "-", sizeStyle = 'small', callback=self.buttonRemoveCallback)
		box.editTextStemName = EditText((22, 100, 118, 22), callback=self.editTextDummyCallback)
		box.editTextStemWidth = EditText((140, 100, 80, 22), callback=self.editTextWidthCallback)

		box.editTextStem1px = EditText((220, 100, 30, 22), callback=self.editTextIntegerCallback)
		box.editTextStem2px = EditText((250, 100, 30, 22), callback=self.editTextIntegerCallback)
		box.editTextStem3px = EditText((280, 100, 30, 22), callback=self.editTextIntegerCallback)
		box.editTextStem4px = EditText((310, 100, 30, 22), callback=self.editTextIntegerCallback)
		box.editTextStem5px = EditText((340, 100, 30, 22), callback=self.editTextIntegerCallback)
		box.editTextStem6px = EditText((370, 100, 30, 22), callback=self.editTextIntegerCallback)
		box.buttonAddStem = SquareButton((-22, 100, 22, 22), u"↵", sizeStyle = 'small', callback=self.buttonAddCallback)

	def set(self, uiStems):
		self.UIStems = uiStems
		self.box.stemsList.setSelection([])
		self.box.stemsList.set(uiStems)

	def stemsList_editCallback(self, sender):
		if self.lock or (sender.getSelection() == []):
			return
		self.lock = True
		selection = sender.getSelection()
		sender.setSelection([])
		sel = selection[0]
		try:
			oldStemName = self.UIStems[sel]['Name']
		except:
			oldStemName = "" # probably a new stem was created
			print("ERROR SHOULD NEVER HAPPEN in StemView.stemsList_EditCallBack")

		stemDict = sender[sel]

		if 'Name' in stemDict:
			newStemName = stemDict['Name']
		else:
			newStemName = self.ID + '_' + str(sel)
			sender[sel]['Name'] = newStemName

		if oldStemName != newStemName:
			print("Original stem name = ", oldStemName, ", new stem name = ", newStemName)
			if newStemName in self.controller.stems:
				print("ERROR: Can't use an already existing name.")
				newStemName = oldStemName
				sender[sel]['Name'] = newStemName
				self.lock = False
				return
			else:
				del self.controller.stems[oldStemName]
		self.UIStems[sel] = sender[sel]
		self.controller.EditStem(oldStemName, newStemName, stemDict, self.isHorizontal)
		self.lock = False

	def editTextDummyCallback(self, sender):
		pass

	def editTextWidthCallback(self, sender):
		if self.lock:
			return
		self.lock = True
		try:
			value = int(sender.get())
		except ValueError:
			value = 1
		sender.set(value)
		stemPitch = float(self.controller.TTHToolInstance.tthtm.UPM)/value
		self.box.editTextStem1px.set(str(0))
		self.box.editTextStem2px.set(str(int(2*stemPitch)))
		self.box.editTextStem3px.set(str(int(3*stemPitch)))
		self.box.editTextStem4px.set(str(int(4*stemPitch)))
		self.box.editTextStem5px.set(str(int(5*stemPitch)))
		self.box.editTextStem6px.set(str(int(6*stemPitch)))
		self.lock = False

	def editTextIntegerCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
		sender.set(value)

	def buttonRemoveCallback(self, sender):
		UI = self.box.stemsList
		selection = UI.getSelection()
		UI.setSelection([])
		selected = [UI[i]['Name'] for i in selection]
		self.lock = True
		self.controller.deleteStems(selected, self)
		self.lock = False

	def buttonAddCallback(self, sender):
		name = self.box.editTextStemName.get()
		horizontal = self.isHorizontal
		width = int(self.box.editTextStemWidth.get())

		px1 = str(self.box.editTextStem1px.get())
		px2 = str(self.box.editTextStem2px.get())
		px3 = str(self.box.editTextStem3px.get())
		px4 = str(self.box.editTextStem4px.get())
		px5 = str(self.box.editTextStem5px.get())
		px6 = str(self.box.editTextStem6px.get())

		stemDict = {'horizontal': self.isHorizontal, 'width': width, 'round': {px1: 1, px2: 2, px3: 3, px4: 4, px5: 5, px6: 6} }
		self.lock = True
		self.controller.addStem(name, stemDict, self)
		self.box.editTextStemName.set("")
		self.box.editTextStemWidth.set("")
		self.box.editTextStem1px.set("")
		self.box.editTextStem2px.set("")
		self.box.editTextStem3px.set("")
		self.box.editTextStem4px.set("")
		self.box.editTextStem5px.set("")
		self.box.editTextStem6px.set("")
		self.lock = False

# ===========================================================================

class FL_TTH_Windows(object):
	def __init__(self, f, TTHToolInstance):
		self.f = f
		self.TTHToolInstance = TTHToolInstance
		self.lock = False

		tth_lib = getOrPutDefault(self.f.lib, FL_tth_key, {})
		self.zones	= getOrPutDefault(tth_lib, "zones", {})
		self.stems	= getOrPutDefault(tth_lib, "stems", {})
		self.codeppm	= getOrPutDefault(tth_lib, "codeppm", 48)
		self.alignppm	= getOrPutDefault(tth_lib, "alignppm", 48)
		self.stemsnap	= getOrPutDefault(tth_lib, "stemsnap", 17)

		self.verticalStemsList = self.buildStemsUIList(horizontal=False)

		# The Zones window
		self.wZones = FloatingWindow((210, 30, 350, 400), "Zones", closable = False, initiallyVisible=False)
		self.topZoneView = ZoneView(self, 34, "Top zones", 'top', self.buildUIZonesList(buildTop=True))
		self.bottomZoneView = ZoneView(self, 200, "Bottom zones", 'bottom', self.buildUIZonesList(buildTop=False))
		self.wZones.ApplyButton = SquareButton((10, -32, -10, 22), "Apply", sizeStyle = 'small', 
				callback=self.ApplyButtonCallback)
		self.wZones.open()

		# The Stems window
		self.wStems = FloatingWindow((210, 30, 450, 400), "Stems", closable = False, initiallyVisible=False)
		self.horizontalStemView	= StemView(self, 34, "Horizontal (Y)", True, self.buildStemsUIList(horizontal=True))
		self.verticalStemView	= StemView(self, 200, "Vertical (X)", False, self.buildStemsUIList(horizontal=False))
		self.wStems.ApplyButton = SquareButton((10, -32, -10, 22), "Apply", sizeStyle = 'small', 
				callback=self.ApplyButtonCallback)
		self.wStems.open()

		# General Options
		self.wGeneral = FloatingWindow((210, 30, 350, 90), "General Options", closable = False, initiallyVisible=False)
		w = self.wGeneral
		w.StemSnapTitle= TextBox((10, 10, 300, 22), "Stem snap precision (/16th of pixel)", sizeStyle = "regular")
		w.AlignmentTitle= TextBox((10, 32, 300, 22), "Stop zone alignment above (ppEm)", sizeStyle = "regular")
		w.InstructionsTitle= TextBox((10, 54, 300, 22), "Do not execute instructions above (ppEm)", sizeStyle = "regular")

		w.editTextStemSnap = EditText((300, 10, 30, 22), callback=self.editTextStemSnapCallback)
		w.editTextStemSnap.set(self.stemsnap)
		w.editTextAlignment = EditText((300, 32, 30, 22), callback=self.editTextAlignmentCallback)
		w.editTextAlignment.set(self.alignppm)
		w.editTextInstructions = EditText((300, 54, 30, 22), callback=self.editTextInstructionsCallback)
		w.editTextInstructions.set(self.codeppm)
		w.open()

	def closeAll(self):
		self.wZones.close()
		self.wStems.close()
		self.wGeneral.close()

	def closeZones(self):
		self.wZones.close()

	def closeStems(self):
		self.wStems.close()

	def closeGeneral(self):
		self.wGeneral.close()

	def hideAll(self):
		self.wZones.hide()
		self.wStems.hide()
		self.wGeneral.hide()

	def hideZones(self):
		self.wZones.hide()

	def hideStems(self):
		self.wStems.hide()

	def hideGeneral(self):
		self.wGeneral.hide()

	def showAll(self):
		self.wZones.show()
		self.wStems.show()
		self.wGeneral.show()

	def showZones(self):
		self.wZones.show()

	def showStems(self):
		self.wStems.show()

	def showGeneral(self):
		self.wGeneral.show()

	def ApplyButtonCallback(self, sender):
		pass


	### Callback for General Window ###

	def editTextStemSnapCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

		self.f.lib[FL_tth_key]["stemsnap"] = value
		self.stemsnap = value

	def editTextAlignmentCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

		self.f.lib[FL_tth_key]["alignppm"] = value
		self.alignppm = value

	def editTextInstructionsCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

		self.f.lib[FL_tth_key]["codeppm"] = value
		self.codeppm = value

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

	#def stemRoundListFromDict(self, d):
	#	stemRoundList = []
	#	ppm_roundsList = d.items()
	#	ppm_roundsList.sort(cmp=lambda (k1,v1), (k2,v2): v1-v2)
	#	for i in ppm_roundsList:
	#		stemRoundList.append(i[0])
	#	return stemRoundList

	#def buildStemsDict(self, stem, name):
	#	c_stemDict = {}
	#	c_stemDict["Name"] = name
	#	c_stemDict["Width"] = stem["width"]
	#	c_roundList = self.stemRoundListFromDict(stem["round"])
	#	c_stemDict["1 px"] = c_roundList[0]
	#	c_stemDict["2 px"] = c_roundList[1]
	#	c_stemDict["3 px"] = c_roundList[2]
	#	c_stemDict["4 px"] = c_roundList[3]
	#	c_stemDict["5 px"] = c_roundList[4]
	#	c_stemDict["6 px"] = c_roundList[5]
	#
	#	return c_stemDict

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

		ttht = self.TTHToolInstance
		ttht.resetFonts() # FIXME: c'est un peu bourin
		ttht.resetglyph()
		UpdateCurrentGlyphView()

	def deleteStems(self, selected, stemView):
		for name in selected:
			try:
				del self.f.lib[FL_tth_key]["stems"][name]
				del self.stems[name]
			except:
				pass
		stemView.set(self.buildStemsUIList(horizontal=stemView.isHorizontal))
		ttht = self.TTHToolInstance
		ttht.resetFonts() # FIXME: c'est un peu bourin
		ttht.resetglyph()
		UpdateCurrentGlyphView()

	def addStem(self, name, stemDict, stemView):
		self.stems[name] = stemDict
		self.f.lib[FL_tth_key]["stems"][name] = stemDict
		stemView.box.stemsList.set(self.buildStemsUIList(horizontal=stemView.isHorizontal))

		ttht = self.TTHToolInstance
		ttht.resetFonts() # FIXME: c'est un peu bourin
		ttht.resetglyph()
		UpdateCurrentGlyphView()

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
		zoneView.UIZones.append(uiZone)

		ttht = self.TTHToolInstance
		ttht.resetFonts() # FIXME: c'est un peu bourin
		ttht.resetglyph()
		UpdateCurrentGlyphView()

	def deleteZones(self, selected, zoneView):
		for zoneName in selected:
			try:
				del self.f.lib[FL_tth_key]["zones"][zoneName]
				del self.zones[zoneName]
			except:
				pass
		zoneView.set(self.buildUIZonesList(buildTop = (zoneView.ID == 'top')))
		UpdateCurrentGlyphView()

	def EditZone(self, oldZoneName, zoneName, zoneDict, isTop):
		self.storeZone(zoneName, zoneDict, isTop)
		self.f.lib[FL_tth_key]["zones"] = self.zones
		ttht = self.TTHToolInstance
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
			dummy = ttht.readGlyphFLTTProgram(ttht.tthtm.g) # recover the correct commands list
		ttht.resetFonts() # FIXME: c'est un peu bourin
		ttht.resetglyph()
		UpdateCurrentGlyphView()

	def storeZone(self, zoneName, entry, isTop):
		if zoneName not in self.zones:
			self.zones[zoneName] = {}
		zone = self.zones[zoneName]
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
