#print 'Should compile TTF Font'

from robofab.interface.all.dialogs import Message as FabMessage

from models.TTHTool import uniqueInstance as tthTool
from commons import helperFunctions
from views import TTHProgressWindow
reload(TTHProgressWindow)

def go():
	font = CurrentFont()
	if (font is None) or (not helperFunctions.fontIsQuadratic(font)):
		FabMessage("This is not a Quadratic/TrueType UFO.\nNothing to do.")
		return

	fname = font.fileName
	if fname[-4:] != ".ufo":
		FabMessage("This is not a UFO.\nNothing to do.")
		return

	fname = fname[:-4]+".ttf"

	fm = tthTool.fontModelForFont(font)
	if fm is None:
		FabMessage("Can't find the TTHFont instance. Sorry. Bye.")
		return

	exn = None
	pbw = TTHProgressWindow.TTHProgressWindow("Preparing tables and glyphs...", len(font)+30)
	try:
		fm.compileAllTTFData(pbw)
		if pbw: pbw.setTitle("Shipping font...")
		if pbw: pbw.setInfo("(please wait)")
		font.generate(fname, 'ttf',\
				decompose     = False,\
				checkOutlines = False,\
				autohint      = False,\
				releaseMode   = False,\
				glyphOrder    = None,\
				progressBar   = None)
		if pbw: pbw.increment(30)
	except Exception as inst:
		exn = inst
	finally:
		if pbw: pbw.close()
	if exn:
		print "[TTH ERROR] An error happened during the compilation of the glyphs' hinting program in font", font.fileName
		print exn
	else:
		print "TTF font shipped to file:", fname

go()
