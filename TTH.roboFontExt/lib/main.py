#coding=utf-8
from mojo.events import *
from mojo.UI import *
from mojo.drawingTools import *
from vanilla import *
from AppKit import *
from robofab import plistlib

from fl_tth import *
import preview

import math, os
import freetype
import Quartz
from objc import allocateBuffer


def loadFonts():
	af = AllFonts()
	if not af:
		return
	return af

def loadCurrentFont(allFonts):
	cf = CurrentFont()
	for f in allFonts:
		if f.fileName == cf.fileName:
			return cf

def createUnicodeToNameDict():
	glyphList = open('../resources/GlyphList.txt', 'r')
	unicodeToNameDict ={}
	for i in glyphList:
		if i[:1] != '#':
			name = i.split(';')[0]
			unicodeGlyph = '0x' + i.split(';')[1][:-1]
			unicodeGlyph = unicodeGlyph.split(' ')[0]
			if int(unicodeGlyph, 16) not in unicodeToNameDict.keys():
				unicodeToNameDict[int(unicodeGlyph, 16)] = name
	return unicodeToNameDict


def getGlyphNameByUnicode(unicodeToNameDict, unicodeChar):
	return unicodeToNameDict[unicodeChar]

stepToSelector = {-8: 0, -7: 1, -6: 2, -5: 3, -4: 4, -3: 5, -2: 6, -1: 7, 1: 8, 2: 9, 3: 10, 4: 11, 5: 12, 6: 13, 7: 14, 8: 15}


class previewWindow(object):
	def __init__(self, f, TTHToolInstance):
		self.f = f
		self.TTHToolInstance = TTHToolInstance
		self.previewString = ''

		self.wPreview = FloatingWindow((210, 600, 600, 200), "Preview", closable = False)
		self.view = preview.PreviewArea.alloc().init_withTTHToolInstance(self.TTHToolInstance)

		self.view.setFrame_(((0, 0), (560, 160)))
		self.wPreview.previewEditText = EditText((10, 10, -10, 22),
										callback=self.previewEditTextCallback)
		self.wPreview.previewScrollview = ScrollView((10, 50, -10, -10),
                                self.view)

		self.wPreview.open()

	def closePreview(self):
		self.wPreview.close()

	def previewEditTextCallback(self, sender):
		self.previewString = sender.get()
		#self.makeActualSizePreviewImage(sender.get())
		self.view.setNeedsDisplay_(True)

	def makeActualSizePreviewImage(self, stringToDisplay):

		print stringToDisplay
		image = NSImage.alloc().initWithSize_(NSMakeSize(100, 100))
		print image
	#	image.lockFocus()
		pixelColor = NSColor.colorWithRed_green_blue_alpha_(0/255, 255/255, 255/255, 1)
		image_rep = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(None, 100, 100, 1, 1, True, False, NSCalibratedRGBColorSpace, 100, 0)
		#image.drawRepresentation_inRect_(image_rep, NSRect(0, 100, 100))
		print image_rep
		#image_rep.setColor_atX_y_(pixelColor, 50, 50)
		#image.addRepresentation_(image_rep)
	#	image.unlockFocus()

