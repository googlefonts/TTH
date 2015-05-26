from AppKit import NSObject, NSView

class ProgramPanelTableDelegate(NSObject):

	# def tableView_mouseDownInHeaderOfTableColumn_(self, tableView, tableColumn):
	# 	print 'hello'

	def tableView_viewForTableColumn_row_(self, tableView, tableColumn, row):
		return NSView.alloc().init()

	# def tableView_dataCellForTableColumn_row_(self, tableView, tableColumn, row):
	# 	return NSView.alloc().init()