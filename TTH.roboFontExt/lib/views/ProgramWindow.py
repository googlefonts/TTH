from mojo.extensions import getExtensionDefault
from vanilla import FloatingWindow, List, CheckBoxListCell, SliderListCell, PopUpButtonListCell
from AppKit import NSLeftMouseUpMask, NSObject, NSCell, NSPopUpButtonCell, NSString, NSAttributedString, NSComboBoxCell, NSMiniControlSize, NSColor
from models.TTHTool import uniqueInstance as tthTool
from commons import helperFunctions as HF
from views import TTHWindow, tableDelegate

DefaultKeyStub = "com.sansplomb.TTH."

defaultKeyProgramWindowPosSize = DefaultKeyStub + "programWindowPosSize"
defaultKeyProgramWindowVisibility = DefaultKeyStub + "programWindowVisibility"

commandKeys = ['code', 'point', 'point1', 'point2', 'align', 'stem', 'round', 'zone', 'ppm1', 'ppm2', 'mono', 'gray', 'index', 'delta', 'active']
alignNameToCode = {'Do Not Align to Grid': '', 'Closest Pixel Edge': 'round', 'Left/Bottom Edge': 'left', 'Right/Top Edge': 'right', 'Center of Pixel': 'center', 'Double Grid': 'double'}
alignCodeToName = HF.invertedDictionary(alignNameToCode)

PPMSizesList = [str(i) for i in range(8, 73)]

def stringOfBool(b):
	if b: return 'true'
	else: return 'false'


