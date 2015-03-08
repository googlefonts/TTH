from defconAppKit.windows.baseWindow import BaseWindowController
from lib.doodleMenus import BaseMenu
from AppKit import *
from vanilla import *
from mojo.extensions import *

buttonXPath = ExtensionBundle("TTH").get("buttonX")
buttonYPath = ExtensionBundle("TTH").get("buttonY")
buttonAlignPath = ExtensionBundle("TTH").get("buttonAlign")
buttonSingleLinkPath = ExtensionBundle("TTH").get("buttonSingleLink")
buttonDoubleLinkPath = ExtensionBundle("TTH").get("buttonDoubleLink")
buttonInterpolationPath = ExtensionBundle("TTH").get("buttonInterpolation")
buttonMiddleDeltaPath = ExtensionBundle("TTH").get("buttonMiddleDelta")
buttonFinalDeltaPath = ExtensionBundle("TTH").get("buttonFinalDelta")
buttonSelectionPath = ExtensionBundle("TTH").get("buttonSelection")

DefaultKeyStub = "com.sansplomb.TTH."

defaultKeyToolsWindowPosSize = DefaultKeyStub + "toolsWindowPosSize"
defaultKeyPreviewWindowPosSize = DefaultKeyStub + "previewWindowPosSize"
defaultKeyProgramWindowPosSize = DefaultKeyStub + "programWindowPosSize"
defaultKeyAssemblyWindowPosSize = DefaultKeyStub + "assemblyWindowPosSize"

defaultKeyProgramWindowVisibility = DefaultKeyStub + "programWindowVisibility"
defaultKeyPreviewWindowVisibility = DefaultKeyStub + "previewWindowVisibility"
defaultKeyAssemblyWindowVisibility = DefaultKeyStub + "assemblyWindowVisibility"

