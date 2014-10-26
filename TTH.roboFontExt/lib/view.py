#coding=utf-8

from vanilla import *
from mojo.UI import *
from mojo.extensions import *
from mojo.canvas import Canvas
from lib.doodleMenus import BaseMenu
from AppKit import *
from defconAppKit.windows.baseWindow import BaseWindowController

import string

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

defaultKeyPreviewWindowVisibility = DefaultKeyStub + "previewWindowVisibility"
defaultKeyProgramWindowVisibility = DefaultKeyStub + "programWindowVisibility"
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

		self.wTools.DeltaOffsetText = TextBox((10, 42, 50, 15), "Offset:", sizeStyle = "mini")
		self.wTools.DeltaOffsetSlider = Slider((10, 57, -10, 15), maxValue=16, value=8, tickMarkCount=17, continuous=False, stopOnTickMarks=True, sizeStyle= "small",
				callback=self.DeltaOffsetSliderCallback)
		self.wTools.DeltaOffsetEditText = EditText((60, 40, 30, 15), sizeStyle = "mini", 
				callback=self.DeltaOffsetEditTextCallback)
		self.wTools.DeltaOffsetText.show(False)
		self.wTools.DeltaOffsetSlider.show(False)
		self.wTools.DeltaOffsetEditText.set(self.tthtm.deltaOffset)
		self.wTools.DeltaOffsetEditText.show(False)

		self.wTools.DeltaRangeText = TextBox((-120, 42, 40, 15), "Range:", sizeStyle = "mini")
		self.wTools.DeltaRange1ComboBox = ComboBox((-80, 40, 33, 15), self.PPMSizesList, sizeStyle = "mini", 
				callback=self.DeltaRange1ComboBoxCallback)
		self.wTools.DeltaRange2ComboBox = ComboBox((-43, 40, 33, 15), self.PPMSizesList, sizeStyle = "mini", 
				callback=self.DeltaRange2ComboBoxCallback)
		self.wTools.DeltaRangeText.show(False)
		self.wTools.DeltaRange1ComboBox.show(False)
		self.wTools.DeltaRange2ComboBox.show(False)
		self.wTools.DeltaRange1ComboBox.set(self.tthtm.deltaRange1)
		self.wTools.DeltaRange2ComboBox.set(self.tthtm.deltaRange2)

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
			self.tthtm.setPreviewWindowVisible(1)
		if gearOption == 8:
			self.showProgramCallback()
			self.tthtm.setProgramWindowVisible(1)
		if gearOption == 9:
			self.showAssemblyCallback()
			self.tthtm.setAssemblyWindowVisible(1)

		if gearOption == 11:
			self.controlValuesCallback()

	def controlValuesCallback(self):
		self.sheet = CV.SheetControlValues(self, self.wTools, self.tthtm, self.TTHToolInstance)

	def showPreviewCallback(self):
		if self.tthtm.previewWindowOpened == 0:
			self.TTHToolInstance.updatePartialFont()
			self.TTHToolInstance.previewWindow = previewWindow(self.TTHToolInstance, self.tthtm)
			self.TTHToolInstance.previewWindow.wPreview.resize(self.tthtm.previewWindowPosSize[2]-1, self.tthtm.previewWindowPosSize[3]-1, animate=False)
			self.TTHToolInstance.previewWindow.wPreview.resize(self.tthtm.previewWindowPosSize[2]+1, self.tthtm.previewWindowPosSize[3]+1, animate=False)

	def showProgramCallback(self):
		if self.tthtm.programWindowOpened == 0:
			self.TTHToolInstance.programWindow = programWindow(self.TTHToolInstance, self.tthtm)
			self.TTHToolInstance.resetglyph(self.TTHToolInstance.getGlyph())

	def showAssemblyCallback(self):
		if self.tthtm.assemblyWindowOpened == 0:
			self.TTHToolInstance.assemblyWindow = assemblyWindow(self.TTHToolInstance, self.tthtm)
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

