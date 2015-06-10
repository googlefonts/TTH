
import weakref, math
import xml.etree.ElementTree as ET
from models.TTHTool import uniqueInstance as tthTool
from commons import helperFunctions
import auto

gPAW = False

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class Alignment(object):
	def __init__(self, pos):
		self.components = []
		self.pos = pos
		self.weight = 0.0
		self.zone = None
		self.inGroup = False

	def leaderPoint(self, pos, contours):
		cont, seg = self.components[pos][0]
		return contours[cont][seg].leader()

	def findZone(self, contours, autoh):
		for comp in self.components:
			for (cont,seg) in comp:
				pt = contours[cont][seg]
				z = autoh.zoneAt(pt.pos.y)
				if z != None:
					self.zone = z
		return self.zone

	def addPoint(self, cont, seg, contours):
		pt = contours[cont][seg]
		pt.alignment = self.pos
		self.weight += pt.weight
		lenc = len(contours[cont])
		prevId = cont, (seg+lenc-1) % lenc
		nextId = cont, (seg+1) % lenc
		found = False
		for comp in self.components:
			if (prevId in comp) or (nextId in comp):
				comp.append((cont,seg))
				found = True
				break
		if not found:
			self.components.append([(cont,seg)])

	def putLeadersFirst(self, contours):
		leaderComp = None
		maxW = 0.0
		comps = self.components
		for i,comp in enumerate(comps):
			compLeader = None
			localMaxW = 0.0
			for j, (cont, seg) in enumerate(comp):
				pt = contours[cont][seg]
				if pt.weight > localMaxW:
					compLeader = j
					localMaxW = pt.weight
				if pt.weight > maxW: #and compLeader == None:
					leaderComp = i
					maxW = pt.weight
			if compLeader == None: compLeader = 0
			if compLeader > 0: comp[compLeader], comp[0] = comp[0], comp[compLeader]
			l = contours[comp[0][0]][comp[0][1]]
			for c,s in comp: contours[c][s].leader = weakref.ref(l)
		if leaderComp != None and leaderComp > 0:
			comps[0], comps[leaderComp] = comps[leaderComp], comps[0]
		# remaining points have themselve as leader
		for c in contours:
			for s in c:
				if s.leader == None:
					s.leader = weakref.ref(s)

	def addLinks(self, leader, contours, isHorizontal, autoh):
		comps = self.components
		cont, seg = comps[leader][0]
		lead = contours[cont][seg]
		lead.touched = True
		startName = lead.name
		for i, comp in enumerate(comps):
			if i == leader: continue
			cont, seg = comp[0]
			hd = contours[cont][seg]
			if hd.touched: continue
			hd.touched = True
			autoh.addSingleLink(startName, hd.name, isHorizontal, None)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class Group:
	def __init__(self):
		self.alignments = set()
		self.leaderPos = None
		self.bounds = (10000000,-10000000)
	def width(self):
		return self.bounds[1] - self.bounds[0]
	def prepare(self, alignments):
		#self.alignments = sorted([alignments[p] for p in self.alignments], key=lambda a:a.weight, reverse=True)
		self.alignments.sort(key=lambda a:a.weight, reverse=True)
		self.avgPos = 0.5 * (self.bounds[0] + self.bounds[1])
		#print "Prepared alignments:",
		#for a in self.alignments:
		#	print '{'+str(a.pos)+', '+str(a.weight)+'}',
		#print ''
	def sticks(self, l, r):
		if l < self.bounds[0] and self.bounds[1] < r: return True
		if self.bounds[0] < l and r < self.bounds[1]: return True
		return ((l,False) in self.alignments) or ((r,True) in self.alignments)
	def add(self, pos):
		self.alignments.add(pos)
		self.bounds = min(self.bounds[0], pos[0]), max(self.bounds[1], pos[0])

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def getWidthOfTwoPointsStem(p1, p2, isHorizontal):
	try:
		if isHorizontal:
			return abs(p1.shearedPos.y - p2.shearedPos.y)
		else:
			return abs(p1.shearedPos.x - p2.shearedPos.x)
	except:
		#print "warning: no access to sheared pos"
		if isHorizontal:
			return abs(p1.y - p2.y)
		else:
			return abs(p1.x - p2.x)

