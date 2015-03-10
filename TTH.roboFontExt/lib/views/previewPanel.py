from mojo.extensions import *
from vanilla import *
from mojo.canvas import Canvas
from AppKit import *
import string

from views import TTHWindow

DefaultKeyStub = "com.sansplomb.TTH."

defaultKeyPreviewWindowPosSize = DefaultKeyStub + "previewWindowPosSize"
defaultKeyPreviewWindowVisibility = DefaultKeyStub + "previewWindowVisibility"

blackColor = NSColor.blackColor()
redColor = NSColor.redColor()


class PreviewPanel(TTHWindow):
	def __init__(self, TTHToolInstance, defaultPosSize):
		super(PreviewPanel, self).__init__(defaultPosSize, defaultKeyPreviewWindowPosSize, defaultKeyPreviewWindowVisibility)
		self.TTHToolController = TTHToolInstance
		self.TTHToolModel = self.TTHToolController.TTHToolModel

		self.FromSize = self.TTHToolModel.previewFrom
		self.ToSize = self.TTHToolModel.previewTo

		self.clickableSizes= {}
		self.clickableGlyphs = {}

		ps = getExtensionDefault(defaultKeyPreviewWindowPosSize, fallback=defaultPosSize)
		win = FloatingWindow(ps, "Preview", minSize=(350, 200))

		previewList = ['HH/?HH/?OO/?OO/?', 'nn/?nn/?oo/?oo/?', '0123456789', string.uppercase, string.lowercase]
		win.previewEditText = ComboBox((10, 10, -10, 22), previewList,
				callback=self.previewEditTextCallback)
		win.previewEditText.set(self.TTHToolModel.previewString)

		win.view = Canvas((10, 50, -10, -40), delegate = self, canvasSize = self.calculateCanvasSize(ps))

		win.DisplaySizesText = TextBox((10, -30, 120, -10), "Display Sizes From:", sizeStyle = "small")
		win.DisplayFromEditText = EditText((130, -32, 30, 19), sizeStyle = "small", 
				callback=self.DisplayFromEditTextCallback)
		win.DisplayFromEditText.set(self.FromSize)

		win.DisplayToSizeText = TextBox((170, -30, 22, -10), "To:", sizeStyle = "small")
		win.DisplayToEditText = EditText((202, -32, 30, 19), sizeStyle = "small", 
				callback=self.DisplayToEditTextCallback)
		win.DisplayToEditText.set(self.ToSize)
		win.ApplyButton = Button((-100, -32, -10, 22), "Apply", sizeStyle = 'small', 
				callback=self.ApplyButtonCallback)
		
		for i in string.lowercase:
			self.TTHToolModel.requiredGlyphsForPartialTempFont.add(i)
		for i in string.uppercase:
			self.TTHToolModel.requiredGlyphsForPartialTempFont.add(i)
		for i in ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'zero']:
			self.TTHToolModel.requiredGlyphsForPartialTempFont.add(i)

		win.bind("move", self.movedOrResizedCallback)
		win.bind("resize", self.movedOrResizedCallback)
		self.setWindow(win) # this will not rebind the events, since they are already bound.

	def calculateCanvasSize(self, winPosSize):
		return (winPosSize[2], winPosSize[3]-90)

	def setNeedsDisplay(self):
		self.window().view.getNSView().setNeedsDisplay_(True)

	def mouseUp(self, event):
		win = self.window()
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
		self.window().view.getNSView().setFrame_(((0, 0), self.calculateCanvasSize(posSize)))

	def movedOrResizedCallback(self, sender):
		super(PreviewPanel, self).movedOrResized(sender)
		self.resizeView(self.window().getPosSize())

	def previewEditTextCallback(self, sender):
		self.TTHToolModel.setPreviewString(sender.get())
		self.TTHToolController.updatePartialFontIfNeeded()
		self.setNeedsDisplay()

	def DisplayFromEditTextCallback(self, sender):
		try:
			size = int(sender.get())
		except:
			size = self.TTHToolModel.previewFrom
		self.FromSize = self.TTHToolController.cleanPreviewSize(size)

	def DisplayToEditTextCallback(self, sender):
		try:
			size = int(sender.get())
		except:
			size = self.TTHToolModel.previewTo
		self.ToSize = self.TTHToolController.cleanPreviewSize(size)

	def ApplyButtonCallback(self, sender):
		win = self.window()
		fromS = self.FromSize
		toS = self.ToSize
		if fromS < 8: fromS = 8
		if toS < 8: toS = 8
		if fromS > toS:
			fromS = toS
		if toS > fromS + 100:
			toS = fromS + 100
		self.FromSize = fromS
		self.ToSize = toS
		self.window().DisplayFromEditText.set(fromS)
		self.window().DisplayToEditText.set(toS)
		self.TTHToolController.changePreviewSize(self.FromSize, self.ToSize)
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

		advanceWidthUserString = 0
		advanceWidthCurrentGlyph = 0
		(namedGlyphList, curGlyphName) = self.TTHToolController.prepareText()
		glyphs = tr.names_to_indices(namedGlyphList)
		curGlyph = tr.names_to_indices([curGlyphName])[0]
		# render user string
		tr.set_cur_size(self.TTHToolModel.PPM_Size)

		ps = self.window().getPosSize()
		tr.set_pen((20, ps[3] - 250))
		tr.render_indexed_glyph_list(glyphs)

		self.clickableGlyphs = {}
		pen = (20, ps[3] - 250)
		for name in namedGlyphList:
			adv = tr.get_name_advance(name)
			newpen = pen[0]+int(adv[0]/64), pen[1]+int(adv[1]/64)
			rect = (pen[0], pen[1], newpen[0], pen[1]+self.TTHToolModel.PPM_Size)
			self.clickableGlyphs[rect] = name
			pen = newpen

		# render user string at various sizes
		y = ps[3] - 310
		x = 30
		for size in range(self.TTHToolModel.previewFrom, self.TTHToolModel.previewTo+1, 1):

			self.clickableSizes[(x-20, y)] = size

			displaysize = str(size)
			if size == self.TTHToolModel.PPM_Size:
				self.drawPreviewSize(displaysize, x-20, y, redColor)
			else:
				self.drawPreviewSize(displaysize, x-20, y, blackColor)

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
		
		for size in range(self.TTHToolModel.previewFrom, self.TTHToolModel.previewTo+1, 1):

			self.clickableSizes[(advance, ps[3] - 200)] = size

			displaysize = str(size)
			if size == self.TTHToolModel.PPM_Size:
				self.drawPreviewSize(displaysize, advance, ps[3] - 200, redColor)
			else:
				self.drawPreviewSize(displaysize, advance, ps[3] - 200, blackColor)
			
			tr.set_cur_size(size)
			tr.set_pen((advance, ps[3] - 165))
			delta_pos = tr.render_named_glyph_list([curGlyphName])
			advance += delta_pos[0] + 5
			advanceWidthCurrentGlyph = advance

		width = ps[2]
		newWidth = max(advanceWidthUserString, advanceWidthCurrentGlyph)

		if width < newWidth:
			ps = ps[0], ps[1], newWidth, ps[3]
			self.resizeView(ps)

	def drawPreviewSize(self, title, x, y, color):
		attributes = {
			NSFontAttributeName : NSFont.boldSystemFontOfSize_(7),
			NSForegroundColorAttributeName : color,
			}

		text = NSAttributedString.alloc().initWithString_attributes_(title, attributes)
		text.drawAtPoint_((x, y))

	def resizeView(self, posSize):
		self.window().view.getNSView().setFrame_(((0, 0), self.calculateCanvasSize(posSize)))