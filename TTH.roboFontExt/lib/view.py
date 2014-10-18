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

defaultKeyStub = "com.sansplomb.TTH."
defaultKeyToolsWindowPosSize = defaultKeyStub + "toolsWindowPosSize"
defaultKeyPreviewWindowPosSize = defaultKeyStub + "previewWindowPosSize"
defaultKeyProgramWindowPosSize = defaultKeyStub + "programWindowPosSize"
defaultKeyAssemblyWindowPosSize = defaultKeyStub + "assemblyWindowPosSize"

defaultKeyPreviewWindowVisibility = defaultKeyStub + "previewWindowVisibility"
defaultKeyProgramWindowVisibility = defaultKeyStub + "programWindowVisibility"
defaultKeyAssemblyWindowVisibility = defaultKeyStub + "assemblyWindowVisibility"

# class centralWindow(object):
# 	def __init__(self, TTHToolInstance):
# 		#self.screenArea = preview.ScreenArea.alloc().init()
# 		# print screenArea.frame()
# 		# screenArea.setFrameOrigin_((800, 800))
# 		# screenArea.setFrameSize_((800, 800))
# 		# screenArea.setNeedsDisplay_(True)
# 		# print screenArea.frame().origin

# 		self.TTHToolInstance = TTHToolInstance
# 		self.tthtm = TTHToolInstance.tthtm
# 		self.wCentral = FloatingWindow(self.tthtm.centralWindowPosSize, "Central", closable = False)

# 		self.PPMSizesList = [str(i) for i in range(9, 73)]

# 		self.BitmapPreviewList = ['Monochrome', 'Grayscale', 'Subpixel']

# 		self.panelsList = [u'…', 'Preview', 'Program', 'Assembly']

# 		self.wCentral.PPEMSizeText= TextBox((10, 12, 50, 15), "ppEm:", sizeStyle = "mini")
		
# 		self.wCentral.PPEMSizeEditText = EditText((60, 10, 30, 15), sizeStyle = "mini", 
# 				callback=self.PPEMSizeEditTextCallback)

# 		self.wCentral.PPEMSizeEditText.set(self.tthtm.PPM_Size)
		
# 		self.wCentral.PPEMSizePopUpButton = PopUpButton((100, 10, 40, 15),
# 				self.PPMSizesList, sizeStyle = "mini",
# 				callback=self.PPEMSizePopUpButtonCallback)

# 		self.wCentral.BitmapPreviewText= TextBox((10, 32, 50, 15), "Preview:", sizeStyle = "mini")
# 		self.wCentral.BitmapPreviewPopUpButton = PopUpButton((60, 30, 80, 15),
# 				self.BitmapPreviewList, sizeStyle = "mini",
# 				callback=self.BitmapPreviewPopUpButtonCallback)

		
# 		self.wCentral.PanelsText= TextBox((10, 52, 50, 15), "Panels:", sizeStyle = "mini")
# 		self.wCentral.PanelsPopButton = PopUpButton((60, 50, -10, 15), self.panelsList, sizeStyle = 'mini', 
# 				callback=self.PanelsPopButtonCallback)

# 		self.wCentral.AlwaysRefreshText = TextBox((10, -63, -10, 15), 'Always Refresh:', sizeStyle = 'mini')
# 		self.wCentral.AlwaysRefreshCheckBox = CheckBox((-20, -65, 15, 15), '',  sizeStyle = 'mini', callback = self.AlwaysRefreshCheckBoxCallback)
# 		self.wCentral.AlwaysRefreshCheckBox.set(1)
# 		self.wCentral.RefreshButton = Button((10, -45, -10, 15), "Refresh Glyph", sizeStyle = 'mini', 
# 				callback=self.RefreshGlyphButtonCallback)


# 		# self.wCentral.AssemblyShowButton = Button((10, -85, -10, 15), "Glyph Assembly", sizeStyle = 'mini', 
# 		# 		callback=self.AssemblyShowButtonCallback)

# 		# self.wCentral.ProgramShowButton = Button((10, -65, -10, 15), "Glyph Program", sizeStyle = 'mini', 
# 		# 		callback=self.ProgramShowButtonCallback)

# 		# self.wCentral.PreviewShowButton = Button((10, -45, -10, 15), "Preview Window", sizeStyle = 'mini', 
# 		# 		callback=self.PreviewShowButtonCallback)

