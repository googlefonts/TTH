
def autoZones(font):
	baselineZone   = None
	capHeightZone  = None
	xHeightZone    = None
	ascendersZone  = None
	descendersZone = None

	if "O" in font and "H" in font:
		baselineZone = (0, -font["O"].box[1])
		capHeightZone = (font["H"].box[3], font["O"].box[3] - font["H"].box[3])
	if "o" in font:
		xHeightZone = (font["o"].box[3] + font["o"].box[1], - font["o"].box[1])
	if "f" in font and "l" in font:
		if font["l"].box[3] < font["f"].box[3]:
			ascendersZone = (font["l"].box[3], font["f"].box[3] - font["l"].box[3])
		elif font["l"].box[3] == font["f"].box[3]:
			ascendersZone = (font["l"].box[3] + font["o"].box[1] , - font["o"].box[1])
	if "g" in font and "p" in font:
		if font["p"].box[1] > font["g"].box[1]:
			descendersZone = (font["p"].box[1], - (font["g"].box[1] - font["p"].box[1]) )

	uiZones = []
	if baselineZone:
		uiZones.append(makeUIZone('baseline',   False, baselineZone[0],   baselineZone[1]  ))
	if capHeightZone:
		uiZones.append(makeUIZone('cap-height', True,  capHeightZone[0],  capHeightZone[1] ))
	if xHeightZone:
		uiZones.append(makeUIZone('x-height',   True,  xHeightZone[0],    xHeightZone[1]   ))
	if ascendersZone:
		uiZones.append(makeUIZone('ascenders',  True,  ascendersZone[0],  ascendersZone[1] ))
	if descendersZone:
		uiZones.append(makeUIZone('descenders', False, descendersZone[0], descendersZone[1]))
	return uiZones

def makeUIZone(name, top, pos, width):
	return {
			'Name': name,
			'Width': width,
			'top': top,
			'Position': pos,
			'Delta': '',
			'Shift': 0
			}
