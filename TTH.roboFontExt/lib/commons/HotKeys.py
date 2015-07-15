
from vanilla import TextBox, Button, EditText
from mojo.extensions import getExtensionDefault, setExtensionDefault

DefaultHotKeyPrefix = "com.sansplomb.TTH.HotKey."

kTTH_HotKey_Select_Align_Tool          = "Select Align Tool"
kTTH_HotKey_Select_Single_Link_Tool    = "Select SingleLink Tool"
kTTH_HotKey_Select_Double_Link_Tool    = "Select DoubleLink Tool"
kTTH_HotKey_Select_Interpolate_Tool    = "Select Interpolate Tool"
kTTH_HotKey_Select_Middle_Delta_Tool   = "Select Middle Delta Tool"
kTTH_HotKey_Select_Final_Delta_Tool    = "Select Final Delta Tool"
kTTH_HotKey_Select_Selection_Tool      = "Select Selection Tool"
kTTH_HotKey_Switch_Show_Outline        = "Switch Show Outline"
kTTH_HotKey_Switch_Show_Bitmap         = "Switch Show Bitmap"
kTTH_HotKey_Switch_Show_Grid           = "Switch Show Grid"
kTTH_HotKey_Switch_Show_Preview_In_GW  = "Switch Show Preview In Glyph Window"
kTTH_HotKey_Switch_Show_Center_Pixels  = "Switch Show Center Pixels"
kTTH_HotKey_Switch_Rounding            = "Switch Rounding"
kTTH_HotKey_Change_Axis                = "Change Axis"
kTTH_HotKey_Change_Alignment           = "Change Alignment"
kTTH_HotKey_Change_Size_Up             = "Change Size Up"
kTTH_HotKey_Change_Size_Down           = "Change Size Down"
kTTH_HotKey_Change_Preview_Mode        = "Change Preview Mode"

hotKeyDefaults = [
        (kTTH_HotKey_Select_Align_Tool, 'a'),
        (kTTH_HotKey_Select_Single_Link_Tool, 's'),
        (kTTH_HotKey_Select_Double_Link_Tool, 'd'),
        (kTTH_HotKey_Select_Interpolate_Tool, 'i'),
        (kTTH_HotKey_Select_Middle_Delta_Tool, 'm'),
        (kTTH_HotKey_Select_Final_Delta_Tool, 'f'),
        (kTTH_HotKey_Select_Selection_Tool, 't'),
        (kTTH_HotKey_Switch_Show_Outline, 'o'),
        (kTTH_HotKey_Switch_Show_Bitmap, 'B'),
        (kTTH_HotKey_Switch_Show_Grid, 'G'),
        (kTTH_HotKey_Switch_Show_Preview_In_GW, 'P'),
        (kTTH_HotKey_Switch_Show_Center_Pixels, 'c'),
        (kTTH_HotKey_Switch_Rounding, 'R'),
        (kTTH_HotKey_Change_Axis, 'hvS'),
        (kTTH_HotKey_Change_Alignment, 'A'),
        (kTTH_HotKey_Change_Size_Up, '+='),
        (kTTH_HotKey_Change_Size_Down, '-'),
        (kTTH_HotKey_Change_Preview_Mode, 'p'),
        ]

def removeSpace(s):
	for c in ' \t':
		s = ''.join(s.split(c))
	return s

gHotKeys = {}

for keyID, default in hotKeyDefaults:
    key = getExtensionDefault(DefaultHotKeyPrefix + removeSpace(keyID), fallback = default)
    setExtensionDefault(DefaultHotKeyPrefix + removeSpace(keyID), key)
    for c in key: # for each character
        #print c,"-->",keyID
        gHotKeys[c] = keyID

class HotKeyPrefChanger(object):
	def __init__(self, parent, top, hotKeyID):
		self.hotKeyID = hotKeyID
		self.attrName = removeSpace(hotKeyID)
                keys = getExtensionDefault(DefaultHotKeyPrefix + self.attrName, fallback = '')
		# label
		textLabel = TextBox((10, top, 250, 18), hotKeyID, sizeStyle='small')
		labelAttrName = "hotKeyDescription_" + self.attrName
		parent.__setattr__(labelAttrName, textLabel)
		# hotkey
		self.hotText = EditText((-150, top, 60, 18), sizeStyle='small', continuous=False, callback=self.edit)
		self.hotText.set(keys)
		hotAttrName = "hotKeyText_" + self.attrName
		parent.__setattr__(hotAttrName, self.hotText)
		# reset button
		but = Button((-80, top, 70, 18), "Reset", sizeStyle = "small", callback=self.reset)
		butAttrName = "hotKeyReset_" + self.attrName
		parent.__setattr__(butAttrName, but)

	def reset(self, sender):
		pass#self.hotText.set(self.default)

        def edit(self, sender):
            defKey = DefaultHotKeyPrefix + self.attrName
            curKeys = getExtensionDefault(defKey, fallback = '')
            wish = sender.get()
            newKeys = []
            for c in wish:
                if c in [' ', '\t', '\n', '\r']: continue
                h = gHotKeys.get(c, None)
                if (h is None) or (h == self.attrName):
                    newKeys.append(c)
            if newKeys == []:
                sender.set(''.join(curKeys))
                return
            for c in curKeys:
                if c not in newKeys:
                    del gHotKeys[c]
            for c in newKeys:
                gHotKeys[c] = self.hotKeyID
            s = ''.join(newKeys)
            setExtensionDefault(defKey, s)
            sender.set(s)

def fillBox(box):
    changers = []
    top = 10
    for keyID, default in hotKeyDefaults:
        changers.append(HotKeyPrefChanger(box, top, keyID))
        top += 25
    return changers, top
