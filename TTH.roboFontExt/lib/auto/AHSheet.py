#coding=utf-8
from vanilla import Box, Button, CheckBox, Group, EditText, ProgressBar, Sheet, TextBox
import auto
from models.TTHTool import uniqueInstance as tthTool
from models import TTHGlyph
from auto import hint

class AutoHintingSheet(object):
	def __init__(self, parentWindow):
		fm = tthTool.getFontModel()
		yBounds, xBounds = fm.stemSizeBounds

		sheetWidth  = 320
		sheetHeight = 170
		sheetSize = (sheetWidth, sheetHeight)

		self.w = Sheet(sheetSize, minSize=sheetSize, maxSize=sheetSize, parentWindow=parentWindow)
		w = self.w

		w.hintXBox = CheckBox((10,17,70,22), 'X Hinting:', value=True)
		w.xGroup = Group((10, 15, -10, 22))
		w.xGroup.minW    = EditText((100,0,40,22), text=str(xBounds[0]), continuous=False, callback=self.handleStemBounds)
		w.xGroup.stemLabel = TextBox((140,2,-40,22), '<= stem width <=', alignment='center')
		w.xGroup.maxW    = EditText((-40,0,40,22), text=str(xBounds[1]), continuous=False, callback=self.handleStemBounds)

		w.hintYBox = CheckBox((10,52,70,22), 'Y Hinting:', value=True)
		w.yGroup = Group((10, 50, -10, 22))
		w.yGroup.minW    = EditText((100,0,40,22), text=str(yBounds[0]), continuous=False, callback=self.handleStemBounds)
		w.yGroup.stemLabel = TextBox((140,2,-40,22), '<= stem width <=', alignment='center')
		w.yGroup.maxW    = EditText((-40,0,40,22), text=str(yBounds[1]), continuous=False, callback=self.handleStemBounds)

		w.tolLabel = TextBox((-160, 87, -60, 22), 'Angle Tolerance:', alignment='right')
		w.tolerance = EditText((-50, 85, 40, 22), text=str(fm.angleTolerance), continuous=False, callback=self.handleTolerance)

		bGroup = Group((10, 120, -10, -10))

		bGroup.progressBar = ProgressBar((5,-45,-5,20))
		bGroup.progressBar.show(0)
		bGroup.closeButton = Button((0,-22,50,20), "Close", sizeStyle='small', callback=self.close)
		bGroup.autoHintLabel = TextBox((-235,-20,100,20), 'Auto Hint:', alignment='right')
		bGroup.hintGlyphButton = Button((-125,-22,60,20), "Glyph", sizeStyle='small', callback=self.hintGlyph)
		bGroup.hintFontButton = Button((-60,-22,60,20), "Font", sizeStyle='small', callback=self.hintFont)

		setattr(w, 'bGroup', bGroup)
		w.open()

	def close(self, sender):
		self.w.close()
		tthTool.mainPanel.curSheet = None

	def hintGlyph(self, sender):
		gm, fm = tthTool.getGlyphAndFontModel()
		doX = self.w.hintXBox.get()
		doY = self.w.hintYBox.get()
		if not (doX or doY): return
		reload(hint)
		hint.AutoHinting(fm).autohint(gm, doX, doY)
		tthTool.hintingProgramHasChanged(fm)

	def hintFont(self, sender):
		gm, fm = tthTool.getGlyphAndFontModel()
		doX = self.w.hintXBox.get()
		doY = self.w.hintYBox.get()
		if not (doX or doY): return
		reload(hint)
		AH = hint.AutoHinting(fm)
		TTHGlyph.silent = True
		counter = 0
		maxCount = len(fm.f)
		progress = self.w.bGroup.progressBar
		progress._nsObject.setMaxValue_(maxCount)
		progress.set(0)
		progress.show(1)
		for g in fm.f:
			hasG = fm.hasGlyphModelForGlyph(g)
			gm = fm.glyphModelForGlyph(g)
			AH.autohint(gm, doX, doY)
			if not hasG: fm.delGlyphModelForGlyph(g)
			counter += 1
			if counter == 30:
				progress.increment(30)
				counter = 0
		progress.increment(counter)
		progress.show(0)
		TTHGlyph.silent = False
		tthTool.hintingProgramHasChanged(fm)

	def handleTolerance(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
		value = max(0, min(45, abs(value)))
		sender.set(value)
		fm = tthTool.getFontModel()
		fm.angleTolerance = value

	def handleStemBounds(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
		value = min(9999, abs(value))
		xg = self.w.xGroup
		yg = self.w.yGroup
		maxX = int(xg.maxW.get())
		minX = int(xg.minW.get())
		maxY = int(yg.maxW.get())
		minY = int(yg.minW.get())
		if sender is xg.minW:
			value = min(value, maxX)
			minX = value
		elif sender is xg.maxW:
			value = max(value, minX)
			maxX = value
		elif sender is yg.minW:
			value = min(value, maxY)
			minY = value
		elif sender is yg.maxW:
			value = max(value, minY)
			maxY = value
		sender.set(value)
		fm = tthTool.getFontModel()
		fm.stemSizeBounds = ((minY, maxY), (minX, maxX))