def zoneData((zoneName, zone)):
	isTop = zone['top']
	if isTop:
		y_start = int(zone['position'])
		y_end = int(zone['position']) + int(zone['width'])
	else:
		y_start = int(zone['position']) - int(zone['width'])
		y_end = int(zone['position'])
	return (zoneName, isTop, y_start, y_end)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class AutoHinting():
	def __init__(self, fontModel = None):
		if fontModel == None:
			self.fm = tthTool.getFontModel()
		else:
			self.fm = fontModel
		self.gm = None
		self.singleLinkCommandName = { False: 'singleh', True:'singlev' }
		self.doubleLinkCommandName = { False: 'doubleh', True:'doublev' }
		self.alignCommandName = { False: 'alignb', True:'alignt' }

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def makeAlignments(self, contours, X):
		if X: X = 0
		else: X = 1
		proj = lambda p: p[X]
		ortho_proj = lambda p: p[1-X]
		self.proj = proj
		self.ortho_proj = ortho_proj
		byPos = {}
		# make a copy of all contours with hinting data and groups the ON points
		# having the same 'proj' coordinate (sheared X or Y)
		minCosine = abs(math.cos(math.radians(self.fm.angleTolerance)))
		for cont, contour in enumerate(contours):
			for seg, hd in enumerate(contour):
				hd.weight = hd.weight2D[1-X]
				goodAngle = abs( hd.inTangent[1-X]) > minCosine \
					   or abs(hd.outTangent[1-X]) > minCosine
				if not goodAngle: continue
				pos = int(round(proj(hd.shearedPos)))
				ptsAtPos = helperFunctions.getOrPutDefault(byPos, pos, [])
				ptsAtPos.append((ortho_proj(hd.shearedPos), (cont, seg)))

		# make it a list, so we can sort it by X position ('k' below)
		byPos = [(k, sorted(v)) for (k, v) in byPos.iteritems()]
		byPos.sort()
		alignments = {}
		lastPos = -100000
		for pos, pts in byPos:
			# Merge everything within 10 units : maybe too big or not
			# adapted to some situation...
			if pos - lastPos < 10:
				pos = lastPos
				alignment = alignments[pos]
			else:
				alignment = Alignment(pos)
				lastPos = pos
			for _, (cont, seg) in pts:
				alignment.addPoint(cont, seg, contours)
			alignments[pos] = alignment
		return alignments

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def printAlignments(self, alignments, axis):
		print "Alignments for", axis
		for pos, alignment in sorted(alignments.iteritems(), reverse=True):
			print pos, ":",
			for comp in alignment.components:
				print '{',
				for cont,seg in comp:
					print str(cont)+'.'+str(seg),
				print "}",
			print ""

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def makeGroups(self, contours, alignments, stems, mergeLoneAlignments=False, debug=False):
		groups = []
		for stem in stems:
			src = contours[stem[0].csi[0]][stem[0].csi[1]]
			tgt = contours[stem[1].csi[0]][stem[1].csi[1]]
			pos0 = src.alignment
			pos1 = tgt.alignment
			if debug: print "(",pos0,pos1,src.pos,tgt.pos,")"
			if pos0 == None or pos1 == None: continue
			if pos1 < pos0:
				pos0, pos1 = pos1, pos0
				src, tgt = tgt, src
			grp = None
			for c in groups:
				if c.sticks(pos0, pos1):
					grp = c
			if grp == None:
				groups.append(Group())
				grp = groups[-1]
			alignments[pos0].inGroup = True
			alignments[pos1].inGroup = True
			grp.add((pos0,False))
			grp.add((pos1,True))
		for pos,ali in alignments.iteritems():
			if ali.inGroup: continue
			grp = Group()
			groups.append(grp)
			grp.alignments = [(pos, False)]
			grp.bounds = (pos, pos)
		groups.sort(key=lambda g: g.bounds[0]+g.bounds[1])
		# Merging groups
		if mergeLoneAlignments and len(groups) > 1:
			if len(groups[0].alignments) == 1 and len(groups[1].alignments) > 1:
				pos = groups[0].alignments[0][0]
				b = groups[1].bounds
				if b[0]-pos < b[1]-b[0]:
					groups[1].add((pos, False))
					del groups[0]
		if mergeLoneAlignments and len(groups) > 1:
			if len(groups[-1].alignments) == 1 and len(groups[-2].alignments) > 1:
				pos = groups[-1].alignments[0][0]
				b = groups[-2].bounds
				if pos-b[1] < b[1]-b[0]:
					groups[-2].add((pos, True))
					del groups[-1]
		# End Of Merging groups
		if debug:
			print "Groups:"
			for grp in groups:
				for (p,x) in grp.alignments:
					print p,
				print ""
		for grp in groups:
			grp.alignments = [alignments[p] for (p,x) in grp.alignments]
		return groups

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def findLeftRight(self, groups):
		if len(groups) == 0: return None, None, None, None
		groupWeights = [((i,g), sum([a.weight for a in g.alignments])) for (i, g) in enumerate(groups)]
		atLeastTwoGroups = (len(groups) >= 2)
		(i,lg), w0 = groupWeights[0]
		if atLeastTwoGroups:
			(i1,g1),w1 = groupWeights[1]
			#if w1 > 1.6 * w0 and g1.avgPos < lg.bounds[1]+1.2*lg.width():
			if w1 > 1.6 * w0 and (helperFunctions.intervalsIntersect(lg.bounds, g1.bounds)):# or len(lg.alignments)==1)):
				i,lg = i1,g1
		#----------------
		(j,rg), w0 = groupWeights[-1]
		if atLeastTwoGroups:
			(j1,g1),w1 = groupWeights[-2]
			#if w1 > 1.6 * w0 and g1.avgPos > rg.bounds[0]-1.2*rg.width():
			if w1 > 1.6 * w0 and (helperFunctions.intervalsIntersect(rg.bounds, g1.bounds)):# or len(rg.alignments)==1)):
				j,rg = j1,g1
		if i == j and i > 0: (i,lg),_ = groupWeights[0]
		if i == j and j < len(groups)-1: (j,rg),_ = groupWeights[-1]
		#----------------
		if len(lg.alignments) == 1 or (lg.alignments[0].pos < lg.alignments[1].pos):
			leftmost = 0
		else:
			leftmost = 1
		#----------------
		if len(rg.alignments) > 1 and (rg.alignments[0].pos < rg.alignments[1].pos):
			rightmost = 1
		else:
			rightmost = 0
		#----------------
		ret = i,leftmost, j,rightmost
		#print "findLeftRight returns", ret
		return ret

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def linearPropagation(self, lead, alignments, contours, isHorizontal):
		src = lead
		srcpos = self.proj(src.shearedPos)
		for ali in alignments:
			tgt = ali.leaderPoint(0, contours)
			tgtpos = self.proj(tgt.shearedPos)
			if not tgt.touched:
				tgt.touched = True
				stemWidth = getWidthOfTwoPointsStem(src, tgt, isHorizontal)
				stemName = self.guessStemForWidth(stemWidth, isHorizontal)
				link = self.addSingleLink(src.name, tgt.name, isHorizontal, stemName)
				if stemName == None and abs(srcpos-tgtpos) > 20.0:
					link.set('round', 'true')
			src = tgt
			srcpos = tgtpos
			ali.addLinks(0, contours, isHorizontal, self)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def propagate(self, grp, contours, isHorizontal):
		leadAli = grp.alignments[grp.leaderPos]
		lead = leadAli.leaderPoint(0, contours)
		leftAlignments = [a for a in grp.alignments if a.pos < leadAli.pos]
		rightAlignments = [a for a in grp.alignments if a.pos > leadAli.pos]
		leftAlignments.sort(key=lambda a:a.pos, reverse=True)
		rightAlignments.sort(key=lambda a:a.pos, reverse=False)
		leadAli.addLinks(0, contours, isHorizontal, self)
		self.linearPropagation(lead,  leftAlignments, contours, isHorizontal)
		self.linearPropagation(lead, rightAlignments, contours, isHorizontal)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def processGroup_X(self, grp, contours, interpolateIsPossible, bounds):
		if len(grp.alignments) == 1:
			if len(grp.alignments[0].components) == 1:
				return
		# Find a leader position, preferably the position of a nice stem
		if grp.leaderPos == None:
			grp.leaderPos = 0
			for (i, ali) in enumerate(grp.alignments):
				if ali.leaderPoint(0, contours).touched:
					grp.leaderPos = i
					break
		# Find the leader control point in the leader alignment (= the alignment at the leaderPos)
		leadAli = grp.alignments[grp.leaderPos]
		lead = leadAli.leaderPoint(0, contours)
		if (not lead.touched) and interpolateIsPossible:
			# If NO alignment in the group had beed processed yet,
			# then add a starting point by interpolation:
			leftmost, rightmost = bounds
			self.addInterpolate(leftmost, lead, rightmost, False)
		lead.touched = True
		self.propagate(grp, contours, False)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def processGroup_Y(self, grp, contours, interpolateIsPossible, bounds, findZone):
		zone = None
		if grp.leaderPos == None:
			if not findZone:
				grp.leaderPos = 0
			for (i, ali) in enumerate(grp.alignments):
				if ali.leaderPoint(0, contours).touched:
					grp.leaderPos = i
					break
		if grp.leaderPos == None:
			# Here, it must be the case that findZone == True, so we
			# look for a zone
			findTopMostZone = True
			for pos, ali in enumerate(grp.alignments):
				if ali.zone == None: continue
				if not ali.zone[1]: findTopMostZone = False # bottom zone
				if ((zone == None) or
				   ((    findTopMostZone) and (zone[2] < ali.zone[2])) or
				   ((not findTopMostZone) and (zone[2] > ali.zone[2]))):
					zone = ali.zone
					grp.leaderPos = pos
		if grp.leaderPos == None: # no zone
			return None
		# Find the leader control point in the leader alignment (= the alignment at the leaderPos)
		leadAli = grp.alignments[grp.leaderPos]
		lead = leadAli.leaderPoint(0, contours)
		if not lead.touched:
			if zone != None:
				self.addAlign(lead.name, zone)
				lead.touched = True
			elif interpolateIsPossible:
				# If NO alignment in the group had beed processed yet,
				# then add a starting point by interpolation:
				bottommost, topmost = bounds
				self.addInterpolate(bottommost, lead, topmost, True)
				lead.touched = True
		if not lead.touched: return None
		self.propagate(grp, contours, True)
		return lead

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def guessStemForWidth(self, width, isHorizontal):
		candidatesList = []
		bestD = 10000000
		bestName = None
		if isHorizontal:
			stems = self.fm.horizontalStems
		else:
			stems = self.fm.verticalStems
		for stemName, stem in stems.iteritems():
			w = int(stem['width'])
			d = abs(w - width)
			if ( width >= w/1.22 and
			     width <= w*1.22 and
			     d < bestD ):
				bestD = d
				bestName = stemName
		return bestName

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def addSingleLink(self, p1name, p2name, isHorizontal, stemName):
		cmd = ET.Element('ttc')
		cmd.set('active', 'true')
		cmd.set('code', self.singleLinkCommandName[isHorizontal])
		cmd.set('point1', p1name)
		cmd.set('point2', p2name)
		if stemName != None:
			cmd.set('stem', stemName)
		self.gm.addCommand(cmd, update=False)
		return cmd

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def addInterpolate(self, p1, p, p2, isHorizontal):
		cmd = ET.Element('ttc')
		cmd.set('active', 'true')
		if isHorizontal:
			cmd.set('code', 'interpolatev')
		else:
			cmd.set('code', 'interpolateh')
		cmd.set('point1', p1.name)
		cmd.set('point2', p2.name)
		cmd.set('point', p.name)
		cmd.set('align', 'round')
		self.gm.addCommand(cmd, update=False)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def addAlign(self, pointName, (zoneName, isTopZone, ys, ye)):
		cmd = ET.Element('ttc')
		cmd.set('active', 'true')
		if isTopZone:
			cmd.set('code', 'alignt')
		else:
			cmd.set('code', 'alignb')
		cmd.set('point', pointName)
		cmd.set('zone', zoneName)
		self.gm.addCommand(cmd, update=False)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def zoneAt(self, y):
		for item in self.fm.zones.iteritems():
			zd = zoneData(item)
			zoneName, isTop, yStart, yEnd = zd
			if helperFunctions.inInterval(y, (yStart, yEnd)):
				return zd

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def autoHintY(self, contours, stems):
		alignments = self.makeAlignments(contours, False) # for Y auto-hinting
		#self.printAlignments(alignments, 'Y')
		for _, alignment in alignments.iteritems():
			alignment.putLeadersFirst(contours)
			alignment.findZone(contours, self)

		groups = self.makeGroups(contours, alignments, stems, mergeLoneAlignments=False, debug=False)
		for grp in groups: grp.prepare(alignments)

		bottom, top = None, None
		for group in groups:
			pt = self.processGroup_Y(group, contours, False, None, findZone=True)
			if pt == None: continue
			if top == None or pt.pos.y > top.pos.y: top = pt
			if bottom == None or pt.pos.y < bottom.pos.y: bottom = pt
		interpolateIsPossible = (top != None) and (bottom != None) and (not (top is bottom))
		bounds = (bottom, top)
		for group in groups:
			self.processGroup_Y(group, contours, interpolateIsPossible, bounds, findZone=False)
		return (bottom != None and top != None)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def autoHintX(self, g, contours, stems):
		alignments = self.makeAlignments(contours, True) # for X auto-hinting
		#self.printAlignments(alignments, 'X')
		if len(alignments) == 0: return g.name
		for _, alignment in alignments.iteritems():
			alignment.putLeadersFirst(contours)

		groups = self.makeGroups(contours, alignments, stems, mergeLoneAlignments=True, debug=False)
		for grp in groups: grp.prepare(alignments)

		# Find the left and right points to be anchored to lsb and rsb.
		leftGrpIdx,lmPos, rightGrpIdx,rmPos = self.findLeftRight(groups)
		if leftGrpIdx == None: return g.name
		leftGroup = groups[leftGrpIdx]
		rightGroup = groups[rightGrpIdx]
		bounds = None
		interpolateIsPossible = False

		# Anchor the rightmost point
		rightmost = rightGroup.alignments[rmPos].leaderPoint(0, contours)
		self.addSingleLink('lsb', rightmost.name, False, None).set('round', 'true')
		self.addSingleLink(rightmost.name, 'rsb', False, None).set('round', 'true')
		rightGroup.leaderPos = rmPos
		self.processGroup_X(rightGroup, contours, False, None)

		# Anchor the leftmost point if they live in different groups
		# (If not, then the processGroup will take care of the single link
		#  and interpolation will not be possible)
		if leftGrpIdx != rightGrpIdx:
			interpolateIsPossible = True
			leftmost = leftGroup.alignments[lmPos].leaderPoint(0, contours)
			bounds = leftmost, rightmost
			stemWidth = getWidthOfTwoPointsStem(leftmost, rightmost, False)
			stemName = self.guessStemForWidth(stemWidth, False)
			link = self.addSingleLink(rightmost.name, leftmost.name, False, stemName)
			if stemName == None: link.set('round', 'true')
			leftGroup.leaderPos = lmPos
			self.processGroup_X(leftGroup, contours, False, None)

		for grp in groups:
			if grp.leaderPos != None: continue
			self.processGroup_X(grp, contours, interpolateIsPossible, bounds)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def autoHintXPAW(self, g, contours, stems):
		alignments = self.makeAlignments(contours, True) # for X auto-hinting
		#self.printAlignments(alignments, 'X')
		if len(alignments) == 0: return g.name
		for _, alignment in alignments.iteritems():
			alignment.putLeadersFirst(contours)

		groups = self.makeGroups(contours, alignments, stems, mergeLoneAlignments=True, debug=False)
		for grp in groups: grp.prepare(alignments)

		# Find the left and right points to be anchored to lsb and rsb.
		leftGrpIdx,lmPos, rightGrpIdx,rmPos = self.findLeftRight(groups)
		if leftGrpIdx == None: return g.name
		leftGroup = groups[leftGrpIdx]
		rightGroup = groups[rightGrpIdx]
		bounds = None
		interpolateIsPossible = False

		leftmost = leftGroup.alignments[lmPos].leaderPoint(0, contours)
		rightmost = rightGroup.alignments[rmPos].leaderPoint(0, contours)

		# Anchor the leftmost point
		self.addSingleLink('lsb', leftmost.name, False, None).set('round', 'true')
		leftGroup.leaderPos = lmPos
		self.processGroup_X(leftGroup, contours, False, None)
		

		# Anchor the rightmost point if they live in different groups
		# (If not, then the processGroup will take care of the single links
		#  and interpolation will not be possible)
		if leftGrpIdx != rightGrpIdx:
			self.addSingleLink('rsb', rightmost.name, False, None).set('round', 'true')
			interpolateIsPossible = True
			bounds = leftmost, rightmost
			rightGroup.leaderPos = rmPos
			self.processGroup_X(rightGroup, contours, False, None)
		else:
			stemWidth = getWidthOfTwoPointsStem(leftmost, rightmost, False)
			stemName = self.guessStemForWidth(stemWidth, False)
			link = self.addSingleLink(leftmost.name, rightmost.name, False, stemName)
			if stemName == None: link.set('round', 'true')
			self.addSingleLink(rightmost.name, 'rsb', False, None).set('align', 'round')

		for grp in groups:
			if grp.leaderPos != None: continue
			self.processGroup_X(grp, contours, interpolateIsPossible, bounds)

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

	def autohint(self, gm, doX, doY):
		# get the current font
		font = self.fm.f
		# get the italic angle
		if font.info.italicAngle != None:
			self.ital = - font.info.italicAngle
		else:
			self.ital = 0

		g = gm.RFGlyph
		# compute additional contour information in custom structure
		noName, contours = auto.makeContours(g, self.ital)
		if not contours:
			return noName, None, None

		# Clear the hinting program for the current glyph
		gm.clearCommands(doX, doY)
		self.gm = gm

		# compute as much stem as one can find
		yBound, xBound = self.fm.stemSizeBounds
		stemsList = auto.stems.makeStemsList(g, contours, self.ital, xBound, yBound, self.fm.angleTolerance, dedup=False)

		if doX:
			# Do X hinting. 'rx' is None if all is OK and [g.name] is there was a problem
			global gPAW
			if gPAW:
				print "Preserve Advance Width"
				rx = self.autoHintXPAW(g, contours, stemsList[0])
			else:
				print "Preserve Proportions"
				rx = self.autoHintX(g, contours, stemsList[0])
			gPAW = not gPAW
		else:
			rx = None
		for c in contours:
			for hd in c:
				hd.reset()
		if doY:
			# Do Y hinting. 'ry' is True if all is OK and False if there was a problem
			ry = self.autoHintY(contours, stemsList[1])
		else:
			ry = True
		if not ry: ry = g.name
		else: ry = None
		self.gm.compile(self.fm)
		self.gm = None
		return noName, rx, ry
