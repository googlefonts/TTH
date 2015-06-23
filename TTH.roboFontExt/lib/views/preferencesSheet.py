from vanilla import *
from mojo.UI import *
#from mojo.extensions import *
from mojo.events import getActiveEventTool
import string

from commons import helperFunctions
from models.TTHTool import uniqueInstance as tthTool

#reload(helperFunctions)

class PreferencesSheet(object):

	def __init__(self, parentWindow):

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

		self.w.viewAndSettingsBox.displayBitmapCheckBox = CheckBox((10, 10, 18, 18), "", callback=self.displayBitmapCheckBoxCallback, value=tthTool.showBitmap, sizeStyle="small")
		self.w.viewAndSettingsBox.displayBitmapTextBox = TextBox((30, 12, 80, 18), 'Show Bitmap', sizeStyle='small')
		self.w.viewAndSettingsBox.bitmapOpacityTextBox = TextBox((158, 12, 60, 18), 'Opacity', sizeStyle='small')
		self.w.viewAndSettingsBox.bitmapOpacitySlider = Slider((230, 10, -10, 18), minValue=0, maxValue=1, value=tthTool.bitmapOpacity, callback=self.bitmapOpacitySliderCallBack, sizeStyle='small')

		self.w.viewAndSettingsBox.displayHintedOutlineCheckBox = CheckBox((10, 30, 18, 18), "", callback=self.displayHintedOutlineCheckBoxCallback, value=tthTool.showOutline, sizeStyle="small")
		self.w.viewAndSettingsBox.displayHintedOutlineTextBox = TextBox((30, 32, 120, 18), 'Show Hinted Outline', sizeStyle='small')
		self.w.viewAndSettingsBox.outlineThicknessTextBox = TextBox((158, 32, 60, 18), 'Thickness', sizeStyle='small')
		self.w.viewAndSettingsBox.outlineThicknessSlider = Slider((230, 30, -10, 18), minValue=0.1, maxValue=8, value=tthTool.outlineThickness, callback=self.outlineThicknessSliderCallBack, sizeStyle='small')

		self.w.viewAndSettingsBox.displayGridCheckBox = CheckBox((10, 50, 18, 18), "", callback=self.displayGridCheckBoxCallback, value=tthTool.showGrid, sizeStyle="small")
		self.w.viewAndSettingsBox.displayGridTextBox = TextBox((30, 52, 120, 18), 'Show Pixel Grid', sizeStyle='small')
		self.w.viewAndSettingsBox.gridOpacityTextBox = TextBox((158, 52, 60, 18), 'Opacity', sizeStyle='small')
		self.w.viewAndSettingsBox.gridOpacitySlider = Slider((230, 50, -10, 18), minValue=0, maxValue=1, value=tthTool.gridOpacity, callback=self.gridOpacitySliderCallBack, sizeStyle='small')

		self.w.viewAndSettingsBox.displayPixelCentersCheckBox = CheckBox((10, 70, 18, 18), "", callback=self.displayPixelCentersCheckBoxCallback, value=tthTool.showCenterPixel, sizeStyle="small")
		self.w.viewAndSettingsBox.displayPixelCentersTextBox = TextBox((30, 72, 120, 18), 'Show Pixel Centers', sizeStyle='small')
		self.w.viewAndSettingsBox.pixelCentersSizeTextBox = TextBox((158, 72, 60, 18), 'Size', sizeStyle='small')
		self.w.viewAndSettingsBox.pixelCentersSizeSlider = Slider((230, 70, -10, 18), minValue=1, maxValue=10, value=tthTool.centerPixelSize, callback=self.pixelCentersSizeSliderCallBack, sizeStyle='small')

		self.w.viewAndSettingsBox.displayPreviewInGlyphWindowCheckBox = CheckBox((10, 90, 18, 18), "", callback=self.displayPreviewInGlyphWindowCheckBoxCallback, value=tthTool.showPreviewInGlyphWindow, sizeStyle="small")
		self.w.viewAndSettingsBox.displayPreviewInGlyphWindowText = TextBox((30, 92, -10, 18), "Show Preview in Glyph Window", sizeStyle = "small")

		self.w.viewAndSettingsBox.displaySizesText = TextBox((10, 120, 200, 18), "Display Preview Sizes From:", sizeStyle = "small")
		self.w.viewAndSettingsBox.displayFromEditText = EditText((180, 117, 30, 19), sizeStyle = "small", continuous=False,
				callback=self.displayFromEditTextCallback)
		self.w.viewAndSettingsBox.displayFromEditText.set(tthTool.previewFrom)

		self.w.viewAndSettingsBox.displayToSizeText = TextBox((220, 120, 22, 18), "To:", sizeStyle = "small")
		self.w.viewAndSettingsBox.displayToEditText = EditText((252, 117, 30, 19), sizeStyle = "small", continuous=False,
				callback=self.displayToEditTextCallback)
		self.w.viewAndSettingsBox.displayToEditText.set(tthTool.previewTo)

		self.w.viewAndSettingsBox.previewSampleStringsTextBox = TextBox((10, 140, -10, 18), 'Preview Samples:', sizeStyle='small')
		self.w.viewAndSettingsBox.previewSampleStringsList = List((10, 155, -10, 80), [{"PreviewString": v} for v in tthTool.previewSampleStringsList], columnDescriptions=[{"title": "PreviewString", "width": 465, "editable": True}], showColumnTitles=False, editCallback=self.previewSampleStringsListEditCallBack)
		self.w.viewAndSettingsBox.addStringButton = SquareButton((10, 235, 22, 22), "+", sizeStyle = 'small', callback=self.addStringButtonCallback)
		self.w.viewAndSettingsBox.removeStringButton = SquareButton((32, 235, 22, 22), "-", sizeStyle = 'small', callback=self.removeStringButtonCallback)

		self.w.closeButton = Button((-70, -32, 60, 22), "Close", sizeStyle = "small", callback=self.closeButtonCallback)
		self.w.open()

	def resetUI(self):
		b = self.w.viewAndSettingsBox
		b.displayBitmapCheckBox.set(tthTool.showBitmap)
		b.bitmapOpacitySlider.set(tthTool.bitmapOpacity)
		b.displayHintedOutlineCheckBox.set(tthTool.showOutline)
		b.outlineThicknessSlider.set(tthTool.outlineThickness)
		b.displayGridCheckBox.set(tthTool.showGrid)
		b.gridOpacitySlider.set(tthTool.gridOpacity)
		b.displayPixelCentersCheckBox.set(tthTool.showCenterPixel)
		b.pixelCentersSizeSlider.set(tthTool.centerPixelSize)
		b.displayPreviewInGlyphWindowCheckBox.set(tthTool.showPreviewInGlyphWindow)
		b.displayFromEditText.set(tthTool.previewFrom)
		b.displayToEditText.set(tthTool.previewTo)

	###########
	# Callbacks
	###########

	def closeButtonCallback(self, sender):
		self.close()

	def close(self):
		self.w.close()
		tthTool.mainPanel.curSheet = None

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
		tthTool.setBitmapOpacity(sender.get())
		UpdateCurrentGlyphView()

	def previewSampleStringsListEditCallBack(self, sender):
		updatedSampleStrings = []
		for i in sender.get():
			for k, v in i.iteritems():
				updatedSampleStrings.append(v)
		tthTool.samplesStringsHaveChanged(updatedSampleStrings)

	def addStringButtonCallback(self, sender):
		updatedSampleStrings = tthTool.previewSampleStringsList
		updatedSampleStrings.append('/?')
		self.w.viewAndSettingsBox.previewSampleStringsList.set([{"PreviewString": v} for v in updatedSampleStrings])
		tthTool.samplesStringsHaveChanged(updatedSampleStrings)
		event = getActiveEventTool().getCurrentEvent()
		tableview = self.w.viewAndSettingsBox.previewSampleStringsList.getNSTableView()
		tableview.editColumn_row_withEvent_select_(0, len(self.w.viewAndSettingsBox.previewSampleStringsList)-1, event, True)

	def removeStringButtonCallback(self, sender):
		selected = self.w.viewAndSettingsBox.previewSampleStringsList.getSelection()
		updatedSampleStrings = []
		for i, s in enumerate(tthTool.previewSampleStringsList):
			if i not in selected:
				updatedSampleStrings.append(s)
		self.w.viewAndSettingsBox.previewSampleStringsList.set([{"PreviewString": v} for v in updatedSampleStrings])
		tthTool.samplesStringsHaveChanged(updatedSampleStrings)

	def displayFromEditTextCallback(self, sender):
		try:
			size = int(sender.get())
		except:
			size = tthTool.previewFrom
		tthTool.setPreviewSizeRange(size, tthTool.previewTo, self)

	def displayToEditTextCallback(self, sender):
		try:
			size = int(sender.get())
		except:
			size = tthTool.previewTo
		tthTool.setPreviewSizeRange(tthTool.previewFrom, size, self)

	def displayPreviewInGlyphWindowCheckBoxCallback(self, sender):
		tthTool.setPreviewInGlyphWindowState(sender.get())

	def displayBitmapCheckBoxCallback(self, sender):
		tthTool.setShowBitmap(sender.get())
		UpdateCurrentGlyphView()

	def displayHintedOutlineCheckBoxCallback(self, sender):
		tthTool.setShowOutline(sender.get())
		UpdateCurrentGlyphView()

	def outlineThicknessSliderCallBack(self, sender):
		tthTool.setOutlineThickness(sender.get())
		UpdateCurrentGlyphView()

	def displayGridCheckBoxCallback(self, sender):
		tthTool.setShowGrid(sender.get())
		UpdateCurrentGlyphView()

	def gridOpacitySliderCallBack(self, sender):
		tthTool.setGridOpacity(sender.get())
		UpdateCurrentGlyphView()

	def displayPixelCentersCheckBoxCallback(self, sender):
		tthTool.setShowCenterPixels(sender.get())
		UpdateCurrentGlyphView()

	def pixelCentersSizeSliderCallBack(self, sender):
		tthTool.setCenterPixelSize(sender.get())
		UpdateCurrentGlyphView()

