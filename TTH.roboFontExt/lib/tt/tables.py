import math, time
from fontTools.ttLib.tables._g_a_s_p import GASP_SYMMETRIC_GRIDFIT, GASP_SYMMETRIC_SMOOTHING, GASP_DOGRAY, GASP_GRIDFIT
from lib.fontObjects.doodleFontCompiler.ttfCompiler import TTFCompilerSettings
from commons import helperFunctions as HF
from drawing import textRenderer as TR

#import novo

k_hdmx_key = TTFCompilerSettings.roboHintHdmxLibKey
k_VDMX_key = 'com.robofont.robohint.VDMX'
k_LTSH_key = TTFCompilerSettings.roboHintLtshLibKey
k_CVT_key  = TTFCompilerSettings.roboHintCvtLibKey
k_prep_key = 'com.robofont.robohint.prep'
k_fpgm_key = TTFCompilerSettings.roboHintFpgmLibKey
k_gasp_key = TTFCompilerSettings.roboHintGaspLibKey
k_maxp_maxStorage_key = TTFCompilerSettings.roboHintMaxpMaxStorageLibKey
k_glyph_assembly_key  = TTFCompilerSettings.roboHintGlyphAssemblyLibKey

stepToSelector = {-8: 0, -7: 1, -6: 2, -5: 3, -4: 4, -3: 5, -2: 6, -1: 7, 1: 8, 2: 9, 3: 10, 4: 11, 5: 12, 6: 13, 7: 14, 8: 15}

def autoPush(*args):
	# The '*' indicates that autoPush can have any number of
	# arguments and they are all gathered in the tuple 'args'
	nArgs = len(args)
	# Check and Fix mnemonic
	if max(args) > 255 or min(args) < 0:
		mnemonic = "PUSHW[ ]"
	else:
		mnemonic = "PUSHB[ ]"
	if 8 < nArgs < 256:
		mnemonic = "N" + mnemonic
	elif nArgs >= 256:
		raise tt_instructions_error, "More than 255 push arguments (%s)" % nArgs

	return (' '.join([mnemonic]+[str(a) for a in args]))

def write_hdmx(fm):
	fm.generateFullTempFont()
	ppems = {}
	for size in fm.hdmx_ppem_sizes:
		widths = {}
		tr = TR.TextRenderer(fm.tempFullFontPath, 'Monochrome', cacheContours=False)
		tr.set_cur_size(size)
		for glyphName in fm.f.glyphOrder:
			widths[glyphName] = (tr.get_name_advance(glyphName)[0]+32) / 64
		ppems[str(size)] = widths
	fm.f.lib[k_hdmx_key] = ppems

def write_VDMX(fm):
	fm.generateFullTempFont()
	upm = fm.UPM
	halfUpm = upm / 2
	VDMX = {
			'version':   1,
			'ratRanges': [],
			'groups':    []
		}
	# We will add only one range here, with those settings:
	ratRange = {
			'bCharSet':    0,
			'xRatio':      0,
			'yStartRatio': 0,
			'yEndRatio':   0,
			'groupIndex':  0
		}
	# We will add only one record here from 8 to 255 ppem
	vTableRecord = {}
	for yPelHeight in range(8, 256, 1):
		tr = TR.TextRenderer(fm.tempFullFontPath, 'Monochrome', cacheContours=False)
		tr.set_cur_size(yPelHeight)
		linYMax = (tr.face.bbox.yMax * yPelHeight + halfUpm) / upm
		linYMin = (tr.face.bbox.yMin * yPelHeight + halfUpm) / upm
		yMin = +10000
		yMax = -10000
		for g in fm.f:
			bmg = tr.get_name_bitmap(g.name)
			hi = bmg.top
			lo = hi - bmg.bitmap.rows
			if hi > yMax: yMax = hi
			if lo < yMin: yMin = lo
		if linYMax != yMax or linYMin != yMin:
			vTableRecord[str(yPelHeight)] = (yMax, yMin)
	#print "Group has", len(vTableRecord), "records"
	VDMX['ratRanges'].append(ratRange)
	VDMX['groups'].append(vTableRecord)
	fm.f.lib[k_VDMX_key] = VDMX

