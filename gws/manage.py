# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import sys
import os
import json

dep_paths = {}
loaded_modules = []

def read_module_name(cwd):
    module_name = None
    with open(os.path.join(cwd,"settings.json")) as f:
        try:
            settings = json.load(f)
        except:
            raise Exception("Error while parsing the settings JSON file. Please check file setting file.")

    module_name = settings.get("name",None)
    if module_name is None:
        raise Exception("The module name is required. Please check file setting file.")
    
    return module_name

def _update_json(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = _update_json(d.get(k, {}), v)
        elif isinstance(v, list):
            d[k]= d.get(k, []) + v
        else:
            d[k] = v
    return d

def _update_relative_static_paths(dep_rel_path, dep_settings):
    for k in dep_settings:
        if k.endswith("_dir"):
            if not isinstance(dep_settings[k], str):
                raise Exception("Error while parsing setting. Parameter " + k + " must be a string")
            dep_settings[k] = os.path.abspath(os.path.join(dep_rel_path,dep_settings[k]))
    
    for k in dep_settings.get("dirs",{}):
        if not isinstance(dep_settings["dirs"][k], str):
            raise Exception("Error while parsing setting. Parameter " + k + " must be a string")
        dep_settings["dirs"][k] = os.path.abspath(os.path.join(dep_rel_path,dep_settings["dirs"][k]))

    for k in dep_settings.get("app",{}).get("statics",{}):
        dep_settings["app"]["statics"][k] = os.path.abspath(os.path.join(dep_rel_path,dep_settings["app"]["statics"][k]))

    for k in dep_settings.get("app",{}):
        if k in ["scripts","modules","styles"]:
            length = len(dep_settings["app"][k])
            for i in range(length):
                dep_settings["app"][k][i] = os.path.abspath(os.path.join(dep_rel_path,dep_settings["app"][k][i]))
    
    return dep_settings

def _parse_settings(module_cwd: str = None, module_name:str = None, module_settings_file_path:str = None):    
    if module_name in loaded_modules:
        return {}

    loaded_modules.append(module_name)

    if module_cwd is None:
        raise Exception("Paremeter module_cwd is required")
    
    if module_name is None:
        raise Exception("Paremeter module_name is required")

    if not os.path.exists(module_settings_file_path):
        raise Exception("The setting file of module '"+module_name+"' is not found. Please check that file '"+module_settings_file_path+"'.")
        
    with open(module_settings_file_path) as f:
        try:
            settings = json.load(f)
        except:
            raise Exception("Error while parsing the settings JSON file. Please check file.")
    
    import copy
    
    dep_paths[module_name] = [module_name]
    for k in settings["dependencies"]:
        dep_paths[module_name].append(k)

    if settings["dependencies"].get(module_name, None) is None:
        settings["dependencies"][module_name] = "./"

    # recursive load of dependencies
    for dep_name in settings["dependencies"]:
        if dep_name == ":external:":
            for dep_urls in settings["dependencies"][dep_name]:
                dep_cwd = os.path.join(module_cwd,dep_urls)
                settings["dependencies"][dep_name] = os.path.abspath(dep_cwd)
                sys.path.insert(0,dep_cwd) 
        else:
            dep_rel_path = settings["dependencies"][dep_name]
            dep_cwd = os.path.join(module_cwd,dep_rel_path)
            settings["dependencies"][dep_name] = os.path.abspath(dep_cwd)

            #print(dep_cwd)
            
            dep_setting_file = os.path.join(dep_cwd,"./settings.json")

            sys.path.insert(0,dep_cwd)                                 

            if not dep_name == module_name:
                dep_settings = _parse_settings(module_cwd=dep_cwd, module_name=dep_name, module_settings_file_path=dep_setting_file)
                if len(dep_settings) > 0:
                    dep_settings = _update_relative_static_paths(dep_cwd,dep_settings)
                    settings = _update_json(dep_settings, settings)
            else:
                if len(settings) > 0:
                    settings = _update_relative_static_paths(dep_cwd,settings)

    return settings
 
def parse_settings(module_cwd: str = None):
    module_name = read_module_name(module_cwd)
    module_settings_file_path = os.path.join(module_cwd, "settings.json")
    default_settings = {
        "app_dir"       : "./",
        "app_host"      : "localhost",
        "app_port"      : 3000,
        "db_dir"        : "./",
        "db_name"       : "db.sqlite3",
        "is_test"       : False,
        "dependencies"  : {},
        "static_dirs"   : {},
        "__cwd__"       : module_cwd
    }

    settings = _update_json(default_settings, _parse_settings(module_cwd=module_cwd, module_name=module_name, module_settings_file_path=module_settings_file_path))
    settings["dependency_paths"] = dep_paths

    if not os.path.exists(settings.get("db_dir")):
        os.mkdir(settings.get("db_dir"))
    
    return settings

def load_settings(module_cwd: str = None):
    from gws.settings import Settings
    settings = parse_settings(module_cwd)
    Settings.init(settings)
    settings = Settings.retrieve()
    return settings