import math
from fontTools.ttLib.tables._g_a_s_p import GASP_SYMMETRIC_GRIDFIT, GASP_SYMMETRIC_SMOOTHING, GASP_DOGRAY, GASP_GRIDFIT
from lib.fontObjects.doodleFontCompiler.ttfCompiler import TTFCompilerSettings


# variables globales qui n'existent qu'en un seul exemplaire.
# peut poser probleme s'il y a plusieurs fontes ouvertes en meme temps
stem_to_cvt = {}
zone_to_cvt = {}
stepToSelector = {-8: 0, -7: 1, -6: 2, -5: 3, -4: 4, -3: 5, -2: 6, -1: 7, 1: 8, 2: 9, 3: 10, 4: 11, 5: 12, 6: 13, 7: 14, 8: 15}

def writegasp(f, gasp_ranges):
	f.lib[TTFCompilerSettings.roboHintGaspLibKey] = gasp_ranges


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

# 	f.lib[TTFCompilerSettings.roboHintGaspLibKey] = gasp_ranges

	# print "GASP_SYMMETRIC_GRIDFIT", GASP_SYMMETRIC_GRIDFIT
	# print "GASP_SYMMETRIC_SMOOTHING", GASP_SYMMETRIC_SMOOTHING
	# print "GASP_DOGRAY", GASP_DOGRAY
	# print "GASP_GRIDFIT", GASP_GRIDFIT

