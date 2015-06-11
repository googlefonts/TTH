#coding=utf-8
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.roboFont import AllFonts
from vanilla import Box, Button, CheckBox, Group, EditText, FloatingWindow, PopUpButton, ProgressBar, TextBox, ImageButton
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
		panelSize = 320, 170
		ps = panelSize[0], panelSize[1]
		win = FloatingWindow(ps, "Auto-Match", minSize=panelSize, maxSize=panelSize)
		self.fontsNames = [displayName(f) for f in AllFonts()]
		self.fontsNames.sort()

		win.boxFonts = Box((10, 10, -10, 80), title='Fonts')

		imgRefresh = NSImage.imageNamed_(NSImageNameRefreshTemplate)
		imgRefresh.setSize_((10, 13))
		win.refreshFontsButton = ImageButton((-30, 5, 30, 18), imageObject=imgRefresh, bordered=False, callback=self.refreshFontsButtonCallback, sizeStyle="small")

		top = 10
		win.boxFonts.srcFontsLabel = TextBox((10, top+2, 85, 20), "Source: ", sizeStyle="small")
		win.boxFonts.srcFontsPopup = PopUpButton((95, top, -10, 20), self.fontsNames, sizeStyle="small", callback=self.updateUI)

		top = 30
		win.boxFonts.tgtFontsLabel = TextBox((10, top+2, 85, 20), "Target: ", sizeStyle="small")
		win.boxFonts.tgtFontsPopup = PopUpButton((95, top, -10, 20), self.fontsNames, sizeStyle="small", callback=self.updateUI)

		# top = 70
		# win.glyphLabel = TextBox((10,top+4,85,22), 'Glyph Name:', sizeStyle="small", alignment='left')
		# win.glyphName  = EditText((95,top,-10,22), text=gName, continuous=False, sizeStyle="small", callback=self.checkGlyphName)

		top = 105
		td = getExtensionDefault(defaultKeyDoTransferDelta, fallback=False)
		win.transferDeltaCheckBox = CheckBox((10, top, -10,20), 'Also transfer delta commands', None, td, sizeStyle="small")

		top = -50
		win.progressBar = ProgressBar((10,top,-10,20))
		win.progressBar.show(0)

		top = -30
		win.closeButton = Button((10, top, 70, 20), "Close", callback=self.close, sizeStyle="small")
		left = -190
		win.transferGlyphButton = Button((left, top, 110, 20), "Selected Glyphs", callback=self.transferGlyphs, sizeStyle="small")
		left += 120
		win.transferFontButton = Button((left, top, 60, 20), "Font", callback=self.transferFont, sizeStyle="small")

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
		self.window.transferGlyphButton.enable(diffFont)
		self.window.transferFontButton.enable(diffFont)

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

	def transferGlyphs(self, sender):
		sfm, tfm = self.getFontModels()
		if sfm is tfm: return
		td = self.window.transferDeltaCheckBox.get()
		self.window.progressBar.set(0)
		self.window.progressBar.show(1)
		gNamesList = []
		for g in CurrentFont():
			if g.selected:
				gNamesList.append(g.name)
		if gNamesList == []: return
		inc = 100/len(gNamesList)
		for gName in gNamesList:
			if (gName in sfm.f) and (gName in tfm.f):
				sg = sfm.f[gName]
				tg = tfm.f[gName]
				matching.transfertHintsBetweenTwoGlyphs(sfm, sg, tfm, tg, td)
				tfm.f[gName].mark = (1, .5, 0, .5)
				self.window.progressBar.increment(inc)
		self.window.progressBar.show(0)
		tthTool.hintingProgramHasChanged(tfm)

	def transferFont(self, sender):
		sfm, tfm = self.getFontModels()
		if sfm is tfm: return
		td = self.window.transferDeltaCheckBox.get()
		self.window.progressBar._nsObject.setMaxValue_(len(sfm.f))
		self.window.progressBar.set(0)
		self.window.progressBar.show(1)
		matching.transferHintsBetweenTwoFonts(sfm, tfm, td, self.window.progressBar)
		self.window.progressBar.show(0)
		tthTool.hintingProgramHasChanged(tfm)

	def refreshFontsButtonCallback(self, sender):
		self.fontsNames = [displayName(f) for f in AllFonts()]
		self.fontsNames.sort()
		self.updatePopUps()
		self.updateUI(None)