# 		self.wCentral.ControlValuesButton = Button((10, -25, -10, 15), "Control Values", sizeStyle = 'mini', 
# 				callback=self.ControlValuesButtonCallback)

# 		self.wCentral.bind("move", self.centralWindowMovedorResized)
# 		self.wCentral.open()

# 	def closeCentral(self):
# 		self.wCentral.close()

# 	def centralWindowMovedorResized(self, sender):
# 		self.tthtm.centralWindowPosSize = self.wCentral.getPosSize()

# 	def PPEMSizeEditTextCallback(self, sender):
# 		self.TTHToolInstance.changeSize(sender.get())

# 	def PPEMSizePopUpButtonCallback(self, sender):
# 		if self.tthtm.g == None:
# 			return
# 		size = self.PPMSizesList[sender.get()]
# 		self.TTHToolInstance.changeSize(size)

# 	def BitmapPreviewPopUpButtonCallback(self, sender):
# 		self.TTHToolInstance.changeBitmapPreview(self.BitmapPreviewList[sender.get()])

# 	def PrintTTProgramButtonCallback(self, sender):
# 		FLTTProgram = self.TTHToolInstance.readGlyphFLTTProgram(self.tthtm.g)
# 		if not FLTTProgram:
# 			print 'There is no Program in this glyph'
# 			return
# 		for i in FLTTProgram:
# 			print i

# 	def PrintAssemblyButtonCallback(self, sender):
# 		glyphAssembly = ''
# 		if 'com.robofont.robohint.assembly' in self.tthtm.g.lib:
# 			glyphAssembly = self.tthtm.g.lib['com.robofont.robohint.assembly']
# 		if not glyphAssembly:
# 			print 'There is no Assembly in this glyph'
# 			return
# 		for i in glyphAssembly:
# 			print i

# 	def RefreshGlyphButtonCallback(self, sender):
# 		self.TTHToolInstance.refreshGlyph()
# 		self.TTHToolInstance.updateGlyphProgram()

# 	def AlwaysRefreshCheckBoxCallback(self, sender):
# 		self.TTHToolInstance.changeAlwaysRefresh(sender.get())

# 	def PanelsPopButtonCallback(self, sender):
# 		selection = sender.get()
# 		if selection == 1:
# 			self.PreviewShowButtonCallback(sender)
# 		if selection == 2:
# 			self.ProgramShowButtonCallback(sender)
# 		if selection == 3:
# 			self.AssemblyShowButtonCallback(sender)
# 		sender.set(0)


# 	def PreviewShowButtonCallback(self, sender):
# 		if self.tthtm.previewWindowOpened == 0:

# 			for i in string.lowercase:
# 				self.tthtm.requiredGlyphsForPartialTempFont.add(i)
# 			for i in string.uppercase:
# 				self.tthtm.requiredGlyphsForPartialTempFont.add(i)
# 			for i in ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'zero']:
# 				self.tthtm.requiredGlyphsForPartialTempFont.add(i)

# 			self.TTHToolInstance.updatePartialFont()
# 			self.TTHToolInstance.previewWindow = previewWindow(self.TTHToolInstance, self.tthtm)
# 			self.TTHToolInstance.previewWindow.wPreview.resize(self.tthtm.previewWindowPosSize[2]-1, self.tthtm.previewWindowPosSize[3]-1, animate=False)
# 			self.TTHToolInstance.previewWindow.wPreview.resize(self.tthtm.previewWindowPosSize[2]+1, self.tthtm.previewWindowPosSize[3]+1, animate=False)

# 	def ControlValuesButtonCallback(self, sender):
# 		sheet = CV.SheetControlValues(self, self.wCentral, self.tthtm, self.TTHToolInstance)

# 	def ProgramShowButtonCallback(self, sender):
# 		if self.tthtm.programWindowOpened == 0:
# 			self.TTHToolInstance.programWindow = programWindow(self.TTHToolInstance, self.tthtm)
# 			self.TTHToolInstance.resetglyph()

# 	def AssemblyShowButtonCallback(self, sender):
# 		if self.tthtm.assemblyWindowOpened == 0:
# 			self.TTHToolInstance.assemblyWindow = assemblyWindow(self.TTHToolInstance, self.tthtm)
# 			self.TTHToolInstance.resetglyph()

