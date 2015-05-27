from AppKit import NSObject, NSTextFieldCell

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
		# Unlike Python's __init__, initializers MUST return self,
		# because they are allowed to return any object!
		self.dummy = NSTextFieldCell.alloc().init()
		self.dummy.setStringValue_("hi")
		return self

	def tableView_dataCellForTableColumn_row_(self, tableView, tableColumn, row):
		if tableColumn == None: return None
		cell = tableColumn.dataCell()
		if cell == None: return None
		if tableColumn.identifier() == 'delta':
			#cell.setEnabled_(row % 2 == 0)
			if row % 2 == 0:
				return self.dummy
		return cell
