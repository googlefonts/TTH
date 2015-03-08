from controllers import toolController
from models import toolModel
from mojo.events import installTool

reload(toolController)
reload(toolModel)

tthtm = toolModel.TTHToolModel()
installTool(toolController.TTHTool(tthtm))
