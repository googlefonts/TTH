
from tools import TTHCommandTool
from models.TTHTool import uniqueInstance as tthTool
from drawing import geom
from views import popOvers
reload(popOvers)

class SelectionTool(TTHCommandTool):

	def __init__(self, final = False):
		super(SelectionTool, self).__init__("Selection")

	def updateUI(self):
		self.hideUI()

	def mouseDown(self, point, clickCount):
		self.mouseDownClickPos = geom.makePoint(point)
		self.dragging = False

	def mouseUp(self, point):
		if not self.realClick(point): return
		gm, fm = tthTool.getGlyphAndFontModel()
		# Have we clicked on a command label?
		cmd = gm.commandClicked(point)
		if cmd != None:
			popOvers.openForCommand(cmd, point)
		else:
			# Have we clicked on a zone label?
			zoneName, zone = fm.zoneClicked(point)
			if zone:
				popOvers.ZoneDeltaPopover(gm, fm, point, zoneName, zone)
