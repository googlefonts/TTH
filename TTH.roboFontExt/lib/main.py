from controllers import toolController
from models import toolModel
from mojo.events import installTool

reload(toolController)
reload(toolModel)

TTHToolModel = toolModel.TTHToolModel()
installTool(toolController.TTHTool(TTHToolModel))
