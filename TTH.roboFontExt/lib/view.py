#coding=utf-8

from vanilla import *
from mojo.UI import *
from mojo.extensions import *
from mojo.canvas import Canvas
from lib.doodleMenus import BaseMenu
from AppKit import *
from defconAppKit.windows.baseWindow import BaseWindowController

import string
import time

import preview
import view_ControlValues as CV
import Automation

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

class toolsWindow(BaseWindowController):
	def __init__(self, TTHToolInstance):
		BaseWindowController.__init__(self)
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm

		self.axisList = ['X', 'Y']
		self.hintingToolsList = ['Align', 'Single Link', 'Double Link', 'Interpolation', 'Middle Delta', 'Final Delta', 'Selection']
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



		self.wTools = FloatingWindow(getExtensionDefault(defaultKeyToolsWindowPosSize, fallback=self.tthtm.toolsWindowPosSize), "TTH", closable = False)

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

		# self.wTools.PPEMSizeEditText = EditText((10, 14, 25, 15), sizeStyle = "mini", 
		# 		callback=self.PPEMSizeEditTextCallback)
		# self.wTools.PPEMSizeEditText.set(self.tthtm.PPM_Size)

		self.PPMSizesList = [str(i) for i in range(9, 73)]
		#self.wTools.PPEMSizePopUpButton = PopUpButton((40, 14, 40, 16),
		#		self.PPMSizesList, sizeStyle = "mini",
		#		callback=self.PPEMSizePopUpButtonCallback)

		self.wTools.PPEMSizeComboBox = ComboBox((10, 14, 40, 16),
				self.PPMSizesList, sizeStyle = "small",
				callback=self.PPEMSizeComboBoxCallback)
		self.wTools.PPEMSizeComboBox.set(self.tthtm.PPM_Size)

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
		self.wTools.DeltaOffsetEditText.set(self.tthtm.deltaOffset)
		self.wTools.DeltaOffsetEditText.show(False)

		self.wTools.DeltaRangeText = TextBox((-120, 57, 40, 15), "Range:", sizeStyle = "mini")
		self.wTools.DeltaRange1ComboBox = ComboBox((-80, 55, 33, 15), self.PPMSizesList, sizeStyle = "mini", 
				callback=self.DeltaRange1ComboBoxCallback)
		self.wTools.DeltaRange2ComboBox = ComboBox((-43, 55, 33, 15), self.PPMSizesList, sizeStyle = "mini", 
				callback=self.DeltaRange2ComboBoxCallback)
		self.wTools.DeltaRangeText.show(False)
		self.wTools.DeltaRange1ComboBox.show(False)
		self.wTools.DeltaRange2ComboBox.show(False)
		self.wTools.DeltaRange1ComboBox.set(self.tthtm.deltaRange1)
		self.wTools.DeltaRange2ComboBox.set(self.tthtm.deltaRange2)

		self.wTools.DeltaMonochromeText = TextBox((90, 38, 40, 15), "Mono:", sizeStyle = "mini")
		self.wTools.DeltaMonochromeCheckBox = CheckBox((130, 40, 15, 15), "", sizeStyle = "mini",
				callback=self.DeltaMonochromeCheckBoxCallback)
		self.wTools.DeltaMonochromeText.show(False)
		self.wTools.DeltaMonochromeCheckBox.show(False)
		self.wTools.DeltaMonochromeCheckBox.set(self.tthtm.deltaMonoBool)

		self.wTools.DeltaGrayText = TextBox((150, 38, 80, 15), "Gray & Subpixel:", sizeStyle = "mini")
		self.wTools.DeltaGrayCheckBox = CheckBox((-25, 40, 15, 15), "", sizeStyle = "mini",
				callback=self.DeltaGrayCheckBoxCallback)
		self.wTools.DeltaGrayText.show(False)
		self.wTools.DeltaGrayCheckBox.show(False)
		self.wTools.DeltaGrayCheckBox.set(self.tthtm.deltaGrayBool)

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
		#monoItem = NSMenuItem.alloc().init()
		#monoItem.setTitle_("Monochrome")
		#previewSubMenu.addItem_(monoItem)

		previewItem = NSMenuItem.alloc().init()
		previewItem.setTitle_("Preview")
		#previewItem.setSubMenu_(previewSubMenu)


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
			]
			)

		imgRefresh = NSImage.imageNamed_(NSImageNameRefreshTemplate)
		imgRefresh.setSize_((10, 13))

		self.wTools.button = ImageButton((-30, -20, 30, 18), imageObject=imgRefresh, bordered=False, callback=self.refreshButtonCallback, sizeStyle="small")

		self.wTools.bind("move", self.toolsWindowMovedorResized)

		self.wTools.open()
		self.w = self.wTools

	def gearMenuCallback(self, sender):
		gearOption = sender.get()
		if gearOption == 1:
			self.autohintingSheet = SheetAutoHinting(self.wTools, self.TTHToolInstance)

		if gearOption == 3:
			self.TTHToolInstance.changeBitmapPreview("Monochrome")
		if gearOption == 4:
			self.TTHToolInstance.changeBitmapPreview("Grayscale")
		if gearOption == 5:
			self.TTHToolInstance.changeBitmapPreview("Subpixel")

		if gearOption == 7:
			self.showPreviewCallback()
		if gearOption == 8:
			self.showProgramCallback()
		if gearOption == 9:
			self.showAssemblyCallback()

		if gearOption == 11:
			self.controlValuesCallback()

		if gearOption == 13:
			self.preferencesSheet = SheetPreferences(self.wTools, self.TTHToolInstance)

	def controlValuesCallback(self):
		self.sheet = CV.SheetControlValues(self, self.wTools, self.tthtm, self.TTHToolInstance)

	def showPreviewCallback(self):
		self.TTHToolInstance.updatePartialFont()
		self.TTHToolInstance.previewWindow.show()

	def showProgramCallback(self):
		self.TTHToolInstance.programWindow.show()
		self.TTHToolInstance.resetglyph(self.TTHToolInstance.getGlyph())

	def showAssemblyCallback(self):
		self.TTHToolInstance.assemblyWindow.show()
		self.TTHToolInstance.resetglyph(self.TTHToolInstance.getGlyph())


	def refreshButtonCallback(self, sender):
		print 'refresh'

	def closeTools(self):
		self.wTools.close()

	def toolsWindowMovedorResized(self, sender):
		self.tthtm.toolsWindowPosSize = self.wTools.getPosSize()
		setExtensionDefault(defaultKeyToolsWindowPosSize, self.tthtm.toolsWindowPosSize)

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
		self.wTools.DeltaRange1ComboBox.show(False)
		self.wTools.DeltaRange2ComboBox.show(False)
		self.wTools.DeltaOffsetEditText.show(False)
		self.wTools.DeltaMonochromeText.show(False)
		self.wTools.DeltaMonochromeCheckBox.show(False)
		self.wTools.DeltaGrayText.show(False)
		self.wTools.DeltaGrayCheckBox.show(False)

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
		self.wTools.DeltaRange1ComboBox.show(False)
		self.wTools.DeltaRange2ComboBox.show(False)
		self.wTools.DeltaOffsetEditText.show(False)
		self.wTools.DeltaMonochromeText.show(False)
		self.wTools.DeltaMonochromeCheckBox.show(False)
		self.wTools.DeltaGrayText.show(False)
		self.wTools.DeltaGrayCheckBox.show(False)

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
		self.wTools.DeltaRange1ComboBox.show(False)
		self.wTools.DeltaRange2ComboBox.show(False)
		self.wTools.DeltaOffsetEditText.show(False)
		self.wTools.DeltaMonochromeText.show(False)
		self.wTools.DeltaMonochromeCheckBox.show(False)
		self.wTools.DeltaGrayText.show(False)
		self.wTools.DeltaGrayCheckBox.show(False)

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
		self.wTools.DeltaRange1ComboBox.show(False)
		self.wTools.DeltaRange2ComboBox.show(False)
		self.wTools.DeltaOffsetEditText.show(False)
		self.wTools.DeltaMonochromeText.show(False)
		self.wTools.DeltaMonochromeCheckBox.show(False)
		self.wTools.DeltaGrayText.show(False)
		self.wTools.DeltaGrayCheckBox.show(False)

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
		self.wTools.DeltaRange1ComboBox.show(True)
		self.wTools.DeltaRange2ComboBox.show(True)
		self.wTools.DeltaOffsetEditText.show(True)
		self.wTools.DeltaMonochromeText.show(True)
		self.wTools.DeltaMonochromeCheckBox.show(True)
		self.wTools.DeltaGrayText.show(True)
		self.wTools.DeltaGrayCheckBox.show(True)

	def SelectionSettings(self):
		self.wTools.AlignmentTypeText.show(False)
		self.wTools.AlignmentTypePopUpButton.show(False)
		self.wTools.StemTypeText.show(False)
		self.wTools.StemTypePopUpButton.show(False)
		self.wTools.RoundDistanceText.show(False)
		self.wTools.RoundDistanceCheckBox.show(False)
		self.wTools.DeltaOffsetText.show(False)
		self.wTools.DeltaOffsetSlider.show(False)
		self.wTools.DeltaRangeText.show(False)
		self.wTools.DeltaRange1ComboBox.show(False)
		self.wTools.DeltaRange2ComboBox.show(False)
		self.wTools.DeltaOffsetEditText.show(False)
		self.wTools.DeltaMonochromeText.show(False)
		self.wTools.DeltaMonochromeCheckBox.show(False)
		self.wTools.DeltaGrayText.show(False)
		self.wTools.DeltaGrayCheckBox.show(False)

	# def PPEMSizeEditTextCallback(self, sender):
	# 	self.TTHToolInstance.changeSize(sender.get())

	# def PPEMSizePopUpButtonCallback(self, sender):
	# 	g = self.TTHToolInstance.getGlyph()
	# 	if g == None:
	# 		return
	# 	size = self.PPMSizesList[sender.get()]
	# 	self.TTHToolInstance.changeSize(size)

	def PPEMSizeComboBoxCallback(self, sender):
		g = self.TTHToolInstance.getGlyph()
		if g == None:
			return
		size = sender.get()
		try:
			int(size)
		except:
			size = self.tthtm.PPM_Size
			sender.set(size)

		self.TTHToolInstance.changeSize(size)


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

	def DeltaMonochromeCheckBoxCallback(self, sender):
		self.TTHToolInstance.changeDeltaMono(sender.get())

	def DeltaGrayCheckBoxCallback(self, sender):
		self.TTHToolInstance.changeDeltaGray(sender.get())

	def DeltaOffsetSliderCallback(self, sender):
		self.TTHToolInstance.changeDeltaOffset(int(sender.get() - 8))

	def DeltaOffsetEditTextCallback(self, sender):
		self.TTHToolInstance.changeDeltaOffset(sender.get())

	def DeltaRange1ComboBoxCallback(self, sender):
		size = sender.get()
		try:
			int(size)
		except:
			size = self.tthtm.deltaRange1
			sender.set(size)
		self.TTHToolInstance.changeDeltaRange(sender.get(), self.tthtm.deltaRange2)

	def DeltaRange2ComboBoxCallback(self, sender):
		size = sender.get()
		try:
			int(size)
		except:
			size = self.tthtm.deltaRange2
			sender.set(size)
		self.TTHToolInstance.changeDeltaRange(self.tthtm.deltaRange1, sender.get())

	# def DeltaRange1EditTextCallback(self, sender):
	# 	self.TTHToolInstance.changeDeltaRange(sender.get(), self.tthtm.deltaRange2)

	# def DeltaRange2EditTextCallback(self, sender):
	# 	self.TTHToolInstance.changeDeltaRange(self.tthtm.deltaRange1, sender.get())


	def axisSegmentedButtonCallback(self, sender):
		if sender.get() == 0:
			self.TTHToolInstance.changeAxis('X')
			self.TTHToolInstance.makeStemsListsPopUpMenu()
			self.wTools.StemTypePopUpButton.setItems(self.tthtm.stemsListX)
			self.TTHToolInstance.changeSelectedStemX(self.tthtm.selectedStemX)
		else:
			self.TTHToolInstance.changeAxis('Y')
			self.TTHToolInstance.makeStemsListsPopUpMenu()
			self.wTools.StemTypePopUpButton.setItems(self.tthtm.stemsListY)
			self.TTHToolInstance.changeSelectedStemY(self.tthtm.selectedStemY)
	
	def toolsSegmentedButtonCallback(self, sender):
		if sender.get() == 0:
			self.AlignSettings()
			self.TTHToolInstance.changeSelectedAlignmentTypeAlign(self.tthtm.selectedAlignmentTypeAlign)
			self.TTHToolInstance.changeSelectedHintingTool('Align')
		if sender.get() == 1:
			self.LinkSettings()
			self.TTHToolInstance.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)
			if self.tthtm.selectedAxis == 'X':
				self.TTHToolInstance.changeSelectedStemX(self.tthtm.selectedStemX)
			else:
				self.TTHToolInstance.changeSelectedStemY(self.tthtm.selectedStemY)
			self.TTHToolInstance.changeSelectedHintingTool('Single Link')
		if sender.get() == 2:
			self.DoubleLinkSettings()
			if self.tthtm.selectedAxis == 'X':
				self.TTHToolInstance.changeSelectedStemX(self.tthtm.selectedStemX)
			else:
				self.TTHToolInstance.changeSelectedStemY(self.tthtm.selectedStemY)
			self.TTHToolInstance.changeSelectedHintingTool('Double Link')
		if sender.get() == 3:
			self.InterpolationSettings()
			self.TTHToolInstance.changeSelectedAlignmentTypeLink(self.tthtm.selectedAlignmentTypeLink)
			self.TTHToolInstance.changeSelectedHintingTool('Interpolation')
		if sender.get() == 4:
			self.DeltaSettings()
			self.TTHToolInstance.changeSelectedHintingTool('Middle Delta')
		if sender.get() == 5:
			self.DeltaSettings()
			self.TTHToolInstance.changeSelectedHintingTool('Final Delta')
		if sender.get() == 6:
			self.SelectionSettings()
			self.TTHToolInstance.changeSelectedHintingTool('Selection')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class TTHWindow(object):
	def __init__(self, defaultPosSize, posSizeKey, visibilityKey):
		self.window_          = None
		self.defaultPosSize_  = defaultPosSize
		self.posSizeKey_      = posSizeKey
		self.visibilityKey_   = visibilityKey
	def __del__(self):
		if self.window_ != None:
			self.window_.close()
	def window(self):
		return self.window_
	def setWindow(self, w):
		self.window_ = w
		w.bind("move", self.movedOrResized)
		w.bind("resize", self.movedOrResized)
		w.bind("should close", self.shouldClose)

	def isVisible(self):
		return self.window().isVisible()
	def showOrHide(self):
		if 1 == getExtensionDefault(self.visibilityKey_, fallback=0):
			self.window().show()
		else:
			self.window().hide()
	def show(self):
		setExtensionDefault(self.visibilityKey_, 1)
		self.showOrHide()
	def hide(self):
		self.window().hide()
	def setNeedsDisplay(self):
		self.window().getNSWindow().setViewsNeedDisplay_(True)

	# callbacks
	def shouldClose(self, sender):
		self.hide()
		setExtensionDefault(self.visibilityKey_, 0)
		return False # which means, no please don't close the window
	def movedOrResized(self, sender):
		setExtensionDefault(self.posSizeKey_, self.window().getPosSize())

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class PreviewWindow(TTHWindow):
	def __init__(self, TTHToolInstance, defaultPosSize):
		super(PreviewWindow, self).__init__(defaultPosSize, defaultKeyPreviewWindowPosSize, defaultKeyPreviewWindowVisibility)
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm

		self.FromSize = self.tthtm.previewFrom
		self.ToSize = self.tthtm.previewTo

		ps = getExtensionDefault(defaultKeyPreviewWindowPosSize, fallback=defaultPosSize)
		win = FloatingWindow(ps, "Preview", minSize=(350, 200))

		previewList = ['HH/?HH/?OO/?OO/?', 'nn/?nn/?oo/?oo/?', '0123456789', string.uppercase, string.lowercase]
		win.previewEditText = ComboBox((10, 10, -10, 22), previewList,
				callback=self.previewEditTextCallback)
		win.previewEditText.set(self.tthtm.previewString)

		win.view = Canvas((10, 50, -10, -40), delegate = self, canvasSize = self.calculateCanvasSize(ps))

		win.DisplaySizesText = TextBox((10, -30, 120, -10), "Display Sizes From:", sizeStyle = "small")
		win.DisplayFromEditText = EditText((130, -32, 30, 19), sizeStyle = "small", 
				callback=self.DisplayFromEditTextCallback)
		win.DisplayFromEditText.set(self.FromSize)

		win.DisplayToSizeText = TextBox((170, -30, 22, -10), "To:", sizeStyle = "small")
		win.DisplayToEditText = EditText((202, -32, 30, 19), sizeStyle = "small", 
				callback=self.DisplayToEditTextCallback)
		win.DisplayToEditText.set(self.ToSize)
		win.ApplyButton = Button((-100, -32, -10, 22), "Apply", sizeStyle = 'small', 
				callback=self.ApplyButtonCallback)
		
		for i in string.lowercase:
			self.tthtm.requiredGlyphsForPartialTempFont.add(i)
		for i in string.uppercase:
			self.tthtm.requiredGlyphsForPartialTempFont.add(i)
		for i in ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'zero']:
			self.tthtm.requiredGlyphsForPartialTempFont.add(i)

		win.bind("move", self.movedOrResizedCallback)
		win.bind("resize", self.movedOrResizedCallback)
		self.setWindow(win) # this will not rebind the events, since they are already bound.

	def calculateCanvasSize(self, winPosSize):
		return (winPosSize[2], winPosSize[3]-90)

	def setNeedsDisplay(self):
		self.window().view.getNSView().setNeedsDisplay_(True)

	def mouseUp(self, event):
		win = self.window()
		cnt = win.view.scrollView._getContentView().contentView()
		pos = win.getNSWindow().contentView().convertPoint_toView_(event.locationInWindow(), cnt)
		x, y = pos.x, pos.y
		for i in self.TTHToolInstance.clickableSizes:
			if x >= i[0] and x <= i[0]+10 and y >= i[1] and y <= i[1]+8:
				self.TTHToolInstance.changeSize(self.TTHToolInstance.clickableSizes[i])
				break
		for coords, glyphName in self.TTHToolInstance.clickableGlyphs.items():
			if x >= coords[0] and x <= coords[2] and y >= coords[1] and y <= coords[3]:
				SetCurrentGlyphByName(glyphName[0])
				break

	def draw(self):
		self.TTHToolInstance.drawPreviewWindow()
	
	def resizeView(self, posSize):
		self.window().view.getNSView().setFrame_(((0, 0), self.calculateCanvasSize(posSize)))

	def movedOrResizedCallback(self, sender):
		super(PreviewWindow, self).movedOrResized(sender)
		self.resizeView(self.window().getPosSize())
	
		# self.viewSize = (self.tthtm.previewWindowViewSize[0], self.tthtm.previewWindowPosSize[3]-110)
		# self.view.setFrame_(((0, 0), self.viewSize))
		# self.view.setFrameOrigin_((0, 10*(self.viewSize[1]/2)))
		# self.view.setAutoresizingMask_(NSViewMinXMargin | NSViewMaxXMargin | NSViewMinYMargin | NSViewMaxYMargin)

	def previewEditTextCallback(self, sender):
		self.tthtm.setPreviewString(sender.get())
		self.TTHToolInstance.updatePartialFontIfNeeded()
		self.setNeedsDisplay()

	def DisplayFromEditTextCallback(self, sender):
		try:
			size = int(sender.get())
		except:
			size = self.tthtm.previewFrom
		self.FromSize = self.TTHToolInstance.cleanPreviewSize(size)

	def DisplayToEditTextCallback(self, sender):
		try:
			size = int(sender.get())
		except:
			size = self.tthtm.previewTo
		self.ToSize = self.TTHToolInstance.cleanPreviewSize(size)

	def ApplyButtonCallback(self, sender):
		win = self.window()
		fromS = self.FromSize
		toS = self.ToSize
		if fromS < 8: fromS = 8
		if toS < 8: toS = 8
		if fromS > toS:
			fromS = toS
		if toS > fromS + 100:
			toS = fromS + 100
		self.FromSize = fromS
		self.ToSize = toS
		self.window().DisplayFromEditText.set(fromS)
		self.window().DisplayToEditText.set(toS)
		self.TTHToolInstance.changePreviewSize(self.FromSize, self.ToSize)
		self.setNeedsDisplay()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class ProgramWindow(TTHWindow):
	def __init__(self, TTHToolInstance, defaultPosSize):
		super(ProgramWindow, self).__init__(defaultPosSize, defaultKeyProgramWindowPosSize, defaultKeyProgramWindowVisibility)
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm
		self.lock = False

		ps = getExtensionDefault(defaultKeyProgramWindowPosSize, fallback=defaultPosSize)
		win = FloatingWindow(ps, "Program", minSize=(600, 80))

		columnDescriptions = [
			{"title": "index", "width": 30, "editable": False}, 
			dict(title="active", cell=CheckBoxListCell(), width=35, editable=True),
			{"title": "code", "editable": False}, 
			{"title": "point", "editable": False},
			{"title": "point1", "editable": False}, 
			{"title": "point2", "editable": False}, 
			{"title": "align", "editable": False},
			{"title": "round", "editable": False}, 
			{"title": "stem", "editable": False}, 
			{"title": "zone", "editable": False},
			#dict(title='delta', cell=sliderCell, width=90, editable=True),
			{"title": "delta", "editable": False}, 
			{"title": "ppm1", "editable": False}, 
			{"title": "ppm2", "editable": False},
			{"title": "mono", "editable": False},
			{"title": "gray", "editable": False}
			]
		self.programList = []
		win.programList = List((0, 0, -0, -0), self.programList, 
					columnDescriptions=columnDescriptions,
					enableDelete=False, 
					showColumnTitles=True,
					selectionCallback=self.selectionCallback,
					editCallback = self.editCallback)

		self.setWindow(win) # this will not rebind the events, since they are already bound.

	def selectionCallback(self, sender):
		pass
		# if sender.getSelection() != []:
		# 	self.TTHToolInstance.popOverIsOpened = True
		# 	self.TTHToolInstance.commandClicked = sender.getSelection()[0]
		# 	self.TTHToolInstance.selectedCommand = self.TTHToolInstance.glyphTTHCommands[self.TTHToolInstance.commandClicked]
		# 	UpdateCurrentGlyphView()
		#print sender.getSelection()

	def editCallback(self, sender):
		if self.lock or (sender.getSelection() == []):
			return
		self.lock = True
		updatedCommands = []
		g = self.TTHToolInstance.getGlyph()
		g.prepareUndo('Edit Program')
		keys = ['code', 'point', 'point1', 'point2', 'align', 'round', 'stem', 'zone', 'ppm1', 'ppm2', 'mono', 'gray']
		for commandUI in sender.get():
			command = { k : str(commandUI[k]) for k in keys if commandUI[k] != '' }
			if commandUI['active'] == 1:
				command['active'] = 'true'
			else:
				command['active'] = 'false'
			if commandUI['delta'] != '':
				command['delta'] = str(int(commandUI['delta']))

			updatedCommands.append(command)

		self.TTHToolInstance.glyphTTHCommands = updatedCommands

		self.TTHToolInstance.updateGlyphProgram(g)
		if self.tthtm.alwaysRefresh == 1:
			self.TTHToolInstance.refreshGlyph(g)

		g.performUndo()

		self.lock = False


	def updateProgramList(self, commands):
		self.commands =  [dict(c) for c in commands]
		def putIfNotThere(c, key):
			if key not in c:
				c[key] = ''
			if key == 'index':
				c[key] = self.i
				self.i += 1
			if key == 'active':
				c[key] = (c[key] == 'true')
		self.i = 0
		for command in self.commands:
			for key in ['index', 'code', 'point', 'point1', 'point2', 'align', 'round', 'stem', 'zone', 'delta', 'ppm1', 'ppm2', 'active', 'mono', 'gray']:
				putIfNotThere(command, key)
		self.window().programList.set(self.commands)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class AssemblyWindow(TTHWindow):
	def __init__(self, TTHToolInstance, defaultPosSize):
		super(AssemblyWindow, self).__init__(defaultPosSize, defaultKeyAssemblyWindowPosSize, defaultKeyAssemblyWindowVisibility)
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm

		self.assemblyList = []

		ps = getExtensionDefault(defaultKeyAssemblyWindowPosSize, fallback=defaultPosSize)
		win = FloatingWindow(ps, "Assembly", minSize=(150, 100))
		win.assemblyList = List((0, 0, -0, -0), self.assemblyList,
					columnDescriptions=[{"title": "Assembly", "width": 150, "editable": False}],
					showColumnTitles=False)
		self.setWindow(win)

	def updateAssemblyList(self, assembly):
		assemlblyDictList = []
		for a in assembly:
			assemblyDict = {}
			assemblyDict["Assembly"] = a
			assemlblyDictList.append(assemblyDict)
		self.window().assemblyList.set(assemlblyDictList)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class SheetAutoHinting(object):

	def __init__(self, parent, controller):
		self.controller = controller
		self.c_fontModel = controller.c_fontModel
		self.model = controller.tthtm

		self.autohinting = Automation.AutoHinting(self.controller)

		self.w = Sheet((300, 150), parentWindow=parent)

		self.w.autohintFontButton = Button((120, -64, 100, 22), "Auto-hint Font", sizeStyle = "small", callback=self.autoHintFontCallBack)
		self.w.autohintGlyphButton = Button((10, -64, 100, 22), "Auto-hint Glyph", sizeStyle = "small", callback=self.autoHintGlyphCallBack)
		self.w.bar = ProgressBar((10, -29, -80, 16))
		self.w.bar.show(0)
		self.w.closeButton = Button((-70, -32, 60, 22), "Close", sizeStyle = "small", callback=self.closeButtonCallback)
		self.w.open()


	def closeButtonCallback(self, sender):
		self.w.close()

	def autoHintGlyphCallBack(self, sender):
		g = self.controller.getGlyph()
		g.prepareUndo("Auto-hint Glyph")
		self.autohinting.autohint(g, None)
		self.controller.updateGlyphProgram(g)
		if self.model.alwaysRefresh == 1:
			self.controller.refreshGlyph(g)
		g.performUndo()

	def autoHintFontCallBack(self, sender):
		self.w.bar.show(1)
		self.w.bar.set(0)
		font = self.c_fontModel.f
		increment = 100.0/len(font)
		maxStemSize = Automation.computeMaxStemOnO(self.controller.tthtm, font)
		elapsedTime = time.clock()
		for g in self.c_fontModel.f:
			g.prepareUndo("Auto-hint Glyph")
			self.autohinting.autohint(g, maxStemSize)
			self.controller.updateGlyphProgram(g)
			g.performUndo()
			self.w.bar.increment(increment)
		elapsedTime = time.clock() - elapsedTime
		print "Font auto-hinted in", elapsedTime, "seconds."
		self.w.bar.show(0)
		self.controller.resetFont()