class centralWindow(object):
	def __init__(self, f, TTHToolInstance):
		self.f = f
		self.TTHToolInstance = TTHToolInstance
		self.wCentral = FloatingWindow((10, 30, 200, 600), "Central", closable = False)

		self.PPMSizesList = ['9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', 
							'21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
							'31', '32', '33', '34', '35', '36', '37', '38', '39', '40',
							'41', '42', '43', '44', '45', '46', '47', '48', '60', '72' ]

		self.BitmapPreviewList = ['Monochrome', 'Grayscale', 'Subpixel']

		self.wCentral.PPEMSizeText= TextBox((10, 10, 70, 14), "ppEm Size:", sizeStyle = "small")
		
		self.wCentral.PPEMSizeEditText = EditText((110, 8, 30, 19), sizeStyle = "small", 
                            callback=self.PPEMSizeEditTextCallback)

		self.wCentral.PPEMSizeEditText.set(self.TTHToolInstance.PPM_Size)
		
		self.wCentral.PPEMSizePopUpButton = PopUpButton((150, 10, 40, 14),
                              self.PPMSizesList, sizeStyle = "small",
                              callback=self.PPEMSizePopUpButtonCallback)

		self.wCentral.BitmapPreviewText= TextBox((10, 30, 70, 14), "Preview:", sizeStyle = "small")
		self.wCentral.BitmapPreviewPopUpButton = PopUpButton((90, 30, 100, 14),
                              self.BitmapPreviewList, sizeStyle = "small",
                              callback=self.BitmapPreviewPopUpButtonCallback)


		
		self.wCentral.ReadTTProgramButton = SquareButton((10, 60, -10, 22), "Read Glyph TT program", sizeStyle = 'small', 
                           					callback=self.ReadTTProgramButtonCallback)

		self.wCentral.BuildCVTButton = SquareButton((10, 82, -10, 22), "Build CVT", sizeStyle = 'small', 
                           					callback=self.BuildCVTButtonCallback)
		self.wCentral.BuildPREPButton = SquareButton((10, 104, -10, 22), "Build PREP", sizeStyle = 'small', 
                           					callback=self.BuildPREPButtonCallback)
		self.wCentral.BuildFPGMButton = SquareButton((10, 126, -10, 22), "Build FPGM", sizeStyle = 'small', 
                           					callback=self.BuildFPGMButtonCallback)
		

		self.wCentral.GeneralShowButton = SquareButton((10, -76, -10, 22), "Show General Options", sizeStyle = 'small', 
                           					callback=self.GeneralShowButtonCallback)
		self.wCentral.GeneralHideButton = SquareButton((10, -76, -10, 22), "Hide General Options", sizeStyle = 'small', 
                           					callback=self.GeneralHideButtonCallback)
		self.wCentral.GeneralHideButton.show(False)

		self.wCentral.StemsShowButton = SquareButton((10, -54, -10, 22), "Show Stems Settings", sizeStyle = 'small', 
                           					callback=self.StemsShowButtonCallback)
		self.wCentral.StemsHideButton = SquareButton((10, -54, -10, 22), "Hide Stems Settings", sizeStyle = 'small', 
                           					callback=self.StemsHideButtonCallback)
		self.wCentral.StemsHideButton.show(False)

		self.wCentral.ZonesShowButton = SquareButton((10, -32, -10, 22), "Show Zones Settings", sizeStyle = 'small', 
                           					callback=self.ZonesShowButtonCallback)
		self.wCentral.ZonesHideButton = SquareButton((10, -32, -10, 22), "Hide Zones Settings", sizeStyle = 'small', 
                           					callback=self.ZonesHideButtonCallback)
		self.wCentral.ZonesHideButton.show(False)


		self.wCentral.open()

	def closeCentral(self):
		self.wCentral.close()

	def writeCVT(self, f, UPM, alignppm, stems, zones):
		table_CVT = []
		self.stem_to_cvt = {}
		self.zone_to_cvt = {}

		cvt_index = 0
		cvt = int(math.floor(UPM/alignppm))
		table_CVT.append(cvt)

		self.stemsHorizontal = []
		self.stemsVertical = []
		for name in stems.keys():
			if stems[name]['horizontal'] == True:
				self.stemsHorizontal.append((name, stems[name]))
			else:
				self.stemsVertical.append((name, stems[name]))

		for stem in self.stemsHorizontal:
			cvt_index += 1
			cvt = stem[1]['width']
			table_CVT.append(cvt)
			self.stem_to_cvt[stem[0]] = cvt_index

		for stem in self.stemsVertical:
			cvt_index += 1
			cvt = stem[1]['width']
			table_CVT.append(cvt)
			self.stem_to_cvt[stem[0]] = cvt_index

		for name in zones.keys():
			cvt_index += 1
			cvt = zones[name]['position']
			table_CVT.append(cvt)
			self.zone_to_cvt[name] = cvt_index

			cvt_index += 1
			cvt = zones[name]['width']
			table_CVT.append(cvt)

		print table_CVT
		f.lib['com.robofont.robohint.cvt '] = table_CVT
	
	def writePREP(self, f, stems, zones, codePPM):
		table_PREP = [
		'PUSHW[ ] 0',
		'CALL[ ]'
		]
		roundStemHorizontal = [
							'SVTCA[0]'
							]
		callFunction2 = ['PUSHW[ ] ' + str(self.stem_to_cvt[self.stemsHorizontal[0][0]]) + ' ' + str(len(self.stemsHorizontal)) + ' 2']
		call = ['CALL[ ]']
		roundStemHorizontal.extend(callFunction2)
		roundStemHorizontal.extend(call)

		roundStemVertical = [
							'SVTCA[1]'
							]
		callFunction2 = ['PUSHW[ ] ' + str(self.stem_to_cvt[self.stemsVertical[0][0]]) + ' ' + str(len(self.stemsVertical)) + ' 2']
		call = ['CALL[ ]']
		roundStemVertical.extend(callFunction2)
		roundStemVertical.extend(call)


		pixelsStemHorizontal = [
							'SVTCA[0]'
							]
		for stem in self.stemsHorizontal:
			ppm_roundsList = stem[1]['round'].items()
			ppm_roundsList.sort(cmp=lambda (k1,v1), (k2,v2): v2-v1)
			ppm6 = str(int(ppm_roundsList[0][0]))
			ppm5 = str(int(ppm_roundsList[1][0]))
			ppm4 = str(int(ppm_roundsList[2][0]))
			ppm3 = str(int(ppm_roundsList[3][0]))
			ppm2 = str(int(ppm_roundsList[4][0]))
			ppm1 = str(int(ppm_roundsList[5][0]))

			callFunction8 = ['PUSHW[ ] ' +  str(self.stem_to_cvt[stem[0]]) + ' ' + ppm6 + ' ' + ppm5 + ' ' + ppm4 + ' ' + ppm3 + ' ' + ppm2 + ' ' + ppm1 + ' 8']
			call = ['CALL[ ]']

			pixelsStemHorizontal.extend(callFunction8)
			pixelsStemHorizontal.extend(call)


		pixelsStemVertical = [
							'SVTCA[1]'
							]

		for stem in self.stemsVertical:
			ppm_roundsList = stem[1]['round'].items()
			ppm_roundsList.sort(cmp=lambda (k1,v1), (k2,v2): v2-v1)
			ppm6 = str(int(ppm_roundsList[0][0]))
			ppm5 = str(int(ppm_roundsList[1][0]))
			ppm4 = str(int(ppm_roundsList[2][0]))
			ppm3 = str(int(ppm_roundsList[3][0]))
			ppm2 = str(int(ppm_roundsList[4][0]))
			ppm1 = str(int(ppm_roundsList[5][0]))

			callFunction8 = ['PUSHW[ ] ' +  str(self.stem_to_cvt[stem[0]]) + ' ' + ppm6 + ' ' + ppm5 + ' ' + ppm4 + ' ' + ppm3 + ' ' + ppm2 + ' ' + ppm1 + ' 8']
			call = ['CALL[ ]']

			pixelsStemVertical.extend(callFunction8)
			pixelsStemVertical.extend(call)

		roundZones = [
					'SVTCA[0]'
					]
		callFunction7 = ['PUSHW[ ] ' + str(len(self.stemsHorizontal) + len(self.stemsVertical) + 1) + ' ' + str(len(zones)) + ' 7']
		call = ['CALL[ ]']

		roundZones.extend(callFunction7)
		roundZones.extend(call)

		alignmentZones = [
						'PUSHW[ ] 0',
						'DUP[ ]',
						'RCVT[ ]',
						'RDTG[ ]',
						'ROUND[01]',
						'RTG[ ]',
						'WCVTP[ ]'
						]

		#Add support for zones deltas
		deltaZones = []
		for zoneName in zones.keys():
			if 'delta' in zones[zoneName].keys():
				
				for ppmSize, step in zones[zoneName]['delta'].iteritems():
					if step not in stepToSelector:
						continue
					CVT_number = self.zone_to_cvt[zoneName]
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
		table_PREP.extend(deltaZones)
		table_PREP.extend(installControl)
		print table_PREP

		f.lib['com.robofont.robohint.prep'] = table_PREP

	def writeFPGM(self, f):
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

		print table_FPGM
		f.lib['com.robofont.robohint.fpgm'] = table_FPGM

	def PPEMSizeEditTextCallback(self, sender):
		try:
			newValue = int(sender.get())
		except ValueError:
			newValue = 9
			sender.set(9)
		self.TTHToolInstance.PPM_Size = newValue
		self.TTHToolInstance.pitch = int(self.TTHToolInstance.UPM / int(self.TTHToolInstance.PPM_Size))
		self.TTHToolInstance.loadFaceGlyph(self.TTHToolInstance.g.name)
		UpdateCurrentGlyphView()
		self.TTHToolInstance.previewWindow.view.setNeedsDisplay_(True)

	def PPEMSizePopUpButtonCallback(self, sender):
		self.TTHToolInstance.PPM_Size = self.PPMSizesList[sender.get()]
		self.wCentral.PPEMSizeEditText.set(self.TTHToolInstance.PPM_Size)
		self.TTHToolInstance.pitch = int(self.TTHToolInstance.UPM / int(self.TTHToolInstance.PPM_Size))
		self.TTHToolInstance.loadFaceGlyph(self.TTHToolInstance.g.name)
		UpdateCurrentGlyphView()
		self.TTHToolInstance.previewWindow.view.setNeedsDisplay_(True)

	def BitmapPreviewPopUpButtonCallback(self, sender):
		self.TTHToolInstance.bitmapPreviewSelection = self.BitmapPreviewList[sender.get()]
		self.TTHToolInstance.loadFaceGlyph(self.TTHToolInstance.g.name)
		UpdateCurrentGlyphView()
		self.TTHToolInstance.previewWindow.view.setNeedsDisplay_(True)

	def GeneralShowButtonCallback(self, sender):
		self.wCentral.GeneralHideButton.show(True)
		self.wCentral.GeneralShowButton.show(False)
		self.TTHToolInstance.FL_Windows.showGeneral()

	def GeneralHideButtonCallback(self, sender):
		self.wCentral.GeneralHideButton.show(False)
		self.wCentral.GeneralShowButton.show(True)
		self.TTHToolInstance.FL_Windows.hideGeneral()

	def StemsShowButtonCallback(self, sender):
		self.wCentral.StemsHideButton.show(True)
		self.wCentral.StemsShowButton.show(False)
		self.TTHToolInstance.FL_Windows.showStems()

	def StemsHideButtonCallback(self, sender):
		self.wCentral.StemsHideButton.show(False)
		self.wCentral.StemsShowButton.show(True)
		self.TTHToolInstance.FL_Windows.hideStems()

	def ZonesShowButtonCallback(self, sender):
		self.wCentral.ZonesHideButton.show(True)
		self.wCentral.ZonesShowButton.show(False)
		self.TTHToolInstance.FL_Windows.showZones()

	def ZonesHideButtonCallback(self, sender):
		self.wCentral.ZonesHideButton.show(False)
		self.wCentral.ZonesShowButton.show(True)
		self.TTHToolInstance.FL_Windows.hideZones()

	def ReadTTProgramButtonCallback(self, sender):
		self.TTHToolInstance.readGlyphTTProgram(CurrentGlyph())

	def BuildCVTButtonCallback(self, sender):
		self.writeCVT(self.f, self.f.info.unitsPerEm, self.TTHToolInstance.FL_Windows.alignppm, self.TTHToolInstance.FL_Windows.stems, self.TTHToolInstance.FL_Windows.zones)

	def BuildPREPButtonCallback(self, sender):
		self.writePREP(self.f, self.TTHToolInstance.FL_Windows.stems, self.TTHToolInstance.FL_Windows.zones, self.TTHToolInstance.FL_Windows.codeppm)

	def BuildFPGMButtonCallback(self, sender):
		self.writeFPGM(self.f)


