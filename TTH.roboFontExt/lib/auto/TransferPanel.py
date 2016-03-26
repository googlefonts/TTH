#coding=utf-8
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.extensions import getExtensionDefault, setExtensionDefault
from vanilla import Box, Button, CheckBox, Group, EditText, FloatingWindow, PopUpButton, ProgressBar, TextBox, ImageButton, ComboBox
from mojo.roboFont import CurrentGlyph, CurrentFont, AllFonts
from AppKit import NSImage, NSImageNameRefreshTemplate
from models.TTHTool import uniqueInstance as tthTool, DefaultKeyStub
from auto import matching
reload(matching)

defaultKeyDoTransferDelta = DefaultKeyStub + "DoTransferDelta"

def displayName(f):
	return f.info.familyName+'-'+f.info.styleName

class TransferPanel(BaseWindowController):
	def __init__(self):
		super(TransferPanel, self).__init__()
		panelSize = 320, 260
		ps = panelSize[0], panelSize[1]
		win = FloatingWindow(ps, "Auto-Match", minSize=panelSize, maxSize=panelSize)
		self.fontsNames = [displayName(f) for f in AllFonts()]
		self.fontsNames.sort()
		self.sGlyphsNames = []
		self.tGlyphsNames = []

		td = getExtensionDefault(defaultKeyDoTransferDelta, fallback=False)
		win.transferDeltaCheckBox = CheckBox((10, 10, -10,20), 'Also transfer delta commands', None, td, sizeStyle="small")

		win.boxFonts = Box((10, 30, -10, 80), title='Fonts')

		imgRefresh = NSImage.imageNamed_(NSImageNameRefreshTemplate)
		imgRefresh.setSize_((10, 13))
		win.refreshFontsButton = ImageButton((-30, 5, 30, 18), imageObject=imgRefresh, bordered=False, callback=self.refreshFontsButtonCallback, sizeStyle="small")

		top = 10
		win.boxFonts.srcFontsLabel = TextBox((10, top+2, 85, 20), "Source: ", sizeStyle="small")
		win.boxFonts.srcFontsPopup = PopUpButton((95, top, -10, 20), self.fontsNames, sizeStyle="small", callback=self.updateUI)

		top = 30
		win.boxFonts.tgtFontsLabel = TextBox((10, top+2, 85, 20), "Target: ", sizeStyle="small")
		win.boxFonts.tgtFontsPopup = PopUpButton((95, top, -10, 20), self.fontsNames, sizeStyle="small", callback=self.updateUI)

		top = 120
		left = -190
		win.transferGlyphButton = Button((left, top, 110, 20), "Selected Glyphs", callback=self.transferGlyphs, sizeStyle="small")
		left += 120
		win.transferFontButton = Button((left, top, 60, 20), "Font", callback=self.transferFont, sizeStyle="small")

		# top = 70
		# win.glyphLabel = TextBox((10,top+4,85,22), 'Glyph Name:', sizeStyle="small", alignment='left')
		# win.glyphName  = EditText((95,top,-10,22), text=gName, continuous=False, sizeStyle="small", callback=self.checkGlyphName)


		win.boxGlyphs = Box((10, 140, -10, 80), title='Glyphs')
		top = 10
		win.boxGlyphs.srcGlyphsLabel = TextBox((10, top+2, 85, 20), "Source: ", sizeStyle="small")
		win.boxGlyphs.srcGlyphsComboBox = ComboBox((95, top, -10, 20), self.sGlyphsNames, sizeStyle="small")

		top = 30
		win.boxGlyphs.tgtGlyphsLabel = TextBox((10, top+2, 85, 20), "Target: ", sizeStyle="small")
		win.boxGlyphs.tgtGlyphsComboBox = ComboBox((95, top, -10, 20), self.tGlyphsNames, sizeStyle="small")

		top = 210
		

		top = -50
		win.progressBar = ProgressBar((10,top,-10,20))
		win.progressBar.show(0)

		top = -30
		win.closeButton = Button((10, top, 70, 20), "Close", callback=self.close, sizeStyle="small")
		
		win.transferBetweenGlyphButton = Button((-160, top, 150, 20), "Transfer Between Glyphs", callback=self.transferBetweenGlyph, sizeStyle="small")

		self.window = win

		self.updateUI(None)

		win.open()

	def __del__(self):
		self.window = None

	def close(self, sender):
		if self.window:
			setExtensionDefault(defaultKeyDoTransferDelta, self.window.transferDeltaCheckBox.get())
			self.window.close()
			self.window = None

	def updateUI(self, sender):
		sfm, tfm = self.getFontModels()
		diffFont = (not (sfm is tfm)) and (sfm != None)
		self.sGlyphsNames = sorted([g.name for g in sfm.f])
		self.tGlyphsNames = sorted([g.name for g in tfm.f])
		self.window.boxGlyphs.srcGlyphsComboBox.setItems(self.sGlyphsNames)
		self.window.boxGlyphs.tgtGlyphsComboBox.setItems(self.tGlyphsNames)
		# diffGlyph = 
		self.window.transferGlyphButton.enable(diffFont)
		self.window.transferFontButton.enable(diffFont)
		# self.window.transferBetweenGlyphButton.enable(diffGlyph)

	def updatePopUps(self):
		self.window.boxFonts.srcFontsPopup.setItems(self.fontsNames)
		self.window.boxFonts.tgtFontsPopup.setItems(self.fontsNames)

	def getFontModelForName(self, name):
		for f in AllFonts():
			if displayName(f) == name:
				return tthTool.fontModelForFont(f)

	def getFontModels(self):
		if self.fontsNames == []:
			return None, None
		sfpsname = self.fontsNames[self.window.boxFonts.srcFontsPopup.get()]
		tfpsname = self.fontsNames[self.window.boxFonts.tgtFontsPopup.get()]
		sfm = self.getFontModelForName(sfpsname)
		tfm = self.getFontModelForName(tfpsname)
		return sfm, tfm

	def getGlyphModelsForNames(self, sgName, tgName):
		sfm, tfm = self.getFontModels()
		sg = sfm.f[sgName]
		tg = tfm.f[tgName]
		

	def transferGlyphs(self, sender):
		sfm, tfm = self.getFontModels()
		if sfm is tfm: return
		td = self.window.transferDeltaCheckBox.get()
		gNamesList = CurrentFont().selection
		if not gNamesList: return
		self.window.progressBar.set(0)
		self.window.progressBar._nsObject.setMaxValue_(len(gNamesList))
		self.window.progressBar.show(1)
		nInc = max(1, len(gNamesList)/25) # at most 25 increments of the progress bar
		count = 0
		for gName in gNamesList:
			if (gName in sfm.f) and (gName in tfm.f):
				sg = sfm.f[gName]
				tg = tfm.f[gName]
				matching.transfertHintsBetweenTwoGlyphs(sfm, sg, tfm, tg, td)
				tfm.f[gName].mark = (1, .5, 0, .5)
				count += 1
				if count == nInc:
					self.window.progressBar.increment(count)
					count = 0
		self.window.progressBar.increment(count)
		self.window.progressBar.show(0)
		self.window.progressBar.set(0)
		tthTool.hintingProgramHasChanged(tfm)

	def transferBetweenGlyph(self, sender):
		sfm, tfm = self.getFontModels()
		sgName = self.window.boxGlyphs.srcGlyphsComboBox.get()
		sg = None
		tg = None
		if sgName in sfm.f:
			sg = sfm.f[sgName]
		tgName = self.window.boxGlyphs.tgtGlyphsComboBox.get()
		if tgName in tfm.f:
			tg = tfm.f[tgName]
		if not (sg == tg) and (tg is not None) and (sg is not None):
			td = self.window.transferDeltaCheckBox.get()
			matching.transfertHintsBetweenTwoGlyphs(sfm, sg, tfm, tg, td)


	def transferFont(self, sender):
		sfm, tfm = self.getFontModels()
		if sfm is tfm: return
		td = self.window.transferDeltaCheckBox.get()
		self.window.progressBar._nsObject.setMaxValue_(len(sfm.f))
		self.window.progressBar.set(0)
		self.window.progressBar.show(1)
		matching.transferHintsBetweenTwoFonts(sfm, tfm, td, self.window.progressBar)
		self.window.progressBar.show(0)
		self.window.progressBar.set(0)
		tthTool.hintingProgramHasChanged(tfm)

	def refreshFontsButtonCallback(self, sender):
		self.fontsNames = [displayName(f) for f in AllFonts()]
		self.fontsNames.sort()
		self.updatePopUps()
		self.updateUI(None)