class MainPanel(BaseWindowController):
	def __init__(self, TTHToolController):
		BaseWindowController.__init__(self)
		self.TTHToolController = TTHToolController
		self.TTHToolModel = TTHToolController.TTHToolModel

		self.axisList = ['X', 'Y']
		self.hintingToolsList = ['Align', 'Single Link', 'Double Link', 'Interpolation', 'Middle Delta', 'Final Delta', 'Selection']
		if self.TTHToolModel.selectedAxis == 'X':
			self.stemTypeList = self.TTHToolModel.stemsListX
			self.alignmentTypeListDisplay = ['Closest Pixel Edge', 'Left Edge', 'Right Edge', 'Center of Pixel', 'Double Grid']
			self.alignmentTypeListLinkDisplay = ['Do Not Align to Grid', 'Closest Pixel Edge', 'Left Edge', 'Right Edge', 'Center of Pixel', 'Double Grid']
		else:
			self.stemTypeList = self.TTHToolModel.stemsListY
			self.alignmentTypeListDisplay = ['Closest Pixel Edge', 'Bottom Edge', 'Top Edge', 'Center of Pixel', 'Double Grid']
			self.alignmentTypeListLinkDisplay = ['Do Not Align to Grid', 'Closest Pixel Edge', 'Bottom Edge', 'Top Edge', 'Center of Pixel', 'Double Grid']

		self.alignmentTypeList = ['round', 'left', 'right', 'center', 'double']
		self.alignmentTypeListLink = ['None', 'round', 'left', 'right', 'center', 'double']

		self.makeMainPanel()

	def makeMainPanel(self):
		self.wTools = FloatingWindow(getExtensionDefault(defaultKeyToolsWindowPosSize, fallback=self.TTHToolModel.toolsWindowPosSize), "TTH", closable = False)

		axisSegmentDescriptions = [
			dict(width=19, imageObject=buttonXPath, toolTip="Horizontal Axis"),
			dict(width=19, imageObject=buttonYPath, toolTip="Vertical Axis")
		]

		toolsSegmentDescriptions = [
			dict(width=19, imageObject=buttonAlignPath, toolTip="Align Tool"),
			dict(width=19, imageObject=buttonSingleLinkPath, toolTip="Single Link Tool"),
			dict(width=19, imageObject=buttonDoubleLinkPath, toolTip="Double Link Tool"),
			dict(width=19, imageObject=buttonInterpolationPath, toolTip="Interpolation Tool"),
			dict(width=19, imageObject=buttonMiddleDeltaPath, toolTip="Middle Delta Tool"),
			dict(width=19, imageObject=buttonFinalDeltaPath, toolTip="Final Delta Tool"),
			dict(width=19, imageObject=buttonSelectionPath, toolTip="Selection Tool")
		]

		self.PPMSizesList = [str(i) for i in range(9, 73)]

		self.wTools.PPEMSizeComboBox = ComboBox((10, 14, 40, 16),
				self.PPMSizesList, sizeStyle = "small",
				callback=self.PPEMSizeComboBoxCallback)
		self.wTools.PPEMSizeComboBox.set(self.TTHToolModel.PPM_Size)

		self.wTools.axisSegmentedButton = SegmentedButton((60, 12, 70, 18), axisSegmentDescriptions, callback=self.axisSegmentedButtonCallback, sizeStyle="regular")
		self.wTools.axisSegmentedButton.set(0)

		self.wTools.toolsSegmentedButton = SegmentedButton((-158, 12, 150, 18), toolsSegmentDescriptions, callback=self.toolsSegmentedButtonCallback, sizeStyle="regular")
		self.wTools.toolsSegmentedButton.set(0)

		self.wTools.AlignmentTypeText = TextBox((10, 42, 30, 15), "Align:", sizeStyle = "mini")
		self.wTools.AlignmentTypePopUpButton = PopUpButton((40, 40, 105, 16),
				self.alignmentTypeListDisplay, sizeStyle = "mini",
				callback=self.AlignmentTypePopUpButtonCallback)
		self.wTools.AlignmentTypeText.show(True)
		self.wTools.AlignmentTypePopUpButton.show(True)

		self.wTools.StemTypeText = TextBox((10, 59, 30, 15), "Stem:", sizeStyle = "mini")
		self.wTools.StemTypePopUpButton = PopUpButton((40, 57, 105, 16),
				self.stemTypeList, sizeStyle = "mini",
				callback=self.StemTypePopUpButtonCallback)
		self.wTools.StemTypeText.show(False)
		self.wTools.StemTypePopUpButton.show(False)

		self.wTools.RoundDistanceText = TextBox((155, 42, 80, 15), "Round Distance:", sizeStyle = "mini")
		self.wTools.RoundDistanceCheckBox = CheckBox((-25, 44, 15, 15), "", sizeStyle = "mini",
				callback=self.RoundDistanceCheckBoxCallback)
		self.wTools.RoundDistanceText.show(False)
		self.wTools.RoundDistanceCheckBox.show(False)

		self.wTools.DeltaOffsetText = TextBox((10, 38, 40, 15), "Offset:", sizeStyle = "mini")
		self.wTools.DeltaOffsetSlider = Slider((10, 57, 130, 15), maxValue=16, value=8, tickMarkCount=17, continuous=False, stopOnTickMarks=True, sizeStyle= "small",
				callback=self.DeltaOffsetSliderCallback)
		self.wTools.DeltaOffsetEditText = EditText((50, 38, 30, 15), sizeStyle = "mini", 
				callback=self.DeltaOffsetEditTextCallback)
		self.wTools.DeltaOffsetText.show(False)
		self.wTools.DeltaOffsetSlider.show(False)
		self.wTools.DeltaOffsetEditText.set(self.TTHToolModel.deltaOffset)
		self.wTools.DeltaOffsetEditText.show(False)

		self.wTools.DeltaRangeText = TextBox((-120, 57, 40, 15), "Range:", sizeStyle = "mini")
		self.wTools.DeltaRange1ComboBox = ComboBox((-80, 55, 33, 15), self.PPMSizesList, sizeStyle = "mini", 
				callback=self.DeltaRange1ComboBoxCallback)
		self.wTools.DeltaRange2ComboBox = ComboBox((-43, 55, 33, 15), self.PPMSizesList, sizeStyle = "mini", 
				callback=self.DeltaRange2ComboBoxCallback)
		self.wTools.DeltaRangeText.show(False)
		self.wTools.DeltaRange1ComboBox.show(False)
		self.wTools.DeltaRange2ComboBox.show(False)
		self.wTools.DeltaRange1ComboBox.set(self.TTHToolModel.deltaRange1)
		self.wTools.DeltaRange2ComboBox.set(self.TTHToolModel.deltaRange2)

		self.wTools.DeltaMonochromeText = TextBox((90, 38, 40, 15), "Mono:", sizeStyle = "mini")
		self.wTools.DeltaMonochromeCheckBox = CheckBox((130, 38, 15, 15), "", sizeStyle = "mini",
				callback=self.DeltaMonochromeCheckBoxCallback)
		self.wTools.DeltaMonochromeText.show(False)
		self.wTools.DeltaMonochromeCheckBox.show(False)
		self.wTools.DeltaMonochromeCheckBox.set(self.TTHToolModel.deltaMonoBool)

		self.wTools.DeltaGrayText = TextBox((150, 38, 80, 15), "Gray & Subpixel:", sizeStyle = "mini")
		self.wTools.DeltaGrayCheckBox = CheckBox((-25, 38, 15, 15), "", sizeStyle = "mini",
				callback=self.DeltaGrayCheckBoxCallback)
		self.wTools.DeltaGrayText.show(False)
		self.wTools.DeltaGrayCheckBox.show(False)
		self.wTools.DeltaGrayCheckBox.set(self.TTHToolModel.deltaGrayBool)

		self.wTools.gear = PopUpButton((0, -22, 30, 18), [], callback=self.gearMenuCallback, sizeStyle="mini")
		self.wTools.gear.getNSPopUpButton().setPullsDown_(True)
		self.wTools.gear.getNSPopUpButton().setBordered_(False)

		im = NSImage.imageNamed_(NSImageNameActionTemplate)
		im.setSize_((10, 10))

		firstItem = NSMenuItem.alloc().init()
		firstItem.setImage_(im)
		firstItem.setTitle_("")

		previewSubMenu = NSMenu.alloc().init()
		previewSubMenu.initWithTitle_("Preview")

		previewItem = NSMenuItem.alloc().init()
		previewItem.setTitle_("Preview")

		self.wTools.gear.setItems(
			[firstItem,
			"Auto-hinting",
			NSMenuItem.separatorItem(),
			"Monochrome",
			"Grayscale",
			"Subpixel",
			NSMenuItem.separatorItem(),
			"Preview",
			"Program",
			"Assembly",
			NSMenuItem.separatorItem(),
			"Control Values",
			NSMenuItem.separatorItem(),
			"Preferences",
			NSMenuItem.separatorItem(),
			"Transfer",
			]
			)

		self.wTools.bind("move", self.toolsWindowMovedorResized)

		self.wTools.open()
		self.w = self.wTools


	###########
	# Callbacks
	###########

	def PPEMSizeComboBoxCallback(self, sender):
		g = self.TTHToolController.getGlyph()
		if g == None:
			return
		size = sender.get()
		try:
			int(size)
		except:
			size = self.TTHToolModel.PPM_Size
			sender.set(size)

		self.TTHToolController.changeSize(size)

	def axisSegmentedButtonCallback(self, sender):
		if sender.get() == 0:
			self.TTHToolController.changeAxis('X')
			self.TTHToolController.makeStemsListsPopUpMenu()
			self.wTools.StemTypePopUpButton.setItems(self.TTHToolModel.stemsListX)
			self.TTHToolController.changeSelectedStemX(self.TTHToolModel.selectedStemX)
		else:
			self.TTHToolController.changeAxis('Y')
			self.TTHToolController.makeStemsListsPopUpMenu()
			self.wTools.StemTypePopUpButton.setItems(self.TTHToolModel.stemsListY)
			self.TTHToolController.changeSelectedStemY(self.TTHToolModel.selectedStemY)

	def toolsSegmentedButtonCallback(self, sender):
		if sender.get() == 0:
			self.AlignSettings()
			self.TTHToolController.changeSelectedAlignmentTypeAlign(self.TTHToolModel.selectedAlignmentTypeAlign)
			self.TTHToolController.changeSelectedHintingTool('Align')
		if sender.get() == 1:
			self.LinkSettings()
			self.TTHToolController.changeSelectedAlignmentTypeLink(self.TTHToolModel.selectedAlignmentTypeLink)
			if self.TTHToolModel.selectedAxis == 'X':
				self.TTHToolController.changeSelectedStemX(self.TTHToolModel.selectedStemX)
			else:
				self.TTHToolController.changeSelectedStemY(self.TTHToolModel.selectedStemY)
			self.TTHToolController.changeSelectedHintingTool('Single Link')
		if sender.get() == 2:
			self.DoubleLinkSettings()
			if self.TTHToolModel.selectedAxis == 'X':
				self.TTHToolController.changeSelectedStemX(self.TTHToolModel.selectedStemX)
			else:
				self.TTHToolController.changeSelectedStemY(self.TTHToolModel.selectedStemY)
			self.TTHToolController.changeSelectedHintingTool('Double Link')
		if sender.get() == 3:
			self.InterpolationSettings()
			self.TTHToolController.changeSelectedAlignmentTypeLink(self.TTHToolModel.selectedAlignmentTypeLink)
			self.TTHToolController.changeSelectedHintingTool('Interpolation')
		if sender.get() == 4:
			self.DeltaSettings()
			self.TTHToolController.changeSelectedHintingTool('Middle Delta')
		if sender.get() == 5:
			self.DeltaSettings()
			self.TTHToolController.changeSelectedHintingTool('Final Delta')
		if sender.get() == 6:
			self.SelectionSettings()
			self.TTHToolController.changeSelectedHintingTool('Selection')

	def AlignmentTypePopUpButtonCallback(self, sender):
		if self.TTHToolModel.selectedHintingTool in ['Single Link', 'Double Link', 'Interpolation']:
			self.TTHToolController.changeSelectedAlignmentTypeLink(self.alignmentTypeListLink[sender.get()])
		elif self.TTHToolModel.selectedHintingTool == 'Align':
			self.TTHToolController.changeSelectedAlignmentTypeAlign(self.alignmentTypeList[sender.get()])

	def StemTypePopUpButtonCallback(self, sender):
		if self.TTHToolModel.selectedAxis == 'X':
			self.TTHToolController.changeSelectedStemX(self.TTHToolModel.stemsListX[sender.get()])
		else:
			self.TTHToolController.changeSelectedStemY(self.TTHToolModel.stemsListY[sender.get()])

	def RoundDistanceCheckBoxCallback(self, sender):
		self.TTHToolController.changeRoundBool(sender.get())

	def DeltaMonochromeCheckBoxCallback(self, sender):
		self.TTHToolController.changeDeltaMono(sender.get())

	def DeltaGrayCheckBoxCallback(self, sender):
		self.TTHToolController.changeDeltaGray(sender.get())

	def DeltaOffsetSliderCallback(self, sender):
		self.TTHToolController.changeDeltaOffset(int(sender.get() - 8))

	def DeltaOffsetEditTextCallback(self, sender):
		self.TTHToolController.changeDeltaOffset(sender.get())

	def DeltaRange1ComboBoxCallback(self, sender):
		size = sender.get()
		try:
			int(size)
		except:
			size = self.TTHToolModel.deltaRange1
			sender.set(size)
		self.TTHToolController.changeDeltaRange(sender.get(), self.TTHToolModel.deltaRange2)

	def DeltaRange2ComboBoxCallback(self, sender):
		size = sender.get()
		try:
			int(size)
		except:
			size = self.TTHToolModel.deltaRange2
			sender.set(size)
		self.TTHToolController.changeDeltaRange(self.TTHToolModel.deltaRange1, sender.get())

	def gearMenuCallback(self, sender):
		gearOption = sender.get()
		if gearOption == 1:
			#self.autohintingSheet = SheetAutoHinting(self.wTools, self.TTHToolController)
			pass

		if gearOption == 3:
			self.TTHToolController.changeBitmapPreview("Monochrome")
		elif gearOption == 4:
			self.TTHToolController.changeBitmapPreview("Grayscale")
		elif gearOption == 5:
			self.TTHToolController.changeBitmapPreview("Subpixel")

		elif gearOption == 7:
			self.showPreviewCallback()
		elif gearOption == 8:
			self.showProgramCallback()
		elif gearOption == 9:
			self.showAssemblyCallback()

		elif gearOption == 11:
			self.controlValuesCallback()

		elif gearOption == 13:
			#self.preferencesSheet = SheetPreferences(self.wTools, self.TTHToolController)
			pass
		elif gearOption == 15:
			#matching.transfer(self.TTHToolController)
			pass

	##########
	# Bindings
	##########

	def toolsWindowMovedorResized(self, sender):
		self.tthtm.toolsWindowPosSize = self.wTools.getPosSize()
		setExtensionDefault(defaultKeyToolsWindowPosSize, self.TTHToolModel.toolsWindowPosSize)

	def close(self):
		self.wTools.close()