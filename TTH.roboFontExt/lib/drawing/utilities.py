
from AppKit import NSColor, NSFont, NSFontAttributeName,\
		NSForegroundColorAttributeName, NSBezierPath,\
		NSAttributedString, NSGraphicsContext, NSShadow

from drawing import geom

kBorderColor      = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, .8)
kDiscColor        = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .3, .94, 1)
kDoublinkColor    = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .25, 1, 1)
kInactiveColor    = NSColor.colorWithCalibratedRed_green_blue_alpha_(.5, .5, .5, 0.2)
kLinkColor        = NSColor.colorWithCalibratedRed_green_blue_alpha_(.5, 0, 0, 1)
kOutlineColor     = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, .5)
kShadowColor      = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, .8)
kSidebearingColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.4, .8, 1, 1)

kLabelTextAttributes = {
		NSFontAttributeName : NSFont.boldSystemFontOfSize_(9),
		NSForegroundColorAttributeName : NSColor.blackColor(),
		}
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
	d =scale * r
	path = NSBezierPath.bezierPath()
	path.moveToPoint_((x+d, y))
	path.lineToPoint_((x, y+d))
	path.lineToPoint_((x-d, y))
	path.lineToPoint_((x, y-d))
	path.lineToPoint_((x+d, y))
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

def makeArrowPathAndAnchor(scale, lengthInPixel, direction, tip, path=None):
	dir = lengthInPixel * scale * direction.normalized()
	orth = 0.35 * dir.rotateCCW()
	if path is None:
		pathArrow = NSBezierPath.bezierPath()
	else:
		pathArrow = path
	anchor = tip + dir
	pathArrow.moveToPoint_(tip)
	pathArrow.lineToPoint_(anchor-orth)
	pathArrow.lineToPoint_(anchor+orth)
	pathArrow.lineToPoint_(tip)
	return pathArrow, anchor

def drawArrowAtPoint(scale, r, direction, pos, color):
	path, anchor = makeArrowPathAndAnchor(scale, r, direction, pos)
	color.set()
	path.fill()
	path.setLineWidth_(scale)
	kOutlineColor.set()
	path.stroke()

def drawTextAtPoint(scale, title, pos, textColor, backgroundColor, view, active=True):
	labelColor = backgroundColor
	if not active:
		labelColor = kInactiveColor
		textColor = NSColor.whiteColor()
	else:
		labelColor = backgroundColor

	kLabelTextAttributes[NSForegroundColorAttributeName] = textColor
	text = NSAttributedString.alloc().initWithString_attributes_(title, kLabelTextAttributes)
	width, height = text.size()
	fontSize = kLabelTextAttributes[NSFontAttributeName].pointSize()
	width = width*scale
	width += 8.0*scale
	height = 13*scale

	p = pos - 0.5*geom.Point(width, fontSize*scale)
	unit = geom.Point(scale,scale)
	size = geom.Point(width, height)

	shadow = NSShadow.alloc().init()
	shadow.setShadowColor_(kShadowColor)
	shadow.setShadowOffset_((0, -1))
	shadow.setShadowBlurRadius_(2)

	context = NSGraphicsContext.currentContext()
	#if self.popOverIsOpened and cmdIndex == self.commandClicked and cmdIndex != None:
	#	selectedPath = NSBezierPath.bezierPath()
	#	selectedPath.appendBezierPathWithRoundedRect_xRadius_yRadius_((p-2*unit, size+4*unit), 3*scale, 3*scale)
	#	selectedShadow = NSShadow.alloc().init()
	#	selectedShadow.setShadowColor_(selectedColor)
	#	selectedShadow.setShadowOffset_((0, 0))
	#	selectedShadow.setShadowBlurRadius_(10)
	#	context.saveGraphicsState()
	#	selectedShadow.set()
	#	selectedColor.set()
	#	selectedPath.fill()
	#	context.restoreGraphicsState()

	thePath = NSBezierPath.bezierPath()
	thePath.appendBezierPathWithRoundedRect_xRadius_yRadius_((p, size), 3*scale, 3*scale)

	context.saveGraphicsState()
	shadow.set()
	thePath.setLineWidth_(scale)
	labelColor.set()
	thePath.fill()
	kBorderColor.set()
	thePath.stroke()
	context.restoreGraphicsState()

	view._drawTextAtPoint(title, kLabelTextAttributes, p+0.5*size+geom.Point(0,scale), drawBackground=False)
	return size

def drawSingleArrow(scale, pos1, pos2, color, size=10):
	offCurve = geom.computeOffMiddlePoint(scale, pos1, pos2)
	pathArrow, anchor = makeArrowPathAndAnchor(scale, size, offCurve-pos2, pos2)
	path = NSBezierPath.bezierPath()
	path.moveToPoint_(pos1)
	path.curveToPoint_controlPoint1_controlPoint2_(anchor, offCurve, offCurve)
	color.set()
	pathArrow.fill()
	path.setLineWidth_(scale*size/10.0)
	path.stroke()
	return offCurve

def drawDoubleArrow(scale, pos1, pos2, active, iColor, size=10):
	if active:
		color = iColor
	else:
		color = kInactiveColor
	offCurve = geom.computeOffMiddlePoint(scale, pos1, pos2)
	pathArrow1, anchor1 = makeArrowPathAndAnchor(scale, size, offCurve-pos1, pos1)
	pathArrow2, anchor2 = makeArrowPathAndAnchor(scale, size, offCurve-pos2, pos2)
	path = NSBezierPath.bezierPath()
	path.moveToPoint_(anchor1)
	path.curveToPoint_controlPoint1_controlPoint2_(anchor2, offCurve, offCurve)
	color.set()
	pathArrow1.fill()
	pathArrow2.fill()
	path.setLineWidth_(scale*size/10.0)
	path.stroke()
	return offCurve
