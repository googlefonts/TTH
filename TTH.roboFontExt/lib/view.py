#coding=utf-8

from vanilla import *
from mojo.UI import *
from mojo.extensions import *
from lib.doodleMenus import BaseMenu
from AppKit import *

import string

import preview
import view_ControlValues as CV

buttonXPath = ExtensionBundle("TTH").get("buttonX")
buttonYPath = ExtensionBundle("TTH").get("buttonY")
buttonAlignPath = ExtensionBundle("TTH").get("buttonAlign")
buttonSingleLinkPath = ExtensionBundle("TTH").get("buttonSingleLink")
buttonDoubleLinkPath = ExtensionBundle("TTH").get("buttonDoubleLink")
buttonInterpolationPath = ExtensionBundle("TTH").get("buttonInterpolation")
buttonMiddleDeltaPath = ExtensionBundle("TTH").get("buttonMiddleDelta")
buttonFinalDeltaPath = ExtensionBundle("TTH").get("buttonFinalDelta")

class centralWindow(object):
	def __init__(self, TTHToolInstance, tthtm):
		#self.screenArea = preview.ScreenArea.alloc().init()
		# print screenArea.frame()
		# screenArea.setFrameOrigin_((800, 800))
		# screenArea.setFrameSize_((800, 800))
		# screenArea.setNeedsDisplay_(True)
		# print screenArea.frame().origin

		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm
		self.wCentral = FloatingWindow(self.tthtm.centralWindowPosSize, "Central", closable = False)

		self.PPMSizesList = ['9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', 
							'21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
							'31', '32', '33', '34', '35', '36', '37', '38', '39', '40',
							'41', '42', '43', '44', '45', '46', '47', '48', '60', '72' ]

		self.BitmapPreviewList = ['Monochrome', 'Grayscale', 'Subpixel']


		self.wCentral.PPEMSizeText= TextBox((10, 12, 50, 15), "ppEm:", sizeStyle = "mini")
		
		self.wCentral.PPEMSizeEditText = EditText((60, 10, 30, 15), sizeStyle = "mini", 
				callback=self.PPEMSizeEditTextCallback)

		self.wCentral.PPEMSizeEditText.set(self.tthtm.PPM_Size)
		
		self.wCentral.PPEMSizePopUpButton = PopUpButton((100, 10, 40, 15),
				self.PPMSizesList, sizeStyle = "mini",
				callback=self.PPEMSizePopUpButtonCallback)

		self.wCentral.BitmapPreviewText= TextBox((10, 32, 50, 15), "Preview:", sizeStyle = "mini")
		self.wCentral.BitmapPreviewPopUpButton = PopUpButton((60, 30, 80, 15),
				self.BitmapPreviewList, sizeStyle = "mini",
				callback=self.BitmapPreviewPopUpButtonCallback)

		# self.wCentral.AxisText= TextBox((10, 50, 70, 14), "Axis:", sizeStyle = "small")
		# self.wCentral.AxisPopUpButton = PopUpButton((150, 50, 40, 14),
		# 		self.axisList, sizeStyle = "small",
		# 		callback=self.AxisPopUpButtonCallback)

		# self.wCentral.HintingToolText= TextBox((10, 70, 70, 14), "Tool:", sizeStyle = "small")
		# self.wCentral.HintingToolPopUpButton = PopUpButton((90, 70, 100, 14),
		# 		self.hintingToolsList, sizeStyle = "small",
		# 		callback=self.HintingToolPopUpButtonCallback)

		# self.wCentral.PrintTTProgramButton = Button((10, 180, -10, 22), "Print Glyph's Program", sizeStyle = 'small', 
		# 		callback=self.PrintTTProgramButtonCallback)
		# self.wCentral.PrintAssemblyButton = Button((10, 202, -10, 22), "Print Glyph's Assembly", sizeStyle = 'small', 
		# 		callback=self.PrintAssemblyButtonCallback)
		# self.wCentral.RefreshGlyphButton = Button((10, 241, -10, 22), "Apply Program & Refresh", sizeStyle = 'small', 
		# 		callback=self.RefreshGlyphButtonCallback)
		# self.wCentral.AlwaysRefreshText = TextBox((10, 266, 180, 14), "Always Apply & Refresh:", sizeStyle = "small")
		# self.wCentral.AlwaysRefreshCheckBox = CheckBox((-22, 261, -10, 22), "", sizeStyle = "small",
		# 		callback=self.AlwaysRefreshCheckBoxCallback)
		# self.wCentral.AlwaysRefreshCheckBox.set(self.tthtm.alwaysRefresh)
	
		
		
		#self.wCentral.PreviewHideButton = Button((10, -98, -10, 22), "Hide Preview Window", sizeStyle = 'small', 
		#		callback=self.PreviewHideButtonCallback)

		# if self.tthtm.previewWindowVisible == 0:
		# 	self.wCentral.PreviewHideButton.show(False)
		# 	self.wCentral.PreviewShowButton.show(True)
		# elif self.tthtm.previewWindowVisible == 1:
		# 	self.wCentral.PreviewHideButton.show(True)
		# 	self.wCentral.PreviewShowButton.show(False)
		
		# self.wCentral.PanelsShowButton = Button((10, -45, -10, 15), u"Panels…", sizeStyle = 'mini', 
		# 		callback=self.PanelsShowButtonCallback)

		self.wCentral.AssemblyShowButton = Button((10, -85, -10, 15), "Glyph Assembly", sizeStyle = 'mini', 
				callback=self.AssemblyShowButtonCallback)

		self.wCentral.ProgramShowButton = Button((10, -65, -10, 15), "Glyph Program", sizeStyle = 'mini', 
				callback=self.ProgramShowButtonCallback)

		self.wCentral.PreviewShowButton = Button((10, -45, -10, 15), "Preview Window", sizeStyle = 'mini', 
				callback=self.PreviewShowButtonCallback)

		self.wCentral.ControlValuesButton = Button((10, -25, -10, 15), "Control Values", sizeStyle = 'mini', 
				callback=self.ControlValuesButtonCallback)

		self.wCentral.bind("move", self.centralWindowMovedorResized)
		self.wCentral.open()

	def closeCentral(self):
		self.wCentral.close()

	def centralWindowMovedorResized(self, sender):
		self.tthtm.centralWindowPosSize = self.wCentral.getPosSize()

	def PPEMSizeEditTextCallback(self, sender):
		self.TTHToolInstance.changeSize(sender.get())

	def PPEMSizePopUpButtonCallback(self, sender):
		if self.tthtm.g == None:
			return
		size = self.PPMSizesList[sender.get()]
		self.TTHToolInstance.changeSize(size)

	def BitmapPreviewPopUpButtonCallback(self, sender):
		self.TTHToolInstance.changeBitmapPreview(self.BitmapPreviewList[sender.get()])

	# def AxisPopUpButtonCallback(self, sender):
	# 	self.TTHToolInstance.changeAxis(self.axisList[sender.get()])
	# 	self.TTHToolInstance.makeStemsListsPopUpMenu()

	# 	if self.tthtm.selectedAxis == 'X':
	# 		self.wCentral.StemTypePopUpButton.setItems(self.tthtm.stemsListX)
	# 		self.TTHToolInstance.changeSelectedStemX(self.tthtm.selectedStemX)
	# 	else:
	# 		self.wCentral.StemTypePopUpButton.setItems(self.tthtm.stemsListY)
	# 		self.TTHToolInstance.changeSelectedStemY(self.tthtm.selectedStemY)

	# 	UpdateCurrentGlyphView()



	# def HintingToolPopUpButtonCallback(self, sender):
	# 	self.TTHToolInstance.changeSelectedHintingTool(self.hintingToolsList[sender.get()])
	# 	#self.TTHToolInstance.changeSelectedAlignmentTypeAlign(self.tthtm.selectedAlignmentTypeAlign)
	# 	#self.TTHToolInstance.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)

	# 	if self.tthtm.selectedHintingTool == 'Single Link':
	# 		self.centralWindowLinkSettings()
	# 		self.TTHToolInstance.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)
	# 		if self.tthtm.selectedAxis == 'X':
	# 			self.TTHToolInstance.changeSelectedStemX(self.tthtm.selectedStemX)
	# 		else:
	# 			self.TTHToolInstance.changeSelectedStemY(self.tthtm.selectedStemY)
	# 	elif self.tthtm.selectedHintingTool == 'Double Link':
	# 		self.centralWindowDoubleLinkSettings()
	# 		if self.tthtm.selectedAxis == 'X':
	# 			self.TTHToolInstance.changeSelectedStemX(self.tthtm.selectedStemX)
	# 		else:
	# 			self.TTHToolInstance.changeSelectedStemY(self.tthtm.selectedStemY)
	# 	elif self.tthtm.selectedHintingTool == 'Align':
	# 		self.centralWindowAlignSettings()
	# 		self.TTHToolInstance.changeSelectedAlignmentTypeAlign(self.tthtm.selectedAlignmentTypeAlign)
	# 	elif self.tthtm.selectedHintingTool == 'Interpolation':
	# 		self.centralWindowInterpolationSettings()
	# 		self.TTHToolInstance.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)
	# 	elif self.tthtm.selectedHintingTool in ['Middle Delta', 'Final Delta']:
	# 		self.centralWindowDeltaSettings()
	# 	else:
	# 		self.wCentral.AlignmentTypeText.show(False)
	# 		self.wCentral.AlignmentTypePopUpButton.show(False)
	# 		self.wCentral.StemTypeText.show(False)
	# 		self.wCentral.StemTypePopUpButton.show(False)
	# 		self.wCentral.RoundDistanceText.show(False)
	# 		self.wCentral.RoundDistanceCheckBox.show(False)
	# 		self.wCentral.DeltaOffsetText.show(False)
	# 		self.wCentral.DeltaOffsetSlider.show(False)
	# 		self.wCentral.DeltaRangeText.show(False)
	# 		self.wCentral.DeltaRange1EditText.show(False)
	# 		self.wCentral.DeltaRange2EditText.show(False)


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
		if self.tthtm.previewWindowVisible == 0:
			for i in string.lowercase:
				self.tthtm.requiredGlyphsForPartialTempFont.add(i)
			for i in string.uppercase:
				self.tthtm.requiredGlyphsForPartialTempFont.add(i)
			for i in ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'zero']:
				self.tthtm.requiredGlyphsForPartialTempFont.add(i)

			self.TTHToolInstance.updatePartialFont()
			self.TTHToolInstance.previewWindow = previewWindow(self.TTHToolInstance, self.tthtm)

	def ControlValuesButtonCallback(self, sender):
		sheet = CV.SheetControlValues(self.wCentral, self.tthtm, self.TTHToolInstance)

	def ProgramShowButtonCallback(self, sender):
		if self.tthtm.programWindowVisible == 0:
			self.TTHToolInstance.programWindow = programWindow(self.TTHToolInstance, self.tthtm)
			self.TTHToolInstance.resetglyph()

	def AssemblyShowButtonCallback(self, sender):
		if self.tthtm.assemblyWindowVisible == 0:
			self.TTHToolInstance.assemblyWindow = assemblyWindow(self.TTHToolInstance, self.tthtm)
			self.TTHToolInstance.resetglyph()

	def PanelsShowButtonCallback(self, sender):
		self.menuAction = NSMenu.alloc().init()
		items = []
		items.append(('Preview', self.PreviewShowButtonCallback))
		items.append(('Program', self.ProgramShowButtonCallback))
		items.append(('Assembly', self.AssemblyShowButtonCallback))
		menuController = BaseMenu()
		menuController.buildAdditionContectualMenuItems(self.menuAction, items)
		NSMenu.popUpContextMenu_withEvent_forView_(self.menuAction, self.TTHToolInstance.getCurrentEvent(), self.TTHToolInstance.getNSView())

