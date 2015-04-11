from mojo.events import installTool
from controllers import toolController

reload(toolController)

installTool(toolController.TTH_RF_EventTool())
