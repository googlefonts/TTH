
class RenameTracker(object):
	def __init__(self, originals):
		self.renamings = [(o,o) for o in originals]
		self.history = []

	def newNameOf(self, name):
		for (o,n) in self.renamings:
			if o == name:
				return n
		return None

	def rename(self, old, new):
		if old == new: return True
		if old == None: return False
		for (o,n) in self.renamings:
			if n != None and n == new: return False
		idx = -1
		for i, (o,n) in enumerate(self.renamings):
			if n == old:
				idx = i
				break
		if idx == -1: return False
		o, n = self.renamings[i]
		self.renamings[i] = (o, new)
		self.history.append((old, new))
		return True

	def __repr__(self):
		return '\n'.join(' -> '.join([o,n]) for (o,n) in self.renamings)
