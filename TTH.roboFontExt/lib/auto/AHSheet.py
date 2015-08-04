#coding=utf-8
from vanilla import Box, Button, CheckBox, Group, EditText, ProgressBar, Sheet, TextBox, Slider, RadioGroup
import auto
from models.TTHTool import uniqueInstance as tthTool
from models import TTHGlyph
from auto import hint
reload(hint)

class AutoHintingSheet(object):
	def __init__(self, parentWindow):
		fm = tthTool.getFontModel()
		yBounds, xBounds = fm.stemSizeBounds

		sheetWidth  = 320
		sheetHeight = 400
		sheetSize = (sheetWidth, sheetHeight)

		self.w = Sheet(sheetSize, minSize=sheetSize, maxSize=sheetSize, parentWindow=parentWindow)
		w = self.w

		w.boxMethod = Box((10, 10, 210, 100), title='Method')
		w.boxMethod.methodRadioGroup = RadioGroup((10, 10,-10, -10), ['Preserve Proportions', 'Preserve Advance Width', 'Scan'], sizeStyle='small')
		w.boxMethod.methodRadioGroup.set(0)

		w.boxHintingAxis = Box((230, 10, 80, 100), title='Hint Axis')
		w.boxHintingAxis.hintXBox = CheckBox((10, 10, 50, 22), 'X', sizeStyle = 'small', value=True)
		w.boxHintingAxis.hintYBox = CheckBox((10, 30, 50, 22), 'Y', sizeStyle = 'small', value=True)

		w.boxStemDetection = Box((10, 120, -10, 150), title='Stems Detection')
		w.boxStemDetection.xGroup = Group((0, 0, -0, 27))
		w.boxStemDetection.xGroup.minW    = EditText((10, 10, 40, 17), text=str(xBounds[0]), sizeStyle = 'small', continuous=False, callback=self.handleStemBounds)
		w.boxStemDetection.xGroup.stemLabel = TextBox((50, 12 ,-50, 17), u'≤ X Stems ≤', sizeStyle = 'small', alignment='center')
		w.boxStemDetection.xGroup.maxW    = EditText((-50, 10, 40, 17), text=str(xBounds[1]), sizeStyle = 'small', continuous=False, callback=self.handleStemBounds)
		w.boxStemDetection.yGroup = Group((0, 27, -0, 27))
		w.boxStemDetection.yGroup.minW    = EditText((10, 10, 40, 17), text=str(yBounds[0]), sizeStyle = 'small', continuous=False, callback=self.handleStemBounds)
		w.boxStemDetection.yGroup.stemLabel = TextBox((50, 12 ,-50, 17), u'≤ Y Stems ≤', sizeStyle = 'small', alignment='center')
		w.boxStemDetection.yGroup.maxW    = EditText((-50, 10, 40, 17), text=str(yBounds[1]), sizeStyle = 'small', continuous=False, callback=self.handleStemBounds)
		w.boxStemDetection.tolLabel = TextBox((10, 72, 110, 20), u'Angle Tolerance (°)', sizeStyle = 'small', alignment='left')
		w.boxStemDetection.tolerance = EditText((-50, 70, 40, 17), text=str(fm.angleTolerance), sizeStyle = 'small', continuous=False, callback=self.handleTolerance)
		w.boxStemDetection.toleranceSlider = Slider((10, -45, -10, 20 ), sizeStyle='small', minValue=0, maxValue=45, value=fm.angleTolerance, tickMarkCount=46, stopOnTickMarks=True, callback=self.toleranceSliderCallback)
		w.boxStemDetection.groupLabel = TextBox((10, 112, 110, 20), u'Grouping Threshold', sizeStyle = 'small', alignment='left')
		w.boxStemDetection.groupingThreshold = EditText((-50, 110, 40, 17), text=str(fm.groupingThreshold), sizeStyle = 'small', continuous=False, callback=self.handleGroupingThreshold)

		w.boxAutoHint = Box((10, 280, -10, 70), title='Process')
		w.boxAutoHint.hintGlyphButton = Button((10, 5, -10, 20), "Glyph", sizeStyle='small', callback=self.hintGlyph)
		w.boxAutoHint.hintFontButton = Button((10, 30, -10, 20), "Font", sizeStyle='small', callback=self.hintFont)

		w.progressBar = ProgressBar((10, 350, -10, 20))
		w.progressBar.show(0)
		w.closeButton = Button((-90, -32, 80, 20), "Close", sizeStyle='small', callback=self.closeCallback)

		w.open()

	def resetUI(self):
		pass

	def close(self):
		self.w.close()
		tthTool.mainPanel.curSheet = None

	def closeCallback(self, sender):
		self.close()

	def AHMethod(self):
		m = self.w.boxMethod.methodRadioGroup.get()
		if m == 0: return hint.kTTHAutoHintMethod_PreserveProportion
		if m == 1: return hint.kTTHAutoHintMethod_PreserveAdvanceWidth
		if m == 2: return hint.kTTHAutoHintMethod_Scan
		return hint.kTTHAutoHintMethod_PreserveProportion

	def hintGlyph(self, sender):
		gm, fm = tthTool.getGlyphAndFontModel()
		# the undo does not work here, why ?
		doX = self.w.boxHintingAxis.hintXBox.get()
		doY = self.w.boxHintingAxis.hintYBox.get()
		if not (doX or doY): return
		gm.prepareUndo('AutoHinting Glyph')
		hint.AutoHinting(fm).autohint(gm, doX, doY, self.AHMethod())
		tthTool.hintingProgramHasChanged(fm)
		gm.performUndo()

	def hintFont(self, sender):
		gm, fm = tthTool.getGlyphAndFontModel()
		# the undo does not work here, why ?
		doX = self.w.boxHintingAxis.hintXBox.get()
		doY = self.w.boxHintingAxis.hintYBox.get()
		if not (doX or doY): return
		fm.f.prepareUndo('AutoHinting Font')
		AH = hint.AutoHinting(fm)
		TTHGlyph.silent = True
		glyphsWithOnPointsWithNoName = []
		counter = 0
		maxCount = len(fm.f)
		progress = self.w.progressBar
		progress._nsObject.setMaxValue_(maxCount)
		progress.set(0)
		progress.show(1)
		method = self.AHMethod()
		for g in fm.f:
			hasG = fm.hasGlyphModelForGlyph(g)
			gm = fm.glyphModelForGlyph(g)
			noName, rx, ry = AH.autohint(gm, doX, doY, method)
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

	def handleGroupingThreshold(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 10
		value = max(0, min(100, abs(value)))
		fm = tthTool.getFontModel()
		fm.groupingThreshold = value