def write_LTSH(fm, maxSize = 255, verbose=False):
	clock0 = time.time()
	fm.generateFullTempFont()
	font = fm.f
	thresholds = dict((g.name, maxSize) for g in font)

	clock1 = time.time()
	if verbose:
		print "[LTSH] Font generated in", (clock1-clock0), "seconds"
	clock0 = clock1

	#import gc
	#gc.disable()
	#glyphsToCheck = {}
	#for name in font.glyphOrder:
	#	g = font[name]
	#	if self.glyphProgramDoesNotTouchLSBOrRSB(g):
	#		thresholds[name] = 1
	#	else:
	#		glyphsToCheck[name] = g
	#self.readGlyphFLTTProgram(self.getGlyph())
	glyphsToCheck = dict((g.name, g) for g in font)
	#glyphsToCheck = dict((name, font[name]) for name in ['.notdef', 'A'])

	clock1 = time.time()
	if verbose:
		print "[LTSH] Glyph set generated in", (clock1-clock0), "seconds"
	clock0 = clock1
	#gc.enable()

	upm = fm.UPM
	halfUpm = upm / 2
	out = ''
	for size in range(maxSize-1, 0, -1):
		tr = TR.TextRenderer(fm.tempFullFontPath, 'Monochrome', cacheContours=False)
		tr.set_cur_size(size)
		toRemove = []
		for name, g in glyphsToCheck.iteritems():
			if thresholds[name] > size + 1:
				toRemove.append(name)
				continue
			# the scaled widths are rounded on the fine pixel grid (1/64 pixel)
			scaled_instructed_width = tr.get_name_advance(name)[0]
			scaled_linear_width     = (g.width * 64 * size + halfUpm) / upm
			# the widths are rounded on the full pixel grid (1 pixel)
			riw = (scaled_instructed_width + 32) / 64
			rlw = (scaled_linear_width     + 32) / 64
			#rlw = (g.width * size + halfUpm) / upm
			#--------------
			#out += name+'@'+str(size)+': '
			#out += '; RIW: ' + str(riw)
			#out += '; RLW: ' + str(rlw)
			#out += ', ' + str(float(g.width * size + 0) / upm)
			#out += '\n'
			#--------------
			linear_scaling = (riw == rlw)
			if not linear_scaling and size >= 50:
				linear_scaling = 50 * abs(riw-rlw) <= rlw
			if linear_scaling:
				if size < 9:
					toRemove.append(name)
					thresholds[name] = 1
				else:
					thresholds[name] = size
		for name in toRemove:
			del glyphsToCheck[name]
	#print out
	if False:
		s = []
		names = list(font.glyphOrder)
		names.sort()
		count = 0
		for name in names:
			nv = novo.novoval[name]
			if nv != thresholds[name]:
				count += 1
				s.append(	str(font[name].index).rjust(4)
						+' / '+name.ljust(19)+': '+str(thresholds[name]).rjust(3)\
						+', should be '+str(nv)+'\n')
		print count,"errors:"
		print(''.join(s))

	clock1 = time.time()
	if verbose:
		print "LTSH dictionary generated in", (clock1-clock0), "seconds"
	clock0 = clock1

	font.lib[k_LTSH_key] = thresholds

def write_gasp(fm):
	fm.f.lib[k_gasp_key] = fm.gasp_ranges

def computeCVT(fm):
	stem_to_cvt = {}
	zone_to_cvt = {}
	CVT = []

	CVT.append(int(math.floor(fm.UPM / fm.alignppm)))

	stemsH = fm.horizontalStems.items()
	stemsV = fm.verticalStems.items()
	stemsH.sort() # sort by NAME
	stemsV.sort() # sort by NAME

	for name, stem in stemsH:
		CVT.append(int(stem['width']))
		stem_to_cvt[name] = len(CVT)-1
	for name, stem in stemsV:
		CVT.append(int(stem['width']))
		stem_to_cvt[name] = len(CVT)-1

	zones = fm.zones.items()
	zones.sort() # sort by NAME

	for name, zone in zones:
		CVT.append(int(zone['position']))
		zone_to_cvt[name] = len(CVT)-1
		CVT.append(int(zone['width']))
	return (stemsH, stemsV, stem_to_cvt, zone_to_cvt, CVT)

