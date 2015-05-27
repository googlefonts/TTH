from AppKit import NSObject, NSCell, NSTextFieldCell

class ProgramPanelTableDelegate(NSObject):

	def init(self):
		"""
		Designated initializer for ProgramPanelTableDelegate
		"""
		# ALWAYS call the super's designated initializer.
		# Also, make sure to re-bind "self" just in case it
		# returns something else, or even None!
		self = super(ProgramPanelTableDelegate, self).init()
		if self is None: return None
		self.dummy = NSCell.alloc().init()
		self.dummy.setImage_(None)
		self.w = None
		return self

	def setWindow(self, w):
		self.w = w

	def tableView_dataCellForTableColumn_row_(self, tableView, tableColumn, row):
		if tableColumn == None: return None
		if tableColumn.identifier() == 'delta' and self.w != None:
			try:
				if self.w.programList[row]['code'][1:-1] != 'delta':
					return self.dummy
			except:
				pass
		return tableColumn.dataCell()