class toolsWindow(object):
	def __init__(self, TTHToolInstance, tthtm):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm

		self.axisList = ['X', 'Y']
		self.hintingToolsList = ['Align', 'Single Link', 'Double Link', 'Interpolation', 'Middle Delta', 'Final Delta']
		if self.tthtm.selectedAxis == 'X':
			self.stemTypeList = self.tthtm.stemsListX
			self.alignmentTypeListDisplay = ['Closest Pixel Edge', 'Left Edge', 'Right Edge', 'Center of Pixel', 'Double Grid']
			self.alignmentTypeListLinkDisplay = ['Do Not Align to Grid', 'Closest Pixel Edge', 'Left Edge', 'Right Edge', 'Center of Pixel', 'Double Grid']
		else:
			self.stemTypeList = self.tthtm.stemsListY
			self.alignmentTypeListDisplay = ['Closest Pixel Edge', 'Bottom Edge', 'Top Edge', 'Center of Pixel', 'Double Grid']
			self.alignmentTypeListLinkDisplay = ['Do Not Align to Grid', 'Closest Pixel Edge', 'Bottom Edge', 'Top Edge', 'Center of Pixel', 'Double Grid']

		
		self.alignmentTypeList = ['round', 'left', 'right', 'center', 'double']
		self.alignmentTypeListLink = ['None', 'round', 'left', 'right', 'center', 'double']



		self.wTools = FloatingWindow(self.tthtm.toolsWindowPosSize, "Tools", closable = False)

		self.wTools.XButton = GradientButton((10, 10, 18, 18), imageObject = buttonXPath, 
                            callback=self.AxisXButtonCallback)
		self.wTools.YButton = GradientButton((28, 10, 18, 18), imageObject = buttonYPath,
                            callback=self.AxisYButtonCallback)
		self.wTools.AlignButton = GradientButton((-118, 10, 18, 18), imageObject = buttonAlignPath,
                            callback=self.AlignButtonCallback)
		self.wTools.SingleLinkButton = GradientButton((-100, 10, 18, 18), imageObject = buttonSingleLinkPath,
                            callback=self.SingleLinkButtonCallback)
		self.wTools.DoubleLinkButton = GradientButton((-82, 10, 18, 18), imageObject = buttonDoubleLinkPath,
                            callback=self.DoubleLinkButtonCallback)
		self.wTools.InterpolationButton = GradientButton((-64, 10, 18, 18), imageObject = buttonInterpolationPath,
                            callback=self.InterpolationButtonCallback)		
		self.wTools.MiddleDeltaButton = GradientButton((-46, 10, 18, 18), imageObject = buttonMiddleDeltaPath,
                            callback=self.MiddleDeltaButtonCallback)
		self.wTools.FinalDeltaButton = GradientButton((-28, 10, 18, 18), imageObject = buttonFinalDeltaPath,
                            callback=self.FinalDeltaButtonCallback)

		self.wTools.AlignmentTypeText = TextBox((10, 32, 30, 15), "Align:", sizeStyle = "mini")
		self.wTools.AlignmentTypePopUpButton = PopUpButton((40, 30, 65, 15),
				self.alignmentTypeListDisplay, sizeStyle = "mini",
				callback=self.AlignmentTypePopUpButtonCallback)
		self.wTools.AlignmentTypeText.show(True)
		self.wTools.AlignmentTypePopUpButton.show(True)

		self.wTools.StemTypeText = TextBox((110, 32, 30, 15), "Stem:", sizeStyle = "mini")
		self.wTools.StemTypePopUpButton = PopUpButton((140, 30, 65, 15),
				self.stemTypeList, sizeStyle = "mini",
				callback=self.StemTypePopUpButtonCallback)
		self.wTools.StemTypeText.show(False)
		self.wTools.StemTypePopUpButton.show(False)

		self.wTools.RoundDistanceText = TextBox((10, 47, 80, 15), "Round Distance:", sizeStyle = "mini")
		self.wTools.RoundDistanceCheckBox = CheckBox((90, 45, 15, 15), "", sizeStyle = "mini",
				callback=self.RoundDistanceCheckBoxCallback)
		self.wTools.RoundDistanceText.show(False)
		self.wTools.RoundDistanceCheckBox.show(False)

		self.wTools.DeltaOffsetText = TextBox((10, 32, 50, 15), "Offset:", sizeStyle = "mini")
		self.wTools.DeltaOffsetSlider = Slider((10, 45, -10, 15), maxValue=16, value=8, tickMarkCount=17, continuous=False, stopOnTickMarks=True, sizeStyle= "small",
				callback=self.DeltaOffsetSliderCallback)
		self.wTools.DeltaOffsetEditText = EditText((60, 30, 30, 15), sizeStyle = "mini", 
				callback=self.DeltaOffsetEditTextCallback)
		self.wTools.DeltaOffsetText.show(False)
		self.wTools.DeltaOffsetSlider.show(False)
		self.wTools.DeltaOffsetEditText.set(self.tthtm.deltaOffset)
		self.wTools.DeltaOffsetEditText.show(False)

		self.wTools.DeltaRangeText = TextBox((100, 32, 40, 15), "Range:", sizeStyle = "mini")
		self.wTools.DeltaRange1EditText = EditText((-70, 30, 30, 15), sizeStyle = "mini", 
				callback=self.DeltaRange1EditTextCallback)
		self.wTools.DeltaRange2EditText = EditText((-40, 30, 30, 15), sizeStyle = "mini", 
				callback=self.DeltaRange2EditTextCallback)
		self.wTools.DeltaRangeText.show(False)
		self.wTools.DeltaRange1EditText.show(False)
		self.wTools.DeltaRange2EditText.show(False)
		self.wTools.DeltaRange1EditText.set(self.tthtm.deltaRange1)
		self.wTools.DeltaRange2EditText.set(self.tthtm.deltaRange2)

		self.wTools.bind("move", self.toolsWindowMovedorResized)

		self.wTools.open()


	def closeTools(self):
		self.wTools.close()

	def toolsWindowMovedorResized(self, sender):
		self.tthtm.toolsWindowPosSize = self.wTools.getPosSize()


	def LinkSettings(self):
		self.TTHToolInstance.selectedAlignmentTypeLink = self.alignmentTypeListLink[0]
		self.wTools.AlignmentTypePopUpButton.setItems(self.alignmentTypeListLinkDisplay)
		self.wTools.AlignmentTypeText.show(True)
		self.wTools.AlignmentTypePopUpButton.show(True)
		self.wTools.StemTypeText.show(True)
		self.wTools.StemTypePopUpButton.show(True)
		self.wTools.RoundDistanceText.show(True)
		self.wTools.RoundDistanceCheckBox.show(True)
		self.wTools.DeltaOffsetText.show(False)
		self.wTools.DeltaOffsetSlider.show(False)
		self.wTools.DeltaRangeText.show(False)
		self.wTools.DeltaRange1EditText.show(False)
		self.wTools.DeltaRange2EditText.show(False)
		self.wTools.DeltaOffsetEditText.show(False)

	def DoubleLinkSettings(self):
		self.wTools.AlignmentTypeText.show(False)
		self.wTools.AlignmentTypePopUpButton.show(False)
		self.wTools.StemTypeText.show(True)
		self.wTools.StemTypePopUpButton.show(True)
		self.wTools.RoundDistanceText.show(False)
		self.wTools.RoundDistanceCheckBox.show(False)
		self.wTools.DeltaOffsetText.show(False)
		self.wTools.DeltaOffsetSlider.show(False)
		self.wTools.DeltaRangeText.show(False)
		self.wTools.DeltaRange1EditText.show(False)
		self.wTools.DeltaRange2EditText.show(False)
		self.wTools.DeltaOffsetEditText.show(False)

	def AlignSettings(self):
		self.TTHToolInstance.selectedAlignmentTypeAlign = self.alignmentTypeList[0]
		self.wTools.AlignmentTypePopUpButton.setItems(self.alignmentTypeListDisplay)
		self.wTools.AlignmentTypeText.show(True)
		self.wTools.AlignmentTypePopUpButton.show(True)
		self.wTools.StemTypeText.show(False)
		self.wTools.StemTypePopUpButton.show(False)
		self.wTools.RoundDistanceText.show(False)
		self.wTools.RoundDistanceCheckBox.show(False)
		self.wTools.DeltaOffsetText.show(False)
		self.wTools.DeltaOffsetSlider.show(False)
		self.wTools.DeltaRangeText.show(False)
		self.wTools.DeltaRange1EditText.show(False)
		self.wTools.DeltaRange2EditText.show(False)
		self.wTools.DeltaOffsetEditText.show(False)

	def InterpolationSettings(self):
		self.TTHToolInstance.selectedAlignmentTypeLink = self.alignmentTypeListLink[0]
		self.wTools.AlignmentTypePopUpButton.setItems(self.alignmentTypeListLinkDisplay)
		self.wTools.AlignmentTypeText.show(True)
		self.wTools.AlignmentTypePopUpButton.show(True)
		self.wTools.StemTypeText.show(False)
		self.wTools.StemTypePopUpButton.show(False)
		self.wTools.RoundDistanceText.show(False)
		self.wTools.RoundDistanceCheckBox.show(False)
		self.wTools.DeltaOffsetText.show(False)
		self.wTools.DeltaOffsetSlider.show(False)
		self.wTools.DeltaRangeText.show(False)
		self.wTools.DeltaRange1EditText.show(False)
		self.wTools.DeltaRange2EditText.show(False)
		self.wTools.DeltaOffsetEditText.show(False)

	def DeltaSettings(self):
		self.wTools.AlignmentTypeText.show(False)
		self.wTools.AlignmentTypePopUpButton.show(False)
		self.wTools.StemTypeText.show(False)
		self.wTools.StemTypePopUpButton.show(False)
		self.wTools.RoundDistanceText.show(False)
		self.wTools.RoundDistanceCheckBox.show(False)
		self.wTools.DeltaOffsetText.show(True)
		self.wTools.DeltaOffsetSlider.show(True)
		self.wTools.DeltaRangeText.show(True)
		self.wTools.DeltaRange1EditText.show(True)
		self.wTools.DeltaRange2EditText.show(True)
		self.wTools.DeltaOffsetEditText.show(True)

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

	def AxisXButtonCallback(self, sender):
		self.TTHToolInstance.changeAxis('X')
		self.TTHToolInstance.makeStemsListsPopUpMenu()
		self.wTools.StemTypePopUpButton.setItems(self.tthtm.stemsListX)
		self.TTHToolInstance.changeSelectedStemX(self.tthtm.selectedStemX)

	def AxisYButtonCallback(self, sender):
		sender.getNSButton().setBezelStyle_(NSSmallSquareBezelStyle)
		self.TTHToolInstance.changeAxis('Y')
		self.TTHToolInstance.makeStemsListsPopUpMenu()
		self.wTools.StemTypePopUpButton.setItems(self.tthtm.stemsListY)
		self.TTHToolInstance.changeSelectedStemY(self.tthtm.selectedStemY)
	
	def AlignButtonCallback(self, sender):
		self.AlignSettings()
		self.TTHToolInstance.changeSelectedAlignmentTypeAlign(self.tthtm.selectedAlignmentTypeAlign)
		self.TTHToolInstance.changeSelectedHintingTool('Align')

	def SingleLinkButtonCallback(self, sender):
		self.LinkSettings()
		self.TTHToolInstance.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)
		if self.tthtm.selectedAxis == 'X':
			self.TTHToolInstance.changeSelectedStemX(self.tthtm.selectedStemX)
		else:
			self.TTHToolInstance.changeSelectedStemY(self.tthtm.selectedStemY)
		self.TTHToolInstance.changeSelectedHintingTool('Single Link')

	def DoubleLinkButtonCallback(self, sender):
		self.DoubleLinkSettings()
		if self.tthtm.selectedAxis == 'X':
			self.TTHToolInstance.changeSelectedStemX(self.tthtm.selectedStemX)
		else:
			self.TTHToolInstance.changeSelectedStemY(self.tthtm.selectedStemY)
		self.TTHToolInstance.changeSelectedHintingTool('Double Link')
			
	def InterpolationButtonCallback(self, sender):
		self.InterpolationSettings()
		self.TTHToolInstance.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)
		self.TTHToolInstance.changeSelectedHintingTool('Interpolation')

	def MiddleDeltaButtonCallback(self, sender):
		self.DeltaSettings()
		self.TTHToolInstance.changeSelectedHintingTool('Middle Delta')

	def FinalDeltaButtonCallback(self, sender):
		self.DeltaSettings()
		self.TTHToolInstance.changeSelectedHintingTool('Final Delta')


