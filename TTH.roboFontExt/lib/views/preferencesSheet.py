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

		self.w.viewAndSettingsBox.bitmapOpacityTextBox = TextBox((10, 12, 100, 18), 'Bitmap Opacity:', sizeStyle='small')
		self.w.viewAndSettingsBox.bitmapOpacitySlider = Slider((110, 10, -10, 18), minValue=0, maxValue=1, value=self.TTHToolModel.bitmapOpacity, callback=self.bitmapOpacitySliderCallBack, sizeStyle='small')

		self.w.viewAndSettingsBox.previewSampleStringsTextBox = TextBox((10, 30, -10, 18), 'Preview Samples:', sizeStyle='small')
		self.w.viewAndSettingsBox.previewSampleStringsList = List((10, 45, -10, 80), [{"PreviewString": v} for v in self.TTHToolModel.previewSampleStringsList], columnDescriptions=[{"title": "PreviewString", "width": 465, "editable": True}], showColumnTitles=False, editCallback=self.previewSampleStringsListEditCallBack)
		self.w.viewAndSettingsBox.addStringButton = SquareButton((10, 125, 22, 22), "+", sizeStyle = 'small', callback=self.addStringButtonCallback)
		self.w.viewAndSettingsBox.removeStringButton = SquareButton((32, 125, 22, 22), "-", sizeStyle = 'small', callback=self.removeStringButtonCallback)

		self.w.viewAndSettingsBox.displaySizesText = TextBox((10, 150, 120, 18), "Display Sizes From:", sizeStyle = "small")
		self.w.viewAndSettingsBox.displayFromEditText = EditText((130, 147, 30, 19), sizeStyle = "small", continuous=False, 
				callback=self.displayFromEditTextCallback)
		self.w.viewAndSettingsBox.displayFromEditText.set(self.TTHToolModel.previewFrom)

		self.w.viewAndSettingsBox.displayToSizeText = TextBox((170, 150, 22, -10), "To:", sizeStyle = "small")
		self.w.viewAndSettingsBox.displayToEditText = EditText((202, 147, 30, 19), sizeStyle = "small", continuous=False, 
				callback=self.displayToEditTextCallback)
		self.w.viewAndSettingsBox.displayToEditText.set(self.TTHToolModel.previewTo)

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
		self.w.viewAndSettingsBox.previewSampleStringsList.setSelection([len(self.TTHToolModel.previewSampleStringsList)-1])

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
		self.applySizeChange()

	def displayToEditTextCallback(self, sender):
		try:
			size = int(sender.get())
		except:
			size = self.TTHToolModel.previewTo
		self.TTHToolModel.previewTo = helperFunctions.checkIntSize(size)
		self.applySizeChange()

	def applySizeChange(self):
		fromS = self.TTHToolModel.previewFrom
		toS = self.TTHToolModel.previewTo
		if fromS > toS:
			fromS = toS
		if toS > fromS + 100:
			toS = fromS + 100
		self.w.viewAndSettingsBox.displayFromEditText.set(fromS)
		self.w.viewAndSettingsBox.displayToEditText.set(toS)
		self.TTHToolController.changeDisplayPreviewSizesFromTo(fromS, toS)




