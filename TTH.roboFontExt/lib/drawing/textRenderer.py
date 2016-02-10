
from objc import allocateBuffer
from AppKit import *
import Quartz as QZ
from mojo.UI import *
try:
	import freetype as FT
except:
	print 'ERROR: freetype not installed'

grayCS = QZ.CGColorSpaceCreateDeviceGray()
rgbCS = QZ.CGColorSpaceCreateDeviceRGB()

kUTTypePNG = "public.png"

class TRGlyphData(object):
	def __init__(self):
		self.image = None
		self.contours_points_and_tags = None
		self.bezier_paths = None
		self.bitmap = None
		self.advance = None

class TextRenderer(object):

	def __init__(self, face_path, renderMode, cacheContours = True):
		try:
			self.face = FT.Face(face_path)
			# the glyph slot in the face, from which we extract the images
			# (contour) of requested glyphs, before storing them in the
			# cache
			self.slot = self.face.glyph
		except:
			self.face = None
			print 'ERROR: FreeType could not load temporary font', face_path
		# a dictionary mapping text size in pixel to  dict index->TRGlyphData
		# storing the glyph's image/bitmap/advance/... already loaded.
		self.caches = {}
		# The cache for the current text pixel-size
		self.cache = None
		# Should we keep the contours in the cache?
		self.cacheContours = cacheContours
		# current text pixel-size
		self.curSize = 0
		# drawing position
		self.pen = (0,0)
		self.set_cur_size(9)

		self.outlinecolor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.4, .8, 1, 1)

		self.render_mode = FT.FT_RENDER_MODE_NORMAL
		self.render_func = drawBitmapGray
		self.make_bitmap_func = makeBitmapGray
		if renderMode == 'Monochrome':
			self.render_mode = FT.FT_RENDER_MODE_MONO
			self.render_func = drawBitmapMono
			self.make_bitmap_func = makeBitmapMono
		elif renderMode == 'Subpixel':
			self.render_mode = FT.FT_RENDER_MODE_LCD
			self.render_func = drawBitmapSubPixelColor
			self.make_bitmap_func = makeDesaturatedBitmapSubpixel

		self.load_mode = FT.FT_LOAD_DEFAULT
		#self.load_mode = FT.FT_LOAD_RENDER
		if renderMode == 'Monochrome':
			self.load_mode = self.load_mode | FT.FT_LOAD_TARGET_MONO
		elif renderMode == 'Subpixel':
			self.load_mode = self.load_mode | FT.FT_LOAD_TARGET_LCD
		else:
			self.load_mode = self.load_mode | FT.FT_LOAD_TARGET_NORMAL

	def isOK(self):
		return self.face != None

	def __del__(self):
		self.face = None
		self.slot = None
		self.cache = None

	def set_pen(self, p):
		self.pen = p

	def get_pen(self):
		return self.pen

	def set_cur_size(self, size):
		if size < 4:
			self.curSize = 4
		else:
			self.curSize = int(size)
		# select the cache of proper size
		if self.curSize not in self.caches:
			self.caches[self.curSize] = {}
		self.cache = self.caches[self.curSize]
		self.face.set_pixel_sizes(0, self.curSize)

	def render_text_with_scale_and_alpha(self, text, scale, alpha):
		if self.face == None: return
		gl = [self.face.get_char_index(c) for c in text]
		return self.render_indexed_glyph_list(gl, scale, alpha)

	def render_text(self, text):
		return self.render_text_with_scale_and_alpha(text, 1, 1.0)

	def save_indexed_glyph_as_png(self, index, extent, path):
		if self.render_mode == FT.FT_RENDER_MODE_LCD:
			bmg, bitmap = self.get_glyph_bitmap(index)
		else:
			bmg = self.get_glyph_bitmap(index)
			bitmap = self.make_bitmap_func(bmg)

		advance = (self.get_advance(index)[0]+32)/64
		bm = bmg.bitmap
		left = bmg.left
		bottom = bmg.top - bm.rows - extent[1]
		saveAsPNG(bitmap, left, bottom, advance, extent, path)

	def save_named_glyph_as_png(self, gName, extent, path):
		self.save_indexed_glyph_as_png(self.face.get_name_index(gName), extent, path)

	def render_indexed_glyph_list(self, idxes, scale=1, alpha=1.0):
		if self.face == None: return
		ox, oy = self.pen
		x = ox
		try:
			for index in idxes:
				self.render_func(self.get_glyph_bitmap(index), scale, x, oy, alpha)
				x += int((self.get_advance(index)[0]+32)/64)*scale
		except:
			pass
		self.pen = x, oy
		return (x - ox, 0)

	def names_to_indices(self, names):
		return [self.face.get_name_index(name) for name in names]

	def render_named_glyph_list(self, nameList, scale=1, alpha=1.0):
		indices = self.names_to_indices(nameList)
		return self.render_indexed_glyph_list(indices, scale, alpha)

	def get_advance(self, index):
		try:
			return self.cache[index].advance
		except:
			self.get_glyph_image(index)
			return self.cache[index].advance

	def get_char_advance(self, char):
		return self.get_advance(self.face.get_char_index(char))

	def get_name_advance(self, name):
		return self.get_advance(self.face.get_name_index(name))

	def get_glyph_contours_points_and_tags(self, index):
		try:
			return self.cache[index].contours_points_and_tags
		except:
			self.get_glyph_image(index)
			return self.cache[index].contours_points_and_tags

	def get_char_contours_points_and_tags(self, char):
		return self.get_glyph_contours_points_and_tags(self.face.get_char_index(char))

	def get_glyph_image(self, index):
		# a glyph image (contours) is requested. If not in the cache,
		# we load it with freetype and save it in the cache and return
		# it
		try:
			return self.cache[index].image
		except:
			glyphCache = TRGlyphData()
			self.cache[index] = glyphCache
			self.face.set_pixel_sizes(0, int(self.curSize))
			try:
				self.face.load_glyph(index, self.load_mode)
			except FT.FT_Exception as e:
				print "[FT.load_glyph({}) ERROR] {}".format(index, e)
				return None
			result = self.slot.get_glyph() # this returns a copy
			glyphCache.image = result
			glyphCache.advance = (self.slot.advance.x, self.slot.advance.y)
			if self.cacheContours:
				pts = list(self.slot.outline.points) # copy
				cts = list(self.slot.outline.contours) # copy
				tgs = list(self.slot.outline.tags) # copy
				glyphCache.contours_points_and_tags = (cts, pts, tgs)
			return result

	def get_char_image(self, char):
		# convert unicode-char to glyph-index and then call get_glyph_image
		return self.get_glyph_image(self.face.get_char_index(char))

	def get_name_bitmap(self, name):
		return self.get_glyph_bitmap(self.face.get_name_index(name))

	def get_glyph_bitmap(self, index):
		# a glyph bitmap (pixel buffer) is requested. If not in the cache,
		# we render it with freetype and save it in the cache and return
		# it
		image = self.get_glyph_image(index)
		glyphCache = self.cache[index]
		if glyphCache.bitmap == None:
			result = image.to_bitmap(self.render_mode, 0)
			if self.render_mode == FT.FT_RENDER_MODE_LCD:
				result = (result, makeDesaturatedBitmapSubpixel(result))
			#print self.get_glyph_image(index).format
			glyphCache.bitmap = result
		return glyphCache.bitmap

	def isSubPixel(self):
		return (self.render_mode == FT.FT_RENDER_MODE_LCD)

	def get_char_bitmap(self, char):
		# convert unicode-char to glyph-index and then call get_glyph_bitmap
		return self.get_glyph_bitmap(self.face.get_char_index(char))

	def drawOutline(self, scale, paths, thickness):
		if paths is None:
			return
		self.outlinecolor.set()
		for p  in paths:
			p.setLineWidth_(scale*thickness)
			p.stroke()

	def drawOutlineOfChar(self, scale, pitch, char, thickness):
		self.drawOutline(scale, self.getBezierPathOfChar(scale, pitch, char), thickness)

	def drawOutlineOfName(self, scale, pitch, name, thickness):
		self.drawOutline(scale, self.getBezierPathOfName(scale, pitch, name), thickness)

	def getBezierPathOfName(self, scale, pitch, name):
		index = self.face.get_name_index(name)
		return self.getBezierPath(scale, pitch, index)

	def getBezierPathOfChar(self, scale, pitch, char):
		index = self.face.get_char_index(char)
		return self.getBezierPath(scale, pitch, index)

	def getBezierPath(self, scale, pitch, index):
		try:
			bp = self.cache[index].bezier_paths
			if bp != None: return bp
		except:
			pass

		(contours, points, itags) = self.get_glyph_contours_points_and_tags(index)
		if len(contours) == 0:
			return None
		adaptedOutline_points = [(int(pitch*p[0]/64), int(pitch*p[1]/64)) for p in points]
		paths = []
		pathContour = NSBezierPath.bezierPath()
		start = 0
		for end in contours:
			points	= adaptedOutline_points[start:end+1]
			points.append(points[0])
			tags	= itags[start:end+1]
			tags.append(tags[0])

			segments = [ [points[0],], ]

			for j in range(1, len(points) ):
				segments[-1].append(points[j])
				if tags[j] & (1 << 0) and j < (len(points)-1):
					segments.append( [points[j],] )
			pathContour.moveToPoint_((points[0][0], points[0][1]))
			for segment in segments:
				if len(segment) == 2:
					pathContour.lineToPoint_(segment[1])
				else:
					onCurve = segment[0]
					for i in range(1,len(segment)-2):
						A,B = segment[i], segment[i+1]
						nextOn = ((A[0]+B[0])/2.0, (A[1]+B[1])/2.0)
						antenne1 = ((onCurve[0] + 2 * A[0]) / 3.0 , (onCurve[1] + 2 * A[1]) / 3.0)
						antenne2 = ((nextOn[0] + 2 * A[0]) / 3.0 , (nextOn[1] + 2 * A[1]) / 3.0)
						pathContour.curveToPoint_controlPoint1_controlPoint2_(nextOn, antenne1, antenne2)
						onCurve = nextOn
					nextOn = segment[-1]
					A = segment[-2]
					antenne1 = ((onCurve[0] + 2 * A[0]) / 3.0 , (onCurve[1] + 2 * A[1]) / 3.0)
					antenne2 = ((nextOn[0] + 2 * A[0]) / 3.0 , (nextOn[1] + 2 * A[1]) / 3.0)
					pathContour.curveToPoint_controlPoint1_controlPoint2_(nextOn, antenne1, antenne2)
			start = end+1
			paths.append(pathContour)
		self.cache[index].bezier_paths = paths
		return paths