class previewWindow(object):
	def __init__(self, TTHToolInstance, tthtm):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm

		self.FromSize = self.tthtm.previewFrom
		self.ToSize = self.tthtm.previewTo

		self.viewSize = (self.tthtm.previewWindowPosSize[2]-40, self.tthtm.previewWindowPosSize[3]-110)

		self.wPreview = FloatingWindow(self.tthtm.previewWindowPosSize, "Preview", minSize=(350, 200))
		self.view = preview.PreviewArea.alloc().init_withTTHToolInstance(self.TTHToolInstance)

		self.view.setFrame_(((0, 0), self.viewSize))
		self.view.setFrameOrigin_((0, 10*(self.viewSize[1]/2)))
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
		self.wPreview.bind("close", self.previewWindowWillClose)
		self.wPreview.bind("move", self.previewWindowMovedorResized)
		self.wPreview.bind("resize", self.previewWindowMovedorResized)
		self.wPreview.open()

		self.wPreview.resize(self.tthtm.previewWindowPosSize[2], self.tthtm.previewWindowPosSize[3])

	def closePreview(self):
		self.wPreview.close()

	def previewWindowWillClose(self, sender):
		self.tthtm.previewWindowVisible = 0

	def previewWindowMovedorResized(self, sender):
		self.tthtm.previewWindowPosSize = self.wPreview.getPosSize()

		self.viewSize = (self.tthtm.previewWindowPosSize[2]-40, self.tthtm.previewWindowPosSize[3]-110)
		self.view.setFrame_(((0, 0), self.viewSize))
		self.view.setFrameOrigin_((0, 10*(self.viewSize[1]/2)))
		self.view.setAutoresizingMask_(NSViewMinXMargin | NSViewMaxXMargin | NSViewMinYMargin | NSViewMaxYMargin)

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