class SheetPreferences(object):

	def __init__(self, parent, controller):
		self.controller = controller
		self.c_fontModel = controller.c_fontModel
		self.model = controller.tthtm

		self.w = Sheet((505, 480), parentWindow=parent)

		self.w.viewAndSettingsBox = Box((10, 19, -10, -40))

		self.w.autohintingBox = Box((10, 19, -10, -40))

		self.w.hotKeysBox = Box((10, 19, -10, -40))

		preferencesSegmentDescriptions = [
			dict(width=67, title="View", toolTip="View"),
			dict(width=67, title="Auto-hinting", toolTip="Auto-hinting"),
			dict(width=67, title="Hot Keys", toolTip="Hot Keys")
		]

		self.w.controlsSegmentedButton = SegmentedButton((137, 10, 220, 18), preferencesSegmentDescriptions, callback=self.preferencesSegmentedButtonCallback, sizeStyle="mini")
		self.w.controlsSegmentedButton.set(0)

		self.w.viewAndSettingsBox.show(True)
		self.w.autohintingBox.show(False)
		self.w.hotKeysBox.show(False)

		self.w.closeButton = Button((-70, -32, 60, 22), "Close", sizeStyle = "small", callback=self.closeButtonCallback)
		self.w.open()


	def closeButtonCallback(self, sender):
		self.w.close()

	def preferencesSegmentedButtonCallback(self, sender):
		if sender.get() == 0:
			self.w.viewAndSettingsBox.show(True)
			self.w.autohintingBox.show(False)
			self.w.hotKeysBox.show(False)
		if sender.get() == 1:
			self.w.viewAndSettingsBox.show(False)
			self.w.autohintingBox.show(True)
			self.w.hotKeysBox.show(False)
		if sender.get() == 2:
			self.w.viewAndSettingsBox.show(False)
			self.w.autohintingBox.show(False)
			self.w.hotKeysBox.show(True)


reload(CV)
