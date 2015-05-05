
class TTHCommandTool(object):

	def __init__(self, name):
		self.name = name
		self.alignment = 0
		self.allowedAlignments = ['Unused']

	allowedAlignmentTypes = ['round', 'left', 'right', 'center', 'double']
	displayX = [	'Closest Pixel Edge',
				'Left Edge',
				'Right Edge',
				'Center of Pixel',
				'Double Grid']
	displayY = [	'Closest Pixel Edge',
				'Bottom Edge',
				'Top Edge',
				'Center of Pixel',
				'Double Grid']
	allowedAlignmentTypesWithNone = ['None'] + allowedAlignmentTypes
	displayXWithNone = ['Do Not Align to Grid'] + displayX
	displayYWithNone = ['Do Not Align to Grid'] + displayY

	def updateUI(self, panel):
		pass

	def setAlignment(self, index):
		if index < 0 or index >= len(self.allowedAlignments):
			index = 0
		self.alignment = index
		print "{}.setAlignment({}) --> {}".format(self.name, index, self.getAlignment())

	def getAlignment(self):
		return self.allowedAlignments[self.alignment]
