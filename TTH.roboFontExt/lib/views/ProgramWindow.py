from mojo.extensions import getExtensionDefault
from vanilla import FloatingWindow, List, CheckBoxListCell
from views import TTHWindow
from models.TTHTool import uniqueInstance as tthTool

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

		columnDescriptions = [
			{"title": "index", "width": 30, "editable": False},
			dict(title="active", cell=CheckBoxListCell(), width=35, editable=True),
			{"title": "code", "width": 100, "editable": False},
			{"title": "point", "width": 100, "editable": False},
			{"title": "point1", "width": 100, "editable": False},
			{"title": "point2", "width": 100, "editable": False},
			{"title": "align", "width": 100, "editable": False},
			{"title": "round", "width": 80, "editable": False},
			{"title": "stem", "width": 100, "editable": False},
			{"title": "zone", "width": 100, "editable": False},
			#dict(title='delta', cell=sliderCell, width=90, editable=True),
			{"title": "delta", "width": 50, "editable": False},
			{"title": "ppm1", "width": 50,"editable": False},
			{"title": "ppm2", "width": 50, "editable": False},
			{"title": "mono", "width": 50, "editable": False},
			{"title": "gray", "width": 50, "editable": False}
			]
		win.programList = List((0, 0, -0, -0), [],
					columnDescriptions=columnDescriptions,
					enableDelete=False,
					showColumnTitles=True,
					selectionCallback=self.selectionCallback,
					editCallback = self.editCallback)

		self.window = win # this will not rebind the events, since they are already bound.

	def selectionCallback(self, sender):
		pass
		# if sender.getSelection() != []:
		# 	self.TTHToolInstance.popOverIsOpened = True
		# 	self.TTHToolInstance.commandClicked = sender.getSelection()[0]
		# 	self.TTHToolInstance.selectedCommand = self.TTHToolInstance.glyphTTHCommands[self.TTHToolInstance.commandClicked]
		# 	UpdateCurrentGlyphView()
		#print sender.getSelection()

	def editCallback(self, sender):
		if self.lock or (sender.getSelection() == []):
			return
		self.lock = True
		updatedCommands = []
		gm, fm = tthTool.getGlyphAndFontModel()
		g = gm.RFGlyph
		g.prepareUndo('Edit Program')
		for commandUI in sender.get():
			command = { k : str(commandUI[k]) for k in commandKeys if commandUI[k] != '' }
			if commandUI['active'] == 1:
				command['active'] = 'true'
			else:
				command['active'] = 'false'
			if commandUI['delta'] != '':
				command['delta'] = str(int(commandUI['delta']))
			updatedCommands.append(command)

		#gm.hintingCommands = updatedCommands
		gm.updateGlyphProgram(fm)
		g.performUndo()
		self.lock = False

	def updateProgramList(self):
		gm = tthTool.getGlyphModel()
		commands =  [dict(c) for c in gm.sortedHintingCommands]
		def putIfNotThere(c, i, key):
			if key not in c:
				c[key] = ''
			if key == 'index':
				c[key] = i
			if key == 'active':
				c[key] = (c[key] == 'true')
		for i, command in enumerate(commands):
			for key in extendedCommandKeys:
				putIfNotThere(command, i, key)
		self.window.programList.set(commands)
