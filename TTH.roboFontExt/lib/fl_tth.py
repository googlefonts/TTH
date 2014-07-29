#coding=utf-8
from mojo.UI import *
from mojo.events import *
from vanilla import *
from AppKit import *

import tt_tables
import TTHintAsm

FL_tth_key = "com.fontlab.v2.tth"

def invertedDictionary( dico ):
	return dict([(v,k) for (k,v) in dico.iteritems()])

#class FL_TTH():
#	def __init__(self, font):
#		if FL_tth_key in font.lib:
#			tth = font.lib[FL_tth_key]
#			self.FL_zones = tth["zones"]
#			self.FL_stems = tth["stems"]
#			self.FL_codeppm = tth["codeppm"]
#		else:
#			self.FL_zones = {}
#			self.FL_stems = {}
#			self.FL_codeppm = 0
#
#	def __call__(self):
#		print '--------------'
#		print "FL_TTH zones:"
#		print '--------------'
#		for name, flzone in self.FL_zones.iteritems():
#			print name
#			if flzone['top']:
#				print 'top zone'
#			else:
#				print 'bottom zone'
#			print 'position:', flzone['position']
#			print 'width:', flzone['width']
#			if 'delta' in flzone:
#				for ppEmSize, d in flzone['delta'].iteritems():
#					print 'delta:', d, 'at size',  ppEmSize, 'ppEm'
#			print '--------------'
#
#		print '--------------'
#		print "FL_TTH stems:"
#		print '--------------'
#		for name, flstem in self.FL_stems.iteritems():
#			print name
#			if flstem['horizontal']:
#				print 'horizontal stem'
#			else:
#				print 'vertical stem'
#			print 'width', flstem['width']
#			print 'round', 
#			ppm_roundsList = flstem['round'].items()
#			ppm_roundsList.sort(cmp=lambda (k1,v1), (k2,v2): v1-v2)
#			print int(ppm_roundsList[0][0]), int(ppm_roundsList[1][0]), int(ppm_roundsList[2][0]), int(ppm_roundsList[3][0]), int(ppm_roundsList[4][0]), int(ppm_roundsList[5][0])
#			print '--------------'
#		print 'do not execute instructions above:', self.FL_codeppm


