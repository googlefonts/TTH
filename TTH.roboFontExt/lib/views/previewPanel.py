from mojo.extensions import *
from vanilla import *
from mojo.canvas import Canvas
from mojo.UI import *
from AppKit import *
import string

from views import TTHWindow
from commons import drawing as DR

DefaultKeyStub = "com.sansplomb.TTH."

defaultKeyPreviewWindowPosSize = DefaultKeyStub + "previewWindowPosSize"
defaultKeyPreviewWindowVisibility = DefaultKeyStub + "previewWindowVisibility"

blackColor = NSColor.blackColor()
redColor = NSColor.redColor()

class PreviewPanel(TTHWindow):
	def __init__(self, TTHToolInstance, defaultPosSize):
		super(PreviewPanel, self).__init__(defaultKeyPreviewWindowPosSize, defaultKeyPreviewWindowVisibility)
		self.TTHToolController = TTHToolInstance
		tthtm = self.TTHToolController.TTHToolModel

		self.FromSize = tthtm.previewFrom
		self.ToSize = tthtm.previewTo

		self.clickableSizes= {}
		self.clickableGlyphs = {}

		ps = getExtensionDefault(defaultKeyPreviewWindowPosSize, fallback=defaultPosSize)
		win = FloatingWindow(ps, "Preview", minSize=(350, 200))

		win.previewEditText = ComboBox((10, 10, -10, 22), tthtm.previewSampleStringsList,
			callback=self.previewEditTextCallback)
		win.previewEditText.set(tthtm.previewString)

		win.view = Canvas((10, 50, -10, -10), delegate = self, canvasSize = self.calculateCanvasSize(ps))

		win.bind("move", self.movedOrResizedCallback)
		win.bind("resize", self.movedOrResizedCallback)
		self.window = win # this will not rebind the events, since they are already bound.

	def calculateCanvasSize(self, winPosSize):
		return (winPosSize[2], winPosSize[3]-60)

	def setNeedsDisplay(self):
		self.window.view.getNSView().setNeedsDisplay_(True)

	def mouseUp(self, event):
		win = self.window
		cnt = win.view.scrollView._getContentView().contentView()
		pos = win.getNSWindow().contentView().convertPoint_toView_(event.locationInWindow(), cnt)
		x, y = pos.x, pos.y
		for i in self.clickableSizes:
			if x >= i[0] and x <= i[0]+10 and y >= i[1] and y <= i[1]+8:
				self.TTHToolController.changeSize(self.clickableSizes[i])
				break
		for coords, glyphName in self.clickableGlyphs.items():
			if x >= coords[0] and x <= coords[2] and y >= coords[1] and y <= coords[3]:
				SetCurrentGlyphByName(glyphName[0])
				break

	def draw(self):
		self.drawPreviewPanel()
	
	def resizeView(self, posSize):
		self.window.view.getNSView().setFrame_(((0, 0), self.calculateCanvasSize(posSize)))

	def movedOrResizedCallback(self, sender):
		super(PreviewPanel, self).movedOrResized(sender)
		self.resizeView(self.window.getPosSize())

	def previewEditTextCallback(self, sender):
		self.TTHToolController.TTHToolModel.setPreviewString(sender.get())
		self.TTHToolController.updatePartialFontIfNeeded()
		self.setNeedsDisplay()

	def drawPreviewPanel(self):
		if self.TTHToolController.ready == False:
			return
		if self.TTHToolController.getGlyph() == None:
			return
		self.clickableSizes= {}

		tr = self.TTHToolController.c_fontModel.textRenderer
		if not tr:
			return

		tthtm = self.TTHToolController.TTHToolModel

		advanceWidthUserString = 0
		advanceWidthCurrentGlyph = 0
		(namedGlyphList, curGlyphName) = self.TTHToolController.prepareText()
		glyphs = tr.names_to_indices(namedGlyphList)
		curGlyph = tr.names_to_indices([curGlyphName])[0]
		# render user string
		tr.set_cur_size(tthtm.PPM_Size)

		ps = self.window.getPosSize()
		tr.set_pen((20, ps[3] - 220))
		tr.render_indexed_glyph_list(glyphs)

		self.clickableGlyphs = {}
		pen = (20, ps[3] - 220)
		for name in namedGlyphList:
			adv = tr.get_name_advance(name)
			newpen = pen[0]+int(adv[0]/64), pen[1]+int(adv[1]/64)
			rect = (pen[0], pen[1], newpen[0], pen[1]+tthtm.PPM_Size)
			self.clickableGlyphs[rect] = name
			pen = newpen

		# render user string at various sizes
		y = ps[3] - 280
		x = 30
		for size in range(tthtm.previewFrom, tthtm.previewTo+1, 1):

			self.clickableSizes[(x-20, y)] = size

			displaysize = str(size)
			if size == tthtm.PPM_Size:
				DR.drawPreviewSize(displaysize, x-20, y, redColor)
			else:
				DR.drawPreviewSize(displaysize, x-20, y, blackColor)

			tr.set_cur_size(size)
			tr.set_pen((x, y))
			tr.render_indexed_glyph_list(glyphs)
			advanceWidthUserString = tr.get_pen()[0]
			y -= size + 1
			if y < 0:
				width, height = tr.pen
				x = width+40
				y = ps[3] - 310

		# render current glyph at various sizes
		advance = 10
		
		for size in range(tthtm.previewFrom, tthtm.previewTo+1, 1):

			self.clickableSizes[(advance, ps[3] - 170)] = size

			displaysize = str(size)
			if size == tthtm.PPM_Size:
				DR.drawPreviewSize(displaysize, advance, ps[3] - 170, redColor)
			else:
				DR.drawPreviewSize(displaysize, advance, ps[3] - 170, blackColor)
			
			tr.set_cur_size(size)
			tr.set_pen((advance, ps[3] - 135))
			delta_pos = tr.render_named_glyph_list([curGlyphName])
			advance += delta_pos[0] + 5
			advanceWidthCurrentGlyph = advance

		width = ps[2]
		newWidth = max(advanceWidthUserString, advanceWidthCurrentGlyph)

		if width < newWidth:
			ps = ps[0], ps[1], newWidth, ps[3]
			self.resizeView(ps)

	def resizeView(self, posSize):
		self.window.view.getNSView().setFrame_(((0, 0), self.calculateCanvasSize(posSize)))
