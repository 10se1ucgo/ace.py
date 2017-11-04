import importlib


def load_scripts(protocol, config: dict):
    modules = []
    for plugin in config["scripts"]:
        module = importlib.import_module(f"acescripts.{plugin}")
        modules.append(module)
        globals()[plugin] = module

    for module in modules:
        module.init(protocol, config)
