from mojo.extensions import *
from mojo.events import *

toolbarIcon = ExtensionBundle("TTH").get("toolbarIcon")

class TTHTool(BaseEventTool):

	def __init__(self, tthtm):
		BaseEventTool.__init__(self)
		self.tthtm = tthtm

	def getToolbarIcon(self):
		return toolbarIcon

	def getToolbarTip(self):
		return "TTH"