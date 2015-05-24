#coding=utf-8
from vanilla import Box, Button, CheckBox, Group, EditText, ProgressBar, Sheet, TextBox
import auto
#import commons
from commons import helperFunctions
from models.TTHTool import uniqueInstance as tthTool

class AutoHintingSheet(object):
	def __init__(self, parentWindow):
		fm = tthTool.getFontModel()
		yBounds, xBounds = fm.stemSizeBounds

		sheetHeight = 200
		sheetWidth  = 320
		sheetSize = (sheetWidth, sheetHeight)

		self.w = Sheet(sheetSize, minSize=sheetSize, maxSize=sheetSize, parentWindow=parentWindow)
		w = self.w

		w.hintXBox = CheckBox((10,17,70,22), 'X Hinting:', value=True)
		w.xGroup = Group((10, 15, -10, 22))
		w.xGroup.minW    = EditText((100,0,40,22), text=str(xBounds[0]), continuous=False, callback=self.handleStemBounds)
		w.xGroup.stemLabel = TextBox((140,2,-40,22), '<= stem width <=', alignment='center')
		w.xGroup.maxW    = EditText((-40,0,40,22), text=str(xBounds[1]), continuous=False, callback=self.handleStemBounds)

		w.hintYBox = CheckBox((10,52,70,22), 'Y Hinting:', value=True)
		w.yGroup = Group((10, 50, -10, 22))
		w.yGroup.minW    = EditText((100,0,40,22), text=str(yBounds[0]), continuous=False, callback=self.handleStemBounds)
		w.yGroup.stemLabel = TextBox((140,2,-40,22), '<= stem width <=', alignment='center')
		w.yGroup.maxW    = EditText((-40,0,40,22), text=str(yBounds[1]), continuous=False, callback=self.handleStemBounds)

		w.tolLabel = TextBox((-160, 87, -60, 22), 'Angle Tolerance:', alignment='right')
		w.tolerance = EditText((-50, 85, 40, 22), text=str(fm.angleTolerance), continuous=False, callback=self.handleTolerance)

		bGroup = Group((10, 120, -10, -10))

		bGroup.closeButton = Button((0,-20,100,20), "Close", sizeStyle='small', callback=self.close)

		setattr(w, 'bGroup', bGroup)
		w.open()

	def close(self, sender):
		self.w.close()

	def handleTolerance(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
		value = max(0, min(45, abs(value)))
		sender.set(value)
		fm = tthTool.getFontModel()
		fm.angleTolerance = value

	def handleStemBounds(self, sender):
		try:
			value = int(sender.get())
		except ValueError:
			value = 0
		value = min(9999, abs(value))
		xg = self.w.xGroup
		yg = self.w.yGroup
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
