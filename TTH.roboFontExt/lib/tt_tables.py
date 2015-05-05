import math
from fontTools.ttLib.tables._g_a_s_p import GASP_SYMMETRIC_GRIDFIT, GASP_SYMMETRIC_SMOOTHING, GASP_DOGRAY, GASP_GRIDFIT
from lib.fontObjects.doodleFontCompiler.ttfCompiler import TTFCompilerSettings
from commons import helperFunctions as HF

k_hdmx_key = TTFCompilerSettings.roboHintHdmxLibKey
k_VDMX_key = 'com.robofont.robohint.VDMX'
k_LTSH_key = 'com.robofont.robohint.LTSH'
k_CVT_key  = 'com.robofont.robohint.cvt '
k_prep_key = 'com.robofont.robohint.prep'
k_fpgm_key = 'com.robofont.robohint.FPGM'
k_gasp_key   = TTFCompilerSettings.roboHintGaspLibKey

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

def writehdmx(f, hdmx_ppems):
	f.lib[k_hdmx_key] = hdmx_ppems

def writeVDMX(f, VDMX):
	f.lib[k_VDMX_key] = VDMX

def writeLTSH(f, LTSH):
	f.lib[k_LTSH_key] = LTSH
		
def writegasp(fm):
	fm.f.lib[k_gasp_key] = fm.gasp_ranges

# def writegasp(f, codeppm):
# 	try:
# 		lower = str(f.info.openTypeHeadLowestRecPPEM - 1)
# 	except:
# 		lower = "7"

# 	try:
# 		stopgridfit = str(codeppm)
# 	except:
# 		stopgridfit = "72"

# 	gasp_ranges = {
# 		lower:				GASP_DOGRAY + GASP_SYMMETRIC_SMOOTHING, # lowestRecPPEM - 1
# 		"20":				GASP_GRIDFIT + GASP_DOGRAY + GASP_SYMMETRIC_GRIDFIT,
# 		stopgridfit:		GASP_GRIDFIT + GASP_DOGRAY + GASP_SYMMETRIC_GRIDFIT + GASP_SYMMETRIC_SMOOTHING, # com.fontlab.v2.tth[codeppm]
# 		"65535":			GASP_DOGRAY + GASP_SYMMETRIC_SMOOTHING
# 	}

# 	f.lib[k_gasp_key] = gasp_ranges

	# print "GASP_SYMMETRIC_GRIDFIT", GASP_SYMMETRIC_GRIDFIT
	# print "GASP_SYMMETRIC_SMOOTHING", GASP_SYMMETRIC_SMOOTHING
	# print "GASP_DOGRAY", GASP_DOGRAY
	# print "GASP_GRIDFIT", GASP_GRIDFIT

def writeCVTandPREP(fm):# 'fm' is instance of TTHFont
	f = fm.f
	f.lib[TTFCompilerSettings.roboHintMaxpMaxFunctionDefsLibKey] = 11
	f.lib[TTFCompilerSettings.roboHintMaxpMaxStorageLibKey] = 5

	stem_to_cvt = {}
	zone_to_cvt = {}
	CVT = []

	CVT.append(int(math.floor(fm.UPM / fm.alignppm)))

	stemsHorizontal = fm.horizontalStems.items()
	stemsVertical   = fm.verticalStems.items()

	for stem in stemsHorizontal + stemsVertical:
		CVT.append(int(stem[1]['width']))
		stem_to_cvt[stem[0]] = len(CVT)-1
	
	for name, zone in fm.zones.iteritems():
		CVT.append(int(zone['position']))
		zone_to_cvt[name] = len(CVT)-1
		CVT.append(int(zone['width']))

	f.lib[k_CVT_key] = CVT

	table_PREP = [ autoPush(0), 'CALL[ ]' ]
	roundStemHorizontal = [ 'SVTCA[0]' ]
	if stemsHorizontal != []:
		callFunction2 = [ # index of first ControlValue for horizontal stems, number of horizontal stems
				autoPush(stem_to_cvt[stemsHorizontal[0][0]], len(stemsHorizontal), 2),
				'CALL[ ]' ]
		roundStemHorizontal.extend(callFunction2)

	roundStemVertical = [ 'SVTCA[1]' ]
	if stemsVertical != []:
		callFunction2 = [ # index of first ControlValue for vertical stems, number of horizontal stems
				autoPush(stem_to_cvt[stemsVertical[0][0]], len(stemsVertical), 2),
				'CALL[ ]' ]
		roundStemVertical.extend(callFunction2)

	pixelsStemHorizontal = [ 'SVTCA[0]' ]
	for stemName, stem in stemsHorizontal:
		ppm_roundsList = stem['round'].items()
		ppm_roundsList.sort(cmp=lambda (k1,v1), (k2,v2): v2-v1)
		ppmsAnd8 = [int(p[0]) for p in ppm_roundsList]+[8]
		callFunction8 = [ autoPush(stem_to_cvt[stemName], *ppmsAnd8), 'CALL[ ]' ]
		pixelsStemHorizontal.extend(callFunction8)

	pixelsStemVertical = [ 'SVTCA[1]' ]
	for stemName, stem in stemsVertical:
		ppm_roundsList = stem['round'].items()
		ppm_roundsList.sort(cmp=lambda (k1,v1), (k2,v2): v2-v1)
		ppmsAnd8 = [int(p[0]) for p in ppm_roundsList]+[8]
		callFunction8 = [ autoPush(stem_to_cvt[stemName], *ppmsAnd8), 'CALL[ ]' ]
		pixelsStemVertical.extend(callFunction8)

	roundZones = [ 'SVTCA[0]' ]
	callFunction7 = [ autoPush(len(stemsHorizontal) + len(stemsVertical) + 1, len(fm.zones), 7),
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
	if f.lib['com.sansplomb.tth']['deactivateStemWhenGrayScale'] == 1:
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

	return (stem_to_cvt, zone_to_cvt)

def writeFPGM(fm):
	table_FPGM = []
	CVT_cut_in = fm.f.lib["com.fontlab.v2.tth"]["stemsnap"] * 4
	CutInPush = autoPush(CVT_cut_in)

	FPGM_0= [
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