def write_CVT_PREP(fm):# 'fm' is instance of TTHFont
	f = fm.f
	f.lib[TTFCompilerSettings.roboHintMaxpMaxFunctionDefsLibKey] = 11
	f.lib[TTFCompilerSettings.roboHintMaxpMaxStorageLibKey] = 5

	stemsH, stemsV, stem_to_cvt, zone_to_cvt, CVT = computeCVT(fm)
	f.lib[k_CVT_key] = CVT

	table_PREP = [ autoPush(0), 'CALL[ ]' ]
	roundStemHorizontal = [ 'SVTCA[0]' ]
	if stemsH != []:
		callFunction2 = [ # index of first ControlValue for horizontal stems, number of horizontal stems
				autoPush(stem_to_cvt[stemsH[0][0]], len(stemsH), 2),
				'CALL[ ]' ]
		roundStemHorizontal.extend(callFunction2)

	roundStemVertical = [ 'SVTCA[1]' ]
	if stemsV != []:
		callFunction2 = [ # index of first ControlValue for vertical stems, number of horizontal stems
				autoPush(stem_to_cvt[stemsV[0][0]], len(stemsV), 2),
				'CALL[ ]' ]
		roundStemVertical.extend(callFunction2)

	pixelsStemHorizontal = [ 'SVTCA[0]' ]
	for stemName, stem in stemsH:
		ppm_roundsList = stem['round'].items()
		ppm_roundsList.sort(cmp=lambda (k1,v1), (k2,v2): v2-v1)
		ppmsAnd8 = [int(p[0]) for p in ppm_roundsList]+[8]
		callFunction8 = [ autoPush(stem_to_cvt[stemName], *ppmsAnd8), 'CALL[ ]' ]
		pixelsStemHorizontal.extend(callFunction8)

	pixelsStemVertical = [ 'SVTCA[1]' ]
	for stemName, stem in stemsV:
		ppm_roundsList = stem['round'].items()
		ppm_roundsList.sort(cmp=lambda (k1,v1), (k2,v2): v2-v1)
		ppmsAnd8 = [int(p[0]) for p in ppm_roundsList]+[8]
		callFunction8 = [ autoPush(stem_to_cvt[stemName], *ppmsAnd8), 'CALL[ ]' ]
		pixelsStemVertical.extend(callFunction8)

	roundZones = [ 'SVTCA[0]' ]
	callFunction7 = [ autoPush(len(stemsH) + len(stemsV) + 1, len(fm.zones), 7),
					'CALL[ ]' ]
	roundZones.extend(callFunction7)

	alignmentZones = [  autoPush(0),
					'DUP[ ]',
					'RCVT[ ]',
					'RDTG[ ]',
					'ROUND[01]',
					'RTG[ ]',
					'WCVTP[ ]'
					]
	deltaZones = []
	for zoneName, zone in fm.zones.iteritems():
		if not ('delta' in zone):
			continue
		for ppmSize, step in zone['delta'].iteritems():
			if step not in stepToSelector:
				continue
			CVT_number = zone_to_cvt[zoneName]
			relativeSize = int(ppmSize) - 9
			if 0 <= relativeSize <= 15:
				arg = (relativeSize << 4 ) + stepToSelector[step]
				deltaC = [ autoPush(arg, CVT_number, 1), 'DELTAC1[ ]' ]
			elif 16 <= relativeSize <= 31:
				arg = ((relativeSize -16) << 4 ) + stepToSelector[step]
				deltaC = [ autoPush(arg, CVT_number, 1), 'DELTAC2[ ]' ]
			elif 32 <= relativeSize <= 47:
				arg = ((relativeSize -32) << 4 ) + stepToSelector[step]
				deltaC = [ autoPush(arg, CVT_number, 1), 'DELTAC3[ ]' ]
			else:
				deltaC = []
			deltaZones.extend(deltaC)

	installControl = [ 'MPPEM[ ]' ]
	maxPPM = [autoPush(fm.codeppm)]
	installcontrol2 = [		'GT[ ]',
						'IF[ ]',
						autoPush(1),
						'ELSE[ ]',
						autoPush(0),
						'EIF[ ]',
						autoPush(1),
						'INSTCTRL[ ]'
						]
	installControl.extend(maxPPM)
	installControl.extend(installcontrol2)

	rasterSensitive = []
	if fm.deactivateStemWhenGrayScale == 1:
		rasterSensitive.extend([
					autoPush(10),
					'CALL[ ]',
					'DUP[ ]',
					autoPush(0),
					'SWAP[ ]',
					'WS[ ]',
					autoPush(1),
					'SWAP[ ]',
					'WS[ ]',
						])
	else:
		rasterSensitive.extend([
					autoPush(0),
					autoPush(0),
					'WS[ ]',
					autoPush(10),
					'CALL[ ]',
					autoPush(1),
					'SWAP[ ]',
					'WS[ ]',
					])

	table_PREP.extend(roundStemHorizontal)
	table_PREP.extend(roundStemVertical)
	table_PREP.extend(pixelsStemHorizontal)
	table_PREP.extend(pixelsStemVertical)
	table_PREP.extend(roundZones)
	table_PREP.extend(alignmentZones)
	table_PREP.extend(deltaZones)
	table_PREP.extend(installControl)
	table_PREP.extend(rasterSensitive)
	f.lib[k_prep_key] = table_PREP

	return (stem_to_cvt, zone_to_cvt, CVT)

