from vanilla import *
from mojo.UI import *
import preview

class centralWindow(object):
	def __init__(self, TTHToolInstance, tthtm):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm
		self.wCentral = FloatingWindow((10, 30, 200, 600), "Central", closable = False)

		self.PPMSizesList = ['9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', 
							'21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
							'31', '32', '33', '34', '35', '36', '37', '38', '39', '40',
							'41', '42', '43', '44', '45', '46', '47', '48', '60', '72' ]
		self.axisList = ['X', 'Y']
		self.hintingToolsList = ['Align', 'Single Link', 'Double Link', 'Interpolation', 'Middle Delta', 'Final Delta']
		if self.tthtm.selectedAxis == 'X':
			self.stemTypeList = self.tthtm.stemsListX
		else:
			self.stemTypeList = self.tthtm.stemsListY
		#self.stemsVertical = []
		# for name, stem in self.TTHToolInstance.FL_Windows.stems.iteritems():
		# 	if stem['horizontal'] == False:
		# 		self.stemsVertical.append(name)
		# self.stemTypeList.extend(self.stemsVertical)

		self.BitmapPreviewList = ['Monochrome', 'Grayscale', 'Subpixel']

		self.alignmentTypeListDisplay = ['Closest Pixel Edge', 'Left/Bottom Edge', 'Right/Top Edge', 'Center of Pixel', 'Double Grid']
		self.alignmentTypeList = ['round', 'left', 'right', 'center', 'double']

		self.alignmentTypeListLinkDisplay = ['Do Not Align to Grid', 'Closest Pixel Edge', 'Left/Bottom Edge', 'Right/Top Edge', 'Center of Pixel', 'Double Grid']
		self.alignmentTypeListLink = ['None', 'round', 'left', 'right', 'center', 'double']

		self.wCentral.PPEMSizeText= TextBox((10, 10, 70, 14), "ppEm Size:", sizeStyle = "small")
		
		self.wCentral.PPEMSizeEditText = EditText((110, 8, 30, 19), sizeStyle = "small", 
				callback=self.PPEMSizeEditTextCallback)

		self.wCentral.PPEMSizeEditText.set(self.tthtm.PPM_Size)
		
		self.wCentral.PPEMSizePopUpButton = PopUpButton((150, 10, 40, 14),
				self.PPMSizesList, sizeStyle = "small",
				callback=self.PPEMSizePopUpButtonCallback)

		self.wCentral.BitmapPreviewText= TextBox((10, 30, 70, 14), "Preview:", sizeStyle = "small")
		self.wCentral.BitmapPreviewPopUpButton = PopUpButton((90, 30, 100, 14),
				self.BitmapPreviewList, sizeStyle = "small",
				callback=self.BitmapPreviewPopUpButtonCallback)

		self.wCentral.AxisText= TextBox((10, 50, 70, 14), "Axis:", sizeStyle = "small")
		self.wCentral.AxisPopUpButton = PopUpButton((150, 50, 40, 14),
				self.axisList, sizeStyle = "small",
				callback=self.AxisPopUpButtonCallback)

		self.wCentral.HintingToolText= TextBox((10, 70, 70, 14), "Tool:", sizeStyle = "small")
		self.wCentral.HintingToolPopUpButton = PopUpButton((90, 70, 100, 14),
				self.hintingToolsList, sizeStyle = "small",
				callback=self.HintingToolPopUpButtonCallback)

		self.wCentral.AlignmentTypeText = TextBox((10, 90, 70, 14), "Alignment:", sizeStyle = "small")
		self.wCentral.AlignmentTypePopUpButton = PopUpButton((90, 90, 100, 14),
				self.alignmentTypeListDisplay, sizeStyle = "small",
				callback=self.AlignmentTypePopUpButtonCallback)
		self.wCentral.AlignmentTypeText.show(True)
		self.wCentral.AlignmentTypePopUpButton.show(True)

		self.wCentral.StemTypeText = TextBox((10, 110, 70, 14), "Stem:", sizeStyle = "small")
		self.wCentral.StemTypePopUpButton = PopUpButton((90, 110, 100, 14),
				self.stemTypeList, sizeStyle = "small",
				callback=self.StemTypePopUpButtonCallback)
		self.wCentral.StemTypeText.show(False)
		self.wCentral.StemTypePopUpButton.show(False)

		self.wCentral.RoundDistanceText = TextBox((10, 130, 180, 14), "Round Distance:", sizeStyle = "small")
		self.wCentral.RoundDistanceCheckBox = CheckBox((-22, 125, -10, 22), "", sizeStyle = "small",
				callback=self.RoundDistanceCheckBoxCallback)
		self.wCentral.RoundDistanceText.show(False)
		self.wCentral.RoundDistanceCheckBox.show(False)

		self.wCentral.DeltaOffsetText = TextBox((10, 90, 120, 14), "Delta Offset:", sizeStyle = "small")
		self.wCentral.DeltaOffsetSlider = Slider((10, 110, -10, 15), maxValue=16, value=8, tickMarkCount=17, continuous=False, stopOnTickMarks=True, sizeStyle= "small",
				callback=self.DeltaOffsetSliderCallback)
		self.wCentral.DeltaOffsetText.show(False)
		self.wCentral.DeltaOffsetSlider.show(False)

		self.wCentral.DeltaRangeText = TextBox((10, 140, 120, 14), "Delta Range:", sizeStyle = "small")
		self.wCentral.DeltaRange1EditText = EditText((110, 138, 30, 19), sizeStyle = "small", 
				callback=self.DeltaRange1EditTextCallback)
		self.wCentral.DeltaRange2EditText = EditText((150, 138, 30, 19), sizeStyle = "small", 
				callback=self.DeltaRange2EditTextCallback)
		self.wCentral.DeltaRangeText.show(False)
		self.wCentral.DeltaRange1EditText.show(False)
		self.wCentral.DeltaRange2EditText.show(False)

		self.wCentral.ReadTTProgramButton = SquareButton((10, 180, -10, 22), "Read Glyph TT program", sizeStyle = 'small', 
				callback=self.ReadTTProgramButtonCallback)
	

		self.wCentral.PreviewShowButton = SquareButton((10, -98, -10, 22), "Show Preview", sizeStyle = 'small', 
				callback=self.PreviewShowButtonCallback)
		self.wCentral.PreviewHideButton = SquareButton((10, -98, -10, 22), "Hide Preview", sizeStyle = 'small', 
				callback=self.PreviewHideButtonCallback)

		if self.tthtm.previewWindowVisible == 0:
			self.wCentral.PreviewHideButton.show(False)
			self.wCentral.PreviewShowButton.show(True)
		elif self.tthtm.previewWindowVisible == 1:
			self.wCentral.PreviewHideButton.show(True)
			self.wCentral.PreviewShowButton.show(False)

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

	def PPEMSizeEditTextCallback(self, sender):
		self.TTHToolInstance.changeSize(sender.get())

	def PPEMSizePopUpButtonCallback(self, sender):
		if self.tthtm.g == None:
			return
		size = self.PPMSizesList[sender.get()]
		self.TTHToolInstance.changeSize(size)

	def BitmapPreviewPopUpButtonCallback(self, sender):
		self.TTHToolInstance.changeBitmapPreview(self.BitmapPreviewList[sender.get()])

	def AxisPopUpButtonCallback(self, sender):
		self.TTHToolInstance.changeAxis(self.axisList[sender.get()])
		self.TTHToolInstance.makeStemsListsPopUpMenu()

		if self.tthtm.selectedAxis == 'X':
			self.wCentral.StemTypePopUpButton.setItems(self.tthtm.stemsListX)
			self.TTHToolInstance.changeSelectedStemX(self.tthtm.selectedStemX)
		else:
			self.wCentral.StemTypePopUpButton.setItems(self.tthtm.stemsListY)
			self.TTHToolInstance.changeSelectedStemY(self.tthtm.selectedStemY)

		UpdateCurrentGlyphView()

	def centralWindowLinkSettings(self):
		self.TTHToolInstance.selectedAlignmentTypeLink = self.alignmentTypeListLink[0]
		self.wCentral.AlignmentTypePopUpButton.setItems(self.alignmentTypeListLinkDisplay)
		self.wCentral.AlignmentTypeText.show(True)
		self.wCentral.AlignmentTypePopUpButton.show(True)
		self.wCentral.StemTypeText.show(True)
		self.wCentral.StemTypePopUpButton.show(True)
		self.wCentral.RoundDistanceText.show(True)
		self.wCentral.RoundDistanceCheckBox.show(True)
		self.wCentral.DeltaOffsetText.show(False)
		self.wCentral.DeltaOffsetSlider.show(False)
		self.wCentral.DeltaRangeText.show(False)
		self.wCentral.DeltaRange1EditText.show(False)
		self.wCentral.DeltaRange2EditText.show(False)

	def centralWindowDoubleLinkSettings(self):
		self.wCentral.AlignmentTypeText.show(False)
		self.wCentral.AlignmentTypePopUpButton.show(False)
		self.wCentral.StemTypeText.show(True)
		self.wCentral.StemTypePopUpButton.show(True)
		self.wCentral.RoundDistanceText.show(False)
		self.wCentral.RoundDistanceCheckBox.show(False)
		self.wCentral.DeltaOffsetText.show(False)
		self.wCentral.DeltaOffsetSlider.show(False)
		self.wCentral.DeltaRangeText.show(False)
		self.wCentral.DeltaRange1EditText.show(False)
		self.wCentral.DeltaRange2EditText.show(False)

	def centralWindowAlignSettings(self):
		self.TTHToolInstance.selectedAlignmentTypeAlign = self.alignmentTypeList[0]
		self.wCentral.AlignmentTypePopUpButton.setItems(self.alignmentTypeListDisplay)
		self.wCentral.AlignmentTypeText.show(True)
		self.wCentral.AlignmentTypePopUpButton.show(True)
		self.wCentral.StemTypeText.show(False)
		self.wCentral.StemTypePopUpButton.show(False)
		self.wCentral.RoundDistanceText.show(False)
		self.wCentral.RoundDistanceCheckBox.show(False)
		self.wCentral.DeltaOffsetText.show(False)
		self.wCentral.DeltaOffsetSlider.show(False)
		self.wCentral.DeltaRangeText.show(False)
		self.wCentral.DeltaRange1EditText.show(False)
		self.wCentral.DeltaRange2EditText.show(False)

	def centralWindowInterpolationSettings(self):
		self.TTHToolInstance.selectedAlignmentTypeLink = self.alignmentTypeListLink[0]
		self.wCentral.AlignmentTypePopUpButton.setItems(self.alignmentTypeListLinkDisplay)
		self.wCentral.AlignmentTypeText.show(True)
		self.wCentral.AlignmentTypePopUpButton.show(True)
		self.wCentral.StemTypeText.show(False)
		self.wCentral.StemTypePopUpButton.show(False)
		self.wCentral.RoundDistanceText.show(False)
		self.wCentral.RoundDistanceCheckBox.show(False)
		self.wCentral.DeltaOffsetText.show(False)
		self.wCentral.DeltaOffsetSlider.show(False)
		self.wCentral.DeltaRangeText.show(False)
		self.wCentral.DeltaRange1EditText.show(False)
		self.wCentral.DeltaRange2EditText.show(False)

	def centralWindowDeltaSettings(self):
		self.wCentral.AlignmentTypeText.show(False)
		self.wCentral.AlignmentTypePopUpButton.show(False)
		self.wCentral.StemTypeText.show(False)
		self.wCentral.StemTypePopUpButton.show(False)
		self.wCentral.RoundDistanceText.show(False)
		self.wCentral.RoundDistanceCheckBox.show(False)
		self.wCentral.DeltaOffsetText.show(True)
		self.wCentral.DeltaOffsetSlider.show(True)
		self.wCentral.DeltaRangeText.show(True)
		self.wCentral.DeltaRange1EditText.show(True)
		self.wCentral.DeltaRange2EditText.show(True)



	def HintingToolPopUpButtonCallback(self, sender):
		self.TTHToolInstance.changeSelectedHintingTool(self.hintingToolsList[sender.get()])
		#self.TTHToolInstance.changeSelectedAlignmentTypeAlign(self.tthtm.selectedAlignmentTypeAlign)
		#self.TTHToolInstance.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)

		if self.tthtm.selectedHintingTool == 'Single Link':
			self.centralWindowLinkSettings()
			self.TTHToolInstance.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)
			if self.tthtm.selectedAxis == 'X':
				self.TTHToolInstance.changeSelectedStemX(self.tthtm.selectedStemX)
			else:
				self.TTHToolInstance.changeSelectedStemY(self.tthtm.selectedStemY)
		elif self.tthtm.selectedHintingTool == 'Double Link':
			self.centralWindowDoubleLinkSettings()
			if self.tthtm.selectedAxis == 'X':
				self.TTHToolInstance.changeSelectedStemX(self.tthtm.selectedStemX)
			else:
				self.TTHToolInstance.changeSelectedStemY(self.tthtm.selectedStemY)
		elif self.tthtm.selectedHintingTool == 'Align':
			self.centralWindowAlignSettings()
			self.TTHToolInstance.changeSelectedAlignmentTypeAlign(self.tthtm.selectedAlignmentTypeAlign)
		elif self.tthtm.selectedHintingTool == 'Interpolation':
			self.centralWindowInterpolationSettings()
			self.TTHToolInstance.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)
		elif self.tthtm.selectedHintingTool in ['Middle Delta', 'Final Delta']:
			self.centralWindowDeltaSettings()
		else:
			self.wCentral.AlignmentTypeText.show(False)
			self.wCentral.AlignmentTypePopUpButton.show(False)
			self.wCentral.StemTypeText.show(False)
			self.wCentral.StemTypePopUpButton.show(False)
			self.wCentral.RoundDistanceText.show(False)
			self.wCentral.RoundDistanceCheckBox.show(False)
			self.wCentral.DeltaOffsetText.show(False)
			self.wCentral.DeltaOffsetSlider.show(False)
			self.wCentral.DeltaRangeText.show(False)
			self.wCentral.DeltaRange1EditText.show(False)
			self.wCentral.DeltaRange2EditText.show(False)


	def AlignmentTypePopUpButtonCallback(self, sender):
		if self.tthtm.selectedHintingTool in ['Single Link', 'Double Link', 'Interpolation']:
			self.TTHToolInstance.changeSelectedAlignmentTypeLink(self.alignmentTypeListLink[sender.get()])
		elif self.tthtm.selectedHintingTool == 'Align':
			self.TTHToolInstance.changeSelectedAlignmentTypeAlign(self.alignmentTypeList[sender.get()])

	def StemTypePopUpButtonCallback(self, sender):
		if self.tthtm.selectedAxis == 'X':
			self.TTHToolInstance.changeSelectedStemX(self.tthtm.stemsListX[sender.get()])
		else:
			self.TTHToolInstance.changeSelectedStemY(self.tthtm.stemsListY[sender.get()])

	def RoundDistanceCheckBoxCallback(self, sender):
		self.TTHToolInstance.changeRoundBool(sender.get())

	def DeltaOffsetSliderCallback(self, sender):
		print sender.get() - 8

	def DeltaRange1EditTextCallback(self, sender):
		print sender.get()

	def DeltaRange2EditTextCallback(self, sender):
		print sender.get()

	def ReadTTProgramButtonCallback(self, sender):
		FLTTProgram = self.TTHToolInstance.readGlyphFLTTProgram(self.tthtm.g)
		for i in FLTTProgram:
			print i

		for i in self.tthtm.g.lib['com.robofont.robohint.assembly']:
			print i

	def PreviewShowButtonCallback(self, sender):
		self.wCentral.PreviewHideButton.show(True)
		self.wCentral.PreviewShowButton.show(False)
		self.TTHToolInstance.previewWindow.showPreview()
		self.tthtm.showPreviewWindow(1)

	def PreviewHideButtonCallback(self, sender):
		self.wCentral.PreviewHideButton.show(False)
		self.wCentral.PreviewShowButton.show(True)
		self.TTHToolInstance.previewWindow.hidePreview()
		self.tthtm.showPreviewWindow(0)

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


class previewWindow(object):
	def __init__(self, TTHToolInstance, tthtm):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm

		self.wPreview = FloatingWindow((210, 600, 600, 200), "Preview", closable = False, initiallyVisible=False)
		self.view = preview.PreviewArea.alloc().init_withTTHToolInstance(self.TTHToolInstance)

		self.view.setFrame_(((0, 0), (1500, 160)))
		self.wPreview.previewEditText = EditText((10, 10, -10, 22),
				callback=self.previewEditTextCallback)
		self.wPreview.previewEditText.set(self.tthtm.previewString)
		self.wPreview.previewScrollview = ScrollView((10, 50, -10, -10),
				self.view)

		self.wPreview.open()

	def closePreview(self):
		self.wPreview.close()

	def showPreview(self):
		self.wPreview.show()

	def hidePreview(self):
		self.wPreview.hide()

	def previewEditTextCallback(self, sender):
		#self.previewString = sender.get()
		self.tthtm.setPreviewString(sender.get())
		self.view.setNeedsDisplay_(True)
