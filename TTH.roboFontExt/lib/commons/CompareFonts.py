#coding=utf-8
from defconAppKit.windows.baseWindow import BaseWindowController
from lib.tools.defaults import getDefault, setDefault
from lib.UI.spaceCenter.glyphSequenceEditText import splitText
from mojo.extensions import *
from vanilla import *
from mojo.canvas import Canvas
from robofab.world import *

from models import TTHFont
from commons import helperFunctions
from drawing import utilities as DR

DefaultKeyStub = "com.sansplomb.TTH."
defaultKeyCompareFontsWindowPosSize = DefaultKeyStub + "compareFontsWindowPosSize"
defaultKeyCompareFontsWindowVisibility = DefaultKeyStub + "compareFontsWindowVisibility"

class UFOdata(object):
	def __init__(self, path, fontModel):
		self.path = path
		self.fm = fontModel
		self.tail = os.path.split(path)[1]
		self.weight = self.fm.f.info.openTypeOS2WeightClass
		self.requiredGlyphs = set('space')

class CompareFontsWindow(BaseWindowController):
	def __init__(self):
		super(CompareFontsWindow, self).__init__()
		self.originalCurveDrawingPref = getDefault('drawingSegmentType')
		# and set quadratic mode
		if self.originalCurveDrawingPref != 'qcurve':
			setDefault('drawingSegmentType', 'qcurve')

		self.previewString = 'hamburgefontsiv'

		self.UFOList = []
		self.size1 = 9
		self.size2 = 9
		self.PPMSizesList = [str(i) for i in range(8, 73)]
		self.scale = 1
		self.scaleList = [str(i) for i in range(1, 10)]
		self.rasteriserMode = 'Monochrome'
		self.rModes = ['Monochrome', 'Grayscale', 'Subpixel']

		panelSize = 600, 500
		ps = 0, 0, panelSize[0], panelSize[1]
		win = Window(ps, "Compare Fonts", minSize=(350, 200))

		win.previewEditText = ComboBox((10, 10, -130, 22), [self.previewString],
			callback=self.previewEditTextCallback)
		win.previewEditText.set(self.previewString)
		win.loadUFOButton = Button((-120, 10, 90, 22), 'Load UFOs', callback=self.loadUFOButtonCallback)
		win.buttonrefreshUFOs = Button((-20, 10, 10, 10), u"↺", callback=self.buttonRefreshUFOsCallback)
		win.buttonrefreshUFOs.getNSButton().setBordered_(False)

		win.UIList = List((30, 40, -10, 70), 
						[], 
						allowsMultipleSelection=False,
						showColumnTitles=False,
						columnDescriptions=[{'title':'tail', 'width':600}],
						enableDelete=False
						)

		win.upButton = Button((10, 40, 10, 10), u'↑', sizeStyle = "small", callback = self.upButtonCallback)
		win.upButton.getNSButton().setBordered_(False)
		win.removeButton = Button((10, 65, 10, 10), u'-', sizeStyle = "small", callback = self.removeButtonCallback)
		win.removeButton.getNSButton().setBordered_(False)
		win.downButton = Button((10, 95, 10, 10), u'↓', sizeStyle = "small", callback = self.downButtonCallback)
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

		win.bind("move", self.movedOrResizedCallback)
		win.bind("resize", self.movedOrResizedCallback)
		win.bind("close", self.closedCallback)

		win.view = Canvas((10, 130, -10, -10), delegate = self, canvasSize = self.calculateCanvasSize(ps))

		self.w = win

		win.open()

	def upButtonCallback(self, sender):
		if self.w.UIList.getSelection() == []: return
		sel = self.w.UIList.getSelection()[0]
		if sel == 0: return
		UIList = self.w.UIList.get()
		UIList[sel], UIList[sel-1] = UIList[sel-1], UIList[sel]
		T = self.UFOList
		T[sel], T[sel-1] = T[sel-1], T[sel]
		self.w.UIList.set(UIList)
		self.setNeedsDisplay()

	def removeButtonCallback(self, sender):
		if len(self.w.UIList.getSelection()) == 1:
			self.UFOList.pop(self.w.UIList.getSelection()[0])
			self.w.UIList.setSelection([])
			self.w.UIList.set([{'tail':x.tail} for x in self.UFOList])
			self.setNeedsDisplay()

	def downButtonCallback(self, sender):
		if self.w.UIList.getSelection() == []: return
		sel = self.w.UIList.getSelection()[0]
		if sel == len(self.w.UIList.get())-1: return
		UIList = self.w.UIList.get()
		UIList[sel], UIList[sel+1] = UIList[sel+1], UIList[sel]
		T = self.UFOList
		T[sel], T[sel+1] = T[sel+1], T[sel]
		self.w.UIList.set(UIList)
		self.setNeedsDisplay()

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
		self.showGetFile(['ufo'], callback=self.OpenUFOCallback,allowsMultipleSelection=True)

	def fontModelForFont(self, font):
		if not helperFunctions.fontIsQuadratic(font):
			return None
		model = TTHFont.TTHFont(font)
		return model

	def OpenUFOCallback(self, sender):
		for path in sender:
			if path is None:
				continue
			elif not path.endswith(".ufo"):
				continue
			else:
				UFO = RFont(path, showUI=False)
				myUFO = UFOdata(path, self.fontModelForFont(UFO))
				myUFO.requiredGlyphs = self.updatePartialFontIfNeeded(myUFO.fm, myUFO.requiredGlyphs)
				self.UFOList.append(myUFO)
		self.UFOList.sort(key=lambda x:x.weight)
		self.w.UIList.set([{'tail':x.tail} for x in self.UFOList])
		self.setNeedsDisplay()

	def buttonRefreshUFOsCallback(self, sender):
		pathList = [x.path for x in self.UFOList]
		self.UFOList = []
		self.OpenUFOCallback(pathList)

	def calculateCanvasSize(self, winPosSize):
		return (winPosSize[2], winPosSize[3])#-140)

	def movedOrResizedCallback(self, sender):
		pass
		#self.resizeView(self.w.getPosSize())

	def closedCallback(self, sender):
		setDefault('drawingSegmentType', self.originalCurveDrawingPref)

	def resizeView(self, posSize):
		self.w.view.getNSView().setFrame_(((0, 0), self.calculateCanvasSize(posSize)))

	def setNeedsDisplay(self):
		self.w.view.getNSView().setNeedsDisplay_(True)

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
			self.previewString = ''
		self.w.previewEditText.set(self.previewString)
		if self.UFOList == []: return
		for ufo in self.UFOList:
			ufo.requiredGlyphs = self.updatePartialFontIfNeeded(ufo.fm, ufo.requiredGlyphs)
		self.setNeedsDisplay()

	def draw(self):
		if self.UFOList == []: return
		s1 = self.size1
		s2 = self.size2
		canvasHeight = 10+self.scale*((s1+s2+20)*(s2-s1+1)/2.0 + 10.0)
		trGlyphs = []

		for uiUfo in self.w.UIList:
			ufos = [u for u in self.UFOList if u.tail == uiUfo['tail']]
			if ufos == []: continue
			ufo = ufos[0]
			if ufo.fm == None: continue
			ufo.fm.bitmapPreviewMode = self.rasteriserMode
			tr = ufo.fm.textRenderer
			if not tr: continue
			if not tr.isOK(): continue
			glyphs = tr.names_to_indices(self.prepareText(ufo.fm.f))
			trGlyphs.append((tr, glyphs))

		xPos = 10
		yPos = 10
		for tr, glyphs in trGlyphs:	
			tr.set_cur_size(s2)
			tr.set_pen((xPos + 10*self.scale, -200*self.scale))
			x, y = tr.render_indexed_glyph_list(glyphs, scale=self.scale)
			xPos += x + 10*self.scale
		canvasWidth = xPos

		ps = self.w.getPosSize()
		ps = ps[2]-20, ps[3]-140
		newWidth  = max(ps[0], canvasWidth)
		newHeight = max(ps[1], canvasHeight)
		v = self.w.view.getNSView()
		boundsSize = v.bounds().size
		boundsSize = boundsSize.width, boundsSize.height
		frameSize = v.frame().size
		frameSize = frameSize.width, frameSize.height
		newSize = newWidth, newHeight
		if boundsSize != newSize or frameSize != newSize:
			self.w.view.getNSView().setFrame_(((0,0),(newWidth, newHeight)))
			self.w.view.getNSView().setBoundsSize_((newWidth, newHeight))
		
		xPos = 10
		for tr, glyphs in trGlyphs:
			yPos = max(10, newHeight - canvasHeight)
			colWidth = 0
			for size in range(s2, s1-1, -1):
				displaysize = str(size)
				DR.drawPreviewSize(str(size), xPos, yPos, DR.kBlackColor)
				tr.set_cur_size(size)
				tr.set_pen((xPos + 10*self.scale, yPos))
				x, y = tr.render_indexed_glyph_list(glyphs, scale=self.scale)
				if size == self.size2: colWidth = x
				yPos += (size + 10)*self.scale
			xPos += colWidth + 10*self.scale