def write_FPGM(fm):
	table_FPGM = []
	CVT_cut_in = fm.stemsnap * 4
	CutInPush = autoPush(CVT_cut_in)

	FPGM_0 = [
	autoPush(0),
	'FDEF[ ]',
		'MPPEM[ ]',
		autoPush(9),
		'LT[ ]',
		'IF[ ]',
			autoPush(1, 1),
			'INSTCTRL[ ]',
		'EIF[ ]',
		autoPush(511),
		'SCANCTRL[ ]',
		CutInPush,
		'SCVTCI[ ]',
		'PUSHW[ ] 9 3',
		'SDS[ ]',
		'SDB[ ]',
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_0)
	FPGM_1 = [
	autoPush(1),
	'FDEF[ ]',
		'DUP[ ]',
		'DUP[ ]',
		'RCVT[ ]',
		'ROUND[01]',
		'WCVTP[ ]',
		autoPush(1),
		'ADD[ ]',
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_1)
	FPGM_2 =[
	autoPush(2),
	'FDEF[ ]',
		autoPush(1),
		'LOOPCALL[ ]',
		'POP[ ]',
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_2)
	FPGM_3 = [
	autoPush(3),
	'FDEF[ ]',
		'DUP[ ]',
		'GC[0]',
		autoPush(3),
		'CINDEX[ ]',
		'GC[0]',
		'GT[ ]',
		'IF[ ]',
			'SWAP[ ]',
		'EIF[ ]',
		'DUP[ ]',
		'ROLL[ ]',
		'DUP[ ]',
		'ROLL[ ]',
		'MD[0]',
		'ABS[ ]',
		'ROLL[ ]',
		'DUP[ ]',
		'GC[0]',
		'DUP[ ]',
		'ROUND[00]',
		'SUB[ ]',
		'ABS[ ]',
		autoPush(4),
		'CINDEX[ ]',
		'GC[0]',
		'DUP[ ]',
		'ROUND[00]',
		'SUB[ ]',
		'ABS[ ]',
		'GT[ ]',
		'IF[ ]',
			'SWAP[ ]',
			'NEG[ ]',
			'ROLL[ ]',
		'EIF[ ]',
		'MDAP[1]',
		'DUP[ ]',
		autoPush(0),
		'GTEQ[ ]',
		'IF[ ]',
			'ROUND[01]',
			'DUP[ ]',
			autoPush(0),
			'EQ[ ]',
			'IF[ ]',
				'POP[ ]',
				autoPush(64),
			'EIF[ ]',
		'ELSE[ ]',
			'ROUND[01]',
			'DUP[ ]',
			autoPush(0),
			'EQ[ ]',
			'IF[ ]',
				'POP[ ]',
				autoPush(64),
				'NEG[ ]',
			'EIF[ ]',
		'EIF[ ]',
		'MSIRP[0]',
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_3)
	FPGM_4 = [
	autoPush(4),
	'FDEF[ ]',
		'DUP[ ]',
		'GC[0]',
		autoPush(4),
		'CINDEX[ ]',
		'GC[0]',
		'GT[ ]',
		'IF[ ]',
			'SWAP[ ]',
			'ROLL[ ]',
		'EIF[ ]',
		'DUP[ ]',
		'GC[0]',
		'DUP[ ]',
		'ROUND[10]',
		'SUB[ ]',
		'ABS[ ]',
		autoPush(4),
		'CINDEX[ ]',
		'GC[0]',
		'DUP[ ]',
		'ROUND[10]',
		'SUB[ ]',
		'ABS[ ]',
		'GT[ ]',
		'IF[ ]',
			'SWAP[ ]',
			'ROLL[ ]',
		'EIF[ ]',
		'MDAP[1]',
		'MIRP[11101]',
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_4)
	FPGM_5= [
	autoPush(5),
	'FDEF[ ]',
		'MPPEM[ ]',
		'DUP[ ]',
		autoPush(3),
		'MINDEX[ ]',
		'LT[ ]',
		'IF[ ]',
			'LTEQ[ ]',
			'IF[ ]',
				autoPush(128),
				'WCVTP[ ]',
			'ELSE[ ]',
				autoPush(64),
				'WCVTP[ ]',
			'EIF[ ]',
		'ELSE[ ]',
			'POP[ ]',
			'POP[ ]',
			'DUP[ ]',
			'RCVT[ ]',
			autoPush(192),
			'LT[ ]',
			'IF[ ]',
				autoPush(192),
				'WCVTP[ ]',
				'ELSE[ ]',
				'POP[ ]',
			'EIF[ ]',
		'EIF[ ]',
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_5)
	FPGM_6 = [
	autoPush(6),
	'FDEF[ ]',
		'DUP[ ]',
		'DUP[ ]',
		'RCVT[ ]',
		'ROUND[01]',
		'WCVTP[ ]',
		autoPush(1),
		'ADD[ ]',
		'DUP[ ]',
		'DUP[ ]',
		'RCVT[ ]',
		'RDTG[ ]',
		'ROUND[01]',
		'RTG[ ]',
		'WCVTP[ ]',
		autoPush(1),
		'ADD[ ]',
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_6)
	FPGM_7 = [
	autoPush(7),
	'FDEF[ ]',
		autoPush(6),
		'LOOPCALL[ ]',
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_7)
	FPGM_8 = [
	autoPush(8),
	'FDEF[ ]',
		'MPPEM[ ]',
		'DUP[ ]',
		autoPush(3),
		'MINDEX[ ]',
		'GTEQ[ ]',
		'IF[ ]',
			autoPush(64),
		'ELSE[ ]',
			autoPush(0),
		'EIF[ ]',
		'ROLL[ ]',
		'ROLL[ ]',
		'DUP[ ]',
		autoPush(3),
		'MINDEX[ ]',
		'GTEQ[ ]',
		'IF[ ]',
			'SWAP[ ]',
			'POP[ ]',
			autoPush(128),
			'ROLL[ ]',
			'ROLL[ ]',
		'ELSE[ ]',
			'ROLL[ ]',
			'SWAP[ ]',
		'EIF[ ]',
		'DUP[ ]',
		autoPush(3),
		'MINDEX[ ]',
		'GTEQ[ ]',
		'IF[ ]',
			'SWAP[ ]',
			'POP[ ]',
			autoPush(192),
			'ROLL[ ]',
			'ROLL[ ]',
		'ELSE[ ]',
			'ROLL[ ]',
			'SWAP[ ]',
		'EIF[ ]',
		'DUP[ ]',
		autoPush(3),
		'MINDEX[ ]',
		'GTEQ[ ]',
		'IF[ ]',
			'SWAP[ ]',
			'POP[ ]',
			autoPush(256),
			'ROLL[ ]',
			'ROLL[ ]',
		'ELSE[ ]',
			'ROLL[ ]',
			'SWAP[ ]',
		'EIF[ ]',
		'DUP[ ]',
		autoPush(3),
		'MINDEX[ ]',
		'GTEQ[ ]',
		'IF[ ]',
			'SWAP[ ]',
			'POP[ ]',
			autoPush(320),
			'ROLL[ ]',
			'ROLL[ ]',
			'ELSE[ ]',
			'ROLL[ ]',
			'SWAP[ ]',
		'EIF[ ]',
		'DUP[ ]',
		autoPush(3),
		'MINDEX[ ]',
		'GTEQ[ ]',
		'IF[ ]',
			autoPush(3),
			'CINDEX[ ]',
			'RCVT[ ]',
			autoPush(384),
			'LT[ ]',
			'IF[ ]',
				'SWAP[ ]',
				'POP[ ]',
				autoPush(384),
				'SWAP[ ]',
				'POP[ ]',
			'ELSE[ ]',
				autoPush(3),
				'CINDEX[ ]',
				'RCVT[ ]',
				'SWAP[ ]',
				'POP[ ]',
				'SWAP[ ]',
				'POP[ ]',
			'EIF[ ]',
		'ELSE[ ]',
			'POP[ ]',
		'EIF[ ]',
		'WCVTP[ ]',
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_8)
	FPGM_9 = [
	autoPush(9),
	'FDEF[ ]',
		'MPPEM[ ]',
		'GTEQ[ ]',
		'IF[ ]',
			'RCVT[ ]',
			'WCVTP[ ]',
		'ELSE[ ]',
			'POP[ ]',
			'POP[ ]',
		'EIF[ ]',
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_9)
	#A function to ckeck if the rasterizer is Grayscale
	FPGM_10 = [
	autoPush(10),
	'FDEF[ ]',
		autoPush(1),
		'GETINFO[ ]',
		autoPush(35),
		'GTEQ[ ] ',
		'IF[ ]',
			autoPush(2**5),
			'GETINFO[ ]',
			autoPush(2**12),
			'AND[ ]',
		'ELSE[ ]',
			autoPush(0),
		'EIF[ ]',
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_10)

	# print table_FPGM
	fm.f.lib[k_fpgm_key] = table_FPGM
