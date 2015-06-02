from mojo.extensions import *
from vanilla import *
from mojo.canvas import Canvas
from mojo.UI import *
#from AppKit import *
import string

from views import TTHWindow
from drawing import utilities as DR

DefaultKeyStub = "com.sansplomb.TTH."

defaultKeyPreviewWindowPosSize = DefaultKeyStub + "previewWindowPosSize"
defaultKeyPreviewWindowVisibility = DefaultKeyStub + "previewWindowVisibility"

from models.TTHTool import uniqueInstance as tthTool

class PreviewPanel(TTHWindow):
	def __init__(self):
		super(PreviewPanel, self).__init__(defaultKeyPreviewWindowPosSize, defaultKeyPreviewWindowVisibility)

		self.clickableSizes= {}
		self.clickableGlyphs = {}

		ps = getExtensionDefault(defaultKeyPreviewWindowPosSize, fallback=(-510, 30, 500, 600))
		win = FloatingWindow(ps, "Preview", minSize=(350, 200))

		win.previewEditText = ComboBox((10, 10, -10, 22), tthTool.previewSampleStringsList,
			callback=self.previewEditTextCallback)
		win.previewEditText.set(tthTool.previewString)

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
				tthTool.changeSize(self.clickableSizes[i])
				break
		for coords, glyphName in self.clickableGlyphs.items():
			if x >= coords[0] and x <= coords[2] and y >= coords[1] and y <= coords[3]:
				SetCurrentGlyphByName(glyphName)
				break

	def resizeView(self, posSize):
		self.window.view.getNSView().setFrame_(((0, 0), self.calculateCanvasSize(posSize)))

	def movedOrResizedCallback(self, sender):
		super(PreviewPanel, self).movedOrResized(sender)
		self.resizeView(self.window.getPosSize())

	def previewEditTextCallback(self, sender):
		tthTool.setPreviewString(sender.get())
		tthTool.updatePartialFontIfNeeded()
		self.setNeedsDisplay()

	def draw(self):
		glyph, fm = tthTool.getRGAndFontModel()
		if fm == None: return
		self.clickableSizes= {}
		tr = fm.textRenderer
		if not tr: return
		if not tr.isOK(): return

		advanceWidthUserString = 0
		advanceWidthCurrentGlyph = 0
		(namedGlyphList, curGlyphName) = tthTool.prepareText(glyph, fm.f)
		glyphs = tr.names_to_indices(namedGlyphList)
		curGlyph = tr.names_to_indices([curGlyphName])[0]
		# render user string
		tr.set_cur_size(tthTool.PPM_Size)

		ps = self.window.getPosSize()
		tr.set_pen((20, ps[3] - 220))
		tr.render_indexed_glyph_list(glyphs)

		self.clickableGlyphs = {}
		pen = (20, ps[3] - 220)
		for name in namedGlyphList:
			adv = tr.get_name_advance(name)
			newpen = pen[0]+int(adv[0]/64), pen[1]+int(adv[1]/64)
			rect = (pen[0], pen[1], newpen[0], pen[1]+tthTool.PPM_Size)
			self.clickableGlyphs[rect] = name
			pen = newpen

		# render user string at various sizes
		y = ps[3] - 280
		x = 30
		for size in range(tthTool.previewFrom, tthTool.previewTo+1, 1):

			self.clickableSizes[(x-20, y)] = size

			displaysize = str(size)
			if size == tthTool.PPM_Size:
				DR.drawPreviewSize(displaysize, x-20, y, DR.kRedColor)
			else:
				DR.drawPreviewSize(displaysize, x-20, y, DR.kBlackColor)

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

		for size in range(tthTool.previewFrom, tthTool.previewTo+1, 1):

			self.clickableSizes[(advance, ps[3] - 170)] = size

			displaysize = str(size)
			if size == tthTool.PPM_Size:
				DR.drawPreviewSize(displaysize, advance, ps[3] - 170, DR.kRedColor)
			else:
				DR.drawPreviewSize(displaysize, advance, ps[3] - 170, DR.kBlackColor)

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

if tthTool._printLoadings: print "previewPanel, ",