class TTHCommand(object):
	def __init__(self, command, TTHToolInstance):
		self.code = command['code']
		#print '---> code:', self.code

		if self.code == 'alignv' or self.code == 'alignh':
			self.point = command['point']
			# if self.point == 'rsb' or self.point == 'lsb':
			# 	print 'point:', self.point
			# else:
			# 	print 'point:', TTHToolInstance.pointNameToUniqueID[self.point]

			self.align = command['align']
			# print 'align:', self.align

		if self.code == 'alignt' or self.code == 'alignb':
			self.point = command['point']
			# if self.point == 'rsb' or self.point == 'lsb':
			# 	print 'point:', self.point
			# else:
			# 	print 'point:', TTHToolInstance.pointNameToUniqueID[self.point]

			self.zone = command['zone']
			# print 'zone:', self.zone
			

		if self.code == 'singleh' or self.code == 'singlev':
			self.point1 = command['point1']
			# if self.point1 == 'rsb' or self.point1 == 'lsb':
			# 	print 'point1:', self.point1
			# else:
			# 	print 'point1:', TTHToolInstance.pointNameToUniqueID[self.point1]

			self.point2 = command['point2']
			# if self.point2 == 'rsb' or self.point2 == 'lsb':
			# 	print 'point2:', self.point2
			# else:
			# 	print 'point2:', TTHToolInstance.pointNameToUniqueID[self.point2]

			if 'stem' in command.keys():
				self.stem = command['stem']
				# print 'stem:', self.stem
			if 'round' in command.keys():
				self.round = command['round']
				# print 'round:', self.round

		if self.code == 'doubleh' or self.code == 'doublev':
			self.point1 = command['point1']
			# if self.point1 == 'rsb' or self.point1 == 'lsb':
			# 	print 'point1:', self.point1
			# else:
			# 	print 'point1:', TTHToolInstance.pointNameToUniqueID[self.point1]

			self.point2 = command['point2']
			# if self.point2 == 'rsb' or self.point2 == 'lsb':
			# 	print 'point2:', self.point2
			# else:
			# 	print 'point2:', TTHToolInstance.pointNameToUniqueID[self.point2]

			if 'stem' in command.keys():
				self.stem = command['stem']
				# print 'stem:', stem
			if 'round' in command.keys():
				self.round = command['round']
				# print 'round:', self.round

		if self.code == 'mdeltav' or self.code == 'mdeltah':
			self.point = command['point']
			# if self.point == 'rsb' or self.point == 'lsb':
			# 	print 'point:', self.point
			# else:
			# 	print 'point:', TTHToolInstance.pointNameToUniqueID[self.point]

			self.delta = command['delta']
			# print 'delta:', self.delta
			self.ppm1 = command['ppm1']
			# print 'ppm1:', self.ppm1
			self.ppm2 = command['ppm2']
			# print 'ppm2', self.ppm2

		if self.code == 'fdeltav' or self.code == 'fdeltah':
			self.point = command['point']
			# if self.point == 'rsb' or self.point == 'lsb':
			# 	print 'point:', self.point
			# else:
			# 	print 'point:', TTHToolInstance.pointNameToUniqueID[self.point]

			self.delta = command['delta']
			# print 'delta:', self.delta
			self.ppm1 = command['ppm1']
			# print 'ppm1:', self.ppm1
			self.ppm2 = command['ppm2']
			# print 'ppm2', self.ppm2

		if self.code == 'interpolatev' or self.code == 'interpolateh':
			self.point = command['point']
			# if self.point == 'rsb' or self.point == 'lsb':
			# 	print 'point:', self.point
			# else:
			# 	print 'point:', TTHToolInstance.pointNameToUniqueID[self.point]

			self.point1 = command['point1']
			# if self.point1 == 'rsb' or self.point1 == 'lsb':
			# 	print 'point1:', self.point1
			# else:
			# 	print 'point1:', TTHToolInstance.pointNameToUniqueID[self.point1]

			self.point2 = command['point2']
			# if self.point2 == 'rsb' or self.point2 == 'lsb':
			# 	print 'point2:', self.point2
			# else:
			# 	print 'point2:', TTHToolInstance.pointNameToUniqueID[self.point2]
			if 'align' in command.keys():
				self.align = command['align']
				# print 'align:', self.align


