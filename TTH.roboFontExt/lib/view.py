from vanilla import *
from mojo.UI import *
from mojo.extensions import *
import preview
import view_ControlValues as CV

buttonAlignPath = ExtensionBundle("TTH").get("buttonAlign")
buttonSingleLinkPath = ExtensionBundle("TTH").get("buttonSingleLink")
buttonDoubleLinkPath = ExtensionBundle("TTH").get("buttonDoubleLink")
buttonInterpolationPath = ExtensionBundle("TTH").get("buttonInterpolation")
buttonMiddleDeltaPath = ExtensionBundle("TTH").get("buttonMiddleDelta")
buttonFinalDeltaPath = ExtensionBundle("TTH").get("buttonFinalDelta")

class centralWindow(object):
	def __init__(self, TTHToolInstance, tthtm):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm
		self.wCentral = FloatingWindow((10, 30, 200, 422), "Central", closable = False)

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
		self.wCentral.DeltaOffsetEditText = EditText((110, 90, 30, 19), sizeStyle = "small", 
				callback=self.DeltaOffsetEditTextCallback)
		self.wCentral.DeltaOffsetText.show(False)
		self.wCentral.DeltaOffsetSlider.show(False)
		self.wCentral.DeltaOffsetEditText.set(self.tthtm.deltaOffset)
		self.wCentral.DeltaOffsetEditText.show(False)

		self.wCentral.DeltaRangeText = TextBox((10, 140, 120, 14), "Delta Range:", sizeStyle = "small")
		self.wCentral.DeltaRange1EditText = EditText((110, 138, 30, 19), sizeStyle = "small", 
				callback=self.DeltaRange1EditTextCallback)
		self.wCentral.DeltaRange2EditText = EditText((150, 138, 30, 19), sizeStyle = "small", 
				callback=self.DeltaRange2EditTextCallback)
		self.wCentral.DeltaRangeText.show(False)
		self.wCentral.DeltaRange1EditText.show(False)
		self.wCentral.DeltaRange2EditText.show(False)
		self.wCentral.DeltaRange1EditText.set(self.tthtm.deltaRange1)
		self.wCentral.DeltaRange2EditText.set(self.tthtm.deltaRange2)

		self.wCentral.PrintTTProgramButton = Button((10, 180, -10, 22), "Print Glyph's Program", sizeStyle = 'small', 
				callback=self.PrintTTProgramButtonCallback)
		self.wCentral.PrintAssemblyButton = Button((10, 202, -10, 22), "Print Glyph's Assembly", sizeStyle = 'small', 
				callback=self.PrintAssemblyButtonCallback)
		self.wCentral.RefreshGlyphButton = Button((10, 241, -10, 22), "Apply Program & Refresh", sizeStyle = 'small', 
				callback=self.RefreshGlyphButtonCallback)
		self.wCentral.AlwaysRefreshText = TextBox((10, 266, 180, 14), "Always Apply & Refresh:", sizeStyle = "small")
		self.wCentral.AlwaysRefreshCheckBox = CheckBox((-22, 261, -10, 22), "", sizeStyle = "small",
				callback=self.AlwaysRefreshCheckBoxCallback)
		self.wCentral.AlwaysRefreshCheckBox.set(self.tthtm.alwaysRefresh)
	

		self.wCentral.PreviewShowButton = Button((10, -98, -10, 22), "Preview", sizeStyle = 'small', 
				callback=self.PreviewShowButtonCallback)
		self.wCentral.AlignButton = ImageButton((10, -120, 18, 18), imageObject = buttonAlignPath,
                            callback=self.InterpolationButtonCallback)
		self.wCentral.SingleLinkButton = ImageButton((28, -120, 18, 18), imageObject = buttonSingleLinkPath,
                            callback=self.InterpolationButtonCallback)
		self.wCentral.DoubleLinkButton = ImageButton((46, -120, 18, 18), imageObject = buttonDoubleLinkPath,
                            callback=self.InterpolationButtonCallback)
		self.wCentral.InterpolationButton = ImageButton((64, -120, 18, 18), imageObject = buttonInterpolationPath,
                            callback=self.InterpolationButtonCallback)		
		self.wCentral.MiddleDeltaButton = ImageButton((82, -120, 18, 18), imageObject = buttonMiddleDeltaPath,
                            callback=self.InterpolationButtonCallback)
		self.wCentral.FinalDeltaButton = ImageButton((100, -120, 18, 18), imageObject = buttonFinalDeltaPath,
                            callback=self.InterpolationButtonCallback)
		#self.wCentral.PreviewHideButton = Button((10, -98, -10, 22), "Hide Preview Window", sizeStyle = 'small', 
		#		callback=self.PreviewHideButtonCallback)

		# if self.tthtm.previewWindowVisible == 0:
		# 	self.wCentral.PreviewHideButton.show(False)
		# 	self.wCentral.PreviewShowButton.show(True)
		# elif self.tthtm.previewWindowVisible == 1:
		# 	self.wCentral.PreviewHideButton.show(True)
		# 	self.wCentral.PreviewShowButton.show(False)

		self.wCentral.ControlValuesButton = Button((10, -32, -10, 22), "Control Values", sizeStyle = 'small', 
				callback=self.ControlValuesButtonCallback)


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
		self.wCentral.DeltaOffsetEditText.show(False)

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
		self.wCentral.DeltaOffsetEditText.show(False)

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
		self.wCentral.DeltaOffsetEditText.show(False)

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
		self.wCentral.DeltaOffsetEditText.show(False)

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
		self.wCentral.DeltaOffsetEditText.show(True)



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
		self.TTHToolInstance.changeDeltaOffset(int(sender.get() - 8))

	def DeltaOffsetEditTextCallback(self, sender):
		self.TTHToolInstance.changeDeltaOffset(sender.get())

	def DeltaRange1EditTextCallback(self, sender):
		self.TTHToolInstance.changeDeltaRange(sender.get(), self.tthtm.deltaRange2)

	def DeltaRange2EditTextCallback(self, sender):
		self.TTHToolInstance.changeDeltaRange(self.tthtm.deltaRange1, sender.get())

	def PrintTTProgramButtonCallback(self, sender):
		FLTTProgram = self.TTHToolInstance.readGlyphFLTTProgram(self.tthtm.g)
		if not FLTTProgram:
			print 'There is no Program in this glyph'
			return
		for i in FLTTProgram:
			print i

	def PrintAssemblyButtonCallback(self, sender):
		glyphAssembly = ''
		if 'com.robofont.robohint.assembly' in self.tthtm.g.lib:
			glyphAssembly = self.tthtm.g.lib['com.robofont.robohint.assembly']
		if not glyphAssembly:
			print 'There is no Assembly in this glyph'
			return
		for i in glyphAssembly:
			print i

	def RefreshGlyphButtonCallback(self, sender):
		self.TTHToolInstance.refreshGlyph()
		self.TTHToolInstance.updateGlyphProgram()

	def AlwaysRefreshCheckBoxCallback(self, sender):
		self.TTHToolInstance.changeAlwaysRefresh(sender.get())

	def PreviewShowButtonCallback(self, sender):
		#self.wCentral.PreviewHideButton.show(True)
		#self.wCentral.PreviewShowButton.show(False)
		# self.TTHToolInstance.previewWindow.showPreview()
		# self.tthtm.showPreviewWindow(1)
		self.TTHToolInstance.previewWindow = previewWindow(self.TTHToolInstance, self.tthtm)

	# def PreviewHideButtonCallback(self, sender):
	# 	self.wCentral.PreviewHideButton.show(False)
	# 	self.wCentral.PreviewShowButton.show(True)
	# 	self.TTHToolInstance.previewWindow.hidePreview()
	# 	self.tthtm.showPreviewWindow(0)

	def ControlValuesButtonCallback(self, sender):
		sheet = CV.SheetControlValues(self.wCentral, self.tthtm, self.TTHToolInstance)

	def InterpolationButtonCallback(self, sender):
		pass


