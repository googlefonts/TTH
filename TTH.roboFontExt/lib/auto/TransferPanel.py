#coding=utf-8
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.roboFont import AllFonts
from vanilla import Box, Button, CheckBox, Group, EditText, FloatingWindow, PopUpButton, ProgressBar, TextBox
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
		ps = 20, 20, panelSize[0], panelSize[1]
		win = FloatingWindow(ps, "Auto-Match", minSize=panelSize, maxSize=panelSize)
		self.fontsNames = [displayName(f) for f in AllFonts()]
		self.fontsNames.sort()

		top = 10
		win.srcFontsLabel = TextBox((10, top+2, 85, 20), "Source Font: ")
		win.srcFontsPopup = PopUpButton((95, top, -10, 20), self.fontsNames, callback=self.updateUI)

		top = 40
		win.tgtFontsLabel = TextBox((10, top+2, 85, 20), "Target Font: ")
		win.tgtFontsPopup = PopUpButton((95, top, -10, 20), self.fontsNames, callback=self.updateUI)

		gm = tthTool.getGlyphModel()
		gName = gm.RFGlyph.name

		top = 70
		win.glyphLabel = TextBox((10,top+4,85,22), 'Glyph Name:', alignment='left')
		win.glyphName  = EditText((95,top,-10,22), text=gName, continuous=False, callback=self.checkGlyphName)

		top = 105
		td = getExtensionDefault(defaultKeyDoTransferDelta, fallback=False)
		win.transferDeltaCheckBox = CheckBox((10, top, -10,20), 'Also transfer delta commands', None, td)

		top = -50
		win.progressBar = ProgressBar((5,top,-5,20))
		win.progressBar.show(0)

		top = -30
		win.closeButton = Button((10, top, 70, 20), "Close", callback=self.close)
		left = -140
		win.transferGlyphButton = Button((left, top, 60, 20), "Glyph", callback=self.transferGlyph)
		left += 70
		win.transferFontButton = Button((left, top, 60, 20), "Font", callback=self.transferFont)

		# imgRefresh = NSImage.imageNamed_(NSImageNameRefreshTemplate)
		# imgRefresh.setSize_((10, 13))
		#self.wTools.button = ImageButton((-30, -20, 30, 18), imageObject=imgRefresh, bordered=False, callback=self.refreshButtonCallback, sizeStyle="small")
		
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
		diffFont = not (sfm is tfm)
		gName = self.window.glyphName.get()
		okGlyph = (gName in sfm.f) and (gName in tfm.f)
		self.window.transferGlyphButton.enable(diffFont and okGlyph)
		self.window.transferFontButton.enable(diffFont)

	def getFontModelForName(self, name):
		for f in AllFonts():
			if displayName(f) == name:
				return tthTool.fontModelForFont(f)

	def getFontModels(self):
		sfpsname = self.fontsNames[self.window.srcFontsPopup.get()]
		tfpsname = self.fontsNames[self.window.tgtFontsPopup.get()]
		sfm = self.getFontModelForName(sfpsname)
		tfm = self.getFontModelForName(tfpsname)
		return sfm, tfm

	def checkGlyphName(self, sender):
		sfm, tfm = self.getFontModels()
		gName = self.window.glyphName.get()
		ok = (gName in sfm.f) and (gName in tfm.f)
		if not ok:
			print 'Glyph not found'

	def transferGlyph(self, sender):
		sfm, tfm = self.getFontModels()
		if sfm is tfm: return
		gName = self.window.glyphName.get()
		td = self.window.transferDeltaCheckBox.get()
		if (gName in sfm.f) and (gName in tfm.f):
			sg = sfm.f[gName]
			tg = tfm.f[gName]
			matching.transfertHintsBetweenTwoGlyphs(sfm, sg, tfm, tg, td)
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
