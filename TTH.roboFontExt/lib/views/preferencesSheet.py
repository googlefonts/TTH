from vanilla import *
from mojo.UI import *
from mojo.extensions import *
import string

DefaultKeyStub = "com.sansplomb.TTH."

defaultKeyPreviewSampleStrings = DefaultKeyStub + "previewSampleStrings"
defaultKeyBitmapOpacity = DefaultKeyStub + "bitmapOpacity"

class PreferencesSheet(object):

	def __init__(self, parentWindow, TTHToolController):
		self.TTHToolController = TTHToolController
		self.c_fontModel = self.TTHToolController.c_fontModel
		self.TTHToolModel = self.TTHToolController.TTHToolModel

		self.w = Sheet((505, 480), parentWindow=parentWindow)

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

		self.w.viewAndSettingsBox.bitmapOpacityTextBox = TextBox((10, 12, 80, 18), 'Bitmap Opacity:', sizeStyle='mini')
		self.w.viewAndSettingsBox.bitmapOpacitySlider = Slider((90, 10, -10, 18), minValue=0, maxValue=1, value=self.TTHToolModel.bitmapOpacity, callback=self.bitmapOpacitySliderCallBack, sizeStyle='mini')

		self.w.viewAndSettingsBox.previewSampleStringsTextBox = TextBox((10, 30, -10, 18), 'Preview Sample Strings:', sizeStyle='mini')
		self.w.viewAndSettingsBox.previewSampleStringsList = List((10, 45, -10, 80), [{"PreviewString": v} for v in self.TTHToolModel.previewSampleStringsList], columnDescriptions=[{"title": "PreviewString", "width": 465, "editable": True}], showColumnTitles=False, editCallback=self.previewSampleStringsListEditCallBack)
		self.w.viewAndSettingsBox.addStringButton = SquareButton((10, 125, 22, 22), "+", sizeStyle = 'small', callback=self.addStringButtonCallback)
		self.w.viewAndSettingsBox.removeStringButton = SquareButton((32, 125, 22, 22), "-", sizeStyle = 'small', callback=self.removeStringButtonCallback)

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
		self.TTHToolModel.bitmapOpacity = sender.get()
		setExtensionDefault(defaultKeyBitmapOpacity, self.TTHToolModel.bitmapOpacity)
		UpdateCurrentGlyphView()

	def previewSampleStringsListEditCallBack(self, sender):
		updatedSampleStrings = []
		for i in sender.get():
			for k, v in i.iteritems():
				updatedSampleStrings.append(v)
		self.TTHToolModel.previewSampleStringsList = updatedSampleStrings
		setExtensionDefault(defaultKeyPreviewSampleStrings, self.TTHToolModel.previewSampleStringsList)
		self.TTHToolController.previewPanel.win.previewEditText.setItems(self.TTHToolModel.previewSampleStringsList)

	def addStringButtonCallback(self, sender):
		self.TTHToolModel.previewSampleStringsList.append('/?')
		self.w.viewAndSettingsBox.previewSampleStringsList.set([{"PreviewString": v} for v in self.TTHToolModel.previewSampleStringsList])
		setExtensionDefault(defaultKeyPreviewSampleStrings, self.TTHToolModel.previewSampleStringsList)
		self.TTHToolController.previewPanel.win.previewEditText.setItems(self.TTHToolModel.previewSampleStringsList)
		self.w.viewAndSettingsBox.previewSampleStringsList.setSelection([len(self.TTHToolModel.previewSampleStringsList)-1])

	def removeStringButtonCallback(self, sender):
		selected = self.w.viewAndSettingsBox.previewSampleStringsList.getSelection()
		updatedSampleString = []
		for i, s in enumerate(self.TTHToolModel.previewSampleStringsList):
			if i not in selected:
				updatedSampleString.append(s)
		self.TTHToolModel.previewSampleStringsList = updatedSampleString
		self.w.viewAndSettingsBox.previewSampleStringsList.set([{"PreviewString": v} for v in self.TTHToolModel.previewSampleStringsList])
		setExtensionDefault(defaultKeyPreviewSampleStrings, self.TTHToolModel.previewSampleStringsList)
		self.TTHToolController.previewPanel.win.previewEditText.setItems(self.TTHToolModel.previewSampleStringsList)