class FL_TTH_Windows(object):
	def __init__(self, f, TTHToolInstance):
		self.f = f
		self.TTHToolInstance = TTHToolInstance
		self.lock = False

		if FL_tth_key in self.f.lib:
			tth_lib = self.f.lib[FL_tth_key]
			if "zones" in tth_lib:
				self.zones = tth_lib["zones"]
			else: 
				tth_lib["zones"] = {}
				self.zones = {}

			if "stems" in tth_lib:
				self.stems = tth_lib["stems"]
			else:
				tth_lib["stems"] = {}
				self.stems = {}

			if "codeppm" in tth_lib:
				self.codeppm = tth_lib["codeppm"]
			else:
				tth_lib["codeppm"] = 48
				self.codeppm = 48
			if "alignppm" in tth_lib:
				self.alignppm = tth_lib["alignppm"]
			else:
				tth_lib["alignppm"] = 48
				self.alignppm = 48
			if "stemsnap" in tth_lib:
				self.stemsnap = tth_lib["stemsnap"]
			else:
				tth_lib["stemsnap"] = 17
				self.stemsnap = 17

		else:
			self.f.lib[FL_tth_key] = {}
			tth_lib = self.f.lib[FL_tth_key]
			tth_lib["zones"] = {}
			tth_lib["stems"] = {}
			tth_lib["codeppm"] = 48
			tth_lib["alignppm"] = 48
			tth_lib["stemsnap"] = 17
			self.zones = {}
			self.stems = {}
			self.codeppm = 48
			self.alignppm = 48
			self.stemsnap = 17


		self.buildUIZonesList(self.zones, buildTop=True)
		self.buildUIZonesList(self.zones, buildTop=False)

		self.horizontalStemsList = self.buildHorizontalStemsList(self.stems)
		self.verticalStemsList = self.buildVerticalStemsList(self.stems)

		self.wZones = FloatingWindow((210, 30, 350, 400), "Zones", closable = False, initiallyVisible=False)

		### TOP Zones window elements###
		self.wZones.topzonesTitle= TextBox((10, 10, 70, 14), "Top", sizeStyle = "small")
		self.wZones.topbox = Box((10, 34, 330, 132))
		self.wZones.topbox.topzones_List = List((0, 0, -0, 100), self.topUIZones,
											columnDescriptions=[{"title": "Name", "editable": True}, {"title": "Position", "editable": True}, {"title": "Width", "editable": True}, {"title": "Delta", "editable": True}],
											selectionCallback=self.topUIZones_SelectionCallback,
											editCallback=self.topUIZones_EditCallBack )
		self.wZones.topbox.buttonRemoveTopZone = SquareButton((0, 100, 22, 22), "-", sizeStyle = 'small', 
			    callback=self.buttonRemoveTopZoneCallback)

		self.wZones.topbox.editTextTopZoneName = EditText((22, 100, 100, 22),
			    callback=self.editTextTopZoneNameCallback)

		self.wZones.topbox.editTextTopZonePosition = EditText((122, 100, 50, 22),
			    callback=self.editTextTopZonePositionCallback)

		self.wZones.topbox.editTextTopZoneWidth = EditText((172, 100, 50, 22),
			    callback=self.editTextTopZoneWidthCallback)

		self.wZones.topbox.editTextTopZoneDelta = EditText((222, 100, 78, 22),
			    callback=self.editTextTopZoneDeltaCallback)

		self.wZones.topbox.buttonAddTopZone = SquareButton((-22, 100, 22, 22), u"↵", sizeStyle = 'small', 
			    callback=self.buttonAddTopZoneCallback)
		#########################

		### BOTTOM Zones window elements###
		self.wZones.bottomzonesTitle= TextBox((10, 176, 70, 14), "Bottom", sizeStyle = "small")
		self.wZones.bottombox = Box((10, 200, 330, 132))
		self.wZones.bottombox.bottomzones_List = List((0, 0, -0, 100), self.bottomUIZones,
											columnDescriptions=[{"title": "Name", "editable": True}, {"title": "Position", "editable": True}, {"title": "Width", "editable": True}, {"title": "Delta", "editable": True}],
											selectionCallback=self.bottomUIZones_SelectionCallback,
											editCallback=self.bottomUIZones_EditCallBack)
		self.wZones.bottombox.buttonRemoveBottomZone = SquareButton((0, 100, 22, 22), "-", sizeStyle = 'small', 
			    callback=self.buttonRemoveBottomZoneCallback)

		self.wZones.bottombox.editTextBottomZoneName = EditText((22, 100, 100, 22),
			    callback=self.editTextBottomZoneNameCallback)

		self.wZones.bottombox.editTextBottomZonePosition = EditText((122, 100, 50, 22),
			    callback=self.editTextBottomZonePositionCallback)

		self.wZones.bottombox.editTextBottomZoneWidth = EditText((172, 100, 50, 22),
			    callback=self.editTextBottomZoneWidthCallback)

		self.wZones.bottombox.editTextBottomZoneDelta = EditText((222, 100, 78, 22),
			    callback=self.editTextBottomZoneDeltaCallback)

		self.wZones.bottombox.buttonAddBottomZone = SquareButton((-22, 100, 22, 22), u"↵", sizeStyle = 'small', 
			    callback=self.buttonAddBottomZoneCallback)

		self.wZones.open()

		#########################

		self.wStems = FloatingWindow((210, 30, 450, 400), "Stems", closable = False, initiallyVisible=False)

		### Horizontal Stems window elements###
		self.wStems.horizontalstemsTitle= TextBox((10, 10, 100, 14), "Horizontal (Y)", sizeStyle = "small")
		self.wStems.horizontalbox = Box((10, 34, 430, 132))
		self.wStems.horizontalbox.horizontalStems_List = List((0, 0, -0, 100 ), self.horizontalStemsList,
											columnDescriptions=[{"title": "Name", "editable": True}, {"title": "Width", "editable": True}, {"title": "1 px", "editable": True}, {"title": "2 px", "editable": True}, {"title": "3 px", "editable": True}, {"title": "4 px", "editable": True}, {"title": "5 px", "editable": True}, {"title": "6 px", "editable": True}], 
											selectionCallback = self.horizontalStemsList_SelectionCallback,
											editCallback = self.horizontalStemsList_EditCallback)
		self.wStems.horizontalbox.buttonRemoveHorizontalStem = SquareButton((0, 100, 22, 22), "-", sizeStyle = 'small', 
								callback=self.buttonRemoveHorizontalStemCallback)
		self.wStems.horizontalbox.editTextHorizontalStemName = EditText((22, 100, 118, 22),
			    callback=self.editTextHorizontalStemNameCallback)
		self.wStems.horizontalbox.editTextHorizontalStemWidth = EditText((140, 100, 80, 22),
			    callback=self.editTextHorizontalStemWidthCallback)

		self.wStems.horizontalbox.editTextHorizontalStem1px = EditText((220, 100, 30, 22),
			    callback=self.editTextHorizontalStem1pxCallback)
		self.wStems.horizontalbox.editTextHorizontalStem2px = EditText((250, 100, 30, 22),
			    callback=self.editTextHorizontalStem2pxCallback)
		self.wStems.horizontalbox.editTextHorizontalStem3px = EditText((280, 100, 30, 22),
			    callback=self.editTextHorizontalStem3pxCallback)
		self.wStems.horizontalbox.editTextHorizontalStem4px = EditText((310, 100, 30, 22),
			    callback=self.editTextHorizontalStem4pxCallback)
		self.wStems.horizontalbox.editTextHorizontalStem5px = EditText((340, 100, 30, 22),
			    callback=self.editTextHorizontalStem5pxCallback)
		self.wStems.horizontalbox.editTextHorizontalStem6px = EditText((370, 100, 30, 22),
			    callback=self.editTextHorizontalStem6pxCallback)

		self.wStems.horizontalbox.buttonAddHorizontalStem = SquareButton((-22, 100, 22, 22), u"↵", sizeStyle = 'small', 
			    callback=self.buttonAddHorizontalStemCallback)

		### Vertical Stems window elements###
		self.wStems.verticalstemsTitle= TextBox((10, 176, 70, 14), "Vertical (X)", sizeStyle = "small")
		self.wStems.verticalbox = Box((10, 200, 430, 132))
		self.wStems.verticalbox.verticalStems_List = List((0, 0, -0, 100 ), self.verticalStemsList,
											columnDescriptions=[{"title": "Name", "editable": True}, {"title": "Width", "editable": True}, {"title": "1 px", "editable": True}, {"title": "2 px", "editable": True}, {"title": "3 px", "editable": True}, {"title": "4 px", "editable": True}, {"title": "5 px", "editable": True}, {"title": "6 px", "editable": True}], 
											selectionCallback = self.verticalStemsList_SelectionCallback,
											editCallback = self.verticalStemsList_EditCallback)
		self.wStems.verticalbox.buttonRemoveVerticalStem = SquareButton((0, 100, 22, 22), "-", sizeStyle = 'small', 
                           					callback=self.buttonRemoveVerticalStemCallback)
		self.wStems.verticalbox.editTextVerticalStemName = EditText((22, 100, 118, 22),
                            callback=self.editTextVerticalStemNameCallback)
		self.wStems.verticalbox.editTextVerticalStemWidth = EditText((140, 100, 80, 22),
                            callback=self.editTextVerticalStemWidthCallback)

		self.wStems.verticalbox.editTextVerticalStem1px = EditText((220, 100, 30, 22),
                            callback=self.editTextVerticalStem1pxCallback)
		self.wStems.verticalbox.editTextVerticalStem2px = EditText((250, 100, 30, 22),
                            callback=self.editTextVerticalStem2pxCallback)
		self.wStems.verticalbox.editTextVerticalStem3px = EditText((280, 100, 30, 22),
                            callback=self.editTextVerticalStem3pxCallback)
		self.wStems.verticalbox.editTextVerticalStem4px = EditText((310, 100, 30, 22),
                            callback=self.editTextVerticalStem4pxCallback)
		self.wStems.verticalbox.editTextVerticalStem5px = EditText((340, 100, 30, 22),
                            callback=self.editTextVerticalStem5pxCallback)
		self.wStems.verticalbox.editTextVerticalStem6px = EditText((370, 100, 30, 22),
                            callback=self.editTextVerticalStem6pxCallback)

		self.wStems.verticalbox.buttonAddVerticalStem = SquareButton((-22, 100, 22, 22), u"↵", sizeStyle = 'small', 
                            callback=self.buttonAddVerticalStemCallback)

		self.wStems.open()
		#########################

		### General Options ###
		self.wGeneral = FloatingWindow((210, 30, 350, 90), "General Options", closable = False, initiallyVisible=False)
		self.wGeneral.StemSnapTitle= TextBox((10, 10, 300, 22), "Stem snap precision (/16th of pixel)", sizeStyle = "regular")
		self.wGeneral.AlignmentTitle= TextBox((10, 32, 300, 22), "Stop zone alignment above (ppEm)", sizeStyle = "regular")
		self.wGeneral.InstructionsTitle= TextBox((10, 54, 300, 22), "Do not execute instructions above (ppEm)", sizeStyle = "regular")

		self.wGeneral.editTextStemSnap = EditText((300, 10, 30, 22), callback=self.editTextStemSnapCallback)
		self.wGeneral.editTextStemSnap.set(self.stemsnap)
		self.wGeneral.editTextAlignment = EditText((300, 32, 30, 22), callback=self.editTextAlignmentCallback)
		self.wGeneral.editTextAlignment.set(self.alignppm)
		self.wGeneral.editTextInstructions = EditText((300, 54, 30, 22), callback=self.editTextInstructionsCallback)
		self.wGeneral.editTextInstructions.set(self.codeppm)
		self.wGeneral.open()


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
	###########################

	## Functions for Stems ###

	def stemRoundListFromDict(self, d):
		stemRoundList = []
		ppm_roundsList = d.items()
		ppm_roundsList.sort(cmp=lambda (k1,v1), (k2,v2): v1-v2)
		for i in ppm_roundsList:
			stemRoundList.append(i[0])
		return stemRoundList


	def buildStemsDict(self, stem, name):
		c_stemDict = {}
		c_stemDict["Name"] = name
		c_stemDict["Width"] = stem["width"]
		c_roundList = self.stemRoundListFromDict(stem["round"])
		c_stemDict["1 px"] = c_roundList[0]
		c_stemDict["2 px"] = c_roundList[1]
		c_stemDict["3 px"] = c_roundList[2]
		c_stemDict["4 px"] = c_roundList[3]
		c_stemDict["5 px"] = c_roundList[4]
		c_stemDict["6 px"] = c_roundList[5]

		return c_stemDict

	def buildHorizontalStemsList(self, stemsDict):
		stems_List = []
		for name, stem in stemsDict.iteritems():
			if stem['horizontal'] == True:
				c_stemDict = self.buildStemsDict(stem, name)
				stems_List.append(c_stemDict)
		return stems_List

	def buildVerticalStemsList(self, stemsDict):
		stems_List = []
		for name, stem in stemsDict.iteritems():
			if stem['horizontal'] == False:
				c_stemDict = self.buildStemsDict(stem, name)
				stems_List.append(c_stemDict)
		return stems_List

	def readHorizontalStems(self):
		horizontalStems = {}
		for name, stem in self.stems.iteritems():
			if stem['horizontal'] == True:
				horizontalStems[name] = stem

		return horizontalStems

	def readVerticalStems(self):
		verticalStems = {}
		for name, stem in self.stems.iteritems():
			if stem['horizontal'] == False:
				verticalStems[name] = stem

		return verticalStems

	def storeStem(self, stemName, entry):
		stem = self.stems[stemName]
		if 'Width' in entry:
			stem['width'] = int(entry['Width'])
		else:
			stem['width'] = 0
			entry['Width'] = 0
		#clear stems round dict
		stem['round'] = {}
		if '1 px' in entry:
			stem['round'][str(entry['1 px'])] = 1
		else:
			stem['round']['0'] = 1
			entry['1 px'] = 0
		if '2 px' in entry:
			stem['round'][str(entry['2 px'])] = 2
		else:
			stem['round']['12'] = 2
			entry['2 px'] = 12
		if '3 px' in entry:
			stem['round'][str(entry['3 px'])] = 3
		else:
			stem['round']['16'] = 3
			entry['3 px'] = 16
		if '4 px' in entry:
			stem['round'][str(entry['4 px'])] = 4
		else:
			stem['round']['24'] = 4
			entry['4 px'] = 24
		if '5 px' in entry:
			stem['round'][str(entry['5 px'])] = 5
		else:
			stem['round']['32'] = 5
			entry['5 px'] = 32
		if '6 px' in entry:
			stem['round'][str(entry['6 px'])] = 6
		else:
			stem['round']['64'] = 6
			entry['6 px'] = 64

	def storeHorizontalStem(self, stemName, entry):
		if stemName not in self.stems:
			self.stems[stemName] = {}
		self.stems[stemName]['horizontal'] = True
		self.storeStem(stemName, entry)

	def storeVerticalStem(self, stemName, entry):
		if stemName not in self.stems:
			self.stems[stemName] = {}
		self.stems[stemName]['horizontal'] = False
		self.storeStem(stemName, entry)

	def buildStemDict(self, stem, name):
		c_stemDict = {}
		c_stemDict['Name'] = name
		c_stemDict['Width'] = stem['width']
		invDico = invertedDictionary(stem['round'])
		def getKeyForVal(v):
			try:
				return invDico[v]
			except:
				return '0'
		for i in range(1,7):
			c_stemDict[str(i)+' px'] = getKeyForVal(i)
		
		return c_stemDict


	def buildHorizontalStemsList(self, stemsDict):
		stems_List = []
		for name, stem in stemsDict.iteritems():
			if stem['horizontal'] == True:
				c_stemDict = self.buildStemDict(stem, name)
				stems_List.append(c_stemDict)
		return stems_List

	def buildVerticalStemsList(self, stemsDict):
		stems_List = []
		for name, stem in stemsDict.iteritems():
			if stem['horizontal'] == False:
				c_stemDict = self.buildStemDict(stem, name)
				stems_List.append(c_stemDict)
		return stems_List
			

	########################

	### Horizontal Stems Callback ###

	def horizontalStemsList_SelectionCallback(self, sender):
		self.selectedHorizontalStems = []
		if len(sender.getSelection()) != 0:
			for i in range(len(sender.getSelection())):
				selectedStem = self.horizontalStemsList[sender.getSelection()[i]]
				self.selectedHorizontalStems.append(selectedStem)

	def horizontalStemsList_EditCallback(self, sender):
		stemsList = sender.get()
		self.stems = self.readVerticalStems()

		for entry in stemsList:
			if 'Name' in entry:
				stemName = entry['Name']
			else:
				stemName = 'Y' + '_' + str(len(stemsList))
				entry['Name'] = stemName

			self.storeHorizontalStem(stemName, entry)

		self.horizontalStemsList = self.buildHorizontalStemsList(self.readHorizontalStems())

		self.f.lib[FL_tth_key]["stems"] = self.stems

	def buttonRemoveHorizontalStemCallback(self, sender):
		try:
			for stem in self.selectedHorizontalStems:
				del self.f.lib[FL_tth_key]["stems"][stem['Name']]
				del self.stems[stem['Name']]
		except:
			pass
		self.horizontalStemsList = self.buildHorizontalStemsList(self.readHorizontalStems())
		self.wStems.horizontalbox.horizontalStems_List.set(self.horizontalStemsList)

	def editTextHorizontalStemNameCallback(self, sender):
		sender.get()

	def editTextHorizontalStemWidthCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def editTextHorizontalStem1pxCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def editTextHorizontalStem2pxCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def editTextHorizontalStem3pxCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def editTextHorizontalStem4pxCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def editTextHorizontalStem5pxCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def editTextHorizontalStem6pxCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def buttonAddHorizontalStemCallback(self, sender):
		name = self.wStems.horizontalbox.editTextHorizontalStemName.get()
		horizontal = True
		width = int(self.wStems.horizontalbox.editTextHorizontalStemWidth.get())
		px1 = str(self.wStems.horizontalbox.editTextHorizontalStem1px.get())
		px2 = str(self.wStems.horizontalbox.editTextHorizontalStem2px.get())
		px3 = str(self.wStems.horizontalbox.editTextHorizontalStem3px.get())
		px4 = str(self.wStems.horizontalbox.editTextHorizontalStem4px.get())
		px5 = str(self.wStems.horizontalbox.editTextHorizontalStem5px.get())
		px6 = str(self.wStems.horizontalbox.editTextHorizontalStem6px.get())
		
		self.stems[name] = {'horizontal': horizontal, 'width': width, 'round': {px1: 1, px2: 2, px3: 3, px4: 4, px5: 5, px6: 6} }
		self.f.lib[FL_tth_key]["stems"][name] = {'horizontal': horizontal, 'width': width, 'round': {px1: 1, px2: 2, px3: 3, px4: 4, px5: 5, px6: 6} }
		
		self.horizontalStemsList = self.buildHorizontalStemsList(self.readHorizontalStems())
		self.wStems.horizontalbox.horizontalStems_List.set(self.horizontalStemsList)


	########################

	### Vertical Stems Callback ###

	def verticalStemsList_SelectionCallback(self, sender):
		self.selectedVerticalStems = []
		if len(sender.getSelection()) != 0:
			for i in range(len(sender.getSelection())):
				selectedStem = self.verticalStemsList[sender.getSelection()[i]]
				self.selectedVerticalStems.append(selectedStem)

	def verticalStemsList_EditCallback(self, sender):
		stemsList = sender.get()
		self.stems = self.readHorizontalStems()

		for entry in stemsList:
			if 'Name' in entry:
				stemName = entry['Name']
			else:
				stemName = 'X' + '_' + str(len(stemsList))
				entry['Name'] = stemName

			self.storeVerticalStem(stemName, entry)

		self.verticalStemsList = self.buildVerticalStemsList(self.readVerticalStems())

		self.f.lib[FL_tth_key]["stems"] = self.stems


	def buttonRemoveVerticalStemCallback(self, sender):
		try:
			for stem in self.selectedVerticalStems:
				del self.f.lib[FL_tth_key]["stems"][stem['Name']]
				del self.stems[stem['Name']]
		except:
			pass
		self.verticalStemsList = self.buildVerticalStemsList(self.readVerticalStems())
		self.wStems.verticalbox.verticalStems_List.set(self.verticalStemsList)

	def editTextVerticalStemNameCallback(self, sender):
		sender.get()

	def editTextVerticalStemWidthCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def editTextVerticalStem1pxCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def editTextVerticalStem2pxCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def editTextVerticalStem3pxCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def editTextVerticalStem4pxCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def editTextVerticalStem5pxCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def editTextVerticalStem6pxCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def buttonAddVerticalStemCallback(self, sender):
		name = self.wStems.verticalbox.editTextVerticalStemName.get()
		horizontal = False
		width = int(self.wStems.verticalbox.editTextVerticalStemWidth.get())
		px1 = str(self.wStems.verticalbox.editTextVerticalStem1px.get())
		px2 = str(self.wStems.verticalbox.editTextVerticalStem2px.get())
		px3 = str(self.wStems.verticalbox.editTextVerticalStem3px.get())
		px4 = str(self.wStems.verticalbox.editTextVerticalStem4px.get())
		px5 = str(self.wStems.verticalbox.editTextVerticalStem5px.get())
		px6 = str(self.wStems.verticalbox.editTextVerticalStem6px.get())
		
		self.stems[name] = {'horizontal': horizontal, 'width': width, 'round': {px1: 1, px2: 2, px3: 3, px4: 4, px5: 5, px6: 6} }
		self.f.lib[FL_tth_key]["stems"][name] = {'horizontal': horizontal, 'width': width, 'round': {px1: 1, px2: 2, px3: 3, px4: 4, px5: 5, px6: 6} }
		
		self.verticalStemsList = self.buildVerticalStemsList(self.readVerticalStems())
		self.wStems.verticalbox.verticalStems_List.set(self.verticalStemsList)

	########################


	## Functions for Zones ###

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

	def storeZone(self, zoneName, entry):
		zone = self.zones[zoneName]
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

	def storeTopZone(self, zoneName, entry):
		if zoneName not in self.zones:
			self.zones[zoneName] = {}
		self.zones[zoneName]['top'] = True
		self.storeZone(zoneName, entry)

	def storeBottomZone(self, zoneName, entry):
		if zoneName not in self.zones:
			self.zones[zoneName] = {}
		self.zones[zoneName]['top'] = False
		self.storeZone(zoneName, entry)

	def clearBottomZones(self):
		self.zones = dict((k,v) for k,v in self.zones.iteritems() if v['top'])

	def clearTopZones(self):
		self.zones = dict((k,v) for k,v in self.zones.iteritems() if not v['top'])

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


	def buildUIZonesList(self, zonesDict, buildTop):
		zones_List = []
		for name, zone in zonesDict.iteritems():
			if zone['top'] == buildTop:
				c_zoneDict = self.buildUIZoneDict(zone, name)
				zones_List.append(c_zoneDict)
		if buildTop:
			self.topUIZones = zones_List
		else:
			self.bottomUIZones = zones_List

	#########################

	## TOP Zones CallBacks###

	def topUIZones_SelectionCallback(self, sender):
		self.selectedTopZones = []
		if len(sender.getSelection()) != 0:
			for i in range(len(sender.getSelection())):
				selectedZone = self.topUIZones[sender.getSelection()[i]]
				self.selectedTopZones.append(selectedZone)


	def topUIZones_EditCallBack(self, sender):
		if self.lock:
			return
		self.lock = True
		zonesList = sender.get()
		sel = sender.getSelection()[0]
		try:
			oldZoneName = self.topUIZones[sel]['Name']
		except:
			oldZoneName = "" # probably a new zone was created
			print("ERROR SHOULD NEVER HAPPEN in fl_tth.topUIZones_EditCallBack")
		
		zoneDict = zonesList[sel]

		if 'Name' in zoneDict:
			zoneName = zoneDict['Name']
		else:
			zoneName = 'Top' + '_' + str(entryIndex)
			zoneDict['Name'] = zoneName

		print("Original zone name = ", oldZoneName, ", new zone name = ", zoneName)
		if oldZoneName != zoneName:
			if zoneName in self.zones:
				print("ERROR: Can't use an already existing name.")
				zoneName = oldZoneName
				zoneDict['Name'] = zoneName
				self.lock = False
				return
			else:
				del self.zones[oldZoneName]
		self.storeTopZone(zoneName, zoneDict)
		self.topUIZones[sel] = self.buildUIZoneDict(self.zones[zoneName], zoneName)

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
			dummy = ttht.readGlyphFLTTProgram(ttht.g) # recover the correct commands list

		ttht.resetFonts() # FIXME: c'est un peu bourin
		ttht.resetglyph()
		UpdateCurrentGlyphView()
		self.lock = False


	def buttonRemoveTopZoneCallback(self, sender):
		try:
			for zone in self.selectedTopZones:
				del self.f.lib[FL_tth_key]["zones"][zone['Name']]
				del self.zones[zone['Name']]
		except:
			pass
		self.buildUIZonesList(self.zones, buildTop=True)
		self.wZones.topbox.topzones_List.set(self.topUIZones)

	def editTextTopZoneNameCallback(self, sender):
		sender.get()

	def editTextTopZonePositionCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def editTextTopZoneWidthCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def editTextTopZoneDeltaCallback(self, sender):
		sender.get()

	def buttonAddTopZoneCallback(self, sender):
		try:
			name = self.wZones.topbox.editTextTopZoneName.get()
			top = True
			position = int(self.wZones.topbox.editTextTopZonePosition.get())
			width = int(self.wZones.topbox.editTextTopZoneWidth.get())
			delta = self.wZones.topbox.editTextTopZoneDelta.get()
			deltaDict = self.deltaDictFromString(delta)
			if deltaDict == {}:
				self.zones[name] = {'top': top, 'position': position, 'width': width }
				self.f.lib[FL_tth_key]["zones"][name] = {'top': top, 'position': position, 'width': width }
			else:
				self.zones[name] = {'top': top, 'position': position, 'width': width, 'delta': deltaDict }
				self.f.lib[FL_tth_key]["zones"][name] = {'top': top, 'position': position, 'width': width, 'delta': deltaDict }

			self.buildUIZonesList(self.zones, buildTop=True)
			self.wZones.topbox.topzones_List.set(self.topUIZones)
		except:
			pass


	##############################

	## BOTTOM Zones CallBacks###
	def bottomUIZones_SelectionCallback(self, sender):
		self.selectedBottomZones = []
		if len(sender.getSelection()) != 0:
			for i in range(len(sender.getSelection())):
				selectedZone = self.bottomUIZones[sender.getSelection()[i]]
				self.selectedBottomZones.append(selectedZone)

	def bottomUIZones_EditCallBack(self, sender):
		zonesList = sender.get()
		self.clearBottomZones()

		for entry in zonesList:
			if 'Name' in entry:
				zoneName = entry['Name']
			else:
				zoneName = 'Top' + '_' + str(len(zonesList))
				entry['Name'] = zoneName
			self.storeBottomZone(zoneName, entry)

		self.buildUIZonesList(self.zones, buildTop=False)

		self.f.lib[FL_tth_key]["zones"] = self.zones
		UpdateCurrentGlyphView()

	def buttonRemoveBottomZoneCallback(self, sender):
		try:
			for zone in self.selectedBottomZones:
				del self.f.lib[FL_tth_key]["zones"][zone['Name']]
				del self.zones[zone['Name']]
		except:
			pass
		self.buildUIZonesList(self.zones, buildTop=False)
		self.wZones.bottombox.bottomzones_List.set(self.bottomUIZones)

	def editTextBottomZoneNameCallback(self, sender):
		sender.get()

	def editTextBottomZonePositionCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def editTextBottomZoneWidthCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

	def editTextBottomZoneDeltaCallback(self, sender):
		sender.get()

	def buttonAddBottomZoneCallback(self, sender):
		try:
			name = self.wZones.bottombox.editTextBottomZoneName.get()
			top = False
			position = int(self.wZones.bottombox.editTextBottomZonePosition.get())
			width = int(self.wZones.bottombox.editTextBottomZoneWidth.get())
			delta = self.wZones.bottombox.editTextBottomZoneDelta.get()
			deltaDict = self.deltaDictFromString(delta)
			if deltaDict == {}:
				self.zones[name] = {'top': top, 'position': position, 'width': width }
				self.f.lib[FL_tth_key]["zones"][name] = {'top': top, 'position': position, 'width': width }
			else:
				self.zones[name] = {'top': top, 'position': position, 'width': width, 'delta': deltaDict }
				self.f.lib[FL_tth_key]["zones"][name] = {'top': top, 'position': position, 'width': width, 'delta': deltaDict }

			self.buildUIZonesList(self.zones, buildTop=False)
			self.wZones.bottombox.bottomzones_List.set(self.bottomUIZones)
		except:
			pass
	##############################
