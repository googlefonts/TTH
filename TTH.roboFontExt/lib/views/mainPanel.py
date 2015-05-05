from defconAppKit.windows.baseWindow import BaseWindowController
from lib.doodleMenus import BaseMenu
from AppKit import *
from vanilla import *
from mojo.extensions import ExtensionBundle, setExtensionDefault, getExtensionDefault
from mojo.UI import UpdateCurrentGlyphView

from views import preferencesSheet
from models.TTHTool import uniqueInstance as tthTool

reload(preferencesSheet)

# get some icons
buttonXPath             = ExtensionBundle("TTH").get("buttonX")
buttonYPath             = ExtensionBundle("TTH").get("buttonY")
buttonAlignPath         = ExtensionBundle("TTH").get("buttonAlign")
buttonSingleLinkPath    = ExtensionBundle("TTH").get("buttonSingleLink")
buttonDoubleLinkPath    = ExtensionBundle("TTH").get("buttonDoubleLink")
buttonInterpolationPath = ExtensionBundle("TTH").get("buttonInterpolation")
buttonMiddleDeltaPath   = ExtensionBundle("TTH").get("buttonMiddleDelta")
buttonFinalDeltaPath    = ExtensionBundle("TTH").get("buttonFinalDelta")
buttonSelectionPath     = ExtensionBundle("TTH").get("buttonSelection")

DefaultKeyStub = "com.sansplomb.TTH."

defaultKeyMainPanelPosSize       = DefaultKeyStub + "toolsWindowPosSize"
defaultKeyPreviewWindowPosSize     = DefaultKeyStub + "previewWindowPosSize"
defaultKeyProgramWindowPosSize     = DefaultKeyStub + "programWindowPosSize"
defaultKeyAssemblyWindowPosSize    = DefaultKeyStub + "assemblyWindowPosSize"

defaultKeyProgramWindowVisibility  = DefaultKeyStub + "programWindowVisibility"
defaultKeyPreviewWindowVisibility  = DefaultKeyStub + "previewWindowVisibility"
defaultKeyAssemblyWindowVisibility = DefaultKeyStub + "assemblyWindowVisibility"