class previewWindow(object):
	def __init__(self, TTHToolInstance, tthtm):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm

		self.FromSize = self.tthtm.previewFrom
		self.ToSize = self.tthtm.previewTo

		self.wPreview = FloatingWindow((10, 450, 500, 300), "Preview", minSize=(300, 200))
		self.view = preview.PreviewArea.alloc().init_withTTHToolInstance(self.TTHToolInstance)

		self.view.setFrame_(((0, 0), (2000, 2000)))
		self.view.setFrameOrigin_((0, 20000))
		self.view.setAutoresizingMask_(NSViewMinXMargin | NSViewMaxXMargin | NSViewMinYMargin | NSViewMaxYMargin)
		self.wPreview.previewEditText = EditText((10, 10, -10, 22),
				callback=self.previewEditTextCallback)
		self.wPreview.previewEditText.set(self.tthtm.previewString)
		self.wPreview.previewScrollview = ScrollView((10, 50, -10, -40),
				self.view)
		self.wPreview.DisplaySizesText = TextBox((10, -30, 120, -10), "Display Sizes From:", sizeStyle = "small")
		self.wPreview.DisplayFromEditText = EditText((130, -32, 30, 19), sizeStyle = "small", 
				callback=self.DisplayFromEditTextCallback)
		self.wPreview.DisplayFromEditText.set(self.FromSize)

		self.wPreview.DisplayToSizeText = TextBox((170, -30, 22, -10), "To:", sizeStyle = "small")
		self.wPreview.DisplayToEditText = EditText((202, -32, 30, 19), sizeStyle = "small", 
				callback=self.DisplayToEditTextCallback)
		self.wPreview.DisplayToEditText.set(self.ToSize)
		self.wPreview.ApplyButton = Button((-100, -32, -10, 22), "Apply", sizeStyle = 'small', 
				callback=self.ApplyButtonCallback)
		self.tthtm.previewWindowVisible = 1
		self.wPreview.open()

	def closePreview(self):
		self.tthtm.previewWindowVisible = 0
		self.wPreview.close()

	# def showPreview(self):
	# 	self.wPreview.show()

	# def hidePreview(self):
	# 	self.wPreview.hide()

	def previewEditTextCallback(self, sender):
		self.tthtm.setPreviewString(sender.get())
		self.TTHToolInstance.updatePartialFontIfNeeded()
		self.view.setNeedsDisplay_(True)

	def DisplayFromEditTextCallback(self, sender):
		self.FromSize = self.TTHToolInstance.setPreviewSize(sender.get())

	def DisplayToEditTextCallback(self, sender):
		self.ToSize = self.TTHToolInstance.setPreviewSize(sender.get())

	def ApplyButtonCallback(self, sender):
		self.TTHToolInstance.changePreviewSize(self.FromSize, self.ToSize)
		self.view.setNeedsDisplay_(True)

reload (CV)
