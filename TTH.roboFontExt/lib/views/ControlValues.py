#coding=utf-8
from vanilla import Box, Button, CheckBox, CheckBoxListCell, EditText, List, ProgressBar, SegmentedButton, Sheet, SquareButton, TextBox
import string
from models.TTHTool import uniqueInstance as tthTool
from auto import zones, stems
import commons
from commons import helperFunctions
import tt

class ZoneView(object):
	def __init__(self, zoneBox, height, title, ID):
		self.uiZoneNameCopy = None
		self.lock = False
		self.ID = ID
		self.friend = None
		self.zonesTitle = TextBox((10, height-24, 150, 14), title, sizeStyle = "small")
		self.box = Box((10, height, -10, 142))
		# put the title as a sub-widget of the zoneS box
		zoneBox.__setattr__(ID + 'ZoneViewTitle', self.zonesTitle)
		# put the box as a sub-widget of the zoneS box
		zoneBox.__setattr__(ID + 'ZoneViewBox', self.box)
		box = self.box
		box.zones_List = List((0, 0, -0, -22), [],
			columnDescriptions=[{"title": "Name", "editable": True}, {"title": "Position", "editable": True},
					    {"title": "Width", "editable": True}, {"title": "Delta", "editable": True}],
			editCallback = self.UIZones_EditCallback,
			allowsMultipleSelection = False)
		box.buttonRemoveZone = SquareButton((0, -22, 22, 22), "-", sizeStyle = 'small', callback=self.buttonRemoveZoneCallback)
		box.editTextZoneName = EditText(    (22, -22, 160, 22), sizeStyle = "small")
		box.editTextZonePosition = EditText((182, -22, 55, 22), sizeStyle = "small", callback=self.editTextZoneIntegerCallback)
		box.editTextZoneWidth = EditText(   (237, -22, 55, 22), sizeStyle = "small", callback=self.editTextZoneIntegerCallback)
		box.editTextZoneDelta = EditText(   (292, -22, 135, 22), sizeStyle = "small")
		box.buttonAddZone     = SquareButton((-22, -22, 22, 22), u"↵", sizeStyle = 'small', callback=self.buttonAddZoneCallback)
		self.reset()

	def __del__(self):
		self.friend = None

	def clear(self):
		for n in self.uiZoneNameCopy:
			self.nameChangeTracker.rename(n, None)
		self.uiZoneNameCopy = []
		self.box.zones_List.set([])

	def reset(self):
		buildTop = (self.ID == 'top')
		fm = tthTool.getFontModel()
		zoneNames = fm.zones.keys()
		zoneNames.sort()
		UIZones = [self.uiZoneOfZone(fm.zones[name], name) for name in zoneNames if fm.zones[name]['top'] == buildTop]
		self.box.zones_List.setSelection([])
		self.box.zones_List.set(UIZones)
		self.uiZoneNameCopy = [z['Name'] for z in UIZones]
		self.resetTracker()

	def resetTracker(self):
		self.nameChangeTracker = commons.RenameTracker(self.uiZoneNameCopy)

	def UIZones_EditCallback(self, sender):
		if self.lock or (sender.getSelection() == []):
			return
		self.lock = True
		selection = sender.getSelection()
		sender.setSelection([])
		sel = selection[0]
		try:
			oldZoneName = self.uiZoneNameCopy[sel]
		except:
			oldZoneName = "" # probably a new zone was created
			print "ERROR SHOULD NEVER HAPPEN in ZoneView.UIZones_EditCallback"
		uiZone = sender[sel]
		if 'Name' in uiZone:
			newZoneName = uiZone['Name']
		else:
			newZoneName = self.ID + '_' + str(sel)
			uiZone['Name'] = newZoneName

		fm = tthTool.getFontModel()
		if oldZoneName != newZoneName:
			if (newZoneName == '')	or (newZoneName in self.uiZoneNameCopy) \
								or (newZoneName in self.friend.uiZoneNameCopy):
				print "ERROR: Can't use an already existing name."
				newZoneName = oldZoneName
				uiZone['Name'] = newZoneName
				self.lock = False
				return
			self.nameChangeTracker.rename(oldZoneName, newZoneName)
		self.uiZoneNameCopy[sel] = uiZone['Name']
		self.lock = False

	def buttonRemoveZoneCallback(self, sender):
		selection = self.box.zones_List.getSelection()
		self.box.zones_List.setSelection([])
		items = self.box.zones_List.get()
		selection.sort()
		self.lock = True
		for pos, sel in enumerate(selection):
			i = sel - pos
			self.nameChangeTracker.rename(items[i]['Name'], None)
			print 'deleting', i,':',self.uiZoneNameCopy[i],'=',items[i]['Name']
			self.uiZoneNameCopy.pop(i)
			items.pop(i)
		self.box.zones_List.set(items)
		self.lock = False

	def buttonAddZoneCallback(self, sender):
		name = self.box.editTextZoneName.get()
		fm = tthTool.getFontModel()
		if (name == '') or (name in self.uiZoneNameCopy) or (name in self.friend.uiZoneNameCopy):
			print "ERROR: Can't use an already existing name."
			return
		position = int(self.box.editTextZonePosition.get())
		width = int(self.box.editTextZoneWidth.get())
		delta = self.box.editTextZoneDelta.get()
		deltaDict = helperFunctions.deltaDictFromString(delta)

		newZone = {'top': (self.ID=='top'), 'position': position, 'width': width }
		if deltaDict == {}:
			newZone['delta'] = deltaDict
		self.box.zones_List.setSelection([])
		self.lock = True

		items = self.box.zones_List.get()
		items.append(self.uiZoneOfZone(newZone, name))
		self.box.zones_List.set(items)
		self.uiZoneNameCopy.append(name)

		self.box.editTextZoneName.set("")
		self.box.editTextZonePosition.set("")
		self.box.editTextZoneWidth.set("")
		self.box.editTextZoneDelta.set("")
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
		c_zoneDict = { 'Name': name, 'Position': zone['position'], 'Width': zone['width'] }
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

