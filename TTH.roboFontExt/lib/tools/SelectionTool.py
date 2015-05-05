
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool

class SelectionTool(TTHCommandTool):

	def __init__(self, final = False):
		super(SelectionTool, self).__init__("Selection")

	def updateUI(self):
		self.hideUI()
