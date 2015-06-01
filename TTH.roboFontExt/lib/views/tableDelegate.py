from AppKit import NSObject, NSCell, NSPopUpButtonCell, NSString, NSAttributedString
from vanilla import *

from models.TTHTool import uniqueInstance as tthTool

class ProgramPanelTableDelegate(NSObject):

	def init(self):
		# ALWAYS call the super's designated initializer.  Also, make sure to
		# re-bind "self" just in case it returns something else, or even
		# None!
		self = super(ProgramPanelTableDelegate, self).init()
		if self is None: return None
		self.dummy = NSCell.alloc().init()
		self.dummy.setImage_(None)

		fm = tthTool.getFontModel()
		self.horizontalStemsList = ['None'] + fm.horizontalStems.keys()
		self.verticalStemsList   = ['None'] + fm.verticalStems.keys()

		self.dummyPopup = PopUpButtonListCell([])
		self.dummyPopup.setTransparent_(True)
		self.dummyPopup.setEnabled_(False)
		self.dummyPopup.setMenu_(None)
		
		self.w = None
		return self

	def setWindow(self, w):
		self.w = w

	def tableView_dataCellForTableColumn_row_(self, tableView, tableColumn, row):
		if tableColumn is None: return None
		cell = tableColumn.dataCell()
		if self.w is None:
			return cell
		if (row < 0) or (row >= len(self.w.programList)):
			return cell
		uiCmd   = self.w.programList[row]
		uiCode  = uiCmd['code']
		colID = tableColumn.identifier()
		if colID in ['delta', 'mono', 'gray']:
			if 'delta' not in uiCode:
				return self.dummy
		elif colID == 'round':
			if not('single' in uiCode or 'double' in uiCode):
				return self.dummy
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
		elif colID == 'align':
			if (not ('single' in uiCode or 'double' in uiCode or 'interpolate' in uiCode) ) or (uiCmd['round']) or (not (uiCmd['stem'] in ['', 'None'])):
				return self.dummyPopup
			else:
				cell.removeAllItems()
				cell.addItemsWithTitles_(['Do Not Align to Grid', 'Closest Pixel Edge', 'Left/Bottom Edge', 'Right/Top Edge', 'Center of Pixel', 'Double Grid'])

		return cell
