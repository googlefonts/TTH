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
		horizontalStemsList = ['None'] + fm.horizontalStems.keys()
		verticalStemsList = ['None'] + fm.verticalStems.keys()

		self.popUpCellHorizontalStems = PopUpButtonListCell(horizontalStemsList)
		self.popUpCellVerticalStems = PopUpButtonListCell(verticalStemsList)
		self.dummyStem = PopUpButtonListCell([])
		self.dummyStem.setEnabled_(False)
		
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
		code  = self.w.programList[row]['code']
		colID = tableColumn.identifier()
		if colID in ['delta', 'mono', 'gray']:
			if 'delta' in code:
				return self.dummy
		elif colID == 'round':
			if not('single' in code or 'double' in code):
				return self.dummy
		elif colID == 'stem':
			# trying to disable the cell when not relevant... example
			# woth setBordered works but have to find the proper method
			if 'single' in code or 'double' in code:
				if code[-1] == 'h':
					return self.popUpCellVerticalStems
				else:
					return self.popUpCellHorizontalStems
			else:
				return self.dummyStem
		return cell
