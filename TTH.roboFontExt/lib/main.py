
print "\nInstalling TTH..."

from mojo.events import installTool

from models import TTHTool
reload(TTHTool)

from controllers import RFEventTool
reload(RFEventTool)

installTool(RFEventTool.TTH_RF_EventTool())

if TTHTool.uniqueInstance._printLoadings: print "[TTH installed]"
