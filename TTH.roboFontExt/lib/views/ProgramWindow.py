from mojo.extensions import getExtensionDefault
from vanilla import FloatingWindow, List, CheckBoxListCell, SliderListCell
from views import TTHWindow, tableDelegate
from models.TTHTool import uniqueInstance as tthTool

# from PyObjCTools import Signals
# Signals.dumpStackOnFatalSignal()
# from PyObjCTools import Debugging
# Debugging.installVerboseExceptionHandler()

DefaultKeyStub = "com.sansplomb.TTH."

defaultKeyProgramWindowPosSize = DefaultKeyStub + "programWindowPosSize"
defaultKeyProgramWindowVisibility = DefaultKeyStub + "programWindowVisibility"

commandKeys = ['code', 'point', 'point1', 'point2', 'align', 'round', 'stem', 'zone', 'ppm1', 'ppm2', 'mono', 'gray']
extendedCommandKeys = ['index', 'delta', 'active'] + commandKeys

class ProgramWindow(TTHWindow):
	def __init__(self):
		super(ProgramWindow, self).__init__(defaultKeyProgramWindowPosSize, defaultKeyProgramWindowVisibility)
		self.lock = False

		ps = getExtensionDefault(defaultKeyProgramWindowPosSize, fallback=(10, -300, -10, 300))
		win = FloatingWindow(ps, "Program", minSize=(600, 80))

		sliderCell = SliderListCell(-8, 8)
		sliderCell.setAllowsTickMarkValuesOnly_(True)
		sliderCell.setNumberOfTickMarks_(17)

		columnDescriptions = [
			{"title": "index",  "width":  30, "editable": False},
			{"title": "active", "width":  35, "editable": True, "cell":CheckBoxListCell()},
			{"title": "code",   "width": 100, "editable": False},
			{"title": "point",  "width": 100, "editable": False},
			{"title": "point1", "width": 100, "editable": False},
			{"title": "point2", "width": 100, "editable": False},
			{"title": "align",  "width": 100, "editable": False},
			{"title": "round",  "width":  80, "editable": False},
			{"title": "stem",   "width": 100, "editable": False},
			{"title": "zone",   "width": 100, "editable": False},
			{"title": "delta",  "width":  90, "editable": True, "cell":sliderCell},
			#{"title": "delta", "width":  50, "editable": False},
			{"title": "ppm1",   "width":  50, "editable": False},
			{"title": "ppm2",   "width":  50, "editable": False},
			{"title": "mono",   "width":  35, "editable": True, "cell":CheckBoxListCell()},
			{"title": "gray",   "width":  35, "editable": True, "cell":CheckBoxListCell()}
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

	def editCallback(self, sender):
		selectList = sender.getSelection()
		if self.lock or (selectList == []):
			return
		self.lock = True
		assert len(selectList) == 1
		selectedIdx = selectList[0]
		gm, fm = tthTool.getGlyphAndFontModel()
		g = gm.RFGlyph
		g.prepareUndo('Edit Program')
		uiCmd = sender.get()[selectedIdx]
		cmdIdx = uiCmd['index']
		cmd = gm.sortedHintingCommands[cmdIdx]
		codeTrueFalse = ['active', 'mono', 'gray']
		for code in codeTrueFalse:
			if uiCmd[code]:
				cmd[code] = 'true'
			else:
				cmd[code] = 'false'
		gm.updateGlyphProgram(fm)
		g.performUndo()
		self.lock = False

	def updateProgramList(self):
		gm = tthTool.getGlyphModel()
		if gm is None:
			self.window.programList.set([])
			return
		commands =  [dict(c) for c in gm.sortedHintingCommands]
		def putIfNotThere(c, i, key):
			if key not in c:
				c[key] = ''
			if key == 'index':
				c[key] = i
			if key in ['active', 'mono', 'gray']:
				c[key] = (c[key] == 'true')
		for i, command in enumerate(commands):
			for key in extendedCommandKeys:
				putIfNotThere(command, i, key)
		self.window.programList.set(commands)
