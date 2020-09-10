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
    file_path = os.path.join(cwd,"settings.json")
    with open(file_path) as f:
        try:
            settings = json.load(f)
        except:
            raise Exception(f"Error while parsing the setting JSON file. Please check file setting file '{file_path}'")

    module_name = settings.get("name",None)
    if module_name is None:
        raise Exception(f"The module name is required. Please check file setting file '{file_path}")
    
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

    for k in dep_settings.get("app",{}).get("themes",{}):
        dep_settings["app"]["themes"][k] = os.path.abspath(os.path.join(dep_rel_path,dep_settings["app"]["themes"][k]))

    # for k in dep_settings.get("app",{}):
    #     if k in ["scripts","modules","styles"]:
    #         length = len(dep_settings["app"][k])
    #         for i in range(length):
    #             dep_settings["app"][k][i] = os.path.abspath(os.path.join(dep_rel_path,dep_settings["app"][k][i]))
    
    return dep_settings

# def _parse_themes(settings):
#     themes_settings = {}
#     for k in settings.get("app",{}).get("themes",{}):
#         theme_path = settings["app"]["themes"][k]
#         settings_file_path = os.path.join(theme_path,"settings.json")
#         if not os.path.exists(settings_file_path):
#             raise Exception(f"The setting JSON file of the theme '{k}' does not exists. Expected file path: '{settings_file_path}'")
    
#         with open(settings_file_path) as f:
#             try:
#                 themes_settings = json.load(f)
#             except:
#                 raise Exception(f"Error while parsing the setting JSON file of the themes '{k}'. Please check file setting file '{settings_file_path}'")
    
#     if len(themes_settings) > 0:
#         if len(themes_settings.get("app",{}).get("statics",{})) > 0:
#             if not "scripts" in settings["app"]:
#                 settings["app"]["scripts"] = {}
            
#             for k in themes_settings["app"]["statics"]:
#                 settings["app"]["statics"][k] = themes_settings["app"]["statics"][k]

#         if len(themes_settings.get("app",{}).get("scripts",{})) > 0:
#             if not "scripts" in settings["app"]:
#                 settings["app"]["scripts"] = []
#             settings["app"]["scripts"] = settings["app"]["scripts"] + themes_settings["app"]["scripts"]
            
#         if len(themes_settings.get("app",{}).get("styles",{})) > 0:
#             if not "styles" in settings["app"]:
#                 settings["app"]["styles"] = []
#             settings["app"]["styles"] = settings["app"]["styles"] + themes_settings["app"]["styles"]
    
#     return settings

def _parse_settings(module_cwd: str = None, module_name:str = None, module_settings_file_path:str = None):    
    if module_name in loaded_modules:
        return {}

    loaded_modules.append(module_name)

    if module_cwd is None:
        raise Exception("Paremeter module_cwd is required")
    
    if module_name is None:
        raise Exception("Paremeter module_name is required")

    if not os.path.exists(module_settings_file_path):
        raise Exception(f"The setting file of module '{module_name}' is not found. Please check file '{module_settings_file_path}'")
        
    with open(module_settings_file_path) as f:
        try:
            settings = json.load(f)
        except:
            raise Exception(f"Error while parsing the setting JSON file. Please check file '{module_settings_file_path}'")
    
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
                    #dep_settings = _parse_themes(dep_settings)
                    dep_settings = _update_relative_static_paths(dep_cwd,dep_settings)
                    settings = _update_json(dep_settings, settings)
            else:
                if len(settings) > 0:
                    #settings = _parse_themes(settings)
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