# DRAWING FUNCTIONS

def saveAsPNG(cgimg, left, bottom, advance, extent, path, debug=False):
	# There's a weirdness with kCGImageAlphaNone and CGBitmapContextCreate
	# see Supported Pixel Formats in the QZ 2D Programming Guide
	# Creating a Bitmap Graphics Context section
	# only RGB 8 bit images with alpha of kCGImageAlphaNoneSkipFirst, kCGImageAlphaNoneSkipLast, kCGImageAlphaPremultipliedFirst,
	# and kCGImageAlphaPremultipliedLast, with a few other oddball image kinds are supported
	# The images on input here are likely to be png or jpeg files
	#alphaInfo = QZ.CGImageGetAlphaInfo(cgimg)
	#if alphaInfo == QZ.kCGImageAlphaNone:
	#	print 'Alpha None'
	#	alphaInfo = QZ.kCGImageAlphaNoneSkipLast

	height = extent[0] - extent[1]
	width  = QZ.CGImageGetWidth(cgimg)

	if left < 0:
		advance -= left
		left = 0
	if left + width > advance:
		advance = left + width

	#bitsPerComponent = QZ.CGImageGetBitsPerComponent(cgimg)
	# Build a bitmap context that's the size of the thumbRect
	port = QZ.CGBitmapContextCreate(None,
					advance,  # width
					height, # height
					8,#bitsPerComponent,
					4 * advance, # rowbytes
					rgbCS,
					QZ.kCGImageAlphaPremultipliedLast)
					#QZ.kCGImageAlphaNoneSkipLast)

	# Draw into the context, this scales the image
	destRect = QZ.CGRectMake(left, bottom, width, QZ.CGImageGetHeight(cgimg))
	fullRect = QZ.CGRectMake(0, 0, advance, height)
	QZ.CGContextSetFillColor(port, [1.0, 1.0, 1.0, 1.0])
	QZ.CGContextFillRect(port, fullRect)
	QZ.CGContextSetBlendMode(port, QZ.kCGBlendModeDifference)
	QZ.CGContextSetInterpolationQuality(port, QZ.kCGInterpolationNone)
	QZ.CGContextDrawImage(port, destRect, cgimg);
	QZ.CGContextSetBlendMode(port, QZ.kCGBlendModeNormal)

	# Get an image from the context
	opaque = QZ.CGBitmapContextCreateImage(port);

	maskCtxt = QZ.CGBitmapContextCreate(None,
					advance, height, # width and height
					8, # really needs to always be 8
					1 * advance, # rowbytes
					grayCS, 0)
	QZ.CGContextSetFillColor(maskCtxt, [1.0, 1.0])#, 1.0, 1.0])
	QZ.CGContextFillRect(maskCtxt, fullRect)
	QZ.CGContextSetBlendMode(maskCtxt, QZ.kCGBlendModeDifference)
	QZ.CGContextDrawImage(maskCtxt, fullRect, opaque);
	QZ.CGContextSetBlendMode(maskCtxt, QZ.kCGBlendModeNormal)

	mask = QZ.CGBitmapContextCreateImage(maskCtxt);

	masked = QZ.CGImageCreateWithMask(opaque, mask)

	if debug:
		url = NSURL.fileURLWithPath_(path+'opaque.png')
		destination = QZ.CGImageDestinationCreateWithURL(url, kUTTypePNG, 1, None)
		QZ.CGImageDestinationAddImage(destination, opaque, None)
		QZ.CGImageDestinationFinalize(destination)

		url = NSURL.fileURLWithPath_(path+'mask.png')
		destination = QZ.CGImageDestinationCreateWithURL(url, kUTTypePNG, 1, None)
		QZ.CGImageDestinationAddImage(destination, mask, None)
		QZ.CGImageDestinationFinalize(destination)

	#QZ.CGContextSetBlendMode(port, QZ.kCGBlendModeNormal)
	QZ.CGContextClearRect(port, fullRect)
	#QZ.CGContextSetInterpolationQuality(port, QZ.kCGInterpolationNone)
	QZ.CGContextDrawImage(port, fullRect, masked);
	final = QZ.CGBitmapContextCreateImage(port);

	url = NSURL.fileURLWithPath_(path+'.png')
	destination = QZ.CGImageDestinationCreateWithURL(url, kUTTypePNG, 1, None)
	QZ.CGImageDestinationAddImage(destination, final, None)
	QZ.CGImageDestinationFinalize(destination)

