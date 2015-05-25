#coding=utf-8
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.roboFont import AllFonts
from vanilla import Box, Button, CheckBox, Group, EditText, FloatingWindow, PopUpButton, ProgressBar, TextBox
from models.TTHTool import uniqueInstance as tthTool
from auto import matching

class TransferPanel(BaseWindowController):
	def __init__(self):
		super(TransferPanel, self).__init__()
		panelSize = 320, 170
		ps = 20, 20, panelSize[0], panelSize[1]
		win = FloatingWindow(ps, "Auto Transfer", minSize=panelSize, maxSize=panelSize)

		fontsNames = [f.info.postscriptFullName for f in AllFonts()]

		fontsNames.sort()
		top = 10
		win.srcFontsLabel = TextBox((10, top+2, 65, 20), "Source Font: ")
		win.srcFontsPopup = PopUpButton((130, top, -10, 20), fontsNames)

		top = 40
		win.tgtFontsLabel = TextBox((10, top+2, 65, 20), "Target Font: ")
		win.tgtFontsPopup = PopUpButton((130, top, -10, 20), fontsNames)

		gm = tthTool.getGlyphModel()
		gName = gm.RFGlyph.name

		top = 70
		win.glyphLabel = TextBox((10,top+2,60,22), 'GlyphName:', alignment='right')
		win.glyphName  = EditText((75,top,-10,22), text=gName, continuous=False, callback=self.checkGlyphName)

		top = -50
		win.progressBar = ProgressBar((5,top,-5,20))
		win.progressBar.show(0)

		top = -30
		win.closeButton = Button((10, top, 70, 20), "Close", callback=self.close)
		left = 100
		win.transferGlyphButton = Button((left, top, 60, 20), "Glyph", callback=self.transferGlyph)
		left += 70
		win.transferFontButton = Button((left, top, 60, 20), "Font", callback=self.transferFont)

		self.window = win
		win.open()

	def __del__(self):
		self.window = None

	def close(self, sender):
		self.window.close()

	def getFontModelForName(self, name):
		for f in AllFonts():
			if f.info.postscriptFullName == name:
				return tthTool.getFontModelForFont(f)
		#self.close(None)

	def checkGlyphName(self, sender):
		print self.window.srcFontsPopup.get()
		print self.window.tgtFontsPopup.get()
		sfm = self.getFontModelForName(self.window.srcFontsPopup.get())
		tfm = self.getFontModelForName(self.window.tgtFontsPopup.get())
		gName = self.window.glyphName.get()
		ok = (gName in sfm.f) and (gName in tfm.f)
		if not ok:
			print 'Glyph not found'

	def transferGlyph(self, sender):
		sfm = self.getFontModelForName(self.window.srcFontsPopup.get())
		tfm = self.getFontModelForName(self.window.tgtFontsPopup.get())
		gName = self.window.glyphName.get()
		sg = sfm.f[gName]
		tg = tfm.f[gName]
		matching.transfertHintsBetweenTwoGlyphs(sfm, sg, tfm, tg)

	def transferFont(self, sender):
		sfm = self.getFontModelForName(self.window.srcFontsPopup.get())
		tfm = self.getFontModelForName(self.window.tgtFontsPopup.get())
		matching.transfertHintsBetweenTwoGlyphs(sfm, sg, tfm, tg)
