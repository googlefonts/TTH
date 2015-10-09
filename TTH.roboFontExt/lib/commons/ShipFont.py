#print 'Should compile TTF Font'

from robofab.interface.all.dialogs import Message as FabMessage

from models.TTHTool import uniqueInstance as tthTool
from commons import helperFunctions

def go():
	font = CurrentFont()
	if (font is None) or (not helperFunctions.fontIsQuadratic(font)):
		FabMessage("This is not a Quadratic/TrueType UFO.\nNothing to do.")
		return

	fname = font.fileName
	if fname[-4:] != ".ufo":
		FabMessage("This is not a UFO.\nNothing to do.")
		return

	fname = fname[-4:]+".ttf"

	fm = tthTool.fontModelForFont(font)
	if fm is None:
		FabMessage("Shipping Font Error. Sorry. Bye.")
		return

	fm.compileAllTTFData()
	font.generate(fname, 'ttf',\
			decompose     = False,\
			checkOutlines = False,\
			autohint      = False,\
			releaseMode   = False,\
			glyphOrder    = None,\
			progressBar   = None)
	print "TTF font", fname, "shipped."

go()
