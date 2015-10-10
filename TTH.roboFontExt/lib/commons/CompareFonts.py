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

		win.view = Canvas((10, 130, -10, -10), delegate = self, canvasSize = self.calculateCanvasSize(ps))
		win.bind("move", self.movedOrResizedCallback)
		win.bind("resize", self.movedOrResizedCallback)
		win.bind("close", self.closedCallback)

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
		return (winPosSize[2], winPosSize[3]-140)

	def movedOrResizedCallback(self, sender):
		self.resizeView(self.w.getPosSize())

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
		adv = 0
		height = (self.size1 + 10)*self.scale
		starty = 150 + height
		ps = self.w.getPosSize()
		canvasHeight = 0

		for tail in self.w.UIList:
			ufos = [u for u in self.UFOList if u.tail == tail['tail']]
			if ufos == []: continue
			ufo = ufos[0]
			if ufo.fm == None: return
			ufo.fm.bitmapPreviewMode = self.rasteriserMode
			tr = ufo.fm.textRenderer
			if not tr: return
			if not tr.isOK(): return
			
			glyphs = tr.names_to_indices(self.prepareText(ufo.fm.f))
			
			# render user string
			for size in range(self.size1, self.size2+1, 1):
				displaysize = str(size)
				DR.drawPreviewSize(displaysize, adv + 10, ps[3] - starty - height, DR.kBlackColor)
				tr.set_cur_size(size)
				tr.set_pen((adv + 20, ps[3] - starty - height))
				x, y = tr.render_indexed_glyph_list(glyphs, scale=self.scale)
				height += (size + 10)*self.scale
			canvasHeight = height
			adv += x + 10*self.scale
			height = (self.size1 + 10)*self.scale
			
		newWidth = max(ps[2], adv)
		newHeight = max(ps[3], canvasHeight)
		newPosSize = ps[0], ps[1], newWidth, newHeight
		self.resizeView(newPosSize)
				