class TTHTool(BaseEventTool):

	def __init__(self):
		BaseEventTool.__init__(self)
		self.PPM_Size = 9
		self.ready = False
		self.key = False
		self.unicodeToNameDict = createUnicodeToNameDict()

	def getGlyphIndexByName(self, glyphName):
		try:
			return self.indexOfGlyphNames[glyphName]
		except:
			return None

	def getGlyphNameByIndex(self, glyphIndex, font):
		try:
			return font.lib['public.glyphOrder'][glyphIndex]
		except:
			return None

	### TTH freetype ###
	def generateTempFont(self):
		tempFont = RFont(showUI=False)
		tempGlyph = self.g.copy()

		tempFont.info.unitsPerEm = CurrentFont().info.unitsPerEm
		tempFont.info.ascender = CurrentFont().info.ascender
		tempFont.info.descender = CurrentFont().info.descender
		tempFont.info.xHeight = CurrentFont().info.xHeight
		tempFont.info.capHeight = CurrentFont().info.capHeight

		tempFont.info.familyName = CurrentFont().info.familyName
		tempFont.info.styleName = CurrentFont().info.styleName
		try:
			tempFont.lib['com.robofont.robohint.cvt '] = CurrentFont().lib['com.robofont.robohint.cvt ']
			tempFont.lib['com.robofont.robohint.prep'] = CurrentFont().lib['com.robofont.robohint.prep']
			tempFont.lib['com.robofont.robohint.fpgm'] = CurrentFont().lib['com.robofont.robohint.fpgm']
		except:
			pass

		tempFont.newGlyph(self.g.name)
		tempFont[self.g.name] = tempGlyph

		tempFont.generate(self.tempfontpath, 'ttf', decompose = False, checkOutlines = False, autohint = False, releaseMode = False, glyphOrder=None, progressBar = None )
		self.tempSingleGlyphUFO = OpenFont(self.tempfontpath, showUI=False)

	def deleteTempFont(self):
		os.remove(self.tempfontpath)

	def generateFullTempFont(self):
		root =  os.path.split(self.f.path)[0]
		tail = 'Fulltemp.ttf'
		self.fulltempfontpath = os.path.join(root, tail)

		self.f.generate(self.fulltempfontpath,'ttf', decompose = False, checkOutlines = False, autohint = False, releaseMode = False, glyphOrder=None, progressBar = None )
		self.tempFullUFO = OpenFont(self.fulltempfontpath, showUI=False)



	def mergeSingleGlyphTempFontInFullTempFont(self):
		
		glyphNameToCopy = self.getGlyphNameByIndex(2, self.tempSingleGlyphUFO)

		glyphToCopy = self.tempSingleGlyphUFO[glyphNameToCopy].copy()
		self.tempFullUFO[glyphNameToCopy] = glyphToCopy


	def loadGeneratedGlyphIntoLayer(self):
		tempUFO = OpenFont(self.tempfontpath, showUI=False)
		for temp_g in tempUFO:
			if temp_g.name == self.g.name:
				sourceLayer = temp_g.getLayer("foreground")
				targetLayer = self.g.getLayer("TTH_workingSpace")
				targetLayer.clear()
		 		targetWidth = self.g.width
		 		self.g.flipLayers("foreground", "TTH_workingSpace")
		 		self.f[self.g.name] = temp_g.copy()
		 		self.f[self.g.name].width = targetWidth
		 		self.g.update()


	def loadFaceGlyph(self, glyphName):
		
		self.face.set_pixel_sizes(int(self.PPM_Size), int(self.PPM_Size))
		g_index = self.getGlyphIndexByName(glyphName)
		if self.bitmapPreviewSelection == 'Monochrome':
			self.face.load_glyph(g_index, freetype.FT_LOAD_RENDER |
    	                    freetype.FT_LOAD_TARGET_MONO )
		elif self.bitmapPreviewSelection == 'Grayscale':
			self.face.load_glyph(g_index, freetype.FT_LOAD_RENDER |
							freetype.FT_LOAD_TARGET_NORMAL)
		elif self.bitmapPreviewSelection == 'Subpixel':
			self.face.load_glyph(g_index, freetype.FT_LOAD_RENDER |
                       freetype.FT_LOAD_TARGET_LCD )
		else:
			self.face.load_glyph(g_index)


		self.adaptedOutline_points = []
		for i in range(len(self.face.glyph.outline.points)):
			self.adaptedOutline_points.append( (int( self.pitch*self.face.glyph.outline.points[i][0]/64), int( self.pitch*self.face.glyph.outline.points[i][1]/64  )) )

	def resetfonts(self):

		self.allFonts = loadFonts()
		if not self.allFonts:
			return
		self.f = loadCurrentFont(self.allFonts)
		
		self.g = CurrentGlyph()

		self.generateFullTempFont()
		self.indexOfGlyphNames = dict([(self.tempFullUFO.lib['public.glyphOrder'][idx], idx) for idx in range(len(self.tempFullUFO.lib['public.glyphOrder']))])

		self.UPM = self.f.info.unitsPerEm
		self.pitch = int(self.UPM) / int(self.PPM_Size)

		self.FL_Windows = FL_TTH_Windows(self.f)
		self.centralWindow = centralWindow(self.f, self)
		self.previewWindow = previewWindow(self.f, self)


	def resetglyph(self):
		
		root =  os.path.split(self.f.path)[0]
		tail = 'temp.ttf'
		self.tempfontpath = os.path.join(root, tail)

		self.g = CurrentGlyph()
		if self.g != None:
			self.generateTempFont()
			self.face = freetype.Face(self.fulltempfontpath)
			self.loadFaceGlyph(self.g.name)
			self.mergeSingleGlyphTempFontInFullTempFont()
			self.face = freetype.Face(self.fulltempfontpath)
			self.ready = True
		
	def becomeActive(self):
		self.resetfonts()
		self.bitmapPreviewSelection = 'Monochrome'

	def becomeInactive(self):
		try:
			self.FL_Windows.closeAll()
			self.centralWindow.closeCentral()
			self.previewWindow.closePreview()
		except:
			pass

	def fontResignCurrent(self, font):
		try:
			self.FL_Windows.closeAll()
			self.centralWindow.closeCentral()
			self.previewWindow.closePreview()
			self.resetfonts()
			self.resetglyph()
		except:
			pass

	def fontBecameCurrent(self, font):
		try:
			self.FL_Windows.closeAll()
			self.centralWindow.closeCentral()
			self.previewWindow.closePreview()
			self.resetfonts()
			self.resetglyph()
		except:
			pass

	def viewDidChangeGlyph(self):
		self.resetglyph()
		self.previewWindow.view.setNeedsDisplay_(True)
		self.readGlyphTTProgram(self.g)


	#########################
	def makePointNameToUniqueIDDict(self, g):
		pointNameToUniqueID = {}
		for contour in g:
			for point in contour.points:
				if point.name:
					name =  point.name.split(',')[0]
					uniqueID = point.naked().uniqueID
					pointNameToUniqueID[name] = uniqueID
		return pointNameToUniqueID


	def readGlyphTTProgram(self, g):
		if g == None:
			return
		if 'com.fontlab.ttprogram' in g.lib.keys():
			ttprogram = g.lib['com.fontlab.ttprogram']
			ttprogram = str(ttprogram).split('\\n')
			#print 'TT Program for glyph', g.name
			self.glyphTTHCommands = []
			#print ttprogram
			for line in ttprogram[1:-2]:
				TTHCommandList = []
				TTHCommandDict = {}
				for settings in line[9:-2].split('='):
					setting = settings.split ('"')
					for command in setting:
						if command != '':
							if command[0] == ' ':
								command = command[1:]
							TTHCommandList.append(command)
				for i in range(0, len(TTHCommandList), 2):
					TTHCommandDict[TTHCommandList[i]] = TTHCommandList[i+1]

				self.glyphTTHCommands.append(TTHCommand(TTHCommandDict, self))

			self.pointNameToUniqueID = self.makePointNameToUniqueIDDict(g)

	#def writeGlyphTTProgram(self, g, glyphTTHCommands):

	#########################


	def drawGrid(self, scale, pitch):
		for xPos in range(0, 5000, int(pitch)):
			pathX = NSBezierPath.bezierPath()
			pathX.moveToPoint_((xPos, -5000))
			pathX.lineToPoint_((xPos, 5000))
			NSColor.colorWithRed_green_blue_alpha_(0, 0, 0, 0.1).set()
			pathX.setLineWidth_(scale)
			pathX.stroke()
		for xPos in range(0, -5000, -int(pitch)):
			pathX = NSBezierPath.bezierPath()
			pathX.moveToPoint_((xPos, -5000))
			pathX.lineToPoint_((xPos, 5000))
			NSColor.colorWithRed_green_blue_alpha_(0, 0, 0, 0.1).set()
			pathX.setLineWidth_(scale)
			pathX.stroke()
		for yPos in range(0, 5000, int(pitch)):
			pathX = NSBezierPath.bezierPath()
			pathX.moveToPoint_((-5000, yPos))
			pathX.lineToPoint_((5000, yPos))
			NSColor.colorWithRed_green_blue_alpha_(0, 0, 0, 0.1).set()
			pathX.setLineWidth_(scale)
			pathX.stroke()
		for yPos in range(0, -5000, -int(pitch)):
			pathX = NSBezierPath.bezierPath()
			pathX.moveToPoint_((-5000, yPos))
			pathX.lineToPoint_((5000, yPos))
			NSColor.colorWithRed_green_blue_alpha_(0, 0, 0, 0.1).set()
			pathX.setLineWidth_(scale)
			pathX.stroke()

	def drawZones(self, scale):

		for zone in self.FL_Windows.topZonesList:
			y_start = int(zone['Position'])
			y_end = int(zone['Width'])
			pathZone = NSBezierPath.bezierPath()
			pathZone.moveToPoint_((-5000, y_start))
			pathZone.lineToPoint_((5000, y_start))
			pathZone.lineToPoint_((5000, y_start+y_end))
			pathZone.lineToPoint_((-5000, y_start+y_end))
			pathZone.closePath
			NSColor.colorWithRed_green_blue_alpha_(0/255, 180/255, 50/255, .2).set()
			pathZone.fill()	
		for zone in self.FL_Windows.bottomZonesList:
			y_start = int(zone['Position'])
			y_end = int(zone['Width'])
			pathZone = NSBezierPath.bezierPath()
			pathZone.moveToPoint_((-5000, y_start))
			pathZone.lineToPoint_((5000, y_start))
			pathZone.lineToPoint_((5000, y_start-y_end))
			pathZone.lineToPoint_((-5000, y_start-y_end))
			pathZone.closePath
			NSColor.colorWithRed_green_blue_alpha_(0/255, 180/255, 50/255, .2).set()
			pathZone.fill()	

	def drawBitmapSubPixel(self, pitch, face):
		data = []
		for i in range(face.glyph.bitmap.rows):
			data.append(face.glyph.bitmap.buffer[i*face.glyph.bitmap.pitch:i*face.glyph.bitmap.pitch+face.glyph.bitmap.width])
		
		y = face.glyph.bitmap_top*pitch
		for row_index in range(len(data)):
			y -= pitch
			x = face.glyph.bitmap_left*pitch -pitch/3
			for pix_index in range(len(data[row_index])):
				x += pitch/3
				pix_color = data[row_index][pix_index]

				rect = NSBezierPath.bezierPath()
				rect.moveToPoint_((x, y))
				rect.lineToPoint_((x+pitch/3, y))
				rect.lineToPoint_((x+pitch/3, y+pitch))
				rect.lineToPoint_((x, y+pitch))
				rect.closePath
				NSColor.colorWithRed_green_blue_alpha_(0/255, 0/255, 0/255, .5*pix_color/255).set()
				rect.fill()

	def drawBitmapSubPixelColor(self, pitch, advance, height, alpha, face):
		pyBuffer = face.glyph.bitmap.buffer
		if len(pyBuffer) == 0:
			return
		data = []
		for i in range(face.glyph.bitmap.rows):
			data.append(pyBuffer[i*face.glyph.bitmap.pitch:i*face.glyph.bitmap.pitch+face.glyph.bitmap.width])
		
		row_len = len(data[0])
		rect = NSMakeRect(face.glyph.bitmap_left * pitch + advance,
			face.glyph.bitmap_top * pitch - pitch + height,
			pitch, pitch)
		for row_index in range(len(data)):
			for pix_index in range(0, row_len, 3):
				red = 255 - data[row_index][pix_index]
				green = 255 - data[row_index][pix_index+1]
				blue = 255 - data[row_index][pix_index+2]
				gray = red * 0.3086 + green * 0.6094 + blue * 0.0820
				s = 0.4
				red = (red * s + gray * (1-s)) / 255
				green = (green * s + gray * (1-s)) / 255
				blue = (blue * s + gray * (1-s)) / 255
				NSColor.colorWithRed_green_blue_alpha_(red, green, blue, alpha).set()
				NSBezierPath.fillRect_(rect)
				rect.origin.x += pitch
			rect.origin.x -= int(row_len / 3) * pitch # on rembobine
			rect.origin.y -= pitch

	def drawBitmapSubPixelColorNew(self, pitch, advance, height, alpha, face):
		pyBuffer = face.glyph.bitmap.buffer
		if len(pyBuffer) == 0:
			return
		print len(pyBuffer)
		print face.glyph.bitmap.rows
		print face.glyph.bitmap.width
		print face.glyph.bitmap.pitch
		colorspace = Quartz.CGColorSpaceCreateDeviceRGB()
		buf = allocateBuffer(len(pyBuffer))
		for i in range(len(pyBuffer)):
			buf[i] = pyBuffer[i]

		provider = Quartz.CGDataProviderCreateWithData(None, buf, face.glyph.bitmap.rows*face.glyph.bitmap.pitch, None)

		cgimg = Quartz.CGImageCreate(
                         face.glyph.bitmap.width,
                         face.glyph.bitmap.rows,
                         8, # bit per component
                         24, # size_t bitsPerPixel,
                         face.glyph.bitmap.pitch, # size_t bytesPerRow,
                         colorspace, # CGColorSpaceRef colorspace,
                         Quartz.kCGImageAlphaNone, # CGBitmapInfo bitmapInfo,
                         provider, # CGDataProviderRef provider,
                         None, # const CGFloat decode[],
                         False, # bool shouldInterpolate,
                         Quartz.kCGRenderingIntentDefault # CGColorRenderingIntent intent
                         )
		destRect = Quartz.CGRectMake(face.glyph.bitmap_left*pitch + advance, (face.glyph.bitmap_top-face.glyph.bitmap.rows)*pitch + height, face.glyph.bitmap.width*pitch, face.glyph.bitmap.rows*pitch)
		
		context = NSGraphicsContext.currentContext()
		if alpha < 1:
			Quartz.CGContextSetAlpha(context.graphicsPort(), alpha)
		Quartz.CGContextSetBlendMode(context.graphicsPort(), Quartz.kCGBlendModeMultiply)
		Quartz.CGContextSetInterpolationQuality(context.graphicsPort(), Quartz.kCGInterpolationNone)
		Quartz.CGContextDrawImage(context.graphicsPort(),
                               destRect, cgimg )
		Quartz.CGContextSetAlpha(context.graphicsPort(), 1)
		Quartz.CGContextSetBlendMode(context.graphicsPort(), Quartz.kCGBlendModeNormal)


	def drawBitmapGray(self, pitch, advance, height, alpha, face):
		pyBuffer = face.glyph.bitmap.buffer
		if len(pyBuffer) == 0:
			return

		colorspace = Quartz.CGColorSpaceCreateDeviceGray()
		buf = allocateBuffer(len(pyBuffer))
		for i in range(len(pyBuffer)):
			buf[i] = 255 - pyBuffer[i]

		provider = Quartz.CGDataProviderCreateWithData(None, buf, face.glyph.bitmap.rows*face.glyph.bitmap.pitch, None)

		cgimg = Quartz.CGImageCreate(
                         face.glyph.bitmap.width,
                         face.glyph.bitmap.rows,
                         8, # bit per component
                         8, # size_t bitsPerPixel,
                         face.glyph.bitmap.pitch, # size_t bytesPerRow,
                         colorspace, # CGColorSpaceRef colorspace,
                         Quartz.kCGBitmapByteOrderDefault, # CGBitmapInfo bitmapInfo,
                         provider, # CGDataProviderRef provider,
                         None, # const CGFloat decode[],
                         False, # bool shouldInterpolate,
                         Quartz.kCGRenderingIntentDefault # CGColorRenderingIntent intent
                         )
		destRect = Quartz.CGRectMake(face.glyph.bitmap_left*pitch + advance, (face.glyph.bitmap_top-face.glyph.bitmap.rows)*pitch + height, face.glyph.bitmap.width*pitch, face.glyph.bitmap.rows*pitch)
		
		context = NSGraphicsContext.currentContext()
		if alpha < 1:
			Quartz.CGContextSetAlpha(context.graphicsPort(), alpha)
		Quartz.CGContextSetBlendMode(context.graphicsPort(), Quartz.kCGBlendModeMultiply)
		Quartz.CGContextSetInterpolationQuality(context.graphicsPort(), Quartz.kCGInterpolationNone)
		Quartz.CGContextDrawImage(context.graphicsPort(),
                               destRect, cgimg )
		Quartz.CGContextSetAlpha(context.graphicsPort(), 1)
		Quartz.CGContextSetBlendMode(context.graphicsPort(), Quartz.kCGBlendModeNormal)


	def drawBitmapMono(self, pitch, advance, height, alpha, face):
		pyBuffer = face.glyph.bitmap.buffer
		if len(pyBuffer) == 0:
			return

		colorspace = Quartz.CGColorSpaceCreateDeviceGray()
		buf = allocateBuffer(len(pyBuffer))
		for i in range(len(pyBuffer)):
			buf[i] = pyBuffer[i]^255

		provider = Quartz.CGDataProviderCreateWithData(None, buf, face.glyph.bitmap.rows*face.glyph.bitmap.pitch, None)

		cgimg = Quartz.CGImageCreate(
                         face.glyph.bitmap.width,
                         face.glyph.bitmap.rows,
                         1, # bit per component
                         1, # size_t bitsPerPixel,
                         face.glyph.bitmap.pitch, # size_t bytesPerRow,
                         colorspace, # CGColorSpaceRef colorspace,
                         Quartz.kCGBitmapByteOrderDefault, # CGBitmapInfo bitmapInfo,
                         provider, # CGDataProviderRef provider,
                         None, # const CGFloat decode[],
                         False, # bool shouldInterpolate,
                         Quartz.kCGRenderingIntentDefault # CGColorRenderingIntent intent
                         )
		destRect = Quartz.CGRectMake(face.glyph.bitmap_left*pitch + advance, (face.glyph.bitmap_top-face.glyph.bitmap.rows)*pitch + height, face.glyph.bitmap.width*pitch, face.glyph.bitmap.rows*pitch)
		
		context = NSGraphicsContext.currentContext()
		if alpha < 1:
			Quartz.CGContextSetAlpha(context.graphicsPort(), alpha)
		Quartz.CGContextSetBlendMode(context.graphicsPort(), Quartz.kCGBlendModeMultiply)
		Quartz.CGContextSetInterpolationQuality(context.graphicsPort(), Quartz.kCGInterpolationNone)
		Quartz.CGContextDrawImage(context.graphicsPort(),
                               destRect, cgimg )
		Quartz.CGContextSetAlpha(context.graphicsPort(), 1)
		Quartz.CGContextSetBlendMode(context.graphicsPort(), Quartz.kCGBlendModeNormal)



	def drawOutline(self, scale, face):
		#print outline.contours
		if len(face.glyph.outline.contours) == 0:
			return

		pathContour = NSBezierPath.bezierPath()
		start, end = 0, 0		
		for c_index in range(len(face.glyph.outline.contours)):
			end    = face.glyph.outline.contours[c_index]
			points = self.adaptedOutline_points[start:end+1] 
			points.append(points[0])
			tags   = face.glyph.outline.tags[start:end+1]
			tags.append(tags[0])

			segments = [ [points[0],], ]

			for j in range(1, len(points) ):
				segments[-1].append(points[j])
				if tags[j] & (1 << 0) and j < (len(points)-1):
					segments.append( [points[j],] )
			pathContour.moveToPoint_((points[0][0], points[0][1]))
			for segment in segments:
				if len(segment) == 2:
					pathContour.lineToPoint_(segment[1])
				else:
					onCurve = segment[0]
					for i in range(1,len(segment)-2):
						A,B = segment[i], segment[i+1]
						nextOn = ((A[0]+B[0])/2.0, (A[1]+B[1])/2.0)
						antenne1 = ((onCurve[0] + 2 * A[0]) / 3.0 , (onCurve[1] + 2 * A[1]) / 3.0)
						antenne2 = ((nextOn[0] + 2 * A[0]) / 3.0 , (nextOn[1] + 2 * A[1]) / 3.0)
						pathContour.curveToPoint_controlPoint1_controlPoint2_(nextOn, antenne1, antenne2)
						onCurve = nextOn
					nextOn = segment[-1]
					A = segment[-2]
					antenne1 = ((onCurve[0] + 2 * A[0]) / 3.0 , (onCurve[1] + 2 * A[1]) / 3.0)
					antenne2 = ((nextOn[0] + 2 * A[0]) / 3.0 , (nextOn[1] + 2 * A[1]) / 3.0)
					pathContour.curveToPoint_controlPoint1_controlPoint2_(nextOn, antenne1, antenne2)


			start = end+1

			NSColor.colorWithRed_green_blue_alpha_(0/255, 255/255, 255/255, .5).set()
			pathContour.setLineWidth_(scale)
			pathContour.stroke()
		
	

	def drawPreview(self):
		if self.ready == False:
			return

		self.advance = 10
		startgname = False
		gname = ''
		gnametemp = ''
		count = 0
		for c in self.previewWindow.previewString:
			gname = ''
			count += 1
			if c != '@' and c != '/' and startgname != True:
				unicodeGlyph = ord(c)
				gname = getGlyphNameByUnicode(self.unicodeToNameDict, unicodeGlyph)
			elif c == '@':
				gname = CurrentGlyph().name
			elif c =='/' or c == ' ' :
				if gnametemp in self.tempFullUFO.keys():
					gname = gnametemp
					gnametemp = ''
				if startgname != True:
					startgname = True
				else:
					startgname = False
			elif startgname == True:
				gnametemp += c

			if gname not in self.tempFullUFO.keys():
				continue
			self.loadFaceGlyph(gname)
			if self.bitmapPreviewSelection == 'Monochrome':
				self.drawBitmapMono(1, self.advance, 50, 1, self.face)
			elif self.bitmapPreviewSelection == 'Grayscale':
				self.drawBitmapGray(1, self.advance, 50, 1, self.face)
			elif self.bitmapPreviewSelection == 'Subpixel':
				self.drawBitmapSubPixelColor(1, self.advance, 50, 1, self.face)
			
			self.advance += self.f[gname].width/self.pitch

	def drawAlign(self, scale, pointID, angle):
		#print 'alignh point', pointID
		x = None
		y = None
		if pointID != 'lsb' and pointID != 'rsb':
			for contour in self.g:
				for point in contour.points:
					if point.naked().uniqueID == pointID:
						x = point.x
						y = point.y
		elif pointID == 'lsb':
			x, y = 0, 0
		elif pointID == 'rsb':
			x, y = self.g.width, 0

		self.drawArrowAtPoint(scale, 12, angle, x, y)
		self.drawArrowAtPoint(scale, 12, angle+180, x, y)

	def drawArrowAtPoint(self, scale, r, a, x, y):
	 	arrowAngle = math.radians(20)
	 	initAngle = math.radians(a)

		arrowPoint1_x = x + math.cos(initAngle+arrowAngle)*r*scale
		arrowPoint1_y = y + math.sin(initAngle+arrowAngle)*r*scale
		arrowPoint2_x = x + math.cos(initAngle-arrowAngle)*r*scale
		arrowPoint2_y = y + math.sin(initAngle-arrowAngle)*r*scale

		pathArrow = NSBezierPath.bezierPath()
	 	pathArrow.moveToPoint_((x, y))
		pathArrow.lineToPoint_((arrowPoint1_x, arrowPoint1_y))
		pathArrow.lineToPoint_((arrowPoint2_x, arrowPoint2_y))
		pathArrow.lineToPoint_((x, y))

		NSColor.colorWithRed_green_blue_alpha_(0, 0, 1, 1).set()
		pathArrow.setLineWidth_(scale)
		pathArrow.fill()
		NSColor.colorWithRed_green_blue_alpha_(1, 1, 1, .5).set()
		pathArrow.stroke()

	def drawDiscAtPoint(self, r, x, y):
		NSColor.colorWithRed_green_blue_alpha_(1, 0, 0, 1).set()
		NSBezierPath.bezierPathWithOvalInRect_(((x-r, y-r), (r*2, r*2))).fill()


	def drawBackground(self, scale):
		
		self.loadFaceGlyph(CurrentGlyph().name)
		if self.bitmapPreviewSelection == 'Monochrome':
			self.drawBitmapMono(self.pitch, 0, 0, .4, self.face)
		elif self.bitmapPreviewSelection == 'Grayscale':
			self.drawBitmapGray(self.pitch, 0, 0, .4, self.face)
		elif self.bitmapPreviewSelection == 'Subpixel':
			self.drawBitmapSubPixelColor(self.pitch, 0, 0, .4, self.face)

		r = 5*scale
		self.drawDiscAtPoint(r, 0, 0)
		self.drawDiscAtPoint(r, self.g.width, 0)

		self.drawGrid(scale, self.pitch)
		self.drawZones(scale)

		self.drawOutline(scale, self.face)

	def draw(self, scale):
		for c in self.glyphTTHCommands:
			if c.code == 'alignh':
				if c.point == 'lsb' or c.point == 'rsb':
					self.drawAlign(scale, c.point, 180)
				else:
					self.drawAlign(scale, self.pointNameToUniqueID[c.point], 180)
			if c.code == 'alignv' or c.code == 'alignt' or c.code == 'alignb' :
				if c.point == 'lsb' or c.point == 'rsb':
					self.drawAlign(scale, c.point, 90)
				else:
					self.drawAlign(scale, self.pointNameToUniqueID[c.point], 90)



installTool(TTHTool())

