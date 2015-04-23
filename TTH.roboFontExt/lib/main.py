from mojo.events import installTool
from controllers import RFEventTool

reload(RFEventTool)

installTool(RFEventTool.TTH_RF_EventTool())
