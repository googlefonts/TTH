#coding=utf-8
from mojo.UI import *
from mojo.events import *
from vanilla import *
from AppKit import *

import tt_tables
import TTHintAsm

FL_tth_key = "com.fontlab.v2.tth"

class ZoneView(object):
	def __init__(self, controller, height, title, ID, UIZones):
		self.lock = False
		self.ID = ID
		self.controller = controller
		self.UIZones = UIZones
		self.zonesTitle = TextBox((10, height-24, -10, 14), title, sizeStyle = "small")
		self.box = Box((10, height, -10, 132))
		# put the title as a sub-widget of the zones window
		controller.w.zoneBox.__setattr__(ID + 'ZoneViewTitle', self.zonesTitle)
		# put the box as a sub-widget of the zones window
		controller.w.zoneBox.__setattr__(ID + 'ZoneViewBox', self.box)
		box = self.box
		box.zones_List = List((0, 0, -0, 100), self.UIZones,
			columnDescriptions=[{"title": "Name", "editable": True}, {"title": "Position", "editable": True},
					    {"title": "Width", "editable": True}, {"title": "Delta", "editable": True}],
			editCallback = self.UIZones_EditCallBack )
		box.buttonRemoveZone = SquareButton((0, 100, 22, 22), "-", sizeStyle = 'small', callback=self.buttonRemoveZoneCallback)
		box.editTextZoneName = EditText(    (22, 100, 160, 22), sizeStyle = "small", callback=self.editTextZoneDummyCallback)
		box.editTextZonePosition = EditText(    (182, 100, 55, 22), sizeStyle = "small", callback=self.editTextZoneIntegerCallback)
		box.editTextZoneWidth = EditText(    (237, 100, 55, 22), sizeStyle = "small", callback=self.editTextZoneIntegerCallback)
		box.editTextZoneDelta = EditText(    (292, 100, 135, 22), sizeStyle = "small", callback=self.editTextZoneDummyCallback)
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
			print "ERROR SHOULD NEVER HAPPEN in ZoneView.UIZones_EditCallBack"

		zoneDict = sender[sel]

		if 'Name' in zoneDict:
			newZoneName = zoneDict['Name']
		else:
			newZoneName = self.ID + '_' + str(sel)
			sender[sel]['Name'] = newZoneName

		if oldZoneName != newZoneName:
			print "Original zone name = ", oldZoneName, ", new zone name = ", newZoneName
			if newZoneName in self.controller.tthtm.zones:
				print "ERROR: Can't use an already existing name."
				newZoneName = oldZoneName
				sender[sel]['Name'] = newZoneName
				self.lock = False
				return
			else:
				del self.controller.tthtm.zones[oldZoneName]
		self.controller.controller.EditZone(oldZoneName, newZoneName, zoneDict, self.ID == 'top')
		self.controller.tthtm.UITopZones = self.controller.tthtm.buildUIZonesList(buildTop=True)
		self.controller.tthtm.UIBottomZones = self.controller.tthtm.buildUIZonesList(buildTop=False)
		if self.ID == 'top':
			self.UIZones = self.controller.tthtm.UITopZones
			self.box.zones_List.set(self.controller.tthtm.UITopZones)
		elif self.ID == 'bottom':
			self.UIZones = self.controller.tthtm.UIBottomZones
			self.box.zones_List.set(self.controller.tthtm.UIBottomZones)
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
		if name == '' or name in self.controller.tthtm.zones:
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
		titlebox = TextBox((10, height-24, 100, 14), title, sizeStyle = "small")
		box = Box((10, height, -10, 132))
		self.box = box
		prefix = "vertical"
		if self.isHorizontal:
			prefix = "horizontal"
		# put the title as a sub-widget of the zones window
		controller.w.stemBox.__setattr__(prefix + 'StemViewTitle', titlebox)
		# put the box as a sub-widget of the zones window
		controller.w.stemBox.__setattr__(prefix + 'StemViewBox', box)

		box.stemsList = List((0, 0, -0, 100 ), stemsList,
			columnDescriptions=[{"title": "Name", "editable": True}, {"title": "Width", "editable": True},
				{"title": "1 px", "editable": True}, {"title": "2 px", "editable": True},
				{"title": "3 px", "editable": True}, {"title": "4 px", "editable": True},
				{"title": "5 px", "editable": True}, {"title": "6 px", "editable": True}], 
			editCallback = self.stemsList_editCallback)
		box.buttonRemoveStem = SquareButton((0, 100, 22, 22), "-", sizeStyle = 'small', callback=self.buttonRemoveCallback)
		box.editTextStemName = EditText((22, 100, 128, 22), sizeStyle = "small", callback=self.editTextDummyCallback)
		box.editTextStemWidth = EditText((150, 100, 80, 22), sizeStyle = "small", callback=self.editTextWidthCallback)

		box.editTextStem1px = EditText((230, 100, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.editTextStem2px = EditText((263, 100, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.editTextStem3px = EditText((296, 100, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.editTextStem4px = EditText((329, 100, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.editTextStem5px = EditText((362, 100, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
		box.editTextStem6px = EditText((395, 100, 33, 22), sizeStyle = "small", callback=self.editTextIntegerCallback)
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
			#print("Original stem name = ", oldStemName, ", new stem name = ", newStemName)
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
		stemPitch = float(self.controller.tthtm.UPM)/value
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
		self.controller.tthtm.deleteStems(selected, self)
		self.lock = False

	def buttonAddCallback(self, sender):
		name = self.box.editTextStemName.get()
		if name == '':
			print 'enter a name before adding stem'
			return
		horizontal = self.isHorizontal
		try:
			width = int(self.box.editTextStemWidth.get())
		except:
			print 'enter a width before adding stem'
			return

		px1 = str(self.box.editTextStem1px.get())
		px2 = str(self.box.editTextStem2px.get())
		px3 = str(self.box.editTextStem3px.get())
		px4 = str(self.box.editTextStem4px.get())
		px5 = str(self.box.editTextStem5px.get())
		px6 = str(self.box.editTextStem6px.get())

		stemDict = {'horizontal': self.isHorizontal, 'width': width, 'round': {px1: 1, px2: 2, px3: 3, px4: 4, px5: 5, px6: 6} }
		self.lock = True
		self.controller.tthtm.addStem(name, stemDict, self)
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

	def __init__(self, parent, model, controller):
		self.tthtm = model
		self.controller = controller
		self.w = Sheet((1000, 450), parentWindow=parent)
		w = self.w
		w.generalBox = Box((10, 10, -10, 30))
		w.generalBox.StemSnapTitle= TextBox((10, 2, 250, 22), "Stem snap precision (/16th of pixel)", sizeStyle = "small")
		w.generalBox.AlignmentTitle= TextBox((330, 2, 250, 22), "Stop zone alignment above (ppEm)", sizeStyle = "small")
		w.generalBox.InstructionsTitle= TextBox((690, 2, 250, 22), "Do not execute instructions above (ppEm)", sizeStyle = "small")

		w.generalBox.editTextStemSnap = EditText((230, 0, 30, 17), sizeStyle = "small", callback=self.editTextStemSnapCallback)
		w.generalBox.editTextStemSnap.set(self.tthtm.stemsnap)
		w.generalBox.editTextAlignment = EditText((550, 0, 30, 17), sizeStyle = "small", callback=self.editTextAlignmentCallback)
		w.generalBox.editTextAlignment.set(self.tthtm.alignppm)
		w.generalBox.editTextInstructions = EditText((940, 0, 30, 17), sizeStyle = "small", callback=self.editTextInstructionsCallback)
		w.generalBox.editTextInstructions.set(self.tthtm.codeppm)

		w.zoneBox = Box((10, 50, 485, 350))
		self.topZoneView = ZoneView(self, 34, "Top zones", 'top', self.tthtm.UITopZones)
		self.bottomZoneView = ZoneView(self, 200, "Bottom zones", 'bottom', self.tthtm.UIBottomZones)

		w.stemBox = Box((505, 50, 485, 350))
		self.horizontalStemView	= StemView(self, 34, "Y Stems", True, self.tthtm.buildStemsUIList(horizontal=True))
		self.verticalStemView	= StemView(self, 200, "X Stems", False, self.tthtm.buildStemsUIList(horizontal=False))


		w.applyButton = Button((-130, -32, 120, 22), "Apply and Close", sizeStyle = "small", callback=self.applyButtonCallback)
		w.open()

	def applyButtonCallback(self, sender):
		self.controller.changeStemSnap(self.w.generalBox.editTextStemSnap.get())
		self.controller.changeAlignppm(self.w.generalBox.editTextAlignment.get())
		self.controller.changeCodeppm(self.w.generalBox.editTextInstructions.get())
		self.controller.resetFonts()
		self.controller.updateGlyphProgram()
		self.controller.refreshGlyph()
		self.w.close()

	def editTextStemSnapCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

		self.tthtm.f.lib[FL_tth_key]["stemsnap"] = value
		self.tthtm.stemsnap = value

	def editTextAlignmentCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

		self.tthtm.f.lib[FL_tth_key]["alignppm"] = value
		self.tthtm.alignppm = value

	def editTextInstructionsCallback(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
			sender.set(0)

		self.tthtm.f.lib[FL_tth_key]["codeppm"] = value
		self.tthtm.codeppm = value
