
from AppKit import *

kDiscColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .3, .94, 1)
kSidebearingColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.4, .8, 1, 1)

kPreviewSizeAttributes = {
		NSFontAttributeName : NSFont.boldSystemFontOfSize_(7),
		NSForegroundColorAttributeName : NSColor.blackColor(),
		}

def drawPreviewSize(title, x, y, color):
	kPreviewSizeAttributes[NSForegroundColorAttributeName] = color
	text = NSAttributedString.alloc().initWithString_attributes_(title, kPreviewSizeAttributes)
	text.drawAtPoint_((x, y))

def drawDiscAtPoint(r, x, y, color):
	color.set()
	NSBezierPath.bezierPathWithOvalInRect_(((x-r, y-r), (r*2, r*2))).fill()

def drawLozengeAtPoint(scale, r, x, y, color):
	color.set()
	path = NSBezierPath.bezierPath()
	path.moveToPoint_((x+r*5, y))
	path.lineToPoint_((x, y+r*5))
	path.lineToPoint_((x-r*5, y))
	path.lineToPoint_((x, y-r*5))
	path.lineToPoint_((x+r*5, y))
	path.fill()

def drawSideBearingsPointsOfGlyph(scale, size, glyph):
	r = size*scale
	drawDiscAtPoint(r, 0, 0, kDiscColor)
	drawDiscAtPoint(r, glyph.width, 0, kDiscColor)

def drawHorizontalLines(w, yPositions):
	pathY = NSBezierPath.bezierPath()
	for y in yPositions:
		pathY.moveToPoint_((-5000, y))
		pathY.lineToPoint_((+5000, y))
	kSidebearingColor.set()
	pathY.setLineWidth_(w)
	pathY.stroke()

def drawVerticalLines(w, xPositions):
	path = NSBezierPath.bezierPath()
	for x in xPositions:
		path.moveToPoint_((x, -5000))
		path.lineToPoint_((x, +5000))
	kSidebearingColor.set()
	path.setLineWidth_(w)
	path.stroke()
