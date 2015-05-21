
class RenameTracker(object):
	def __init__(self, originals):
		self.renamings = dict((o,o) for o in originals)
		self.history = []

	def changesDict(self, current):
		d = {}
		for o,n in self.renamings.iteritems():
			if o == n: continue
			if o in current: continue
			d[o] = n
		return d

	def rename(self, old, new):
		if old == new: return True
		if old == None: return False
		key = None
		for (o,n) in self.renamings.iteritems():
			if n == old:
				key = o
				break
		if key is None: return False
		self.renamings[key] = new
		self.history.append((old, new))
		return True

	def __repr__(self):
		return '\n'.join(' -> '.join([str(k),str(v)]) for (k,v) in self.renamings.iteritems())
