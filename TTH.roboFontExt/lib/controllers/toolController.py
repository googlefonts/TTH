from mojo.extensions import *
from mojo.events import *
from robofab.world import *
from lib.tools.defaults import getDefault, setDefault

from commons import helperFunctions
from models import fontModel
from views import mainPanel

reload(helperFunctions)
reload(fontModel)
reload(mainPanel)

toolbarIcon = ExtensionBundle("TTH").get("toolbarIcon")

class TTHTool(BaseEventTool):

	def __init__(self, TTHToolModel):
		BaseEventTool.__init__(self)
		self.TTHToolModel = TTHToolModel
		self.buildModelsForOpenFonts()

		self.drawingPreferencesChanged = False

	def getToolbarIcon(self):
		return toolbarIcon

	def getToolbarTip(self):
		return "TTH"

	def becomeActive(self):
		if helperFunctions.checkDrawingPreferences() == False:
			setDefault('drawingSegmentType', 'qcurve')
			self.drawingPreferencesChanged = True
		self.resetFont(createWindows=True)

	def becomeInactive(self):
		self.mainPanel.close()
		if self.drawingPreferencesChanged == True:
			setDefault('drawingSegmentType', 'curve')

	def buildModelsForOpenFonts(self):
		self.fontModels = {}
		for f in AllFonts():
			key = f.fileName
			self.fontModels[key] = fontModel.FontModel(f)
		if CurrentFont() != None:
			self.c_fontModel = self.fontModels[CurrentFont().fileName]
		else:
			self.c_fontModel = None

	def resetFont(self, createWindows=False):
		if CurrentFont() == None:
			return

		if createWindows:
			self.mainPanel = mainPanel.MainPanel(self)