class previewWindow(object):
	def __init__(self, TTHToolInstance, tthtm):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm

		self.FromSize = self.tthtm.previewFrom
		self.ToSize = self.tthtm.previewTo

		#self.viewSize = self.tthtm.previewWindowViewSize

		self.wPreview = FloatingWindow(getExtensionDefault(defaultKeyPreviewWindowPosSize, fallback=self.tthtm.previewWindowPosSize), "Preview", minSize=(350, 200))
		# self.view = preview.PreviewArea.alloc().init_withTTHToolInstance(self.TTHToolInstance)
		# self.view.setFrame_(((0, 0), self.viewSize))
		# self.view.setFrameOrigin_((0, 10*(self.viewSize[1]/2)))
		# self.view.setAutoresizingMask_(NSViewMinXMargin | NSViewMaxXMargin | NSViewMinYMargin | NSViewMaxYMargin)
		self.previewList = ['HH/?HH/?OO/?OO/?', 'nn/?nn/?oo/?oo/?', '0123456789', string.uppercase, string.lowercase]
		self.wPreview.previewEditText = ComboBox((10, 10, -10, 22), self.previewList,
				callback=self.previewEditTextCallback)
		self.wPreview.previewEditText.set(self.tthtm.previewString)

		self.wPreview.view = Canvas((10, 50, -10, -40), delegate = self, canvasSize= self.tthtm.previewWindowViewSize)
		self.previewWindowMovedorResized(None)

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
		self.tthtm.previewWindowOpened = 1
		self.wPreview.bind("close", self.previewWindowWillClose)
		self.wPreview.bind("move", self.previewWindowMovedorResized)
		self.wPreview.bind("resize", self.previewWindowMovedorResized)
		
		for i in string.lowercase:
			self.tthtm.requiredGlyphsForPartialTempFont.add(i)
		for i in string.uppercase:
			self.tthtm.requiredGlyphsForPartialTempFont.add(i)
		for i in ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'zero']:
			self.tthtm.requiredGlyphsForPartialTempFont.add(i)

		self.wPreview.open()
		self.wPreview.resize(self.tthtm.previewWindowPosSize[2], self.tthtm.previewWindowPosSize[3])

	def mouseUp(self, event):
		cnt = self.wPreview.view.scrollView._getContentView().contentView()
		#print cnt.frame(), cnt.bounds()
		pos = self.wPreview.getNSWindow().contentView().convertPoint_toView_(event.locationInWindow(), cnt)
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

	def closePreview(self):
		self.wPreview.close()

	def previewWindowWillClose(self, sender):
		self.tthtm.previewWindowOpened = 0
		self.tthtm.previewWindowVisible = 0
		setExtensionDefault(defaultKeyPreviewWindowVisibility, self.tthtm.previewWindowVisible)

	def previewWindowMovedorResized(self, sender):
		self.tthtm.previewWindowPosSize = self.wPreview.getPosSize()
		self.wPreview.view.getNSView().setFrame_(((0, 0), (self.tthtm.previewWindowViewSize[0], self.tthtm.previewWindowPosSize[3]-90)))
		setExtensionDefault(defaultKeyPreviewWindowPosSize, self.tthtm.previewWindowPosSize)
		# self.viewSize = (self.tthtm.previewWindowViewSize[0], self.tthtm.previewWindowPosSize[3]-110)
		# self.view.setFrame_(((0, 0), self.viewSize))
		# self.view.setFrameOrigin_((0, 10*(self.viewSize[1]/2)))
		# self.view.setAutoresizingMask_(NSViewMinXMargin | NSViewMaxXMargin | NSViewMinYMargin | NSViewMaxYMargin)

	def previewEditTextCallback(self, sender):
		self.tthtm.setPreviewString(sender.get())
		self.TTHToolInstance.updatePartialFontIfNeeded()
		self.wPreview.view.getNSView().setNeedsDisplay_(True)

	def DisplayFromEditTextCallback(self, sender):
		try:
			size = int(sender.get())
		except:
			size = self.tthtm.previewFrom
		self.FromSize = self.TTHToolInstance.setPreviewSize(size)

	def DisplayToEditTextCallback(self, sender):
		try:
			size = int(sender.get())
		except:
			size = self.tthtm.previewTo
		self.ToSize = self.TTHToolInstance.setPreviewSize(size)

	def ApplyButtonCallback(self, sender):
		self.TTHToolInstance.changePreviewSize(self.FromSize, self.ToSize)
		self.wPreview.resize(self.tthtm.previewWindowPosSize[2]-1, self.tthtm.previewWindowPosSize[3]-1, animate=False)
		self.wPreview.resize(self.tthtm.previewWindowPosSize[2]+1, self.tthtm.previewWindowPosSize[3]+1, animate=False)
		self.wPreview.view.getNSView().setNeedsDisplay_(True)

