
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool
from views import popOvers
reload(popOvers)

class SelectionTool(TTHCommandTool):

	def __init__(self, final = False):
		super(SelectionTool, self).__init__("Selection")

	def updateUI(self):
		self.hideUI()

	def mouseUp(self, point):
		if not self.realClick(point): return
		gm = tthTool.getGlyphModel()
		# Have we clicked on a command label?
		cmd = gm.commandClicked(point)
		if cmd != None:
			popOvers.openForCommand(cmd, point)
