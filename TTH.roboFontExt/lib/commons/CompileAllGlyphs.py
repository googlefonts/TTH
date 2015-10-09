print 'Should compile all glyphs assembly'

from robofab.interface.all.dialogs import Message as FabMessage

from models.TTHTool import uniqueInstance as tthTool
from commons import helperFunctions

def go():
	font = CurrentFont()
	if (font is None) or (not helperFunctions.fontIsQuadratic(font)):
		FabMessage("This is not a Quadratic/TrueType UFO.\nNothing to do.")
		return

	fm = tthTool.fontModelForFont(font)
	#fm.compileAllGlyphs()
	fm.compileAllTTFData()
	print "TTH data compiled for font", font.fileName

go()