# ===========================================================================

class StemView(object):

	def __init__(self, stemBox, height, isHorizontal):
		self.lock = False
		self.isHorizontal = isHorizontal
		if isHorizontal:
			title = "Y Stems"
		else:
			title = "X Stems"
		self.titlebox = TextBox((10, height-24, 120, 14), title, sizeStyle = "small")
		self.box = Box((10, height, -10, 152))
		box = self.box
		prefix = "vertical"
		if self.isHorizontal:
			prefix = "horizontal"
		# put the title as a sub-widget of the zones window
		stemBox.__setattr__(prefix+'StemViewTitle', self.titlebox)
		# put the box as a sub-widget of the zones window
		stemBox.__setattr__(prefix+'StemViewBox', box)

		box.stemsList = List((0, 0, -0, -22), [],
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

		self.reset()

	def clear(self):
		for s in self.UIStems:
			self.nameChangeTracker.rename(s['Name'], None)
		self.UIStems = []
		self.box.stemsList.set([])

	def reset(self):
		fm = tthTool.getFontModel()
		if self.isHorizontal:
			fmStems = fm.horizontalStems
		else:
			fmStems = fm.verticalStems
		names = fmStems.keys()
		names.sort()
		uiStems = [self.uiStemOfStem(fmStems[name], name) for name in names]
		self.UIStems = uiStems
		self.box.stemsList.setSelection([])
		self.box.stemsList.set(uiStems)
		self.resetTracker()

	def allCurrentStemNames(self):
		return [stem['Name'] for stem in self.UIStems]

	def allStemNames(self):
		return [stem['Name'] for stem in self.box.stemsList]

	def resetTracker(self):
		self.nameChangeTracker = commons.RenameTracker(self.allStemNames())

	def editTextWidthCallback(self, sender):
		if self.lock: return
		self.lock = True
		try:
			value = int(sender.get())
		except ValueError:
			value = 1
		sender.set(value)
		roundedStem = helperFunctions.roundbase(value, 20)
		upm = float(tthTool.getFontModel().UPM)
		if roundedStem != 0:
			stemPitch = upm/roundedStem
		else:
			stemPitch = upm/value
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
			print "ERROR SHOULD NEVER HAPPEN in StemView.stemsList_EditCallback"
		uiStem = sender[sel]
		if 'Name' in uiStem:
			newStemName = uiStem['Name']
		else:
			newStemName = self.ID + '_' + str(sel)
			uiStem['Name'] = newStemName

		if not self.sanitizeStem(newStemName, uiStem):
			sender[sel] = self.UIStems[sel]
			sender[sel]['Name'] = oldStemName
			self.lock = False
			return

		allStemNames = self.allCurrentStemNames()+self.friend.allCurrentStemNames()+['']
		if oldStemName != newStemName:
			if newStemName in allStemNames:
				print "ERROR: Can't use an already existing name."
				newStemName = oldStemName
				sender[sel]['Name'] = newStemName
				self.lock = False
				return
			self.nameChangeTracker.rename(oldStemName, newStemName)
		self.UIStems[sel] = sender[sel].copy()
		self.lock = False

	def buttonRemoveCallback(self, sender):
		selection = self.box.stemsList.getSelection()
		self.box.stemsList.setSelection([])
		self.lock = True
		items = self.box.stemsList.get()
		selection.sort()
		for pos, sel in enumerate(selection):
			i = sel - pos
			self.nameChangeTracker.rename(items[i]['Name'], None)
			self.UIStems.pop(i)
			items.pop(i)
		self.box.stemsList.set(items)
		self.lock = False

	def buttonAddCallback(self, sender):
		name = self.box.editTextStemName.get()
		allStemNames = self.allStemNames()+self.friend.allStemNames()
		if name in allStemNames: return
		width = self.box.editTextStemWidth.get()
		px1 = self.box.editTextStem1px.get()
		px2 = self.box.editTextStem2px.get()
		px3 = self.box.editTextStem3px.get()
		px4 = self.box.editTextStem4px.get()
		px5 = self.box.editTextStem5px.get()
		px6 = self.box.editTextStem6px.get()
		uiStem = {'Width':width, '1 px':px1, '2 px':px2, '3 px':px3, '4 px':px4, '5 px':px5, '6 px':px6 }
		if not self.sanitizeStem(name, uiStem): return
		self.lock = True
		items = self.box.stemsList.get()
		items.append(uiStem)
		self.UIStems.append(uiStem.copy())
		self.box.stemsList.set(items)
		self.box.editTextStemName.set("")
		self.box.editTextStemWidth.set("")
		self.box.editTextStem1px.set("")
		self.box.editTextStem2px.set("")
		self.box.editTextStem3px.set("")
		self.box.editTextStem4px.set("")
		self.box.editTextStem5px.set("")
		self.box.editTextStem6px.set("")
		self.lock = False

	def uiStemOfStem(self, stem, name):
		uiStem = { 'Name': name, 'Width': int(stem['width']) }
		invDico = helperFunctions.invertedDictionary(stem['round'])
		for i in range(1,7):
			uiStem[str(i)+' px'] = helperFunctions.getOrDefault(invDico, i, '0')
		return uiStem

	def sanitizeStem(self, name, uiStem):
		try:
			width = int(uiStem['Width'])
		except:
			print 'Enter a width before adding stem'
			return False

		if name == '':
			print 'Enter a name before adding stem'
			return False

		allowed = list(string.letters)
		allowed.extend(list(string.digits))
		allowed.extend(['_', '-', ':', ' '])
		if not all(c in allowed for c in name):
			print 'stem name can only contain characters:', allowed
			return False

		px = [int(uiStem[str(i)+' px']) for i in range(1,7)]
		if not all(px[i]<=px[i+1] for i in range(5)):
			print 'pixel jumps must be in ascending order'
			return False

		return True

# ===========================================================================

class ControlValuesSheet(object):

	def __init__(self, parentWindow):
		self.lock = False
		self.oldRangeValue = 8

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

		gb.editTextStemSnap  = EditText((-40, 10, 30, 17), sizeStyle = "small", callback=self.editTextIntegerCallback)
		gb.editTextAlignment = EditText((-40, 32, 30, 17), sizeStyle = "small", callback=self.editTextIntegerCallback)
		gb.editTextInstructions = EditText((-40, 54, 30, 17), sizeStyle = "small", callback=self.editTextIntegerCallback)
		gb.checkBoxDeactivateStemsWhenGrayscale = CheckBox((-40, 76, 30, 22), "", callback=None,
				value=fm.deactivateStemWhenGrayScale, sizeStyle = "small")
		gb.editTextStemSnap.set(fm.stemsnap)
		gb.editTextAlignment.set(fm.alignppm)
		gb.editTextInstructions.set(fm.codeppm)

		# ZONE EDITOR
		height = self.w.getPosSize()[3]
		w.zoneBox = Box((10, 19, -10, -40))
		self.topZoneView = ZoneView(w.zoneBox, 34, "Top zones", 'top')
		self.bottomZoneView = ZoneView(w.zoneBox, height-260, "Bottom zones", 'bottom')
		self.topZoneView.friend = self.bottomZoneView
		self.bottomZoneView.friend = self.topZoneView
		w.zoneBox.clearButton = Button((10, 382, 60, 20), 'Clear', sizeStyle='small', callback=self.clearZones)
		w.zoneBox.autoZoneButton = Button((-80, 382, 70, 20), "Detect", sizeStyle = "small", callback=self.autoZoneButtonCallback)

		# STEM EDITOR
		w.stemBox = Box((10, 19, -10, -40))
		sb = w.stemBox
		sb.show(0)
		self.horizontalStemView = StemView(sb, 34,  True)
		self.verticalStemView   = StemView(sb, 220, False)
		self.horizontalStemView.friend = self.verticalStemView
		self.verticalStemView.friend = self.horizontalStemView
		sb.clearButton = Button((10, -30, 60, 20), 'Clear', sizeStyle='small', callback=self.clearStems)
		sb.tolLabel = TextBox((250, -26, 100, 20), 'Angle Tolerance:', sizeStyle='small', alignment='right')
		tolStr = str(fm.angleTolerance)
		sb.tol = EditText((350, -31, 40, 22), tolStr, continuous=False, callback=self.handleTolerance)
		sb.autoStemButton       = Button((-80, -30, 70, 20), "Detect", sizeStyle = "small", callback=self.autoStemButtonCallback)

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
			editCallback = self.gaspSettingsList_EditCallback,
			selectionCallback = self.gaspSettingsList_SelectionCallback,
			allowsMultipleSelection = False)
		self.resetGASPBox()

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

		# SHEET BOTTOM BUTTONS AND BAR
		w.closeButton = Button((10, -32, 60, 22), "Close", sizeStyle = "small", callback=self.closeCallback)
		#w.progressLabel  = TextBox((80, -28, 50, 16), '', sizeStyle = "small")
		w.progressBar  = ProgressBar((80, -28, -200, 16), sizeStyle = "small",  maxValue=len(fm.f))
		w.progressBar.show(0)
		w.applyButton = Button((-190, -32, 60, 22), "Apply", sizeStyle = "small", callback=self.applyButtonCallback)
		w.applyAndCloseButton = Button((-120, -32, 110, 22), "Apply and Close", sizeStyle = "small", callback=self.applyAndCloseButtonCallback)

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

	# - - - - - - - - - - - - - - - - - - - - - - - - ZONES FUNCTION

	def clearZones(self, sender):
		self.topZoneView.clear()
		self.bottomZoneView.clear()

	# - - - - - - - - - - - - - - - - - - - - - - - - STEMS FUNCTION

	def clearStems(self, sender):
		self.horizontalStemView.clear()
		self.verticalStemView.clear()

	def handleTolerance(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
		value = max(0, min(45, abs(value)))
		sender.set(value)
		fm = tthTool.getFontModel()
		fm.angleTolerance = value

	# - - - - - - - - - - - - - - - - - - - - - - - - GASP FUNCTIONS

	def gaspSettingsList_SelectionCallback(self, sender):
		selection = sender.getSelection()
		if not selection: return
		self.oldRangeValue = sender[selection[0]]['range']

	def gaspSettingsList_EditCallback(self, sender):
		if self.lock or (sender.getSelection() == []): return

		edited = sender.getEditedColumnAndRow()
		if edited == (-1, -1):
			return
		self.lock = True
		key = 'range'
		rangeUI = sender[edited[1]]
		rangeValue = rangeUI[key]
		try:
			rangeUI[key] = int(rangeValue)
		except:
			rangeUI[key] = self.oldRangeValue
		self.lock = False

	def gaspRangeEditTextCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			sender.set(8)

	def buttonAddRangeCallback(self, sender):
		gasp_range = str(self.w.gaspBox.rangeEditText.get())
		gf = self.w.gaspBox.GF_PopUpButton.get()
		gaa = self.w.gaspBox.GAA_PopUpButton.get()
		sgf = self.w.gaspBox.SGF_PopUpButton.get()
		ss = self.w.gaspBox.SS_PopUpButton.get()
		items = self.w.gaspBox.gaspSettingsList.get()
		gaspUI = {"range": gasp_range, "GAA": gaa, "GF": gf, "SGF": sgf, "SS": ss}
		items.append(gaspUI)
		items.sort(key=lambda gaspUI: int(gaspUI['range']))
		self.w.gaspBox.gaspSettingsList.set(items)

	def buttonRemoveRangeCallback(self, sender):
		UI = self.w.gaspBox.gaspSettingsList
		selection = UI.getSelection()
		self.lock = True
		UI.setSelection([])
		items = self.w.gaspBox.gaspSettingsList.get()
		items.pop(selection[0])
		self.w.gaspBox.gaspSettingsList.set(items)
		self.lock = False

	def resetGASPBox(self):
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

	# - - - - - - - - - - - - - - - - - - - - - - - - CHOOSING THE CONTROLS

	def controlsSegmentedButtonCallback(self, sender):
		b = sender.get()
		if b < 0 or b > 3: return
		boxes = [self.w.zoneBox, self.w.stemBox, self.w.generalBox, self.w.gaspBox]
		for i in range(4):
			boxes[i].show(i==b)
		if b <= 1: self.w.resize(505, 480)
		else:      self.w.resize(505, 220)

	def addUIZoneWithRename(self, uiZone, items, names, otherNames):
		orgName = uiZone['Name']
		r = 0
		while uiZone['Name'] in otherNames:
			uiZone['Name'] = orgName + '_' + str(r)
			r += 1
		try:
			i = names.index(uiZone['Name'])
			items[i] = uiZone
		except:
			items.append(uiZone)

	def autoZoneButtonCallback(self, sender):
		fm = tthTool.getFontModel()
		uiZones = zones.autoZones(fm.f)
		topItems    = self.topZoneView.box.zones_List.get()
		bottomItems = self.bottomZoneView.box.zones_List.get()
		topNames = [z['Name'] for z in topItems]
		bottomNames = [z['Name'] for z in bottomItems]
		for uiZone in uiZones:
			if uiZone['top']:
				self.addUIZoneWithRename(uiZone, topItems, topNames, bottomNames)
			else:
				self.addUIZoneWithRename(uiZone, bottomItems, bottomNames, topNames)
		self.topZoneView.box.zones_List.set(topItems)
		self.bottomZoneView.box.zones_List.set(bottomItems)
		self.topZoneView.uiZoneNameCopy = [z['Name'] for z in topItems]
		self.bottomZoneView.uiZoneNameCopy = [z['Name'] for z in bottomItems]

	def addUIStemWithRename(self, uiStem, items, names, otherNames):
		orgName = uiStem['Name']
		r = 0
		while uiStem['Name'] in otherNames:
			uiStem['Name'] = orgName + '_' + str(r)
			r += 1
		try:
			i = names.index(uiStem['Name'])
			items[i] = uiStem
		except:
			items.append(uiStem)

	def autoStemButtonCallback(self, sender):
		self.w.progressBar.set(0)
		self.w.progressBar.show(1)
		reload(stems)
		hStems, vStems = stems.autoStems(tthTool.getFontModel(), self.w.progressBar)
		self.w.progressBar.show(0)
		hItems = self.horizontalStemView.box.stemsList.get()
		vItems = self.verticalStemView.box.stemsList.get()
		hNames = [s['Name'] for s in hItems]
		vNames = [s['Name'] for s in vItems]
		for n,s in hStems.iteritems():
			self.addUIStemWithRename(self.horizontalStemView.uiStemOfStem(s,n), hItems, hNames, vNames)
		for n,s in vStems.iteritems():
			self.addUIStemWithRename(self.horizontalStemView.uiStemOfStem(s,n), vItems, vNames, hNames)
		self.horizontalStemView.UIStems = hItems
		self.verticalStemView.UIStems = vItems
		self.horizontalStemView.box.stemsList.set(hItems)
		self.verticalStemView.box.stemsList.set(vItems)

	# - - - - - - - - - - - - - - - - - - - - - - - - CLOSING FUNCTIONS

	def close(self):
		self.w.close()
		tthTool.mainPanel.curSheet = None

	def closeCallback(self, sender):
		self.close()

	def applyAndCloseButtonCallback(self, sender):
		self.applyButtonCallback(sender)
		self.close()

	def applyButtonCallback(self, sender):
		fm = tthTool.getFontModel()
		sh, sv, origS2C, origZ2C, origCVT = tt.tables.computeCVT(fm)
		# Zones
		fm.applyChangesFromUIZones(self.topZoneView.box.zones_List, self.bottomZoneView.box.zones_List)
		# Stems
		fm.applyChangesFromUIStems(self.horizontalStemView.box.stemsList, self.verticalStemView.box.stemsList)
		# General
		stemsnap = int(self.w.generalBox.editTextStemSnap.get())
		alignppm = int(self.w.generalBox.editTextAlignment.get())
		codeppm = int(self.w.generalBox.editTextInstructions.get())
		dswgs = self.w.generalBox.checkBoxDeactivateStemsWhenGrayscale.get()
		fm.setOptions(stemsnap, alignppm, codeppm, dswgs)
		# GASP
		fm.gasp_ranges = {}
		for rangeUI in self.w.gaspBox.gaspSettingsList:
			GF  = rangeUI['GF']  * 1
			GAA = rangeUI['GAA'] * 2
			SGF = rangeUI['SGF'] * 4
			SS  = rangeUI['SS']  * 8
			fm.gasp_ranges[str(rangeUI['range'])] = GF + GAA + SGF + SS
		# Finally, write the tables
		newS2C, newZ2C, newCVT = fm.writeCVTandPREP()
		tt.tables.writeFPGM(fm)
		tt.tables.writegasp(fm)
		# We rename the stems and zone at the end, *after* the tables have
		# been rewritten, so that we can use the new zone and stem CVT number
		# when we write the assembly of a glyph...
		# compute zone name changes
		zoneNameChanger = {}
		for t in [self.topZoneView.nameChangeTracker, self.bottomZoneView.nameChangeTracker]:
			zoneNameChanger.update(t.changesDict(fm.zones))
		# compute stem name changes
		stemNameChanger = {}
		names = set(fm.horizontalStems.keys() + fm.verticalStems.keys())
		for t in [self.horizontalStemView.nameChangeTracker, self.verticalStemView.nameChangeTracker]:
			stemNameChanger.update(t.changesDict(names))
		# setup progress bar
		pbMax = len(fm.f)
		if zoneNameChanger: pbMax += len(fm.f)
		if stemNameChanger: pbMax += len(fm.f)
		self.w.progressBar._nsObject.setMaxValue_(pbMax)
		self.w.progressBar.set(0)
		self.w.progressBar.show(1)
		# rename zones
		if zoneNameChanger:
			fm.renameZonesInGlyphs(zoneNameChanger, self.w.progressBar)
		self.topZoneView.resetTracker()
		self.bottomZoneView.resetTracker()
		# rename stems
		if stemNameChanger:
			fm.renameStemsInGlyphs(stemNameChanger, self.w.progressBar)
		self.horizontalStemView.resetTracker()
		self.verticalStemView.resetTracker()
		# re-compile all glyphs
		fm.compileAllGlyphs(self.w.progressBar)
		# cleanup
		self.w.progressBar.show(0)
		#self.w.progressLabel.set('')
		tthTool.hintingProgramHasChanged(fm)
		tthTool.updateDisplay()

	def editTextIntegerCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
		sender.set(value)

reload(tt)
reload(commons)
reload(zones)