class programWindow(object):
	def __init__(self, TTHToolInstance, tthtm):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm
		self.lock = False

		self.wProgram = FloatingWindow(getExtensionDefault(defaultKeyProgramWindowPosSize, fallback=self.tthtm.programWindowPosSize), "Program", minSize=(600, 80))
		self.wProgram.bind("close", self.programWindowWillClose)
		self.programList = []

		# sliderCell = SliderListCell(-8, 8)
		# sliderCell.setAllowsTickMarkValuesOnly_(True)
		# sliderCell.setNumberOfTickMarks_(17)


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
			{"title": "ppm2", "editable": False}
			]
		self.wProgram.programList = List((0, 0, -0, -0), self.programList, 
					columnDescriptions=columnDescriptions,
					enableDelete=False, 
					showColumnTitles=True,
					selectionCallback=self.selectionCallback,
					editCallback = self.editCallback)
		self.tthtm.programWindowOpened = 1
		self.wProgram.bind("close", self.programWindowWillClose)
		self.wProgram.bind("move", self.programWindowMovedorResized)
		self.wProgram.bind("resize", self.programWindowMovedorResized)
		self.wProgram.open()

	def closeProgram(self):
		self.wProgram.close()

	def programWindowWillClose(self, sender):
		self.tthtm.programWindowOpened = 0
		self.tthtm.programWindowVisible = 0
		setExtensionDefault(defaultKeyProgramWindowVisibility, self.tthtm.programWindowVisible)

	def programWindowMovedorResized(self, sender):
		self.tthtm.programWindowPosSize = self.wProgram.getPosSize()
		setExtensionDefault(defaultKeyProgramWindowPosSize, self.tthtm.programWindowPosSize)

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
		keys = ['code', 'point', 'point1', 'point2', 'align', 'round', 'stem', 'zone', 'ppm1', 'ppm2']
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
			for key in ['index', 'code', 'point', 'point1', 'point2', 'align', 'round', 'stem', 'zone', 'delta', 'ppm1', 'ppm2', 'active']:
				putIfNotThere(command, key)
		self.wProgram.programList.set(self.commands)

class assemblyWindow(object):
	def __init__(self, TTHToolInstance, tthtm):
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm

		self.assemblyList = []

		self.wAssembly = FloatingWindow(getExtensionDefault(defaultKeyAssemblyWindowPosSize, fallback=self.tthtm.assemblyWindowPosSize), "Assembly", minSize=(150, 100))
		self.wAssembly.assemblyList = List((0, 0, -0, -0), self.assemblyList)

		self.wAssembly.bind("close", self.assemblyWindowWillClose)
		self.tthtm.assemblyWindowOpened = 1
		self.wAssembly.bind("close", self.assemblyWindowWillClose)
		self.wAssembly.bind("move", self.assemblyWindowMovedorResized)
		self.wAssembly.bind("resize", self.assemblyWindowMovedorResized)
		self.wAssembly.open()

	def closeAssembly(self):
		self.wAssembly.close()

	def assemblyWindowWillClose(self, sender):
		self.tthtm.assemblyWindowOpened = 0
		self.tthtm.assemblyWindowVisible = 0
		setExtensionDefault(defaultKeyAssemblyWindowVisibility, self.tthtm.assemblyWindowVisible)

	def assemblyWindowMovedorResized(self, sender):
		self.tthtm.assemblyWindowPosSize = self.wAssembly.getPosSize()
		setExtensionDefault(defaultKeyAssemblyWindowPosSize, self.tthtm.assemblyWindowPosSize)

	def updateAssemblyList(self, assembly):
		self.wAssembly.assemblyList.set(assembly)

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
		self.autohinting.autohint(g)
		self.controller.updateGlyphProgram(g)
		if self.model.alwaysRefresh == 1:
			self.controller.refreshGlyph(g)
		g.performUndo()

	def autoHintFontCallBack(self, sender):
		self.w.bar.show(1)
		self.w.bar.set(0)
		increment = 100.0/len(self.c_fontModel.f)
		for g in self.c_fontModel.f:
			g.prepareUndo("Auto-hint Glyph")
			self.autohinting.autohint(g)
			self.controller.updateGlyphProgram(g)
			g.performUndo()
			self.w.bar.increment(increment)
		self.w.bar.show(0)
		self.controller.resetFont()


reload(CV)
