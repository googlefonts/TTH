import controller
import TTHToolModel
from mojo.events import installTool

reload(controller)
reload(TTHToolModel)

tthtm = TTHToolModel.TTHToolModel()
installTool(controller.TTHTool(tthtm))
