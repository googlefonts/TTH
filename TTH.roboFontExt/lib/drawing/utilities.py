
from AppKit import NSColor, NSFont, NSFontAttributeName,\
		NSForegroundColorAttributeName, NSBezierPath,\
		NSAttributedString, NSGraphicsContext, NSShadow

from drawing import geom

kArrowColor       = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .25, .5, 1)
kBlackColor       = NSColor.blackColor()
kBorderColor      = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, .8)
kDeltaColor       = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .5, 0, 1)
kDiscColor        = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .3, .94, 1)
kSglDiaglinkColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .6, .6, 1)
kDblDiaglinkColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .25, .25, 1)
kDiaglinkColor    = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .25, .25, 1)
kDoublinkColor    = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .25, 1, 1)
kFinalDeltaColor  = NSColor.colorWithCalibratedRed_green_blue_alpha_(.73, .3, .8, 1)
kInactiveColor    = NSColor.colorWithCalibratedRed_green_blue_alpha_(.5, .5, .5, 0.2)
kInterpolateColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.25, .8, 0, 1)
kLinkColor        = NSColor.colorWithCalibratedRed_green_blue_alpha_(.5, 0, 0, 1)
kOutlineColor     = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, .5)
kRedColor         = NSColor.redColor()
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

def drawCircleAtPoint(r, w, x, y, color):
	color.set()
	path = NSBezierPath.bezierPathWithOvalInRect_(((x-r, y-r), (r*2, r*2)))
	path.setLineWidth_(w)
	path.stroke()

def drawSquareAtPoint(d, x, y, color):
	color.set()
	path = NSBezierPath.bezierPath()
	path.moveToPoint_((x+d, y+d))
	path.lineToPoint_((x-d, y+d))
	path.lineToPoint_((x-d, y-d))
	path.lineToPoint_((x+d, y-d))
	path.fill()

def drawTriangleAtPoint(d, x, y, color):
	color.set()
	path = NSBezierPath.bezierPath()
	path.moveToPoint_((x, y+d))
	path.lineToPoint_((x-d, y-d))
	path.lineToPoint_((x+d, y-d))
	path.fill()

def drawLozengeAtPoint(scale, r, x, y, color):
	color.set()
	d = scale * r
	path = NSBezierPath.bezierPath()
	path.moveToPoint_((x+d, y))
	path.lineToPoint_((x, y+d))
	path.lineToPoint_((x-d, y))
	path.lineToPoint_((x, y-d))
	path.lineToPoint_((x+d, y))
	path.fill()

def drawComponentsPoints(scale, glyph, fontModel):
	for c in glyph.components:
		offset_x, offset_y = c.offset
		for c in fontModel.f[c.baseGlyph]:
			for p in c.points:
				pointType = p.type
				if pointType != 'offCurve':
					drawSquareAtPoint(3*scale, p.x + offset_x, p.y + offset_y, kDiscColor)

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
	offCurve = geom.computeOffMiddlePoint(scale, pos1, pos2, size < 0)
	size = abs(size)
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
	offCurve = geom.computeOffMiddlePoint(scale, pos1, pos2, size < 0)
	size = abs(size)
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

from commons import helperFunctions as HF

class CommandLabel(object):
	def __init__(self, cmd, scale, title, pos, textColor, backgroundColor, active):
		self.cmd = cmd
		self.center = pos
		if not active:
			self.bkgndColor = kInactiveColor
			self.textColor = NSColor.whiteColor()
		else:
			self.bkgndColor = backgroundColor
			self.textColor = textColor

		kLabelTextAttributes[NSForegroundColorAttributeName] = self.textColor
		text = NSAttributedString.alloc().initWithString_attributes_(title, kLabelTextAttributes)
		width, height = text.size()
		self.text = title
		self.fontSize = kLabelTextAttributes[NSFontAttributeName].pointSize()
		width = width*scale
		width += 8.0*scale
		height = 13*scale
		self.size = geom.Point(width, height)
		self.speed = geom.Point(0,0)
		self.count = 0
	
	def reset(self):
		self.speed = geom.Point(0,0);
		self.count = 0
	
	def __lt__(self, other):
		return self.center.y+0.5*self.size.y < other.center.y+0.5*other.size.y

	def lo(self):
		return self.center - 0.5 * self.size

	def hi(self):
		return self.center + 0.5 * self.size
	
	def touch(self, other):
		si = 0.02 * self.size
		lo  = self.lo() + si
		hi  = self.hi() - si
		osi = 0.02 * other.size
		olo = other.lo() + osi
		ohi = other.hi() - osi
		return HF.intervalsIntersect((lo.x, hi.x), (olo.x, ohi.x)) \
			and HF.intervalsIntersect((lo.y, hi.y), (olo.y, ohi.y))

	def printe(self):
		print "{:.2f}:{:.2f}".format(self.center.y-0.5*self.size.y, self.size.y),

	def updateSpeed(self, other):
		diff = self.center - other.center
		adif = diff.absolute()
		minDiffX = 0.5 * (self.size.x + other.size.x) - adif.x
		minDiffY = 0.5 * (self.size.y + other.size.y) - adif.y
		if diff.length() < 0.1:
			diff = geom.Point(0,1)
			adif = diff
		if minDiffX <= 0.0: return
		if minDiffY <= 0.0: return
		workInX = 0
		if minDiffX > 0.0 and adif.x > 0.00001:
			workInX = minDiffX / adif.x
		workInY = 0
		if minDiffY > 0.0 and adif.y > 0.00001:
			workInY = minDiffY / adif.y
		if workInX == 0 and workInY == 0: return
		work = 0.5 * min(w for w in [workInX, workInY] if w > 0)
		self.speed = self.speed   + work * diff
		other.speed = other.speed - work * diff
		self.count += 1
		other.count += 1

	def draw(self, scale, nsView):
		shadow = NSShadow.alloc().init()
		shadow.setShadowColor_(kShadowColor)
		shadow.setShadowOffset_((0, -1))
		shadow.setShadowBlurRadius_(2)

		corner = self.center - 0.5*geom.Point(self.size.x, self.fontSize*scale)

		context = NSGraphicsContext.currentContext()

		thePath = NSBezierPath.bezierPath()
		thePath.appendBezierPathWithRoundedRect_xRadius_yRadius_((corner, self.size), 3*scale, 3*scale)

		context.saveGraphicsState()
		shadow.set()
		thePath.setLineWidth_(scale)
		self.bkgndColor.set()
		thePath.fill()
		kBorderColor.set()
		thePath.stroke()
		context.restoreGraphicsState()
		kLabelTextAttributes[NSForegroundColorAttributeName] = self.textColor
		nsView._drawTextAtPoint(self.text, kLabelTextAttributes, corner+0.5*self.size+geom.Point(0,scale), drawBackground=False)

from bisect import insort

def untangleLabels(labels):
	someContact = False
	for cl in labels:
		cl.reset()
	below = []
	labels.sort(key=lambda l:l.center.y-0.5*l.size.y)
	for cl in labels:
		below_bottom_y = cl.lo().y
		while below and below[0].hi().y < below_bottom_y:
			below.pop(0)
		for candidate in below:
			if cl.touch(candidate):
				someContact = True
				cl.updateSpeed(candidate)
		insort(below, cl)
	if not someContact:
		return False
	for cl in labels:
		if cl.count == 0: continue
		cl.center = cl.center + cl.speed
	return True