def makeBitmapMono(bmg):
	# 'bmg' stands for BitMapGlyph, a data structure from freetype.
	bm = bmg.bitmap
	numBytes = bm.rows * bm.pitch
	if numBytes == 0:
		return None
	buf = allocateBuffer(numBytes)
	ftBuffer = bm._FT_Bitmap.buffer
	for i in range(numBytes):
		buf[i] = ftBuffer[i]

	provider = QZ.CGDataProviderCreateWithData(None, buf, numBytes, None)

	cgimg = QZ.CGImageCreate(
			bm.width,
			bm.rows,
			1, # bit per component
			1, # size_t bitsPerPixel,
			bm.pitch, # size_t bytesPerRow,
			grayCS, # CGColorSpaceRef colorspace,
			QZ.kCGBitmapByteOrderDefault, # CGBitmapInfo bitmapInfo,
			provider, # CGDataProviderRef provider,
			None, # const CGFloat decode[],
			False, # bool shouldInterpolate,
			QZ.kCGRenderingIntentDefault # CGColorRenderingIntent intent
			)
	return cgimg

def drawBitmapMono(bmg, scale, advance, height, alpha):
	bm = bmg.bitmap
	cgimg = makeBitmapMono(bmg)
	destRect = QZ.CGRectMake(bmg.left*scale + advance, (bmg.top-bm.rows)*scale + height, bm.width*scale, bm.rows*scale)

	port = NSGraphicsContext.currentContext().graphicsPort()
	if alpha < 1:
		QZ.CGContextSetAlpha(port, alpha)
	QZ.CGContextSetBlendMode(port, QZ.kCGBlendModeDifference)
	QZ.CGContextSetInterpolationQuality(port, QZ.kCGInterpolationNone)
	QZ.CGContextDrawImage(port, destRect, cgimg)
	if alpha < 1:
		QZ.CGContextSetAlpha(port, 1)
	QZ.CGContextSetBlendMode(port, QZ.kCGBlendModeNormal)

