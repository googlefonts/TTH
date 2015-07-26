#coding=utf-8
from defconAppKit.windows.baseWindow import BaseWindowController
from lib.tools.defaults import getDefault, setDefault
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

		self.loadedUFOs = {}

		panelSize = 600, 500
		ps = 0, 0, panelSize[0], panelSize[1]
		win = FloatingWindow(ps, "Compare Fonts", minSize=(350, 200))

		win.previewEditText = ComboBox((10, 10, -130, 22), tthTool.previewSampleStringsList,
			callback=self.previewEditTextCallback)
		win.previewEditText.set(tthTool.previewString)
		win.loadUFOButton = Button((-120, 10, 90, 22), 'Load UFOs', callback=self.loadUFOButtonCallback)
		win.buttonrefreshUFOs = Button((-20, 10, 10, 10), u"↺", callback=self.buttonRefreshUFOsCallback)
		win.buttonrefreshUFOs.getNSButton().setBordered_(False)

		columnDescriptions = (sorted([{'tail':k} for k in self.loadedUFOs]))

		win.UFOsList = List((10, 40, -10, 70), 
						columnDescriptions, 
						allowsMultipleSelection=False,
						showColumnTitles=False,
						columnDescriptions=[{'title':'tail', 'width':600}],
						enableDelete=False,
						allowsEmptySelection=False,
						selectionCallback=self.UFOSelectedCallBack
						)

		win.view = Canvas((10, 110, -10, -10), delegate = self, canvasSize = self.calculateCanvasSize(ps))
		win.bind("move", self.movedOrResizedCallback)
		win.bind("resize", self.movedOrResizedCallback)
		win.bind("close", self.closedCallback)

		self.w = win

		win.open()

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
		return (winPosSize[2], winPosSize[3]-120)

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


	def previewEditTextCallback(self, sender):
		if sender.get() != None:
			tthTool.previewString = sender.get()
		else:
			tthTool.previewString = '/?'
		self.w.previewEditText.set(tthTool.previewString)


		if self.loadedUFOs == {}: return

		for tail, (path, fm, requiredGlyphs) in self.loadedUFOs.iteritems():
			tr = fm.textRenderer
			if not tr: continue
			if not tr.isOK(): continue
			glyph = fm.f['space']
			(namedGlyphList, curGlyphName) = tthTool.prepareText(glyph, fm.f)
			glyphs = tr.names_to_indices(namedGlyphList)
			for g in namedGlyphList:
				gm = fm.glyphModelForGlyph(fm.f[g])
				requiredGlyphs = fm.updatePartialFontIfNeeded(gm.RFGlyph, requiredGlyphs)

		self.setNeedsDisplay()

	def draw(self):
		if self.loadedUFOs == {}: return
		fm = self.loadedUFOs[self.w.UFOsList[self.w.UFOsList.getSelection()[0]]['tail']][1]
		if fm == None: return
		tr = fm.textRenderer
		if not tr: return
		if not tr.isOK(): return
		glyph = fm.f['space']
		(namedGlyphList, curGlyphName) = tthTool.prepareText(glyph, fm.f)
		glyphs = tr.names_to_indices(namedGlyphList)
		# render user string
		tr.set_cur_size(20)#tthTool.PPM_Size)
		ps = self.w.getPosSize()
		tr.set_pen((20, ps[3] - 220))
		tr.render_indexed_glyph_list(glyphs)