def writeCVTandPREP(f, UPM, alignppm, stems, zones, codePPM):
	
	f.lib[TTFCompilerSettings.roboHintMaxpMaxFunctionDefsLibKey] = 11

	table_CVT = []

	cvt_index = 0
	cvt = int(math.floor(UPM/alignppm))
	table_CVT.append(cvt)

	stemsHorizontal = []
	stemsVertical = []
	for name, stem in stems.iteritems():
		if stem['horizontal'] == True:
			stemsHorizontal.append((name, stem))
		else:
			stemsVertical.append((name, stem))

	for stem in stemsHorizontal:
		cvt_index += 1
		cvt = int(stem[1]['width'])
		table_CVT.append(cvt)
		stem_to_cvt[stem[0]] = cvt_index

	for stem in stemsVertical:
		cvt_index += 1
		cvt = int(stem[1]['width'])
		table_CVT.append(cvt)
		stem_to_cvt[stem[0]] = cvt_index

	for name, zone in zones.iteritems():
		cvt_index += 1
		cvt = int(zone['position'])
		table_CVT.append(cvt)
		zone_to_cvt[name] = cvt_index

		cvt_index += 1
		cvt = int(zone['width'])
		table_CVT.append(cvt)

	f.lib['com.robofont.robohint.cvt '] = table_CVT


	table_PREP = [
	'PUSHW[ ] 0',
	'CALL[ ]'
	]
	roundStemHorizontal = [
						'SVTCA[0]'
						]
	if stemsHorizontal != []:
		callFunction2 = [
						'PUSHW[ ] ' + str(stem_to_cvt[stemsHorizontal[0][0]]) + ' ' + str(len(stemsHorizontal)) + ' 2',
						'CALL[ ]'
						]
		roundStemHorizontal.extend(callFunction2)


	roundStemVertical = [
						'SVTCA[1]'
						]
	if stemsVertical != []:
		callFunction2 = [
						'PUSHW[ ] ' + str(stem_to_cvt[stemsVertical[0][0]]) + ' ' + str(len(stemsVertical)) + ' 2',
						'CALL[ ]'
						]
		roundStemVertical.extend(callFunction2)


	pixelsStemHorizontal = [
						'SVTCA[0]'
						]
	for stem in stemsHorizontal:
		ppm_roundsList = stem[1]['round'].items()
		ppm_roundsList.sort(cmp=lambda (k1,v1), (k2,v2): v2-v1)
		ppm6 = str(int(ppm_roundsList[0][0]))
		ppm5 = str(int(ppm_roundsList[1][0]))
		ppm4 = str(int(ppm_roundsList[2][0]))
		ppm3 = str(int(ppm_roundsList[3][0]))
		ppm2 = str(int(ppm_roundsList[4][0]))
		ppm1 = str(int(ppm_roundsList[5][0]))

		callFunction8 = [
						'PUSHW[ ] ' +  str(stem_to_cvt[stem[0]]) + ' ' + ppm6 + ' ' + ppm5 + ' ' + ppm4 + ' ' + ppm3 + ' ' + ppm2 + ' ' + ppm1 + ' 8',
						'CALL[ ]'
						]

		pixelsStemHorizontal.extend(callFunction8)


	pixelsStemVertical = [
						'SVTCA[1]'
						]

	for stem in stemsVertical:
		ppm_roundsList = stem[1]['round'].items()
		ppm_roundsList.sort(cmp=lambda (k1,v1), (k2,v2): v2-v1)
		ppm6 = str(int(ppm_roundsList[0][0]))
		ppm5 = str(int(ppm_roundsList[1][0]))
		ppm4 = str(int(ppm_roundsList[2][0]))
		ppm3 = str(int(ppm_roundsList[3][0]))
		ppm2 = str(int(ppm_roundsList[4][0]))
		ppm1 = str(int(ppm_roundsList[5][0]))

		callFunction8 = [
						'PUSHW[ ] ' +  str(stem_to_cvt[stem[0]]) + ' ' + ppm6 + ' ' + ppm5 + ' ' + ppm4 + ' ' + ppm3 + ' ' + ppm2 + ' ' + ppm1 + ' 8',
						'CALL[ ]'
						]
		pixelsStemVertical.extend(callFunction8)

	roundZones = [
				'SVTCA[0]'
				]
	callFunction7 = [
					'PUSHW[ ] ' + str(len(stemsHorizontal) + len(stemsVertical) + 1) + ' ' + str(len(zones)) + ' 7',
					'CALL[ ]'
					]

	roundZones.extend(callFunction7)

	alignmentZones = [
					'PUSHW[ ] 0',
					'DUP[ ]',
					'RCVT[ ]',
					'RDTG[ ]',
					'ROUND[01]',
					'RTG[ ]',
					'WCVTP[ ]'
					]

	deltaZones = []
	for zoneName, zone in zones.iteritems():
		if 'delta' in zone:
			
			for ppmSize, step in zone['delta'].iteritems():
				if step not in stepToSelector:
					continue
				CVT_number = zone_to_cvt[zoneName]
				relativeSize = int(ppmSize) - 9
				if 0 <= relativeSize <= 15:
					arg = (relativeSize << 4 ) + stepToSelector[step]
					deltaC = ['PUSHW[ ] ' + str(arg) + ' ' + str(CVT_number) + ' 1', 'DELTAC1[ ]']

				elif 16 <= relativeSize <= 31:
					arg = ((relativeSize -16) << 4 ) + stepToSelector[step]
					deltaC = ['PUSHW[ ] ' + str(arg) + ' ' + str(CVT_number) + ' 1', 'DELTAC2[ ]']

				elif 32 <= relativeSize <= 47:
					arg = ((relativeSize -32) << 4 ) + stepToSelector[step]
					deltaC = ['PUSHW[ ] ' + str(arg) + ' ' + str(CVT_number) + ' 1', 'DELTAC3[ ]']

				else:
					deltaC = []
				deltaZones.extend(deltaC)


	installControl = [
					'MPPEM[ ]'
					]
	maxPPM = ['PUSHW[ ] ' + str(codePPM)]
	installcontrol2 = [
						'GT[ ]',
						'IF[ ]',
						'PUSHB[ ] 1',
						'ELSE[ ]',
						'PUSHB[ ] 0',
						'EIF[ ]',
						'PUSHB[ ] 1',
						'INSTCTRL[ ]'
						]
	installControl.extend(maxPPM)
	installControl.extend(installcontrol2)

	table_PREP.extend(roundStemHorizontal)
	table_PREP.extend(roundStemVertical)
	table_PREP.extend(pixelsStemHorizontal)
	table_PREP.extend(pixelsStemVertical)
	table_PREP.extend(roundZones)
	table_PREP.extend(alignmentZones)
	table_PREP.extend(deltaZones)
	table_PREP.extend(installControl)

	f.lib['com.robofont.robohint.prep'] = table_PREP

