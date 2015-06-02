from mojo.extensions import getExtensionDefault
from vanilla import FloatingWindow, List, CheckBoxListCell, SliderListCell, PopUpButtonListCell
from views import TTHWindow, tableDelegate
from models.TTHTool import uniqueInstance as tthTool
from AppKit import NSLeftMouseUpMask
from commons import helperFunctions as HF

DefaultKeyStub = "com.sansplomb.TTH."

defaultKeyProgramWindowPosSize = DefaultKeyStub + "programWindowPosSize"
defaultKeyProgramWindowVisibility = DefaultKeyStub + "programWindowVisibility"

commandKeys = ['code', 'point', 'point1', 'point2', 'align', 'stem', 'round', 'zone', 'ppm1', 'ppm2', 'mono', 'gray', 'index', 'delta', 'active']
alignNameToCode = {'Do Not Align to Grid': '', 'Closest Pixel Edge': 'round', 'Left/Bottom Edge': 'left', 'Right/Top Edge': 'right', 'Center of Pixel': 'center', 'Double Grid': 'double'}
alignCodeToName = HF.invertedDictionary(alignNameToCode)

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

		fm = tthTool.getFontModel()
		popUpCellStems = PopUpButtonListCell([])
		popUpCellAlign = PopUpButtonListCell([])

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
			{"title": "zone",   "width": 100, "editable": False},
			{"title": "delta",  "width": 120, "editable": True, "cell":sliderCell},
			{"title": "ppm1",   "width":  50, "editable": False},
			{"title": "ppm2",   "width":  50, "editable": False},
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
		self.delegate = tableDelegate.ProgramPanelTableDelegate.alloc().init()
		self.delegate.setWindow(win)
		tableView.setDelegate_(self.delegate)
		self.window = win

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
		if 'interpolate' in code:
			alignCode = alignNameToCode.get(uiCmd['align'], '')
			if alignCode == '':
				HF.delCommandAttrib(cmd, 'align')
			else:
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
		if self.delegate:
			self.delegate.refreshFromFontModel()
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

		self.window.programList.set(uiCommands)

if tthTool._printLoadings: print "ProgramWindow, ",
