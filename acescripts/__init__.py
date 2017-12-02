import importlib
from typing import Dict
from collections import OrderedDict

from aceserver import util, protocol as proto


class Script:
    def __init__(self, protocol):
        self.protocol: 'proto.ServerProtocol' = protocol
        module_name = ''.join(str(self.__module__).split(".")[1:])  # strip package name
        self.config: dict = self.protocol.config.get(f"scripts.{module_name}", {})

    def deinit(self):
        pass


class ScriptLoader:
    def __init__(self, protocol):
        self.protocol = protocol
        self.scripts: Dict[str, Script] = OrderedDict()
        self.on_scripts_loaded = util.Event()
        self.on_scripts_unloaded = util.Event()

    def load_scripts(self, reload=False):
        self.unload_scripts()

        for script_name in self.protocol.config["scripts"]:
            module = importlib.import_module(f"acescripts.{script_name}")
            if reload:
                module = importlib.reload(module)
            script = module.init(self.protocol)
            if not isinstance(script, Script):
                raise TypeError(f"Script {script_name} did not return a Script instance!")
            self.scripts[script_name] = script
        self.on_scripts_loaded(self.scripts)

    def unload_scripts(self):
        for script in reversed(self.scripts.values()):
            script.deinit()
        self.on_scripts_unloaded(self.scripts)
        self.scripts = OrderedDict()

    def get(self, name: str):
        return self.scripts.get(name)
