#coding=utf-8
from vanilla import Box, Button, CheckBox, CheckBoxListCell, EditText, List, ProgressBar, SegmentedButton, Sheet, SquareButton, TextBox
import string

from lib.fontObjects.doodleFontCompiler.ttfCompiler import TTFCompilerSettings

from models.TTHTool import uniqueInstance as tthTool
import commons
from commons import helperFunctions
import tt
from tt import asm, tables
#import Automation

class ZoneView(object):
	def __init__(self, zoneBox, height, title, ID):
		self.lock = False
		self.ID = ID
		self.zonesTitle = TextBox((10, height-24, -10, 14), title, sizeStyle = "small")
		self.box = Box((10, height, -10, 142))
		# put the title as a sub-widget of the zoneS box
		zoneBox.__setattr__(ID + 'ZoneViewTitle', self.zonesTitle)
		# put the box as a sub-widget of the zoneS box
		zoneBox.__setattr__(ID + 'ZoneViewBox', self.box)
		box = self.box
		box.zones_List = List((0, 0, -0, -22), [],
			columnDescriptions=[{"title": "Name", "editable": True}, {"title": "Position", "editable": True},
					    {"title": "Width", "editable": True}, {"title": "Delta", "editable": True}],
			editCallback = self.UIZones_EditCallBack,
			allowsMultipleSelection = False)
		box.buttonRemoveZone = SquareButton((0, -22, 22, 22), "-", sizeStyle = 'small', callback=self.buttonRemoveZoneCallback)
		box.editTextZoneName = EditText(    (22, -22, 160, 22), sizeStyle = "small")
		box.editTextZonePosition = EditText((182, -22, 55, 22), sizeStyle = "small", callback=self.editTextZoneIntegerCallback)
		box.editTextZoneWidth = EditText(   (237, -22, 55, 22), sizeStyle = "small", callback=self.editTextZoneIntegerCallback)
		box.editTextZoneDelta = EditText(   (292, -22, 135, 22), sizeStyle = "small")
		box.buttonAddZone     = SquareButton((-22, -22, 22, 22), u"↵", sizeStyle = 'small', callback=self.buttonAddZoneCallback)
		self.reset()
		self.tracker = commons.RenameTracker(z['Name'] for z in self.UIZones)

	def reset(self):
		buildTop = self.ID == 'top'
		fm = tthTool.getFontModel()
		self.UIZones = [self.uiZoneOfZone(zone, name) for name, zone in fm.zones.iteritems() if zone['top'] == buildTop]
		self.box.zones_List.setSelection([])
		self.box.zones_List.set(self.UIZones)

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

		uiZone = sender[sel]

		if 'Name' in uiZone:
			newZoneName = uiZone['Name']
		else:
			newZoneName = self.ID + '_' + str(sel)
			sender[sel]['Name'] = newZoneName

		fm = tthTool.getFontModel()
		if oldZoneName != newZoneName:
			#print "Original zone name = ", oldZoneName, ", new zone name = ", newZoneName
			if newZoneName in fm.zones:
				print "ERROR: Can't use an already existing name."
				newZoneName = oldZoneName
				sender[sel]['Name'] = newZoneName
				self.lock = False
				return
			else:
				del fm.zones[oldZoneName]
		print "OLD", self.UIZones[sel]
		print "NEW", sender[sel]
		self.UIZones[sel] = sender[sel].copy()

		# fill missing data
		if not ('Position' in uiZone): uiZone['Position'] = 0
		if not ('Width' in uiZone):    uiZone['Width'] = 0
		if not ('Delta' in uiZone):    uiZone['Delta'] = '0@0'
		
		self.tracker.rename(oldZoneName, newZoneName)
		print self.tracker
		fm.editZone(oldZoneName, newZoneName, uiZone, self.ID == 'top')
		self.lock = False

	def buttonRemoveZoneCallback(self, sender):
		UIList = self.box.zones_List
		selection = UIList.getSelection()
		UIList.setSelection([])
		selected = [UIList[i]['Name'] for i in selection]
		self.lock = True
		tthTool.getFontModel().deleteZones(selected)
		self.reset()
		self.lock = False

	def editTextZoneIntegerCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			if sender.get() != '-':
				value = 0
			else:
				value = '-'
			sender.set(value)

	def uiZoneOfZone(self, zone, name):
		c_zoneDict = { 'Name': name, 'Position': int(zone['position']), 'Width': int(zone['width']) }
		deltaString = ''
		if 'delta' in zone:
			deltas = zone['delta']
			strings = []
			keys = deltas.keys()
			keys.sort(key = lambda x: int(x))
			c_zoneDict['Delta'] = ', '.join('@'.join([str(deltas[k]), k]) for k in keys)
		else:
			c_zoneDict['Delta'] = '0@0'
		return c_zoneDict

	def buttonAddZoneCallback(self, sender):
		name = self.box.editTextZoneName.get()
		if name == '' or name in tthTool.getFontModel().zones:
			return
		position = int(self.box.editTextZonePosition.get())
		width = int(self.box.editTextZoneWidth.get())
		delta = self.box.editTextZoneDelta.get()
		deltaDict = tthTool.deltaDictFromString(delta)

		newZone = {'top': (self.ID=='top'), 'position': position, 'width': width }
		if deltaDict == {}:
			newZone['delta'] = deltaDict
		self.box.zones_List.setSelection([])
		self.lock = True
		tthTool.addZone(name, newZone, self)
		self.reset()
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
		self.titlebox = TextBox((10, height-24, 120, 14), title, sizeStyle = "small")
		self.box = Box((10, height, -10, 152))
		box = self.box
		prefix = "vertical"
		if self.isHorizontal:
			prefix = "horizontal"
		# put the title as a sub-widget of the zones window
		controller.w.stemBox.__setattr__(prefix + 'StemViewTitle', self.titlebox)
		# put the box as a sub-widget of the zones window
		controller.w.stemBox.__setattr__(prefix + 'StemViewBox', box)

		box.stemsList = List((0, 0, -0, -22), stemsList,
			columnDescriptions=[{"title": "Name", "editable": True}, {"title": "Width", "editable": True},
				{"title": "1 px", "editable": True}, {"title": "2 px", "editable": True},
				{"title": "3 px", "editable": True}, {"title": "4 px", "editable": True},
				{"title": "5 px", "editable": True}, {"title": "6 px", "editable": True}],
			editCallback = self.stemsList_editCallback,
			allowsMultipleSelection = False)
		box.buttonRemoveStem = SquareButton((0, -22, 22, 22), "-", sizeStyle = 'small', callback=self.buttonRemoveCallback)
		box.editTextStemName = EditText((22, -22, 128, 22), sizeStyle = "small")
		box.editTextStemWidth = EditText((150, -22, 80, 22), sizeStyle = "small", callback=self.editTextWidthCallback)

		box.editTextStem1px = EditText((230, -22, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.editTextStem2px = EditText((263, -22, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.editTextStem3px = EditText((296, -22, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.editTextStem4px = EditText((329, -22, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.editTextStem5px = EditText((362, -22, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.editTextStem6px = EditText((395, -22, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.buttonAddStem = SquareButton((-22, -22, 22, 22), u"↵", sizeStyle = 'small', callback=self.buttonAddCallback)

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
			self.lock = False
			return

		if oldStemName != newStemName:
			#print "Original stem name = ", oldStemName, ", new stem name = ", newStemName
			if newStemName in fm.stems:
				print "ERROR: Can't use an already existing name."
				newStemName = oldStemName
				sender[sel]['Name'] = newStemName
				self.lock = False
				return
			else:
				del fm.stems[oldStemName]
		self.UIStems[sel] = sender[sel]

		tthTool.EditStem(oldStemName, newStemName, stemDict, self.isHorizontal)
		if self.isHorizontal:
			self.box.stemsList.set(fm.buildStemsUIList(horizontal=True))
		else:
			self.box.stemsList.set(fm.buildStemsUIList(horizontal=False))
		self.lock = False

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
			stemPitch = float(fm.UPM)/roundedStem
		else:
			stemPitch = float(fm.UPM)/value
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
		tthTool.deleteStems(selected, self, self.controller.w.stemBox.AutoStemProgressBar)
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
		tthTool.addStem(name, stemDict, self)
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

class ControlValuesSheet(object):

	def __init__(self, parentWindow):
		self.lock = False
		self.oldRangeValue = None

		fm = tthTool.getFontModel()

		self.w = Sheet((505, 480), minSize=(505, 220), maxSize=(505, 1000), parentWindow = parentWindow)
		#self.automation = Automation.Automation(self, self.controller)
		w = self.w

		# GENERAL PREFERENCES
		w.generalBox = Box((10, 19, -10, -40))
		gb = w.generalBox
		gb.show(0)

		gb.StemSnapLabel     = TextBox((10, 10, 250, 22), "Stem snap precision (/16th of pixel)", sizeStyle = "small")
		gb.AlignmentLabel    = TextBox((10, 32, 250, 22), "Stop zone alignment above (ppEm)", sizeStyle = "small")
		gb.InstructionsLabel = TextBox((10, 54, 250, 22), "Do not execute instructions above (ppEm)", sizeStyle = "small")
		gb.NoStemsWhenGLabel = TextBox((10, 76, 300, 22), "Deactivate stems for grayscale and subpixel", sizeStyle = "small")

		gb.editTextStemSnap  = EditText((-40, 10, 30, 17), sizeStyle = "small", callback=self.editTextStemSnapCallback)
		gb.editTextAlignment = EditText((-40, 32, 30, 17), sizeStyle = "small", callback=self.editTextAlignmentCallback)
		gb.editTextInstructions = EditText((-40, 54, 30, 17), sizeStyle = "small", callback=self.editTextInstructionsCallback)
		gb.checkBoxDeactivateStemsWhenGrayscale = CheckBox((-40, 76, 30, 22), "", callback=self.checkBoxDeactivateStemsWhenGrayscaleCallback, value=fm.deactivateStemWhenGrayScale, sizeStyle = "small")
		gb.editTextStemSnap.set(fm.stemsnap)
		gb.editTextAlignment.set(fm.alignppm)
		gb.editTextInstructions.set(fm.codeppm)

		# ZONE EDITOR
		height = self.w.getPosSize()[3]
		w.zoneBox = Box((10, 19, -10, -40))
		self.topZoneView = ZoneView(w.zoneBox, 34, "Top zones", 'top')
		self.bottomZoneView = ZoneView(w.zoneBox, height-260, "Bottom zones", 'bottom')
		w.zoneBox.autoZoneButton = Button((-80, 382, 70, 20), "Detect", sizeStyle = "small", callback=self.autoZoneButtonCallback)

		# STEM EDITOR
		w.stemBox = Box((10, 19, -10, -40))
		sb = w.stemBox
		sb.show(0)
		self.horizontalStemView = StemView(self, 34, "Y Stems", True, [])#fm.buildStemsUIList(True))
		self.verticalStemView   = StemView(self, 220, "X Stems", False, [])#fm.buildStemsUIList(False))
		sb.autoStemButton       = Button((-80, -30, 70, 20), "Detect", sizeStyle = "small", callback=self.autoStemButtonCallback)
		sb.AutoStemProgressBar  = ProgressBar((10, 384, -90, 16), sizeStyle = "small",  maxValue=100)
		sb.AutoStemProgressBar.show(0)

		# GASP EDITOR
		w.gaspBox = Box((10, 19, -10, -40))
		gb = w.gaspBox
		gb.show(0)
		gb.gaspSettingsList = List((10, 10, -10, -32), [],
			columnDescriptions = [
			{"title": "Range",          "width": 50,  "key": "range", "editable": True},
			{"title": "Gray AntiAlias", "width": 100, "key": "GAA",   "editable": True, "cell": CheckBoxListCell()},
			{"title": "GridFit",        "width": 100, "key": "GF",    "editable": True, "cell": CheckBoxListCell()},
			{"title": "Sym. GridFit",   "width": 100, "key": "SGF",   "editable": True, "cell": CheckBoxListCell()},
			{"title": "Sym. Smoothing", "width": 100, "key": "SS",    "editable": True, "cell": CheckBoxListCell()}],
			editCallback = self.gaspSettingsList_EditCallBack,
			selectionCallback = self.gaspSettingsList_SelectionCallback)
		self.setGaspRangesListUI()

		gb.buttonRemoveRange = SquareButton((10, -32, 22, 22), "-", sizeStyle = 'small', callback=self.buttonRemoveRangeCallback)
		gb.rangeEditText = EditText((32, -32, 40, 22), sizeStyle = "small", callback=self.gaspRangeEditTextCallback)
		gb.rangeEditText.set(8)
		gb.GAA_PopUpButton = CheckBox((77, -34, 95, 22), "Gray AntiAlias", value=False, sizeStyle = "small")
		gb.GF_PopUpButton = CheckBox((173, -34, 60, 22), "GridFit", value=False, sizeStyle = "small")
		gb.SGF_PopUpButton = CheckBox((233, -34, 85, 22), "Sym. GridFit", value=False, sizeStyle = "small")
		gb.SS_PopUpButton = CheckBox((323, -34, 105, 22), "Sym. Smoothing", value=False, sizeStyle = "small")
		gb.buttonAddRange = SquareButton((-32, -32, 22, 22), u"↵", sizeStyle = 'small', callback=self.buttonAddRangeCallback)

		# SHEET TOP BUTTONS
		controlsSegmentDescriptions = [
			dict(width=50, title="Zones",   toolTip="Zones Settings"),
			dict(width=50, title="Stems",   toolTip="Stems Settings"),
			dict(width=50, title="General", toolTip="General Settings"),
			dict(width=50, title="<gasp>",  toolTip="gasp Settings")
		]

		w.controlsSegmentedButton = SegmentedButton((137, 10, 220, 18), controlsSegmentDescriptions, callback=self.controlsSegmentedButtonCallback, sizeStyle="mini")
		w.controlsSegmentedButton.set(0) # 0 ==> show zone box

		w.applyButton = Button((-140, -32, 60, 22), "Apply", sizeStyle = "small", callback=self.applyButtonCallback)
		w.closeButton = Button((-70, -32, 60, 22), "OK", sizeStyle = "small", callback=self.closeButtonCallback)

		w.bind("resize", self.sheetResizing)
		w.open()

	def sheetResizing(self, sender):
		height = self.w.getPosSize()[3]
		self.w.zoneBox.autoZoneButton.setPosSize((-80, -30, 70, 20))
		self.w.stemBox.autoStemButton.setPosSize((-80, -30, 70, 20))

		self.topZoneView.box.setPosSize((10, 34, -10, height-(height/2.0)-94))
		self.topZoneView.box.zones_List.setPosSize((0, 0, -0, -22))
		self.bottomZoneView.box.setPosSize((10, height-(height/2.0)-20, -10, height*(112/480)-50))
		self.bottomZoneView.box.zones_List.setPosSize((0, 0, -0, -22))

		self.bottomZoneView.zonesTitle.setPosSize((10, height-(height/2.0)-44, -10, 14))

		self.horizontalStemView.box.setPosSize((10, 34, -10, height-(height/2.0)-94))
		self.horizontalStemView.box.stemsList.setPosSize((0, 0, -0, -22))
		self.verticalStemView.box.setPosSize((10, height-(height/2.0)-20, -10, height*(112/480)-50))
		self.verticalStemView.box.stemsList.setPosSize((0, 0, -0, -22))
		self.verticalStemView.titlebox.setPosSize((10, height-(height/2.0)-44, -10, 14))

	def resetGeneralBox(self):
		self.w.generalBox.editTextStemSnap.set(fm.stemsnap)
		self.w.generalBox.editTextAlignment.set(fm.alignppm)
		self.w.generalBox.editTextInstructions.set(fm.codeppm)

	def resetStemBox(self):
		self.horizontalStemView.set(fm.buildStemsUIList(True))
		self.verticalStemView.set(fm.buildStemsUIList(False))

	def resetZoneBox(self):
		self.topZoneView.reset()
		self.bottomZoneView.reset()

	def checkBoxDeactivateStemsWhenGrayscaleCallback(self, sender):
		fm.setDeactivateStemWhenGrayScale(sender.get())

	def gaspSettingsList_SelectionCallback(self, sender):
		if sender.getSelection() == []:
			return
		selectedRow = sender.getSelection()[0]
		self.oldRangeValue = sender[selectedRow]['range']

	def gaspSettingsList_EditCallBack(self, sender):
		edited = sender.getEditedColumnAndRow()

		if self.lock or (sender.getSelection() == []):
			return
		self.lock = True
		fm.gasp_ranges = {}
		for rangeUI in sender.get():
			GF = rangeUI['GF'] * 1
			GAA = rangeUI['GAA'] * 2
			SGF = rangeUI['SGF'] * 4
			SS = rangeUI['SS'] * 8
			fm.gasp_ranges[str(rangeUI['range'])] = GF + GAA + SGF + SS
		self.lock = False

		if edited == (-1, -1):
			return
		self.lock = True
		key = 'range'
		rangeValue = None

		rangeValue = sender[edited[1]][key]
		try:
			sender[edited[1]][key] = int(rangeValue)
		except:
			sender[edited[1]][key] = self.oldRangeValue
		self.lock = False

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

		fm.gasp_ranges[gasp_range] = GF + GAA + SGF + SS
		self.setGaspRangesListUI()

	def buttonRemoveRangeCallback(self, sender):
		UI = self.w.gaspBox.gaspSettingsList
		selection = UI.getSelection()
		UI.setSelection([])
		selected = [UI[i]['range'] for i in selection]
		self.lock = True
		for sel in selected:
			del fm.gasp_ranges[sel]
		self.setGaspRangesListUI()
		self.lock = False

	def setGaspRangesListUI(self):
		gaspRangesListUI = []
		fm = tthTool.getFontModel()
		for gaspRange, value in fm.gasp_ranges.iteritems():
			gf  = ( value & 1 != 0 )
			gaa = ( value & 2 != 0 )
			sgf = ( value & 4 != 0 )
			ss  = ( value & 8 != 0 )
			gaspUI = {"range": str(gaspRange), "GAA": gaa, "GF": gf, "SGF": sgf, "SS": ss}
			gaspRangesListUI.append(gaspUI)
		gaspRangesListUI.sort(key=lambda x: int(x["range"]))
		self.w.gaspBox.gaspSettingsList.set(gaspRangesListUI)

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
			self.w.resize(505, 220)
		if sender.get() == 3:
			self.w.zoneBox.show(0)
			self.w.stemBox.show(0)
			self.w.generalBox.show(0)
			self.w.gaspBox.show(1)
			self.w.resize(505, 220)

	def autoZoneButtonCallback(self, sender):
		self.automation.autoZones(fm.f)

	def autoStemButtonCallback(self, sender):
		self.w.stemBox.AutoStemProgressBar.show(1)
		self.automation.autoStems(fm.f, self.w.stemBox.AutoStemProgressBar)
		self.w.stemBox.AutoStemProgressBar.show(0)

	def closeButtonCallback(self, sender):
		self.applyButtonCallback(sender)
		self.w.close()

	def applyButtonCallback(self, sender):
		pass
		###self.controller.changeStemSnap(fm.f, self.w.generalBox.editTextStemSnap.get())
		###self.controller.changeAlignppm(fm.f, self.w.generalBox.editTextAlignment.get())
		###self.controller.changeCodeppm(fm.f, self.w.generalBox.editTextInstructions.get())
		###tt_tables.writegasp(fm.f, fm.gasp_ranges)
		###self.controller.resetFont()
		###self.controller.updateGlyphProgram(self.controller.getGlyph())
		###self.controller.refreshGlyph(self.controller.getGlyph())
		###self.controller.previewWindow.setNeedsDisplay()

	def editTextStemSnapCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

		fm.f.lib[tt.FL_tth_key]["stemsnap"] = value
		fm.stemsnap = value

	def editTextAlignmentCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

		fm.f.lib[tt.FL_tth_key]["alignppm"] = value
		fm.alignppm = value

	def editTextInstructionsCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

		fm.f.lib[tt.FL_tth_key]["codeppm"] = value
		fm.codeppm = value

reload(tables)
reload(asm)
reload(commons)
#reload(Automation)
