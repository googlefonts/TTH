#coding=utf-8
from defconAppKit.windows.baseWindow import BaseWindowController
from lib.tools.defaults import getDefault, setDefault
from lib.UI.spaceCenter.glyphSequenceEditText import splitText
from mojo.extensions import *
from vanilla import *
from mojo.canvas import Canvas
from robofab.world import *

from views import TTHWindow
from models.TTHTool import uniqueInstance as tthTool

DefaultKeyStub = "com.sansplomb.TTH."
defaultKeyCompareFontsWindowPosSize = DefaultKeyStub + "compareFontsWindowPosSize"
defaultKeyCompareFontsWindowVisibility = DefaultKeyStub + "compareFontsWindowVisibility"


class CompareFontsWindow(BaseWindowController):
	def __init__(self):
		super(CompareFontsWindow, self).__init__()
		self.originalCurveDrawingPref = getDefault('drawingSegmentType')
		# and set quadratic mode
		if self.originalCurveDrawingPref != 'qcurve':
			setDefault('drawingSegmentType', 'qcurve')

		self.previewString = 'hamburgefontsiv'

		self.loadedUFOs = {}
		self.size1 = 9
		self.size2 = 9
		self.PPMSizesList = [str(i) for i in range(8, 73)]
		self.scale = 1
		self.scaleList = [str(i) for i in range(1, 10)]
		self.rasteriserMode = 'Monochrome'
		self.rModes = ['Monochrome', 'Grayscale', 'Subpixel']

		panelSize = 600, 500
		ps = 0, 0, panelSize[0], panelSize[1]
		win = FloatingWindow(ps, "Compare Fonts", minSize=(350, 200))

		win.previewEditText = ComboBox((10, 10, -130, 22), tthTool.previewSampleStringsList,
			callback=self.previewEditTextCallback)
		win.previewEditText.set(self.previewString)
		win.loadUFOButton = Button((-120, 10, 90, 22), 'Load UFOs', callback=self.loadUFOButtonCallback)
		win.buttonrefreshUFOs = Button((-20, 10, 10, 10), u"↺", callback=self.buttonRefreshUFOsCallback)
		win.buttonrefreshUFOs.getNSButton().setBordered_(False)

		columnDescriptions = (sorted([{'tail':k} for k in self.loadedUFOs]))

		win.UFOsList = List((30, 40, -10, 70), 
						columnDescriptions, 
						allowsMultipleSelection=False,
						showColumnTitles=False,
						columnDescriptions=[{'title':'tail', 'width':600}],
						enableDelete=False,
						allowsEmptySelection=False,
						selectionCallback=self.UFOSelectedCallBack
						)

		win.upButton = Button((10, 40, 10, 35), u'↑', sizeStyle = "small", callback = self.upButtonCallback)
		win.upButton.getNSButton().setBordered_(False)
		win.downButton = Button((10, 75, 10, 35), u'↓', sizeStyle = "small", callback = self.downButtonCallback)
		win.downButton.getNSButton().setBordered_(False)

		win.PPEMSize1ComboBox = ComboBox((10, 110, 40, 16),
				self.PPMSizesList, sizeStyle = "small",
				callback=self.PPEMSize1ComboBoxCallback)
		win.PPEMSize1ComboBox.set(str(self.size1))

		win.PPEMSize2ComboBox = ComboBox((60, 110, 40, 16),
				self.PPMSizesList, sizeStyle = "small",
				callback=self.PPEMSize2ComboBoxCallback)
		win.PPEMSize2ComboBox.set(str(self.size1))

		win.rasterizerModePopUpButton = PopUpButton((110, 110, 100, 16), self.rModes, sizeStyle = "small", callback=self.rasterizerModePopUpButtonCallback)
		win.scalePopUpButton = PopUpButton((220, 110, 40, 16), self.scaleList, sizeStyle = "small", callback=self.scalePopUpButtonCallback)

		win.view = Canvas((10, 130, -10, -10), delegate = self, canvasSize = self.calculateCanvasSize(ps))
		win.bind("move", self.movedOrResizedCallback)
		win.bind("resize", self.movedOrResizedCallback)
		win.bind("close", self.closedCallback)

		self.w = win

		win.open()

	def upButtonCallback(self, sender):
		if self.w.UFOsList.getSelection() == []: return
		sel = self.w.UFOsList.getSelection()[0]
		if sel == 0: return
		UFOsList = self.w.UFOsList.get()
		UFOsList[sel], UFOsList[sel-1] = UFOsList[sel-1], UFOsList[sel]
		self.w.UFOsList.set(UFOsList)


	def downButtonCallback(self, sender):
		if self.w.UFOsList.getSelection() == []: return
		sel = self.w.UFOsList.getSelection()[0]
		if sel == len(self.w.UFOsList.get())-1: return
		UFOsList = self.w.UFOsList.get()
		UFOsList[sel], UFOsList[sel+1] = UFOsList[sel+1], UFOsList[sel]
		self.w.UFOsList.set(UFOsList)

	def PPEMSize1ComboBoxCallback(self, sender):
		try:
			self.size1 = int(sender.get())
			if self.size1 > self.size2:
				self.size1 == self.size2
			sender.set(str(self.size1))
		except ValueError:
			self.size1 = 9
			if self.size1 > self.size2:
				self.size1 == self.size2
			sender.set(str(self.size1))
		self.setNeedsDisplay()

	def PPEMSize2ComboBoxCallback(self, sender):
		try:
			self.size2 = int(sender.get())
			if self.size2 < self.size1:
				self.size2 == self.size1
			sender.set(str(self.size2))
		except ValueError:
			self.size2 = 9
			if self.size2 < self.size1:
				self.size2 == self.size1
			sender.set(str(self.size2))
		self.setNeedsDisplay()

	def rasterizerModePopUpButtonCallback(self, sender):
		self.rasteriserMode = self.rModes[sender.get()]
		self.setNeedsDisplay()

	def scalePopUpButtonCallback(self, sender):
		self.scale = int(self.scaleList[sender.get()])
		self.setNeedsDisplay()

	def loadUFOButtonCallback(self, sender):
		self.loadedUFOs = {}
		self.showGetFile(['ufo'], callback=self.OpenUFOCallback,allowsMultipleSelection=True)


	def OpenUFOCallback(self, sender):
		for path in sender:
			if path is None:
				continue
			elif not path.endswith(".ufo"):
				continue
			else:
				UFO = RFont(path, showUI=False)
				head, tail = os.path.split(path)
				fm = tthTool.fontModelForFont(UFO)
				self.loadedUFOs[tail] = [path, fm, set(['space'])]
		self.w.UFOsList.set([{'tail':tail} for tail in self.loadedUFOs])

	def buttonRefreshUFOsCallback(self, sender):
		pathList = [path for tail, (path, fm, requiredGlyphs) in self.loadedUFOs.iteritems()]
		self.OpenUFOCallback(pathList)

	def calculateCanvasSize(self, winPosSize):
		return (winPosSize[2], winPosSize[3]-140)

	def movedOrResizedCallback(self, sender):
		self.resizeView(self.w.getPosSize())

	def closedCallback(self, sender):
		setDefault('drawingSegmentType', self.originalCurveDrawingPref)

	def resizeView(self, posSize):
		self.w.view.getNSView().setFrame_(((0, 0), self.calculateCanvasSize(posSize)))

	def setNeedsDisplay(self):
		self.w.view.getNSView().setNeedsDisplay_(True)

	def UFOSelectedCallBack(self, sender):
		self.setNeedsDisplay()

	def prepareText(self, font):
		text = self.previewString
		udata = font.naked().unicodeData
		output = []

		# replace /name pattern
		sp = text.split('/')
		nbsp = len(sp)
		output = output + splitText(sp[0], udata)
		for i in range(1,nbsp):
			sub = sp[i].split(' ', 1)
			output.append(str(sub[0]))
			if len(sub) > 1:
				output = output + splitText(sub[1], udata)
		return output


	def updatePartialFontIfNeeded(self, fm, curSet):
		"""Re-create the partial font if new glyphs are required."""
		text = self.prepareText(fm.f)
		newSet = fm.defineGlyphsForPartialTempFont(text, 'space')
		regenerate = not newSet.issubset(curSet)
		n = len(curSet)
		if (n > 128) and (len(newSet) < n):
			regenerate = True
		if regenerate:
			fm.updatePartialFont(newSet)
			return newSet
		return curSet


	def previewEditTextCallback(self, sender):
		if sender.get() != None:
			self.previewString = sender.get()
		else:
			self.previewString = '/?'
		self.w.previewEditText.set(self.previewString)


		if self.loadedUFOs == {}: return

		for tail, (path, fm, requiredGlyphs) in self.loadedUFOs.iteritems():
			tr = fm.textRenderer
			if not tr: continue
			if not tr.isOK(): continue
			namedGlyphList = self.prepareText(fm.f)
			glyphs = tr.names_to_indices(namedGlyphList)
			requiredGlyphs = self.updatePartialFontIfNeeded(fm, requiredGlyphs)

		self.setNeedsDisplay()

	def draw(self):
		if self.loadedUFOs == {}: return
		adv = 0
		height = (self.size1 + 10)*self.scale
		starty = 200 + height
		
		#fm = self.loadedUFOs[self.w.UFOsList[self.w.UFOsList.getSelection()[0]]['tail']][1]
		for tail in self.w.UFOsList:
			path, fm, requiredGlyphs = self.loadedUFOs[tail['tail']]
			if fm == None: return
			fm.bitmapPreviewMode = self.rasteriserMode
			tr = fm.textRenderer
			if not tr: return
			if not tr.isOK(): return
			namedGlyphList = self.prepareText(fm.f)
			glyphs = tr.names_to_indices(namedGlyphList)
			# render user string
			for size in range(self.size1-1, self.size2, 1):
				tr.set_cur_size(size)
				ps = self.w.getPosSize()
				tr.set_pen((adv + 20, ps[3] - starty - height))
				x, y = tr.render_indexed_glyph_list(glyphs, scale=self.scale)
				height += (size + 10)*self.scale
			adv += x + 10*self.scale
			height = (self.size1 + 10)*self.scale
			
			# if tail['tail'] != self.w.UFOsList[0]['tail']:
			# 	tr.set_pen((20, ps[3] - starty - height))
			# 	tr.render_indexed_glyph_list(glyphs, scale=self.scale)
			# 	height += (self.size + 10)*self.scale
				