def makeBitmapGray(bmg):
	bm = bmg.bitmap
	numBytes = bm.rows * bm.pitch
	if numBytes == 0:
		return None
	buf = allocateBuffer(numBytes)
	ftBuffer = bm._FT_Bitmap.buffer
	for i in range(numBytes):
		buf[i] = ftBuffer[i]
	provider = QZ.CGDataProviderCreateWithData(None, buf, numBytes, None)
	cgimg = QZ.CGImageCreate(
			bm.width,
			bm.rows,
			8, # bit per component
			8, # size_t bitsPerPixel,
			bm.pitch, # size_t bytesPerRow,
			grayCS, # CGColorSpaceRef colorspace,
			QZ.kCGBitmapByteOrderDefault, # CGBitmapInfo bitmapInfo,
			provider, # CGDataProviderRef provider,
			None, # const CGFloat decode[],
			False, # bool shouldInterpolate,
			QZ.kCGRenderingIntentDefault # CGColorRenderingIntent intent
			)
	return cgimg

def drawBitmapGray(bmg, scale, advance, height, alpha):
	bm = bmg.bitmap
	cgimg = makeBitmapGray(bmg)
	destRect = QZ.CGRectMake(bmg.left*scale + advance, (bmg.top-bm.rows)*scale + height, bm.width*scale, bm.rows*scale)

	port = NSGraphicsContext.currentContext().graphicsPort()
	if alpha < 1.0:
		QZ.CGContextSetAlpha(port, alpha)
	QZ.CGContextSetBlendMode(port, QZ.kCGBlendModeDifference)
	QZ.CGContextSetInterpolationQuality(port, QZ.kCGInterpolationNone)
	QZ.CGContextDrawImage(port, destRect, cgimg)
	if alpha < 1.0:
		QZ.CGContextSetAlpha(port, 1.0)
	QZ.CGContextSetBlendMode(port, QZ.kCGBlendModeNormal)

