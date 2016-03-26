from mojo.extensions import *
from mojo.UI import MultiLineView
from vanilla import *

from views import TTHWindow

DefaultKeyStub = "com.sansplomb.TTH."

defaultKeyParametricPreviewWindowPosSize = DefaultKeyStub + "parametricPreviewWindowPosSize"
defaultKeyParametricPreviewWindowVisibility = DefaultKeyStub + "parametricPreviewWindowVisibility"

from models.TTHTool import uniqueInstance as tthTool
from models import TTHGlyph
from ps import parametric

reload(TTHGlyph)
reload(parametric)

class parametricPreview(TTHWindow):

	def __init__(self):
		super(parametricPreview, self).__init__(defaultKeyParametricPreviewWindowPosSize, defaultKeyParametricPreviewWindowVisibility)

		ps = getExtensionDefault(defaultKeyParametricPreviewWindowPosSize, fallback=(30, 30, 600, 400))
		win = FloatingWindow(ps, "Parametric Preview", minSize=(300, 300))

		win.lineView = MultiLineView((0, 22, -0, -0), 
											pointSize=tthTool.parametricPreviewSize, 
											selectionCallback=self.lineViewSelectionCallback)
		win.sizeSlider = Slider((-210, 0, 200, 20), minValue=12, maxValue=300, value=tthTool.parametricPreviewSize, callback=self.sizeSliderCallback)
		win.previewEditText = ComboBox((0, 0, -220, 22), tthTool.previewSampleStringsList, continuous=True,
			callback=self.previewEditTextCallback)

		self.window = win # this will not rebind the events, since they are already bound.
		self.updateDisplay()
	
	def lineViewSelectionCallback(self, sender):
		print sender.getSelectedGlyph()

	def updateDisplay(self):
		gm, fm = tthTool.getGlyphAndFontModel()
		(namedGlyphList, curGlyphName) = tthTool.prepareText(gm.RFGlyph, fm.f)
		self.window.lineView.setPointSize(tthTool.parametricPreviewSize)
		self.window.lineView.setFont(fm.f)
		glyphs = []
		for name in namedGlyphList:
			gm = fm.glyphModelForGlyph(fm.f[name])
			if name in fm.f:
				pGlyph = gm._pg
				if pGlyph == None:
					parametric.processParametric(fm, gm)
					pGlyph = gm._pg
				glyphs.append(pGlyph)

		self.window.lineView.set(glyphs)

	def sizeSliderCallback(self, sender):
		tthTool.changePointSize(sender.get())
		self.updateDisplay()

	def previewEditTextCallback(self, sender):
		tthTool.setPreviewString(sender.get())
		self.updateDisplay()



if tthTool._printLoadings: print "parametricPreviewPanel, ",