class programWindow(object):
	def __init__(self, TTHToolInstance, tthtm):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm

		self.wProgram = FloatingWindow(self.tthtm.programWindowPosSize, "Program", minSize=(600, 80))
		self.wProgram.bind("close", self.programWindowWillClose)
		self.programList = []
		self.wProgram.programList = List((0, 0, -0, -0), self.programList, 
					columnDescriptions=[{"title": "index", "editable": False}, {"title": "code", "editable": False}, {"title": "point", "editable": False},
				{"title": "point1", "editable": False}, {"title": "point2", "editable": False}, {"title": "align", "editable": False},
				{"title": "round", "editable": False}, {"title": "stem", "editable": False}, {"title": "zone", "editable": False},
				{"title": "delta", "editable": False}, {"title": "ppm1", "editable": False}, {"title": "ppm2", "editable": False}],
					enableDelete=False, 
					showColumnTitles=True,
					selectionCallback=self.selectionCallback,
					editCallback = self.editCallback)
		self.tthtm.programWindowVisible = 1
		self.wProgram.bind("close", self.programWindowWillClose)
		self.wProgram.bind("move", self.programWindowMovedorResized)
		self.wProgram.bind("resize", self.programWindowMovedorResized)
		self.wProgram.open()

	def closeProgram(self):
		self.wProgram.close()

	def programWindowWillClose(self, sender):
		self.tthtm.programWindowVisible = 0

	def programWindowMovedorResized(self, sender):
		self.tthtm.programWindowPosSize = self.wProgram.getPosSize()

	def selectionCallback(self, sender):
		pass
		# print sender.getSelection()

	def editCallback(self, sender):
		pass

	def updateProgramList(self, commands):
		self.commands =  [dict(c) for c in commands]
		def putIfNotThere(c, key):
			if key not in c:
				c[key] = ''
			if key == 'index':
				c[key] = self.i
				self.i += 1
		self.i = 0
		for command in self.commands:
			for key in ['index', 'point', 'point1', 'point2', 'align', 'round', 'stem', 'zone', 'delta', 'ppm1', 'ppm2']:
				putIfNotThere(command, key)
		self.wProgram.programList.set(self.commands)

class assemblyWindow(object):
	def __init__(self, TTHToolInstance, tthtm):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm

		self.assemblyList = []

		self.wAssembly = FloatingWindow(self.tthtm.assemblyWindowPosSize, "Assembly", minSize=(150, 100))
		self.wAssembly.assemblyList = List((0, 0, -0, -0), self.assemblyList)

		self.wAssembly.bind("close", self.assemblyWindowWillClose)
		self.tthtm.assemblyWindowVisible = 1
		self.wAssembly.bind("close", self.assemblyWindowWillClose)
		self.wAssembly.bind("move", self.assemblyWindowMovedorResized)
		self.wAssembly.bind("resize", self.assemblyWindowMovedorResized)
		self.wAssembly.open()

	def closeAssembly(self):
		self.wAssembly.close()

	def assemblyWindowWillClose(self, sender):
		self.tthtm.assemblyWindowVisible = 0

	def assemblyWindowMovedorResized(self, sender):
		self.tthtm.assemblyWindowPosSize = self.wAssembly.getPosSize()

	def updateAssemblyList(self, assembly):
		self.wAssembly.assemblyList.set(assembly)


reload (CV)
