#coding=utf-8
from mojo.UI import *
from mojo.events import *
from vanilla import *
from AppKit import *
import string
from HelperFunc import roundbase

from lib.fontObjects.doodleFontCompiler.ttfCompiler import TTFCompilerSettings

import tt_tables
import TTHintAsm
import Automation

FL_tth_key = "com.fontlab.v2.tth"


class ZoneView(object):
	def __init__(self, controller, height, title, ID, UIZones):
		self.lock = False
		self.ID = ID
		self.controller = controller
		self.UIZones = UIZones
		self.zonesTitle = TextBox((10, height-24, -10, 14), title, sizeStyle = "small")
		self.box = Box((10, height, -10, 152))
		# put the title as a sub-widget of the zones window
		controller.w.zoneBox.__setattr__(ID + 'ZoneViewTitle', self.zonesTitle)
		# put the box as a sub-widget of the zones window
		controller.w.zoneBox.__setattr__(ID + 'ZoneViewBox', self.box)
		box = self.box
		box.zones_List = List((0, 0, -0, 120), self.UIZones,
			columnDescriptions=[{"title": "Name", "editable": True}, {"title": "Position", "editable": True},
					    {"title": "Width", "editable": True}, {"title": "Delta", "editable": True}],
			editCallback = self.UIZones_EditCallBack )
		box.buttonRemoveZone = SquareButton((0, 120, 22, 22), "-", sizeStyle = 'small', callback=self.buttonRemoveZoneCallback)
		box.editTextZoneName = EditText(    (22, 120, 160, 22), sizeStyle = "small", callback=self.editTextZoneDummyCallback)
		box.editTextZonePosition = EditText(    (182, 120, 55, 22), sizeStyle = "small", callback=self.editTextZoneIntegerCallback)
		box.editTextZoneWidth = EditText(    (237, 120, 55, 22), sizeStyle = "small", callback=self.editTextZoneIntegerCallback)
		box.editTextZoneDelta = EditText(    (292, 120, 135, 22), sizeStyle = "small", callback=self.editTextZoneDummyCallback)
		box.buttonAddZone     = SquareButton((-22, 120, 22, 22), u"↵", sizeStyle = 'small', callback=self.buttonAddZoneCallback)

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
			print "ERROR SHOULD NEVER HAPPEN in ZoneView.UIZones_EditCallBack"

		zoneDict = sender[sel]

		if 'Name' in zoneDict:
			newZoneName = zoneDict['Name']
		else:
			newZoneName = self.ID + '_' + str(sel)
			sender[sel]['Name'] = newZoneName

		if oldZoneName != newZoneName:
			#print "Original zone name = ", oldZoneName, ", new zone name = ", newZoneName
			if newZoneName in self.controller.c_fontModel.zones:
				print "ERROR: Can't use an already existing name."
				newZoneName = oldZoneName
				sender[sel]['Name'] = newZoneName
				self.lock = False
				return
			else:
				del self.controller.c_fontModel.zones[oldZoneName]
		self.UIZones[sel] = sender[sel]
		self.controller.controller.EditZone(oldZoneName, newZoneName, zoneDict, self.ID == 'top')
		self.lock = False

	def buttonRemoveZoneCallback(self, sender):
		UIList = self.box.zones_List
		selection = UIList.getSelection()
		UIList.setSelection([])
		selected = [UIList[i]['Name'] for i in selection]
		self.lock = True
		self.controller.controller.deleteZones(selected, self)
		self.lock = False

	def editTextZoneDummyCallback(self, sender):
		pass

	def editTextZoneIntegerCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			if sender.get() != '-':
				value = 0
			else:
				value = '-'
			sender.set(value)

	def buttonAddZoneCallback(self, sender):
		name = self.box.editTextZoneName.get()
		if name == '' or name in self.controller.c_fontModel.zones:
			return
		position = int(self.box.editTextZonePosition.get())
		width = int(self.box.editTextZoneWidth.get())
		delta = self.box.editTextZoneDelta.get()
		deltaDict = self.controller.controller.deltaDictFromString(delta)

		newZone = {'top': (self.ID=='top'), 'position': position, 'width': width }
		if deltaDict == {}:
			newZone['delta'] = deltaDict
		self.box.zones_List.setSelection([])
		self.lock = True
		self.controller.controller.AddZone(name, newZone, self)
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
		titlebox = TextBox((10, height-24, 120, 14), title, sizeStyle = "small")
		box = Box((10, height, -10, 152))
		self.box = box
		prefix = "vertical"
		if self.isHorizontal:
			prefix = "horizontal"
		# put the title as a sub-widget of the zones window
		controller.w.stemBox.__setattr__(prefix + 'StemViewTitle', titlebox)
		# put the box as a sub-widget of the zones window
		controller.w.stemBox.__setattr__(prefix + 'StemViewBox', box)

		box.stemsList = List((0, 0, -0, 120 ), stemsList,
			columnDescriptions=[{"title": "Name", "editable": True}, {"title": "Width", "editable": True},
				{"title": "1 px", "editable": True}, {"title": "2 px", "editable": True},
				{"title": "3 px", "editable": True}, {"title": "4 px", "editable": True},
				{"title": "5 px", "editable": True}, {"title": "6 px", "editable": True}], 
			editCallback = self.stemsList_editCallback)
		box.buttonRemoveStem = SquareButton((0, 120, 22, 22), "-", sizeStyle = 'small', callback=self.buttonRemoveCallback)
		box.editTextStemName = EditText((22, 120, 128, 22), sizeStyle = "small", callback=self.editTextDummyCallback)
		box.editTextStemWidth = EditText((150, 120, 80, 22), sizeStyle = "small", callback=self.editTextWidthCallback)

		box.editTextStem1px = EditText((230, 120, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.editTextStem2px = EditText((263, 120, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.editTextStem3px = EditText((296, 120, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.editTextStem4px = EditText((329, 120, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.editTextStem5px = EditText((362, 120, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.editTextStem6px = EditText((395, 120, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.buttonAddStem = SquareButton((-22, 120, 22, 22), u"↵", sizeStyle = 'small', callback=self.buttonAddCallback)

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
			print "ERROR SHOULD NEVER HAPPEN in StemView.stemsList_EditCallBack"

		stemDict = sender[sel]

		if 'Name' in stemDict:
			newStemName = stemDict['Name']
		else:
			newStemName = self.ID + '_' + str(sel)
			sender[sel]['Name'] = newStemName

		if self.sanitizeStem(newStemName, int(sender[sel]['Width']), int(sender[sel]['1 px']), int(sender[sel]['2 px']), int(sender[sel]['3 px']), int(sender[sel]['4 px']), int(sender[sel]['5 px']), int(sender[sel]['6 px'])) == False:
			sender[sel]['Name'] = oldStemName
			sender[sel]['1 px'] = self.UIStems[sel]['1 px']
			sender[sel]['2 px'] = self.UIStems[sel]['2 px']
			sender[sel]['3 px'] = self.UIStems[sel]['3 px']
			sender[sel]['4 px'] = self.UIStems[sel]['4 px']
			sender[sel]['5 px'] = self.UIStems[sel]['5 px']
			sender[sel]['6 px'] = self.UIStems[sel]['6 px']
			return

		if oldStemName != newStemName:
			#print "Original stem name = ", oldStemName, ", new stem name = ", newStemName
			if newStemName in self.controller.controller.c_fontModel.stems:
				print "ERROR: Can't use an already existing name."
				newStemName = oldStemName
				sender[sel]['Name'] = newStemName
				self.lock = False
				return
			else:
				del self.controller.controller.c_fontModel.stems[oldStemName]
		self.UIStems[sel] = sender[sel]

		self.controller.controller.EditStem(oldStemName, newStemName, stemDict, self.isHorizontal)
		if self.isHorizontal:
			self.box.stemsList.set(self.controller.c_fontModel.buildStemsUIList(horizontal=True))
		else:
			self.box.stemsList.set(self.controller.c_fontModel.buildStemsUIList(horizontal=False))
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
		roundedStem = roundbase(value, 20)
		if roundedStem != 0:
			stemPitch = float(self.controller.controller.c_fontModel.UPM)/roundedStem
		else:
			stemPitch = float(self.controller.controller.c_fontModel.UPM)/value
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
		self.controller.w.stemBox.AutoStemProgressBar.show(1)
		self.controller.controller.deleteStems(selected, self, self.controller.w.stemBox.AutoStemProgressBar)
		self.controller.w.stemBox.AutoStemProgressBar.show(0)
		self.lock = False

	def sanitizeStem(self, name, width, px1, px2, px3, px4, px5, px6):
		try:
			width = int(width)
		except:
			print 'enter a width before adding stem'
			return False
		
		if name == '':
			print 'enter a name before adding stem'
			return False

		allowed = list(string.letters)
		allowed.extend(list(string.digits))
		allowed.extend(['_', '-', ':', ' '])
		for c in name:
			if c not in allowed:
				print 'stem name can only contain characters:', allowed
				return False

		if (int(px1) > int(px2)) or (int(px2) > int(px3)) or (int(px3) > int(px4)) or (int(px4) > int(px5)) or (int(px5) > int(px6)):
			print 'pixel jumps must be in ascending order'
			return False

		return True

	def buttonAddCallback(self, sender):
		name = self.box.editTextStemName.get()
		horizontal = self.isHorizontal
		width = self.box.editTextStemWidth.get()

		px1 = str(self.box.editTextStem1px.get())
		px2 = str(self.box.editTextStem2px.get())
		px3 = str(self.box.editTextStem3px.get())
		px4 = str(self.box.editTextStem4px.get())
		px5 = str(self.box.editTextStem5px.get())
		px6 = str(self.box.editTextStem6px.get())
		if self.sanitizeStem(name, width, px1, px2, px3, px4, px5, px6) == False:
			return

		stemDict = {'horizontal': self.isHorizontal, 'width': str(width), 'round': {px1: 1, px2: 2, px3: 3, px4: 4, px5: 5, px6: 6} }
		self.lock = True
		self.controller.controller.addStem(name, stemDict, self)
		self.box.editTextStemName.set("")
		self.box.editTextStemWidth.set("")
		self.box.editTextStem1px.set("")
		self.box.editTextStem2px.set("")
		self.box.editTextStem3px.set("")
		self.box.editTextStem4px.set("")
		self.box.editTextStem5px.set("")
		self.box.editTextStem6px.set("")
		self.lock = False



class SheetControlValues(object):

	def __init__(self, baseWindow, parent, model, controller):
		self.c_fontModel = controller.c_fontModel
		self.controller = controller
		self.baseWindow = baseWindow
		self.w = Sheet((505, 480), parentWindow=parent)
		self.automation = Automation.Automation(self, self.controller)
		w = self.w
		w.generalBox = Box((10, 19, -10, -40))
		w.generalBox.StemSnapTitle= TextBox((10, 10, 250, 22), "Stem snap precision (/16th of pixel)", sizeStyle = "small")
		w.generalBox.AlignmentTitle= TextBox((10, 32, 250, 22), "Stop zone alignment above (ppEm)", sizeStyle = "small")
		w.generalBox.InstructionsTitle= TextBox((10, 54, 250, 22), "Do not execute instructions above (ppEm)", sizeStyle = "small")

		w.generalBox.editTextStemSnap = EditText((-40, 10, 30, 17), sizeStyle = "small", callback=self.editTextStemSnapCallback)
		w.generalBox.editTextStemSnap.set(self.c_fontModel.stemsnap)
		w.generalBox.editTextAlignment = EditText((-40, 32, 30, 17), sizeStyle = "small", callback=self.editTextAlignmentCallback)
		w.generalBox.editTextAlignment.set(self.c_fontModel.alignppm)
		w.generalBox.editTextInstructions = EditText((-40, 54, 30, 17), sizeStyle = "small", callback=self.editTextInstructionsCallback)
		w.generalBox.editTextInstructions.set(self.c_fontModel.codeppm)
		w.generalBox.show(0)

		controlsSegmentDescriptions = [
			dict(width=50, title="Zones", toolTip="Zones Settings"),
			dict(width=50, title="Stems", toolTip="Stems Settings"),
			dict(width=50, title="General", toolTip="General Settings"),
			dict(width=50, title="<gasp>", toolTip="gasp Settings")
		]


		w.zoneBox = Box((10, 19, -10, -40))
		self.topZoneView = ZoneView(self, 34, "Top zones", 'top', self.c_fontModel.buildUIZonesList(buildTop=True))
		self.bottomZoneView = ZoneView(self, 220, "Bottom zones", 'bottom', self.c_fontModel.buildUIZonesList(buildTop=False))
		w.zoneBox.autoZoneButton = Button((-80, 382, 70, 20), "Detect", sizeStyle = "small", callback=self.autoZoneButtonCallback)

		w.stemBox = Box((10, 19, -10, -40))
		self.horizontalStemView	= StemView(self, 34, "Y Stems", True, self.c_fontModel.buildStemsUIList(True))
		self.verticalStemView	= StemView(self, 220, "X Stems", False, self.c_fontModel.buildStemsUIList(False))
		w.stemBox.autoStemButton = Button((-80, 382, 70, 20), "Detect", sizeStyle = "small", callback=self.autoStemButtonCallback)
		w.stemBox.AutoStemProgressBar = ProgressBar((10, 384, -90, 16), sizeStyle = "small",  maxValue=100)
		w.stemBox.AutoStemProgressBar.show(0)
		w.stemBox.show(0)

		self.gaspRangesListUI = []
		w.gaspBox = Box((10, 19, -10, -40))
		w.gaspBox.gaspSettingsList = List((10, 10, -10, -32), self.gaspRangesListUI,
			columnDescriptions=[{"title": "Range", "width": 50, "key": "range", "editable": True}, 
								{"title": "Gray AntiAlias", "key": "GAA", "editable": True, "cell": CheckBoxListCell()},
								{"title": "GridFit", "key": "GF", "editable": True, "cell": CheckBoxListCell()},
								{"title": "Sym. GridFit", "key": "SGF", "editable": True, "cell": CheckBoxListCell()},
								{"title": "Sym. Smoothing", "key": "SS", "editable": True, "cell": CheckBoxListCell()}],
			editCallback = self.gaspSettingsList_EditCallBack )

		self.setGaspRangesListUI()

		w.gaspBox.buttonRemoveRange = SquareButton((10, -32, 22, 22), "-", sizeStyle = 'small', callback=self.buttonRemoveRangeCallback)
		w.gaspBox.rangeEditText = EditText((32, -32, 30, 22), sizeStyle = "small", callback=self.gaspRangeEditTextCallback)
		w.gaspBox.rangeEditText.set(8)
		w.gaspBox.GAA_PopUpButton = CheckBox((67, -34, 90, 22), "Gray AntiAlias", value=False, sizeStyle = "small")
		w.gaspBox.GF_PopUpButton = CheckBox((163, -34, 60, 22), "GridFit", value=False, sizeStyle = "small")
		w.gaspBox.SGF_PopUpButton = CheckBox((223, -34, 80, 22), "Sym. GridFit", value=False, sizeStyle = "small")
		w.gaspBox.SS_PopUpButton = CheckBox((313, -34, 100, 22), "Sym. Smoothing", value=False, sizeStyle = "small")
		w.gaspBox.buttonAddRange = SquareButton((-32, -32, 22, 22), u"↵", sizeStyle = 'small', callback=self.buttonAddRangeCallback)
		w.gaspBox.show(0)

		w.controlsSegmentedButton = SegmentedButton((137, 10, 220, 18), controlsSegmentDescriptions, callback=self.controlsSegmentedButtonCallback, sizeStyle="mini")
		w.controlsSegmentedButton.set(0)

		w.applyButton = Button((-140, -32, 60, 22), "Apply", sizeStyle = "small", callback=self.applyButtonCallback)
		w.closeButton = Button((-70, -32, 60, 22), "OK", sizeStyle = "small", callback=self.closeButtonCallback)
		w.open()

	def resetGeneralBox(self):
		self.w.generalBox.editTextStemSnap.set(self.c_fontModel.stemsnap)
		self.w.generalBox.editTextAlignment.set(self.c_fontModel.alignppm)
		self.w.generalBox.editTextInstructions.set(self.c_fontModel.codeppm)

	def resetStemBox(self):
		self.horizontalStemView.set(self.c_fontModel.buildStemsUIList(True))
		self.verticalStemView.set(self.c_fontModel.buildStemsUIList(False))

	def resetZoneBox(self):
		self.topZoneView.set(self.c_fontModel.buildUIZonesList(buildTop=True))
		self.bottomZoneView.set(self.c_fontModel.buildUIZonesList(buildTop=False))


	def gaspSettingsList_EditCallBack(self, sender):
		self.c_fontModel.gasp_ranges = {}
		for rangeUI in sender.get():
			GF = rangeUI['GF'] * 1
			GAA = rangeUI['GAA'] * 2
			SGF = rangeUI['SGF'] * 4
			SS = rangeUI['SS'] * 4
			self.c_fontModel.gasp_ranges[str(rangeUI['range'])] = GF + GAA + SGF + SS

	def gaspRangeEditTextCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 8
			sender.set(8)

	def buttonAddRangeCallback(self, sender):
		gasp_range = str(self.w.gaspBox.rangeEditText.get())
		GF = self.w.gaspBox.GF_PopUpButton.get() * 1
		GAA = self.w.gaspBox.GAA_PopUpButton.get() * 2
		SGF = self.w.gaspBox.SGF_PopUpButton.get() * 4
		SS = self.w.gaspBox.SS_PopUpButton.get() * 8

		self.c_fontModel.gasp_ranges[gasp_range] = GF + GAA + SGF + SS
		self.setGaspRangesListUI()


	def buttonRemoveRangeCallback(self, sender):
		UI = self.w.gaspBox.gaspSettingsList
		selection = UI.getSelection()
		UI.setSelection([])
		selected = [UI[i]['range'] for i in selection]
		self.lock = True
		for sel in selected:
			del self.c_fontModel.gasp_ranges[sel]
		self.setGaspRangesListUI()
		self.lock = False

	def setGaspRangesListUI(self):
		self.gaspRangesListUI = []

		for gaspRange, value in self.c_fontModel.gasp_ranges.iteritems():
			if value == 0:
				gaspUI = {"range": str(gaspRange), "GAA": False, "GF": False, "SGF": False, "SS": False}
			elif value == 1:
				gaspUI = {"range": str(gaspRange), "GAA": False, "GF": True, "SGF": False, "SS": False}
			elif value == 2:
				gaspUI = {"range": str(gaspRange), "GAA": True, "GF": False, "SGF": False, "SS": False}
			elif value == 3:
				gaspUI = {"range": str(gaspRange), "GAA": True, "GF": True, "SGF": False, "SS": False}
			elif value == 4:
				gaspUI = {"range": str(gaspRange), "GAA": False, "GF": False, "SGF": True, "SS": False}
			elif value == 5:
				gaspUI = {"range": str(gaspRange), "GAA": False, "GF": True, "SGF": True, "SS": False}
			elif value == 6:
				gaspUI = {"range": str(gaspRange), "GAA": True, "GF": False, "SGF": True, "SS": False}
			elif value == 7:
				gaspUI = {"range": str(gaspRange), "GAA": True, "GF": True, "SGF": True, "SS": False}
			elif value == 8:
				gaspUI = {"range": str(gaspRange), "GAA": False, "GF": False, "SGF": False, "SS": True}
			elif value == 9:
				gaspUI = {"range": str(gaspRange), "GAA": False, "GF": True, "SGF": False, "SS": True}
			elif value == 10:
				gaspUI = {"range": str(gaspRange), "GAA": True, "GF": False, "SGF": False, "SS": True}
			elif value == 11:
				gaspUI = {"range": str(gaspRange), "GAA": True, "GF": True, "SGF": False, "SS": True}
			elif value == 12:
				gaspUI = {"range": str(gaspRange), "GAA": False, "GF": False, "SGF": True, "SS": True}
			elif value == 13:
				gaspUI = {"range": str(gaspRange), "GAA": False, "GF": True, "SGF": True, "SS": True}
			elif value == 14:
				gaspUI = {"range": str(gaspRange), "GAA": True, "GF": False, "SGF": True, "SS": True}
			elif value == 15:
				gaspUI = {"range": str(gaspRange), "GAA": True, "GF": True, "SGF": True, "SS": True}

			self.gaspRangesListUI.append(gaspUI)

		self.gaspRangesListUI.sort(key=lambda x: int(x["range"]))
		self.w.gaspBox.gaspSettingsList.set(self.gaspRangesListUI)

	def controlsSegmentedButtonCallback(self, sender):
		if sender.get() == 0:
			self.w.zoneBox.show(1)
			self.w.stemBox.show(0)
			self.w.generalBox.show(0)
			self.w.gaspBox.show(0)
			self.w.resize(505, 480)
		if sender.get() == 1:
			self.w.zoneBox.show(0)
			self.w.stemBox.show(1)
			self.w.generalBox.show(0)
			self.w.gaspBox.show(0)
			self.w.resize(505, 480)
		if sender.get() == 2:
			self.w.zoneBox.show(0)
			self.w.stemBox.show(0)
			self.w.generalBox.show(1)
			self.w.gaspBox.show(0)
			self.w.resize(505, 150)
		if sender.get() == 3:
			self.w.zoneBox.show(0)
			self.w.stemBox.show(0)
			self.w.generalBox.show(0)
			self.w.gaspBox.show(1)
			self.w.resize(505, 220)
			

	def autoZoneButtonCallback(self, sender):
		self.automation.autoZones(self.c_fontModel.f)

	def autoStemButtonCallback(self, sender):
		self.w.stemBox.AutoStemProgressBar.show(1)
		self.automation.autoStems(self.c_fontModel.f, self.w.stemBox.AutoStemProgressBar)
		self.w.stemBox.AutoStemProgressBar.show(0)

	def closeButtonCallback(self, sender):
		self.applyButtonCallback(sender)
		self.w.close()

	def applyButtonCallback(self, sender):
		self.controller.changeStemSnap(self.c_fontModel.f, self.w.generalBox.editTextStemSnap.get())
		self.controller.changeAlignppm(self.c_fontModel.f, self.w.generalBox.editTextAlignment.get())
		self.controller.changeCodeppm(self.c_fontModel.f, self.w.generalBox.editTextInstructions.get())
		tt_tables.writegasp(self.c_fontModel.f, self.c_fontModel.gasp_ranges)
		self.controller.resetFont()
		self.controller.updateGlyphProgram(self.controller.getGlyph())
		self.controller.refreshGlyph(self.controller.getGlyph())

	def editTextStemSnapCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

		self.c_fontModel.f.lib[FL_tth_key]["stemsnap"] = value
		self.c_fontModel.stemsnap = value

	def editTextAlignmentCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

		self.c_fontModel.f.lib[FL_tth_key]["alignppm"] = value
		self.c_fontModel.alignppm = value

	def editTextInstructionsCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

		self.c_fontModel.f.lib[FL_tth_key]["codeppm"] = value
		self.c_fontModel.codeppm = value

reload(tt_tables)
reload(TTHintAsm)
reload(Automation)