def makeDesaturatedBitmapSubpixel(bmg):
	bm = bmg.bitmap
	pixelWidth = int(bm.width/3)
	numBytes = 4 * bm.rows * pixelWidth
	if numBytes == 0:
		return None
	buf = allocateBuffer(numBytes)
	ftBuffer = bm._FT_Bitmap.buffer
	pos = 0
	for i in range(bm.rows):
		source = bm.pitch * i
		for j in range(pixelWidth):
			ftSub = ftBuffer[source:source+3];
			gray = (1.0 - 0.4) * sum([x*y for x,y in zip([0.3086, 0.6094, 0.0820], ftSub)])
			buf[pos:pos+3] = [int(0.4 * x + gray) for x in ftSub]
			buf[pos+3] = 0
			pos += 4
			source += 3
	provider = QZ.CGDataProviderCreateWithData(None, buf, numBytes, None)
	cgimg = QZ.CGImageCreate(
			pixelWidth,
			bm.rows,
			8, # bit per component
			32, # size_t bitsPerPixel,
			4 * pixelWidth, # size_t bytesPerRow,
			rgbCS, # CGColorSpaceRef colorspace,
			QZ.kCGImageAlphaNone, # CGBitmapInfo bitmapInfo,
			#QZ.kCGBitmapByteOrderDefault, # CGBitmapInfo bitmapInfo,
			provider, # CGDataProviderRef provider,
			None, # const CGFloat decode[],
			False, # bool shouldInterpolate,
			QZ.kCGRenderingIntentDefault # CGColorRenderingIntent intent
			)
	return cgimg

def drawBitmapSubPixelColor((bmg, cgimg), scale, advance, height, alpha):
	bm = bmg.bitmap
	pixelWidth = int(bm.width/3)
	destRect = QZ.CGRectMake(bmg.left*scale + advance, (bmg.top-bm.rows)*scale + height, pixelWidth*scale, bm.rows*scale)
	port = NSGraphicsContext.currentContext().graphicsPort()
	if alpha < 1:
		QZ.CGContextSetAlpha(port, alpha)
	QZ.CGContextSetBlendMode(port, QZ.kCGBlendModeDifference)
	QZ.CGContextSetInterpolationQuality(port, QZ.kCGInterpolationNone)
	QZ.CGContextDrawImage(port, destRect, cgimg)
	QZ.CGContextSetBlendMode(port, QZ.kCGBlendModeNormal)
	if alpha < 1:
		QZ.CGContextSetAlpha(port, 1)