class ProgramWindow(TTHWindow):
	def __init__(self):
		super(ProgramWindow, self).__init__(defaultKeyProgramWindowPosSize, defaultKeyProgramWindowVisibility)
		self.lock = False

		ps = getExtensionDefault(defaultKeyProgramWindowPosSize, fallback=(10, -300, -10, 300))
		win = FloatingWindow(ps, "Program", minSize=(600, 80))

		sliderCell = SliderListCell(-8, 8)
		sliderCell.setAllowsTickMarkValuesOnly_(True)
		sliderCell.setNumberOfTickMarks_(17)
		sliderCell.setContinuous_(False)
		sliderCell.sendActionOn_(NSLeftMouseUpMask)

		checkBox = CheckBoxListCell()

		comboBoxCellPPM1 = self.ComboBoxListCell(PPMSizesList)
		comboBoxCellPPM2 = self.ComboBoxListCell(PPMSizesList)

		popUpCellStems = PopUpButtonListCell([])
		popUpCellAlign = PopUpButtonListCell([])

		popUpCellZones = PopUpButtonListCell([])

		columnDescriptions = [
			{"title": "index",  "width":  30, "editable": False},
			{"title": "active", "width":  35, "editable": True, "cell":checkBox},
			{"title": "code",   "width": 100, "editable": False},
			{"title": "point",  "width": 100, "editable": False},
			{"title": "point1", "width": 100, "editable": False},
			{"title": "point2", "width": 100, "editable": False},
			{"title": "align",  "width": 170, "editable": True, "cell": popUpCellAlign, "binding": "selectedValue"},
			{"title": "round",  "width":  35, "editable": True, "cell":checkBox},
			{"title": "stem",   "width": 100, "editable": True, "cell": popUpCellStems, "binding": "selectedValue"},
			#{"title": "stem",   "width": 100, "editable": False},
			{"title": "zone",   "width": 100, "editable": True, "cell": popUpCellZones, "binding": "selectedValue"},
			{"title": "delta",  "width": 120, "editable": True, "cell":sliderCell},
			{"title": "ppm1",   "width":  50, "editable": True, "cell": comboBoxCellPPM1},
			{"title": "ppm2",   "width":  50, "editable": True, "cell": comboBoxCellPPM2},
			{"title": "mono",   "width":  35, "editable": True, "cell":checkBox},
			{"title": "gray",   "width":  35, "editable": True, "cell":checkBox}
			]
		win.programList = List((0, 0, -0, -0), [],
					columnDescriptions=columnDescriptions,
					allowsMultipleSelection=False,
					enableDelete=False,
					showColumnTitles=True,
					editCallback = self.editCallback)
		tableView = win.programList.getNSTableView()
		self.delegate = tableDelegate.ProgramPanelTableDelegate.alloc().initWithMaster(self)
		tableView.setDelegate_(self.delegate)
		self.window = win

		# - - - - - - - - - - - NSableViewDelegate stuff
		self.dummyCell = NSCell.alloc().init()
		self.dummyCell.setImage_(None)

		self.refreshFromFontModel()

		self.dummyPopup = PopUpButtonListCell([])
		self.dummyPopup.setTransparent_(True)
		self.dummyPopup.setEnabled_(False)
		self.dummyPopup.setMenu_(None)

		self.dummyCombo = self.ComboBoxListCell(['N/A'])
		self.dummyCombo.setBackgroundColor_(NSColor.grayColor())
		self.dummyCombo.setEnabled_(False)


	def refreshFromFontModel(self):
		fm = tthTool.getFontModel()
		self.horizontalStemsList = ['None'] + fm.horizontalStems.keys()
		self.verticalStemsList   = ['None'] + fm.verticalStems.keys()
		self.zonesList = ['None'] + fm.zones.keys()
		self.topZones = list(zoneName for zoneName, zoneDict in fm.zones.iteritems() if zoneDict['top'] == True)
		self.bottomZones = list(zoneName for zoneName, zoneDict in fm.zones.iteritems() if zoneDict['top'] == False)

	def modifyContent(self, cmd, uiCmd):
		cmd.set('active', stringOfBool(uiCmd['active']))
		code = cmd.get('code')
		# Delta commands
		if 'delta' in code:
			deltaUI = int(uiCmd['delta'])
			delta   = int(cmd.get('delta'))
			if deltaUI != delta and deltaUI != 0:
				cmd.set('delta', str(deltaUI))
			for key in ['mono', 'gray']:
				cmd.set(key, stringOfBool(uiCmd[key]))
			cmd.set('ppm1', str(uiCmd['ppm1']))
			cmd.set('ppm2', str(uiCmd['ppm2']))
		# Single and Double Links
		if ('single' in code) or ('double' in code):
			if uiCmd['round']:
				cmd.set('round', 'true')
				HF.delCommandAttrib(cmd, 'stem')
				HF.delCommandAttrib(cmd, 'align')
			else:
				HF.delCommandAttrib(cmd, 'round')
				if 'stem' in uiCmd:
					if uiCmd['stem'] not in ['None', '']:
						cmd.set('stem', uiCmd['stem'])
					else:
						HF.delCommandAttrib(cmd, 'stem')
						alignCode = alignNameToCode.get(uiCmd['align'], '')
						if alignCode == '':
							HF.delCommandAttrib(cmd, 'align')
						else:
							cmd.set('align', alignCode)
		# Interpolate
		if 'interpolate' in code:
			alignCode = alignNameToCode.get(uiCmd['align'], '')
			if alignCode == '':
				HF.delCommandAttrib(cmd, 'align')
			else:
				cmd.set('align', alignCode)
		# Align
		if code in ['alignt', 'alignb', 'alignv']:
			zoneCode = uiCmd['zone']
			if zoneCode == 'None':
				HF.delCommandAttrib(cmd, 'zone')
				cmd.set('code', 'alignv')
				cmd.set('align', 'round')
			else:
				cmd.set('zone', zoneCode)
				HF.delCommandAttrib(cmd, 'align')
				if uiCmd['zone'] in self.topZones:
					cmd.set('code', 'alignt')
				else:
					cmd.set('code', 'alignb')
		# Align H
		if code == 'alignh':
			alignCode = alignNameToCode.get(uiCmd['align'], '')
			if alignCode != '':
				cmd.set('align', alignCode)


	def editCallback(self, sender):
		selectList = sender.getSelection()
		if self.lock or (selectList == []):
			return
		self.lock = True
		assert len(selectList) == 1
		selectedIdx = selectList[0]
		gm, fm = tthTool.getGlyphAndFontModel()
		gm.prepareUndo('Edit Program')
		uiCmd = sender.get()[selectedIdx]
		cmdIdx = uiCmd['index']
		cmd = gm.sortedHintingCommands[cmdIdx]
		self.modifyContent(cmd, uiCmd)
		gm.updateGlyphProgram(fm)
		gm.performUndo()
		self.lock = False

	def updateProgramList(self):
		gm = tthTool.getGlyphModel()
		if gm is None:
			self.window.programList.set([])
			return
		self.refreshFromFontModel()
		uiCommands =  [dict(c.attrib) for c in gm.sortedHintingCommands]
		for i, c in enumerate(uiCommands):
			c['index'] = i
			if 'single' in c['code'] or 'double' in c['code']:
				if not 'stem' in c:
					c['stem'] = 'None'
			for key in commandKeys:
				if key not in c:
					c[key] = ''
			for key in ['round', 'active', 'mono', 'gray']:
				c[key] = (c[key] == 'true')

			alignName = alignCodeToName.get(c['align'], None)
			if alignName != None:
				c['align'] = alignName

			if c['code'] == 'alignv':
				c['zone'] = 'None'


		self.window.programList.set(uiCommands)

