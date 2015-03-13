from vanilla import *
from mojo.UI import *
from mojo.extensions import *
import string

from commons import helperFunctions

reload(helperFunctions)

class PreferencesSheet(object):

	def __init__(self, parentWindow, TTHToolController):
		self.TTHToolController = TTHToolController
		self.c_fontModel = self.TTHToolController.c_fontModel
		self.TTHToolModel = self.TTHToolController.TTHToolModel

		self.w = Sheet((505, 350), parentWindow=parentWindow)

		self.w.viewAndSettingsBox = Box((10, 19, -10, -40))

		self.w.autohintingBox = Box((10, 19, -10, -40))

		self.w.hotKeysBox = Box((10, 19, -10, -40))

		preferencesSegmentDescriptions = [
			dict(width=67, title="View", toolTip="View"),
			dict(width=67, title="Auto-hinting", toolTip="Auto-hinting"),
			dict(width=67, title="Hot Keys", toolTip="Hot Keys")
		]

		self.w.controlsSegmentedButton = SegmentedButton((147, 10, 220, 18), preferencesSegmentDescriptions, callback=self.preferencesSegmentedButtonCallback, sizeStyle="mini")
		self.w.controlsSegmentedButton.set(0)

		self.w.viewAndSettingsBox.show(True)
		self.w.autohintingBox.show(False)
		self.w.hotKeysBox.show(False)

		self.w.viewAndSettingsBox.displayBitmapCheckBox = CheckBox((10, 10, 18, 18), "", callback=self.displayBitmapCheckBoxCallback, value=self.TTHToolModel.showBitmap, sizeStyle="small")
		self.w.viewAndSettingsBox.displayBitmapTextBox = TextBox((30, 12, 80, 18), 'Show Bitmap', sizeStyle='small')
		self.w.viewAndSettingsBox.bitmapOpacityTextBox = TextBox((158, 12, 60, 18), 'Opacity', sizeStyle='small')
		self.w.viewAndSettingsBox.bitmapOpacitySlider = Slider((230, 10, -10, 18), minValue=0, maxValue=1, value=self.TTHToolModel.bitmapOpacity, callback=self.bitmapOpacitySliderCallBack, sizeStyle='small')

		self.w.viewAndSettingsBox.displayHintedOutlineCheckBox = CheckBox((10, 30, 18, 18), "", callback=self.displayHintedOutlineCheckBoxCallback, value=self.TTHToolModel.showOutline, sizeStyle="small")
		self.w.viewAndSettingsBox.displayHintedOutlineTextBox = TextBox((30, 32, 120, 18), 'Show Hinted Outline', sizeStyle='small')
		self.w.viewAndSettingsBox.outlineThicknessTextBox = TextBox((158, 32, 60, 18), 'Thickness', sizeStyle='small')
		self.w.viewAndSettingsBox.outlineThicknessSlider = Slider((230, 30, -10, 18), minValue=0.1, maxValue=8, value=self.TTHToolModel.outlineThickness, callback=self.outlineThicknessSliderCallBack, sizeStyle='small')

		self.w.viewAndSettingsBox.displayGridCheckBox = CheckBox((10, 50, 18, 18), "", callback=self.displayGridCheckBoxCallback, value=self.TTHToolModel.showGrid, sizeStyle="small")
		self.w.viewAndSettingsBox.displayGridTextBox = TextBox((30, 52, 120, 18), 'Show Pixel Grid', sizeStyle='small')
		self.w.viewAndSettingsBox.gridOpacityTextBox = TextBox((158, 52, 60, 18), 'Opacity', sizeStyle='small')
		self.w.viewAndSettingsBox.gridOpacitySlider = Slider((230, 50, -10, 18), minValue=0, maxValue=1, value=self.TTHToolModel.gridOpacity, callback=self.gridOpacitySliderCallBack, sizeStyle='small')

		self.w.viewAndSettingsBox.displayPixelCentersCheckBox = CheckBox((10, 70, 18, 18), "", callback=self.displayPixelCentersCheckBoxCallback, value=self.TTHToolModel.showCenterPixel, sizeStyle="small")
		self.w.viewAndSettingsBox.displayPixelCentersTextBox = TextBox((30, 72, 120, 18), 'Show Pixel Centers', sizeStyle='small')
		self.w.viewAndSettingsBox.pixelCentersSizeTextBox = TextBox((158, 72, 60, 18), 'Size', sizeStyle='small')
		self.w.viewAndSettingsBox.pixelCentersSizeSlider = Slider((230, 70, -10, 18), minValue=1, maxValue=10, value=self.TTHToolModel.centerPixelSize, callback=self.pixelCentersSizeSliderCallBack, sizeStyle='small')

		self.w.viewAndSettingsBox.displayPreviewInGlyphWindowCheckBox = CheckBox((10, 90, 18, 18), "", callback=self.displayPreviewInGlyphWindowCheckBoxCallback, value=self.TTHToolModel.showPreviewInGlyphWindow, sizeStyle="small")
		self.w.viewAndSettingsBox.displayPreviewInGlyphWindowText = TextBox((30, 92, -10, 18), "Show Preview in Glyph Window", sizeStyle = "small")

		self.w.viewAndSettingsBox.displaySizesText = TextBox((10, 120, 200, 18), "Display Preview Sizes From:", sizeStyle = "small")
		self.w.viewAndSettingsBox.displayFromEditText = EditText((180, 117, 30, 19), sizeStyle = "small", continuous=False, 
				callback=self.displayFromEditTextCallback)
		self.w.viewAndSettingsBox.displayFromEditText.set(self.TTHToolModel.previewFrom)

		self.w.viewAndSettingsBox.displayToSizeText = TextBox((220, 120, 22, 18), "To:", sizeStyle = "small")
		self.w.viewAndSettingsBox.displayToEditText = EditText((252, 117, 30, 19), sizeStyle = "small", continuous=False, 
				callback=self.displayToEditTextCallback)
		self.w.viewAndSettingsBox.displayToEditText.set(self.TTHToolModel.previewTo)

		self.w.viewAndSettingsBox.previewSampleStringsTextBox = TextBox((10, 140, -10, 18), 'Preview Samples:', sizeStyle='small')
		self.w.viewAndSettingsBox.previewSampleStringsList = List((10, 155, -10, 80), [{"PreviewString": v} for v in self.TTHToolModel.previewSampleStringsList], columnDescriptions=[{"title": "PreviewString", "width": 465, "editable": True}], showColumnTitles=False, editCallback=self.previewSampleStringsListEditCallBack)
		self.w.viewAndSettingsBox.addStringButton = SquareButton((10, 235, 22, 22), "+", sizeStyle = 'small', callback=self.addStringButtonCallback)
		self.w.viewAndSettingsBox.removeStringButton = SquareButton((32, 235, 22, 22), "-", sizeStyle = 'small', callback=self.removeStringButtonCallback)

		self.w.closeButton = Button((-70, -32, 60, 22), "Close", sizeStyle = "small", callback=self.closeButtonCallback)
		self.w.open()

	###########
	# Callbacks
	###########

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

	def bitmapOpacitySliderCallBack(self, sender):
		self.TTHToolController.changeBitmapOpacity(sender.get())

	def previewSampleStringsListEditCallBack(self, sender):
		updatedSampleStrings = []
		for i in sender.get():
			for k, v in i.iteritems():
				updatedSampleStrings.append(v)
		self.TTHToolController.samplesStringsHaveChanged(updatedSampleStrings)

	def addStringButtonCallback(self, sender):
		updatedSampleStrings = self.TTHToolModel.previewSampleStringsList
		updatedSampleStrings.append('/?')
		self.w.viewAndSettingsBox.previewSampleStringsList.set([{"PreviewString": v} for v in updatedSampleStrings])
		self.TTHToolController.samplesStringsHaveChanged(updatedSampleStrings)
		event = self.TTHToolController.getCurrentEvent()
		tableview = self.w.viewAndSettingsBox.previewSampleStringsList.getNSTableView()
		tableview.editColumn_row_withEvent_select_(0, len(self.w.viewAndSettingsBox.previewSampleStringsList)-1, event, True)

	def removeStringButtonCallback(self, sender):
		selected = self.w.viewAndSettingsBox.previewSampleStringsList.getSelection()
		updatedSampleStrings = []
		for i, s in enumerate(self.TTHToolModel.previewSampleStringsList):
			if i not in selected:
				updatedSampleStrings.append(s)
		self.w.viewAndSettingsBox.previewSampleStringsList.set([{"PreviewString": v} for v in updatedSampleStrings])
		self.TTHToolController.samplesStringsHaveChanged(updatedSampleStrings)

	def displayFromEditTextCallback(self, sender):
		try:
			size = int(sender.get())
		except:
			size = self.TTHToolModel.previewFrom
		self.TTHToolModel.previewFrom = helperFunctions.checkIntSize(size)
		self.TTHToolController.applySizeChange()

	def displayToEditTextCallback(self, sender):
		try:
			size = int(sender.get())
		except:
			size = self.TTHToolModel.previewTo
		self.TTHToolModel.previewTo = helperFunctions.checkIntSize(size)
		self.TTHToolController.applySizeChange()

	def displayPreviewInGlyphWindowCheckBoxCallback(self, sender):
		self.TTHToolController.changePreviewInGlyphWindowState(sender.get())

	def displayBitmapCheckBoxCallback(self, sender):
		self.TTHToolController.changeShowBitmapState(sender.get())

	def displayHintedOutlineCheckBoxCallback(self, sender):
		self.TTHToolController.changeShowOutlineState(sender.get())

	def outlineThicknessSliderCallBack(self, sender):
		self.TTHToolController.changeOutlineThickness(sender.get())

	def displayGridCheckBoxCallback(self, sender):
		self.TTHToolController.changeShowGridState(sender.get())

	def gridOpacitySliderCallBack(self, sender):
		self.TTHToolController.changeGridOpacity(sender.get())

	def displayPixelCentersCheckBoxCallback(self, sender):
		self.TTHToolController.changeShowCenterPixelState(sender.get())

	def pixelCentersSizeSliderCallBack(self, sender):
		self.TTHToolController.changeCenterPixelSize(sender.get())