class MainPanel(BaseWindowController):
	def __init__(self):
		BaseWindowController.__init__(self)
		self.hintingToolsList = [	'Align',
							'Single Link',
							'Double Link',
							'Interpolation',
							'Middle Delta',
							'Final Delta',
							'Selection']
		self.makeStemsList()
		self.makeMainPanel()

	def makeMainPanel(self):
		self.wTools = FloatingWindow(getExtensionDefault(defaultKeyMainPanelPosSize, fallback=(170, 30, 265, 95)), "TTH", closable = False)
		
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

		self.PPMSizesList = [str(i) for i in range(8, 73)]

		# The PPEM Combobox
		self.wTools.PPEMSizeComboBox = ComboBox((10, 14, 40, 16),
				self.PPMSizesList, sizeStyle = "small",
				callback=self.PPEMSizeComboBoxCallback)
		self.wTools.PPEMSizeComboBox.set(tthTool.PPM_Size)

		# AXIS buttons
		self.wTools.axisSegmentedButton = SegmentedButton((60, 12, 70, 18), axisSegmentDescriptions, callback=self.axisSegmentedButtonCallback, sizeStyle="regular")
		if tthTool.selectedAxis == 'X':
			b = 0
		else:
			b = 1
		self.wTools.axisSegmentedButton.set(b)

		# Tools segmented buttons
		self.wTools.toolsSegmentedButton = SegmentedButton((-158, 12, 150, 18), toolsSegmentDescriptions, callback=self.toolsSegmentedButtonCallback, sizeStyle="regular")
		self.wTools.toolsSegmentedButton.set(6)

		# UI for alignment type
		self.wTools.AlignmentTypeText = TextBox((10, 42, 30, 15), "Align:", sizeStyle = "mini")
		self.wTools.AlignmentTypePopUpButton = PopUpButton((40, 40, 105, 16),
				['In construction...'], sizeStyle = "mini",
				callback=self.AlignmentTypePopUpButtonCallback)
		self.wTools.AlignmentTypeText.show(True)
		self.wTools.AlignmentTypePopUpButton.show(True)

		# UI for stem type
		self.wTools.StemTypeText = TextBox((10, 59, 30, 15), "Stem:", sizeStyle = "mini")
		self.wTools.StemTypePopUpButton = PopUpButton((40, 57, 105, 16),
				self.stemsList, sizeStyle = "mini",
				callback=self.StemTypePopUpButtonCallback)
		self.wTools.StemTypeText.show(False)
		self.wTools.StemTypePopUpButton.show(False)

		# UI for rounding coordinates (checkbox)
		self.wTools.RoundDistanceText = TextBox((155, 42, 80, 15), "Round Distance:", sizeStyle = "mini")
		self.wTools.RoundDistanceCheckBox = CheckBox((-25, 44, 15, 15), "", sizeStyle = "mini",
				callback=self.RoundDistanceCheckBoxCallback)
		self.wTools.RoundDistanceText.show(False)
		self.wTools.RoundDistanceCheckBox.show(False)

		# UI for delta value
		self.wTools.DeltaOffsetText = TextBox((10, 38, 40, 15), "Offset:", sizeStyle = "mini")
		self.wTools.DeltaOffsetSlider = Slider((10, 57, 130, 15), maxValue=16, value=8, tickMarkCount=17, continuous=False, stopOnTickMarks=True, sizeStyle= "small",
				callback=self.DeltaOffsetSliderCallback)
		self.wTools.DeltaOffsetEditText = EditText((50, 38, 30, 15), sizeStyle = "mini", 
				callback=self.DeltaOffsetEditTextCallback)
		self.wTools.DeltaOffsetText.show(False)
		self.wTools.DeltaOffsetSlider.show(False)
		self.wTools.DeltaOffsetEditText.set(tthTool.deltaOffset)
		self.wTools.DeltaOffsetEditText.show(False)

		# UI for delta range
		self.wTools.DeltaRangeText = TextBox((-120, 57, 40, 15), "Range:", sizeStyle = "mini")
		self.wTools.DeltaRange1ComboBox = ComboBox((-80, 55, 33, 15), self.PPMSizesList, sizeStyle = "mini", 
				callback=self.DeltaRange1ComboBoxCallback)
		self.wTools.DeltaRange2ComboBox = ComboBox((-43, 55, 33, 15), self.PPMSizesList, sizeStyle = "mini", 
				callback=self.DeltaRange2ComboBoxCallback)
		self.wTools.DeltaRangeText.show(False)
		self.wTools.DeltaRange1ComboBox.show(False)
		self.wTools.DeltaRange2ComboBox.show(False)
		self.wTools.DeltaRange1ComboBox.set(tthTool.deltaRange1)
		self.wTools.DeltaRange2ComboBox.set(tthTool.deltaRange2)

		# UI for applying delta only in Monochrome
		self.wTools.DeltaMonochromeText = TextBox((90, 38, 40, 15), "Mono:", sizeStyle = "mini")
		self.wTools.DeltaMonochromeCheckBox = CheckBox((130, 38, 15, 15), "", sizeStyle = "mini",
				callback=self.DeltaMonochromeCheckBoxCallback)
		self.wTools.DeltaMonochromeText.show(False)
		self.wTools.DeltaMonochromeCheckBox.show(False)
		self.wTools.DeltaMonochromeCheckBox.set(tthTool.deltaMonoBool)

		# UI for applying delta only in Grayscale & Subpixel
		self.wTools.DeltaGrayText = TextBox((150, 38, 80, 15), "Gray & Subpixel:", sizeStyle = "mini")
		self.wTools.DeltaGrayCheckBox = CheckBox((-25, 38, 15, 15), "", sizeStyle = "mini",
				callback=self.DeltaGrayCheckBoxCallback)
		self.wTools.DeltaGrayText.show(False)
		self.wTools.DeltaGrayCheckBox.show(False)
		self.wTools.DeltaGrayCheckBox.set(tthTool.deltaGrayBool)

		# The Gear Menu
		self.wTools.gear = PopUpButton((0, -22, 30, 18), [], callback=self.gearMenuCallback, sizeStyle="mini")
		self.wTools.gear.getNSPopUpButton().setPullsDown_(True)
		self.wTools.gear.getNSPopUpButton().setBordered_(False)

		im = NSImage.imageNamed_(NSImageNameActionTemplate)
		im.setSize_((10, 10))

		firstItem = NSMenuItem.alloc().init()
		firstItem.setImage_(im)
		firstItem.setTitle_("")

		#previewSubMenu = NSMenu.alloc().init()
		#previewSubMenu.initWithTitle_("Preview")
		#previewItem = NSMenuItem.alloc().init()
		#previewItem.setTitle_("Preview")

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

	def hide(self):
		self.wTools.hide()

	def show(self):
		self.wTools.show()

	###########
	# Callbacks
	###########

	def PPEMSizeComboBoxCallback(self, sender):
		try:
			tthTool.changeSize(int(sender.get()))
		except:
			tthTool.changeSize(tthTool.PPM_Size)

	def axisSegmentedButtonCallback(self, sender):
		if sender.get() == 0: tthTool.changeAxis('X')
		else: tthTool.changeAxis('Y')
		self.makeStemsList()
		self.wTools.StemTypePopUpButton.setItems(self.stemsList)
		#if sender.get() == 0: tthTool.changeSelectedStemX(tthTool.selectedStemX)
		#else: tthTool.changeSelectedStemY(tthTool.selectedStemY)
		UpdateCurrentGlyphView()

	def toolsSegmentedButtonCallback(self, sender):
		if sender.get() == 0:
			tthTool.changeSelectedHintingTool('Align')
		if sender.get() == 1:
			tthTool.changeSelectedAlignmentTypeLink(tthTool.selectedAlignmentTypeLink)
			if tthTool.selectedAxis == 'X':
				tthTool.changeSelectedStemX(tthTool.selectedStemX)
			else:
				tthTool.changeSelectedStemY(tthTool.selectedStemY)
			tthTool.changeSelectedHintingTool('Single Link')
		if sender.get() == 2:
			if tthTool.selectedAxis == 'X':
				tthTool.changeSelectedStemX(tthTool.selectedStemX)
			else:
				tthTool.changeSelectedStemY(tthTool.selectedStemY)
			tthTool.changeSelectedHintingTool('Double Link')
		if sender.get() == 3:
			tthTool.changeSelectedAlignmentTypeLink(tthTool.selectedAlignmentTypeLink)
			tthTool.changeSelectedHintingTool('Interpolation')
		if sender.get() == 4:
			tthTool.changeSelectedHintingTool('Middle Delta')
		if sender.get() == 5:
			tthTool.changeSelectedHintingTool('Final Delta')
		if sender.get() == 6:
			tthTool.changeSelectedHintingTool('Selection')

	def AlignmentTypePopUpButtonCallback(self, sender):
		tthTool.selectedHintingTool.setAlignment(sender.get())

	def StemTypePopUpButtonCallback(self, sender):
		if tthTool.selectedAxis == 'X':
			tthTool.changeSelectedStemX(self.stemsList[sender.get()])
		else:
			tthTool.changeSelectedStemY(self.stemsList[sender.get()])

	def RoundDistanceCheckBoxCallback(self, sender):
		tthTool.changeRoundBool(sender.get())

	def DeltaMonochromeCheckBoxCallback(self, sender):
		tthTool.changeDeltaMono(sender.get())

	def DeltaGrayCheckBoxCallback(self, sender):
		tthTool.changeDeltaGray(sender.get())

	def DeltaOffsetSliderCallback(self, sender):
		tthTool.changeDeltaOffset(int(sender.get() - 8))

	def DeltaOffsetEditTextCallback(self, sender):
		tthTool.changeDeltaOffset(sender.get())

	def DeltaRange1ComboBoxCallback(self, sender):
		size = sender.get()
		try:
			int(size)
		except:
			size = tthTool.deltaRange1
			sender.set(size)
		tthTool.changeDeltaRange(sender.get(), tthTool.deltaRange2)

	def DeltaRange2ComboBoxCallback(self, sender):
		size = sender.get()
		try:
			int(size)
		except:
			size = tthTool.deltaRange2
			sender.set(size)
		tthTool.changeDeltaRange(tthTool.deltaRange1, sender.get())

	def gearMenuCallback(self, sender):
		gearOption = sender.get()
		if gearOption == 1:
			#self.autohintingSheet = SheetAutoHinting(self.wTools, self.tthEventTool)
			pass

		fm = tthTool.getFontModel()

		if gearOption in [3,4,5]:
			modes = ["Monochrome", "Grayscale", "Subpixel"]
			if fm != None and fm.changeBitmapPreviewMode(modes[gearOption-3]):
				if tthTool.previewPanel.isVisible():
					tthTool.previewPanel.setNeedsDisplay()
				UpdateCurrentGlyphView()
		elif gearOption == 7:
			self.showPreviewCallback()
		elif gearOption == 8:
			self.showProgramCallback()
		elif gearOption == 9:
			self.showAssemblyCallback()

		elif gearOption == 11:
			self.controlValuesCallback()

		elif gearOption == 13:
			self.preferencesSheet = preferencesSheet.PreferencesSheet(self.wTools)
		elif gearOption == 15:
			#matching.transfer()
			pass

	def showPreviewCallback(self):
		tthTool.updatePartialFontIfNeeded()
		tthTool.previewPanel.show()

	#################
	# Display updates
	#################

	def displayPPEMSize(self, size):
		self.wTools.PPEMSizeComboBox.set(size)

	def displayDeltaRange(self, v1, v2):
		self.wTools.DeltaRange1ComboBox.set(v1)
		self.wTools.DeltaRange2ComboBox.set(v2)

	def makeStemsList(self):
		self.stemsList = ['None', 'Guess']
		fm = tthTool.getFontModel()
		if fm is None: return
		if tthTool.selectedAxis == 'X':
			self.stemsList += fm.verticalStems.keys()
		else:
			self.stemsList += fm.horizontalStems.keys()

	##########
	# Bindings
	##########

	def toolsWindowMovedorResized(self, sender):
		setExtensionDefault(defaultKeyMainPanelPosSize, self.wTools.getPosSize())

	def close(self):
		self.wTools.close()

if tthTool._printLoadings: print "mainPanel, ",
