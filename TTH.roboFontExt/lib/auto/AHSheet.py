#coding=utf-8
from vanilla import Box, Button, CheckBox, Group, EditText, ProgressBar, Sheet, TextBox, Slider
import auto
from models.TTHTool import uniqueInstance as tthTool
from models import TTHGlyph
from auto import hint

class AutoHintingSheet(object):
	def __init__(self, parentWindow):
		fm = tthTool.getFontModel()
		yBounds, xBounds = fm.stemSizeBounds

		sheetWidth  = 320
		sheetHeight = 190
		sheetSize = (sheetWidth, sheetHeight)

		self.w = Sheet(sheetSize, minSize=sheetSize, maxSize=sheetSize, parentWindow=parentWindow)
		w = self.w

		w.boxHintingAxis = Box((230, 10, 80, 60), title='Hinting Axis')

		w.boxHintingAxis.hintXBox = CheckBox((10,10,50,22), 'X', sizeStyle = 'small', value=True)
		w.boxHintingAxis.hintYBox = CheckBox((-32,10,50,22), 'Y', sizeStyle = 'small', value=True)

		w.boxStemDetection = Box((10, 10, 210, 130), title='Stems Detection')

		w.boxStemDetection.xGroup = Group((0, 0, -0, 30))
		w.boxStemDetection.xGroup.minW    = EditText((10, 10, 40, 17), text=str(xBounds[0]), sizeStyle = 'small', continuous=False, callback=self.handleStemBounds)
		w.boxStemDetection.xGroup.stemLabel = TextBox((50, 12 ,-50, 17), u'≤ X Stems ≤', sizeStyle = 'small', alignment='center')
		w.boxStemDetection.xGroup.maxW    = EditText((-50, 10, 40, 17), text=str(xBounds[1]), sizeStyle = 'small', continuous=False, callback=self.handleStemBounds)

		w.boxStemDetection.yGroup = Group((0, 30, -0, 30))
		w.boxStemDetection.yGroup.minW    = EditText((10, 10, 40, 17), text=str(yBounds[0]), sizeStyle = 'small', continuous=False, callback=self.handleStemBounds)
		w.boxStemDetection.yGroup.stemLabel = TextBox((50, 12 ,-50, 17), u'≤ Y Stems ≤', sizeStyle = 'small', alignment='center')
		w.boxStemDetection.yGroup.maxW    = EditText((-50, 10, 40, 17), text=str(yBounds[1]), sizeStyle = 'small', continuous=False, callback=self.handleStemBounds)

		w.boxStemDetection.tolLabel = TextBox((10, 72, 110, 20), u'Angle Tolerance (°)', sizeStyle = 'small', alignment='left')
		w.boxStemDetection.tolerance = EditText((-50, 70, 40, 17), text=str(fm.angleTolerance), sizeStyle = 'small', continuous=False, callback=self.handleTolerance)
		w.boxStemDetection.toleranceSlider = Slider((10, -20, -10, 20 ), sizeStyle='small', minValue=0, maxValue=45, value=fm.angleTolerance, tickMarkCount=46, stopOnTickMarks=True, callback=self.toleranceSliderCallback)

		w.boxAutoHint = Box((230, 70, 80, 70), title='Process')
		w.boxAutoHint.hintGlyphButton = Button((10, 5, -10, 20), "Glyph", sizeStyle='small', callback=self.hintGlyph)
		w.boxAutoHint.hintFontButton = Button((10, 30, -10, 20), "Font", sizeStyle='small', callback=self.hintFont)

		w.progressBar = ProgressBar((10, 140, -10, 20))
		w.progressBar.show(0)
		w.closeButton = Button((-90, -32, 80, 20), "Close", sizeStyle='small', callback=self.closeCallback)

		w.open()

	def close(self):
		self.w.close()
		tthTool.mainPanel.curSheet = None

	def closeCallback(self, sender):
		self.close()

	def hintGlyph(self, sender):
		gm, fm = tthTool.getGlyphAndFontModel()
		# the undo does not work here, why ?
		gm.prepareUndo('AutoHinting Glyph')
		doX = self.w.boxHintingAxis.hintXBox.get()
		doY = self.w.boxHintingAxis.hintYBox.get()
		if not (doX or doY): return
		reload(hint)
		hint.AutoHinting(fm).autohint(gm, doX, doY)
		tthTool.hintingProgramHasChanged(fm)
		gm.performUndo()

	def hintFont(self, sender):
		gm, fm = tthTool.getGlyphAndFontModel()
		# the undo does not work here, why ?
		fm.f.prepareUndo('AutoHinting Font')
		doX = self.w.boxHintingAxis.hintXBox.get()
		doY = self.w.boxHintingAxis.hintYBox.get()
		if not (doX or doY): return
		reload(hint)
		AH = hint.AutoHinting(fm)
		TTHGlyph.silent = True
		glyphsWithOnPointsWithNoName = []
		counter = 0
		maxCount = len(fm.f)
		progress = self.w.progressBar
		progress._nsObject.setMaxValue_(maxCount)
		progress.set(0)
		progress.show(1)
		for g in fm.f:
			hasG = fm.hasGlyphModelForGlyph(g)
			gm = fm.glyphModelForGlyph(g)
			noName, rx, ry = AH.autohint(gm, doX, doY)
			if noName:
				glyphsWithOnPointsWithNoName.append(g.name)
			if not hasG: fm.delGlyphModelForGlyph(g)
			counter += 1
			if counter == 30:
				progress.increment(30)
				counter = 0
		progress.increment(counter)
		progress.show(0)
		TTHGlyph.silent = False
		tthTool.hintingProgramHasChanged(fm)
		fm.f.performUndo()
		if glyphsWithOnPointsWithNoName:
			print "The following glyphs have ON points that had no name!\n"+' '.join(glyphsWithOnPointsWithNoName)

	def toleranceSliderCallback(self, sender):
		value = int(sender.get())
		self.w.boxStemDetection.tolerance.set(value)
		fm = tthTool.getFontModel()
		fm.angleTolerance = value

	def handleTolerance(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
		value = max(0, min(45, abs(value)))
		self.w.boxStemDetection.toleranceSlider.set(value)
		fm = tthTool.getFontModel()
		fm.angleTolerance = value

	def handleStemBounds(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
		value = min(9999, abs(value))
		xg = self.w.boxStemDetection.xGroup
		yg = self.w.boxStemDetection.yGroup
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