# 	def PanelsShowButtonCallback(self, sender):
# 		self.menuAction = NSMenu.alloc().init()
# 		items = []
# 		items.append(('Preview', self.PreviewShowButtonCallback))
# 		items.append(('Program', self.ProgramShowButtonCallback))
# 		items.append(('Assembly', self.AssemblyShowButtonCallback))
# 		menuController = BaseMenu()
# 		menuController.buildAdditionContectualMenuItems(self.menuAction, items)
# 		NSMenu.popUpContextMenu_withEvent_forView_(self.menuAction, self.TTHToolInstance.getCurrentEvent(), self.TTHToolInstance.getNSView())

class toolsWindow(BaseWindowController):
	def __init__(self, TTHToolInstance):
		BaseWindowController.__init__(self)
		self.TTHToolInstance = TTHToolInstance
		self.tthtm = TTHToolInstance.tthtm

		self.autohinting = Automation.AutoHinting(self.TTHToolInstance)

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
			dict(width=19, imageObject=buttonFinalDeltaPath, toolTip="Final Delta Tool")
		]

		self.wTools.PPEMSizeEditText = EditText((10, 14, 25, 15), sizeStyle = "mini", 
				callback=self.PPEMSizeEditTextCallback)
		self.wTools.PPEMSizeEditText.set(self.tthtm.PPM_Size)

		self.PPMSizesList = [str(i) for i in range(9, 73)]
		self.wTools.PPEMSizePopUpButton = PopUpButton((40, 14, 40, 15),
				self.PPMSizesList, sizeStyle = "mini",
				callback=self.PPEMSizePopUpButtonCallback)

		self.wTools.axisSegmentedButton = SegmentedButton((85, 12, 70, 18), axisSegmentDescriptions, callback=self.axisSegmentedButtonCallback, sizeStyle="regular")
		self.wTools.axisSegmentedButton.set(0)

		self.wTools.toolsSegmentedButton = SegmentedButton((-133, 12, 128, 18), toolsSegmentDescriptions, callback=self.toolsSegmentedButtonCallback, sizeStyle="regular")
		self.wTools.toolsSegmentedButton.set(0)

		self.wTools.AlignmentTypeText = TextBox((10, 42, 30, 15), "Align:", sizeStyle = "mini")
		self.wTools.AlignmentTypePopUpButton = PopUpButton((40, 40, 105, 15),
				self.alignmentTypeListDisplay, sizeStyle = "mini",
				callback=self.AlignmentTypePopUpButtonCallback)
		self.wTools.AlignmentTypeText.show(True)
		self.wTools.AlignmentTypePopUpButton.show(True)

		self.wTools.StemTypeText = TextBox((10, 59, 30, 15), "Stem:", sizeStyle = "mini")
		self.wTools.StemTypePopUpButton = PopUpButton((40, 57, 105, 15),
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
		self.wTools.DeltaOffsetSlider = Slider((10, 55, -10, 15), maxValue=16, value=8, tickMarkCount=17, continuous=False, stopOnTickMarks=True, sizeStyle= "small",
				callback=self.DeltaOffsetSliderCallback)
		self.wTools.DeltaOffsetEditText = EditText((60, 40, 30, 15), sizeStyle = "mini", 
				callback=self.DeltaOffsetEditTextCallback)
		self.wTools.DeltaOffsetText.show(False)
		self.wTools.DeltaOffsetSlider.show(False)
		self.wTools.DeltaOffsetEditText.set(self.tthtm.deltaOffset)
		self.wTools.DeltaOffsetEditText.show(False)

		self.wTools.DeltaRangeText = TextBox((100, 42, 40, 15), "Range:", sizeStyle = "mini")
		self.wTools.DeltaRange1EditText = EditText((-70, 40, 30, 15), sizeStyle = "mini", 
				callback=self.DeltaRange1EditTextCallback)
		self.wTools.DeltaRange2EditText = EditText((-40, 40, 30, 15), sizeStyle = "mini", 
				callback=self.DeltaRange2EditTextCallback)
		self.wTools.DeltaRangeText.show(False)
		self.wTools.DeltaRange1EditText.show(False)
		self.wTools.DeltaRange2EditText.show(False)
		self.wTools.DeltaRange1EditText.set(self.tthtm.deltaRange1)
		self.wTools.DeltaRange2EditText.set(self.tthtm.deltaRange2)

		# self.wTools.AutoGlyphButton = Button((10, -25, self.tthtm.toolsWindowPosSize[2]/2.0 -10, 15), "Auto-Glyph", sizeStyle = 'mini', 
		# 		callback=self.AutoGlyphButtonCallback)
		# self.wTools.AutoFontButton = Button((self.tthtm.toolsWindowPosSize[2]/2.0 +10, -25, -10, 15), "Auto-Font", sizeStyle = 'mini', 
		# 		callback=self.AutoFontButtonCallback)

		self.wTools.gear = PopUpButton((0, -22, 30, 18), [], callback=self.gearMenuCallback, sizeStyle="small")
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
			"Guess Glyph",
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
			self.TTHToolInstance.changeBitmapPreview("Monochrome")
		if gearOption == 2:
			self.TTHToolInstance.changeBitmapPreview("Grayscale")
		if gearOption == 3:
			self.TTHToolInstance.changeBitmapPreview("Subpixel")

		if gearOption == 5:
			self.showPreviewCallback()
			self.tthtm.previewWindowVisible = 1
			setExtensionDefault(defaultKeyPreviewWindowVisibility, self.tthtm.previewWindowVisible)
		if gearOption == 6:
			self.showProgramCallback()
		if gearOption == 7:
			self.showAssemblyCallback()

		if gearOption == 9:
			self.controlValuesCallback()

		if gearOption == 11:
			self.autoGlyphCallback()


	def controlValuesCallback(self):
		sheet = CV.SheetControlValues(self, self.wTools, self.tthtm, self.TTHToolInstance)


	def showPreviewCallback(self):
		if self.tthtm.previewWindowOpened == 0:
			for i in string.lowercase:
				self.tthtm.requiredGlyphsForPartialTempFont.add(i)
			for i in string.uppercase:
				self.tthtm.requiredGlyphsForPartialTempFont.add(i)
			for i in ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'zero']:
				self.tthtm.requiredGlyphsForPartialTempFont.add(i)

			self.TTHToolInstance.updatePartialFont()
			self.TTHToolInstance.previewWindow = previewWindow(self.TTHToolInstance, self.tthtm)
			self.TTHToolInstance.previewWindow.wPreview.resize(self.tthtm.previewWindowPosSize[2]-1, self.tthtm.previewWindowPosSize[3]-1, animate=False)
			self.TTHToolInstance.previewWindow.wPreview.resize(self.tthtm.previewWindowPosSize[2]+1, self.tthtm.previewWindowPosSize[3]+1, animate=False)

	def showProgramCallback(self):
		if self.tthtm.programWindowOpened == 0:
			self.TTHToolInstance.programWindow = programWindow(self.TTHToolInstance, self.tthtm)
			self.TTHToolInstance.resetglyph()

	def showAssemblyCallback(self):
		if self.tthtm.assemblyWindowOpened == 0:
			self.TTHToolInstance.assemblyWindow = assemblyWindow(self.TTHToolInstance, self.tthtm)
			self.TTHToolInstance.resetglyph()

	def autoGlyphCallback(self):
		self.tthtm.g.prepareUndo("Auto-hint Glyph")
		self.autohinting.autohint(self.tthtm.g)
		self.TTHToolInstance.updateGlyphProgram()
		if self.tthtm.alwaysRefresh == 1:
			self.TTHToolInstance.refreshGlyph()
		self.tthtm.g.performUndo()


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

	def PPEMSizeEditTextCallback(self, sender):
		self.TTHToolInstance.changeSize(sender.get())

	def PPEMSizePopUpButtonCallback(self, sender):
		if self.tthtm.g == None:
			return
		size = self.PPMSizesList[sender.get()]
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

	def DeltaRange1EditTextCallback(self, sender):
		self.TTHToolInstance.changeDeltaRange(sender.get(), self.tthtm.deltaRange2)

	def DeltaRange2EditTextCallback(self, sender):
		self.TTHToolInstance.changeDeltaRange(self.tthtm.deltaRange1, sender.get())


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

	def AutoFontButtonCallback(self, sender):
		progress = self.startProgress(u'Auto-hinting Font…')
		progress.setTickCount(len(self.tthtm.f))
		for g in self.tthtm.f:
			g.prepareUndo("Auto-hint Font")
			self.autohinting.autohint(g)
			self.TTHToolInstance.updateGlyphProgram()
			g.performUndo()
			progress.update()
		self.TTHToolInstance.resetFonts()
		progress.close()

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
		self.wPreview.previewEditText = EditText((10, 10, -10, 22),
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

		self.wProgram = FloatingWindow(getExtensionDefault(defaultKeyProgramWindowPosSize, fallback=self.tthtm.programWindowPosSize), "Program", minSize=(600, 80))
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


reload(CV)
