import abc
import importlib
from typing import Dict

class Script(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def deinit(self):
        return


class ScriptLoader:
    def __init__(self, protocol, config: dict):
        self.protocol = protocol
        self.config = config
        self.scripts: Dict[str, Script] = {}

    def load_scripts(self, reload=False):
        self.unload_scripts()

        for script_name in self.config["scripts"]:
            module = importlib.import_module(f"acescripts.{script_name}")
            if reload:
                module = importlib.reload(module)
            script = module.init(self.protocol, self.config)
            if not isinstance(script, Script):
                raise TypeError(f"Script {script_name} did not return a Script instance!")
            self.scripts[script_name] = script

    def unload_scripts(self):
        for script in self.scripts.values():
            script.deinit()
        self.scripts = {}
