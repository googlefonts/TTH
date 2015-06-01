from AppKit import NSObject, NSCell, NSCellDisabled

class ProgramPanelTableDelegate(NSObject):

	def init(self):
		# ALWAYS call the super's designated initializer.  Also, make sure to
		# re-bind "self" just in case it returns something else, or even
		# None!
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
		code = self.w.programList[row]['code']
		if tableColumn.identifier() in ['delta', 'mono', 'gray'] and self.w != None:
			try:
				if code[1:-1] != 'delta':
					return self.dummy
			except:
				pass
		if tableColumn.identifier() == 'round' and self.w != None:
			try:
				if 'single' in code or 'double' in code:
					pass
				else:
					return self.dummy
			except:
				pass
		elif tableColumn.identifier() == 'stem' and self.w != None:
			cell = tableColumn.dataCell()
			# trying to disable the cell when not relevant... example woth setBordered works but have to find the proper method
			try:
				if 'single' in code or 'double' in code:
					cell.setBordered_(True)
				else:
					cell.setBordered_(False)
			except:
				pass
		return tableColumn.dataCell()