
class TTHGlyph(object):

	def __init__(self, rfGlyph):
		# private variables
		self._g = rfGlyph
		self._contours = None
		self._h_stems  = None
		self._v_stems  = None
		self._sortedHintingCommands = None
		# public variables
		self.hintingCommands = []
		self.nameToContSeg   = {}
		# load stuff from the UFO
		self.loadFromUFO()

	@property
	def contours(self):
		if None == self._contours:
			self.computeContours() # or maybe, self._contours = Automation.prepareContours(_g)
		return self._contours

	@property
	def horizontalContours(self):
		if None == self._h_stems:
			self.computeStems() # or maybe, self._v_stems, self._h_tems = Automation.computeStems(_g)
		return self._h_stems

	@property
	def verticalContours(self):
		if None == self._v_stems:
			self.computeStems() # see comment above
		return self._v_stems

	@property
	def sortedHintingCommands(self):
		if None == self._sortedHintingCommands:
			pass # TOPOLOGICAL SORT
		return self._sortedHintingCommands

	def dirtyGeometry(self):
		'''This should be called whenever the geometry of the associated
		glyph (_g) is modified: a point is moved, added, deleted, etc...'''
		self._contours = None
		self._h_stems  = None
		self._v_stems  = None
		self.buildNameToContSegDict()

	def dirtyHinting(self):
		'''Should be called if the list of hinting commands changes, or if
		a command is modified. So this may be called by the
		command-popovers for example.'''
		self._sortedHintingCommands = None

	def buildNameToContSegDict(self):
		'''A `ContSeg` is a pair (cidx,sidx) where cidx is the index of a
		contour in the glyph _g and sidx is the index of a segment in that
		contour. A segment has exactly one ON-point and zero or more
		OFF-points.
		The ON-point is self._g[cidx][sidx].onCurve
		A ContSeg therefore identifies an ON-point in a glyph, as well as
		its contour index and its position in that contour.'''
		self.nameToContSeg = {}
		for cidx, contour in enumerate(g):
			for sidx, seg in enumerate(contour):
				self.nameToContSeg[seg.onCurve.name] = (cidx, sidx)

	def saveToUFO(self):
		"""Save what can be save in the UFO."""
		# write self.hintingCommands to UFO lib.

	def loadFromUFO(self):
		"""Load what can be loaded from the UFO."""
		# read self.hintingCommands from UFO lib.
