from AppKit import NSObject

class ProgramPanelTableDelegate(NSObject):

	def initWithMaster(self, master):
		# ALWAYS call the super's designated initializer.  Also, make sure to
		# re-bind "self" just in case it returns something else, or even
		# None!
		self = super(ProgramPanelTableDelegate, self).init()
		if self is None: return None
		
		self.master = master
		return self

	def tableView_dataCellForTableColumn_row_(self, tableView, tableColumn, row):
		return self.master.tableView_dataCellForTableColumn_row_(tableView, tableColumn, row)
