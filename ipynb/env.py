# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import sys
import os

def activate( brick = "main" ):
    __cdir__ = os.path.dirname(os.path.abspath(__file__))
    
    # add gws to sys path
    def set_path(rel_gws_path):
        for _ in range(0,10):
            rel_gws_path = os.path.join("../", rel_gws_path)
            abs_gws_path = os.path.join(__cdir__, rel_gws_path)
            if os.path.exists(abs_gws_path):
                sys.path.append(abs_gws_path)
                return True
            
    is_set =  set_path("./.gws/bricks/gws") or set_path("./gws/bricks/gws")
    if not is_set:
        raise Exception("Cannot find the base gws brick")
    
    # load settings
    if brick == "main":
        rel_brick_dir = f"./main/{brick}"
    else:
        rel_brick_dir = f"./bricks/{brick}"
    
    OK = False
    for _ in range(0,10):
        rel_brick_dir = os.path.join("../", rel_brick_dir)
        abs_brick_dir = os.path.join(__cdir__, rel_brick_dir)
        
        if os.path.exists(abs_brick_dir):
            from gws.manage import load_settings
            load_settings(abs_brick_dir)
            OK = True
            break
    
    if not OK:
        raise Exception(f"Could not activate the lab")
            
    # activate local db
    from gws.settings import Settings
    settings = Settings.retrieve()
    settings.data["is_test"] = True        
    settings.save()
    
    # return current dir
    return __cdir__