# - - - - - - - - - - - - - - - - - - - - NSableViewDelegate stuff

	def tableView_dataCellForTableColumn_row_(self, tableView, tableColumn, row):
		if tableColumn is None: return None
		cell = tableColumn.dataCell()
		if self.window is None:
			return cell
		if (row < 0) or (row >= len(self.window.programList)):
			return cell
		uiCmd   = self.window.programList[row]
		uiCode  = uiCmd['code']
		colID = tableColumn.identifier()
		if colID in ['delta', 'mono', 'gray']:
			if 'delta' not in uiCode:
				return self.dummyCell
		elif colID == 'round':
			if not('single' in uiCode or 'double' in uiCode):
				return self.dummyCell
		elif colID == 'stem':
			if not ('single' in uiCode or 'double' in uiCode):
				return self.dummyPopup
			else:
				cell.removeAllItems()
				if not uiCmd['round']:
					if uiCode[-1] == 'h':
						cell.addItemsWithTitles_(self.verticalStemsList)
					else:
						cell.addItemsWithTitles_(self.horizontalStemsList)
				else:
					return self.dummyPopup
		elif colID == 'align':
			if (not ('single' in uiCode or 'double' in uiCode or 'interpolate' in uiCode or uiCode == 'alignv' or uiCode == 'alignh') ) or (uiCmd['round']) or (not (uiCmd['stem'] in ['', 'None'])):
				return self.dummyPopup
			else:
				cell.removeAllItems()
				if uiCode not in ['alignv', 'alignh']:
					cell.addItemsWithTitles_(['Do Not Align to Grid', 'Closest Pixel Edge', 'Left/Bottom Edge', 'Right/Top Edge', 'Center of Pixel', 'Double Grid'])
				else:
					cell.addItemsWithTitles_(['Closest Pixel Edge', 'Left/Bottom Edge', 'Right/Top Edge', 'Center of Pixel', 'Double Grid'])


		elif colID in ['ppm1', 'ppm2']:
			if not 'delta' in uiCode:
				return self.dummyCombo

		elif colID == 'zone':
			if uiCode not in ['alignt', 'alignb', 'alignv']:
				cell.addItemsWithTitles_(self.zonesList)

		return cell

	def ComboBoxListCell(self, items):
		cell = NSComboBoxCell.alloc().init()
		cell.setControlSize_(NSMiniControlSize)
		cell.setBordered_(False)
		cell.addItemsWithObjectValues_(items)
		return cell


if tthTool._printLoadings: print "ProgramWindow, ",