def writeFPGM(f):
	table_FPGM = []
	CVT_cut_in = f.lib["com.fontlab.v2.tth"]["stemsnap"] * 4
	CutInPush = 'PUSHW[ ] ' + str(CVT_cut_in)

	FPGM_0= [
	'PUSHW[ ] 0',
	'FDEF[ ]',
		'MPPEM[ ]',
		'PUSHW[ ] 9',
		'LT[ ]',
		'IF[ ]',
			'PUSHB[ ] 1 1',
			'INSTCTRL[ ]',
		'EIF[ ]',
		'PUSHW[ ] 511',
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
	'PUSHW[ ] 1',
	'FDEF[ ]',
		'DUP[ ]',
		'DUP[ ]',
		'RCVT[ ]',
		'ROUND[01]',
		'WCVTP[ ]',
		'PUSHB[ ] 1',
		'ADD[ ]',
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_1)
	FPGM_2 =[
	'PUSHW[ ] 2',
	'FDEF[ ]',
		'PUSHW[ ] 1',
		'LOOPCALL[ ]',
		'POP[ ]',
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_2)
	FPGM_3 = [
	'PUSHW[ ] 3',
	'FDEF[ ]',
		'DUP[ ]',
		'GC[0]',
		'PUSHB[ ] 3',
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
		'PUSHB[ ] 4',
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
		'PUSHB[ ] 0',
		'GTEQ[ ]',
		'IF[ ]',
			'ROUND[01]',
			'DUP[ ]',
			'PUSHB[ ] 0',
			'EQ[ ]',
			'IF[ ]',
				'POP[ ]',
				'PUSHB[ ] 64',
			'EIF[ ]',
		'ELSE[ ]',
			'ROUND[01]',
			'DUP[ ]',
			'PUSHB[ ] 0',
			'EQ[ ]',
			'IF[ ]',
				'POP[ ]',
				'PUSHB[ ] 64',
				'NEG[ ]',
			'EIF[ ]',
		'EIF[ ]',
		'MSIRP[0]',
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_3)
	FPGM_4 = [
	'PUSHW[ ] 4',
	'FDEF[ ]',
		'DUP[ ]',
		'GC[0]',
		'PUSHB[ ] 4',
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
		'PUSHB[ ] 4',
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
	'PUSHW[ ] 5',
	'FDEF[ ]',
		'MPPEM[ ]',
		'DUP[ ]',
		'PUSHB[ ] 3',
		'MINDEX[ ]',
		'LT[ ]',
		'IF[ ]',
			'LTEQ[ ]',
			'IF[ ]',
				'PUSHB[ ] 128',
				'WCVTP[ ]',
			'ELSE[ ]',
				'PUSHB[ ] 64',
				'WCVTP[ ]',
			'EIF[ ]',
		'ELSE[ ]',
			'POP[ ]',
			'POP[ ]',
			'DUP[ ]',
			'RCVT[ ]',
			'PUSHB[ ] 192',
			'LT[ ]',
			'IF[ ]',
				'PUSHB[ ] 192',
				'WCVTP[ ]',
				'ELSE[ ]',
				'POP[ ]',
			'EIF[ ]',
		'EIF[ ]',
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_5)
	FPGM_6 = [
	'PUSHW[ ] 6'
	'FDEF[ ]',
		'DUP[ ]',
		'DUP[ ]',
		'RCVT[ ]',
		'ROUND[01]',
		'WCVTP[ ]',
		'PUSHB[ ] 1',
		'ADD[ ]',
		'DUP[ ]',
		'DUP[ ]',
		'RCVT[ ]',
		'RDTG[ ]',
		'ROUND[01]',
		'RTG[ ]',
		'WCVTP[ ]',
		'PUSHB[ ] 1',
		'ADD[ ]',
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_6)
	FPGM_7 = [
	'PUSHW[ ] 7',
	'FDEF[ ]',
		'PUSHW[ ] 6',
		'LOOPCALL[ ]',
	'ENDF[ ]'
	]	
	table_FPGM.extend(FPGM_7)
	FPGM_8 = [
	'PUSHW[ ] 8',
	'FDEF[ ]',
		'MPPEM[ ]',
		'DUP[ ]',
		'PUSHB[ ] 3',
		'MINDEX[ ]',
		'GTEQ[ ]',
		'IF[ ]',
			'PUSHB[ ] 64',
		'ELSE[ ]',
			'PUSHB[ ] 0',
		'EIF[ ]',
		'ROLL[ ]',
		'ROLL[ ]',
		'DUP[ ]',
		'PUSHB[ ] 3',
		'MINDEX[ ]',
		'GTEQ[ ]',
		'IF[ ]',
			'SWAP[ ]',
			'POP[ ]',
			'PUSHB[ ] 128',
			'ROLL[ ]',
			'ROLL[ ]',
		'ELSE[ ]',
			'ROLL[ ]',
			'SWAP[ ]',
		'EIF[ ]',
		'DUP[ ]',
		'PUSHB[ ] 3',
		'MINDEX[ ]',
		'GTEQ[ ]',
		'IF[ ]',
			'SWAP[ ]',
			'POP[ ]',
			'PUSHW[ ] 192',
			'ROLL[ ]',
			'ROLL[ ]',
		'ELSE[ ]',
			'ROLL[ ]',
			'SWAP[ ]',
		'EIF[ ]',
		'DUP[ ]',
		'PUSHB[ ] 3',
		'MINDEX[ ]',
		'GTEQ[ ]',
		'IF[ ]',
			'SWAP[ ]',
			'POP[ ]',
			'PUSHW[ ] 256',
			'ROLL[ ]',
			'ROLL[ ]',
		'ELSE[ ]',
			'ROLL[ ]',
			'SWAP[ ]',
		'EIF[ ]',
		'DUP[ ]',
		'PUSHB[ ] 3',
		'MINDEX[ ]',
		'GTEQ[ ]',
		'IF[ ]',
			'SWAP[ ]',
			'POP[ ]',
			'PUSHW[ ] 320',
			'ROLL[ ]',
			'ROLL[ ]',
			'ELSE[ ]',
			'ROLL[ ]',
			'SWAP[ ]',
		'EIF[ ]',
		'DUP[ ]',
		'PUSHW[ ] 3',
		'MINDEX[ ]',
		'GTEQ[ ]',
		'IF[ ]',
			'PUSHB[ ] 3',
			'CINDEX[ ]',
			'RCVT[ ]',
			'PUSHW[ ] 384',
			'LT[ ]',
			'IF[ ]',
				'SWAP[ ]',
				'POP[ ]',
				'PUSHW[ ] 384',
				'SWAP[ ]',
				'POP[ ]',
			'ELSE[ ]',
				'PUSHB[ ] 3',
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
	'PUSHW[ ] 9',
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
	#A function to ckeck if the rasterizer is SubPixel/Grayscale
	FPGM_10 = [
	'PUSHW[ ] 10',
	'FDEF[ ]',
		'PUSHW[ ] 1',
		'GETINFO[ ]',
		'PUSHW[ ] 37',
		'LTEQ[ ] ',
		'IF[ ]',
			'PUSHW[ ] 32',
			'GETINFO[ ]',
			'PUSHW[ ] 4096',
			'AND[ ]',
		'ELSE[ ]',
			'PUSHB[ ] 0',
		'EIF[ ]'
	'ENDF[ ]'
	]
	table_FPGM.extend(FPGM_10)

	# print table_FPGM
	f.lib['com.robofont.robohint.fpgm'] = table_FPGM
