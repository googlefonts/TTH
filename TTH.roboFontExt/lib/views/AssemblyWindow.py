from mojo.extensions import getExtensionDefault
from vanilla import FloatingWindow, List
from views import TTHWindow
from models.TTHTool import uniqueInstance as tthTool

DefaultKeyStub = "com.sansplomb.TTH."
defaultKeyAssemblyWindowPosSize = DefaultKeyStub + "assemblyWindowPosSize"
defaultKeyAssemblyWindowVisibility = DefaultKeyStub + "assemblyWindowVisibility"

class AssemblyWindow(TTHWindow):
	def __init__(self):
		super(AssemblyWindow, self).__init__(defaultKeyAssemblyWindowPosSize, defaultKeyAssemblyWindowVisibility)

		ps = getExtensionDefault(defaultKeyAssemblyWindowPosSize, fallback=(10, 150, 150, -400))
		win = FloatingWindow(ps, "Assembly", minSize=(150, 100))
		win.assemblyList = List((0, 0, -0, -0), [],
					columnDescriptions=[{"title": "Assembly", "width": 150, "editable": False}],
					showColumnTitles=False)
		self.window = win

	def updateAssemblyList(self):
		gm = tthTool.getGlyphModel()
		if gm is None:
			assembly = []
		else:
			assembly = gm.getAssembly()
		self.window.assemblyList.set([{"Assembly":a} for a in assembly])
