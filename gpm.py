# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import click
import git
import os
import sys
import json
import requests
import json
import subprocess
import shutil
import pip
import urllib
import re
import glob
from cryptography.fernet import Fernet

__cdir__ = os.path.dirname(os.path.abspath(__file__))

# ####################################################################
#
# GPM class
#
# ####################################################################

class GPM():
    """
    Package manager
    """
    config = []

    def __init__(self, gws_workspace, user_workspace, shallow=True):
        self._read_config()
        self.config["gws_workspace"] = gws_workspace
        self.config["user_workspace"] = user_workspace
        self.config["shallow"] = self.config.get("shallow", shallow)

    # -- C -- 

    def create_wks_dirs(self, workspace, skip_main = False):
        for k in self.__structure:
            if k == "main" and skip_main:
                continue

            d = os.path.join(workspace, k)
            if not os.path.exists(d):
                os.makedirs(d)
            #else:
            #    print(f"Path {d} already exists")

    # -- D --

    def decrypt_message(self, encrypted_message):
        """
        Decrypts an encrypted message
        """
        key = self.load_key()
        f = Fernet(key)
        decrypted_message = f.decrypt(encrypted_message.encode())
        return decrypted_message.decode()

    # -- E --

    def encrypt_message(self, message):
        """
        Encrypts a message
        """
        if not os.path.exists(self.__public_key_file_path):
            self.generate_key()

        key = self.load_key()
        encoded_message = message.encode()
        f = Fernet(key)
        encrypted_message = f.encrypt(encoded_message)
        return encrypted_message.decode()

    # -- G --

    def get_gws_workspace(self):
        if "gws_workspace" in self.config:
            return self.config["gws_workspace"]
        else:
            return ""

    def get_user_workspace(self):
        if "user_workspace" in self.config:
            return self.config["user_workspace"]
        else:
            return ""

    def get_repo_dir(self, repo_name):
        file_path = os.path.join(self.get_gws_workspace(), "bricks", repo_name)
        if os.path.exists(file_path):
            return file_path, "brick", "gws"

        file_path = os.path.join(self.get_gws_workspace(), "externs", repo_name)
        if os.path.exists(file_path):
            return file_path, "externs", "gws"

        file_path = os.path.join(self.get_user_workspace(), "bricks", repo_name)
        if os.path.exists(file_path):
            return file_path, "brick", "user"

        file_path = os.path.join(self.get_user_workspace(), "externs", repo_name)
        if os.path.exists(file_path):
            return file_path, "externs", "user"

        return None, None, None

    def generate_key(self):
        """
        Generates a key and save it into a file
        """
        key = Fernet.generate_key()
        with open(self.__public_key_file_path, "wb") as f:
            f.write(key)

    # -- I --

    def is_ready(self) -> bool:
        return os.path.exists(self.__config_file_path)

    def install_gws(self):
        self.__is_pulled = []
        if self.get_gws_workspace().startswith("/"):
            self.create_wks_dirs(self.get_gws_workspace(), skip_main=True)
            repos = self.get_gws_bricks()
            if not repos:
                repos = { "biox": "DEFAULT_ORIGIN" }
            self.pull(self.get_gws_workspace(), repos=repos)

            #copy notebooks files
            src_files = glob.glob(os.path.join(__cdir__, "./ipynb/**"))
            dest_dir = os.path.join(self.get_gws_workspace(), "./notebooks")
            for src in src_files:
                dst = os.path.join(dest_dir, src.split("/")[-1])
                shutil.copy2(src, dst)

    def install_user(self):
        self.__is_pulled = []
        if self.get_user_workspace().startswith("/"):
            self.create_wks_dirs(self.get_user_workspace(), skip_main=False)
            repos = { 
                "skeleton": "DEFAULT_ORIGIN",
                **self.get_user_bricks()
            }

            self.pull(self.get_user_workspace(), repos=repos)
            self._install_user_main()

            #copy notebooks files
            src_files = glob.glob(os.path.join(__cdir__, "./ipynb/**"))
            dest_dir = os.path.join(self.get_user_workspace(), "./notebooks")
            for src in src_files:
                dst = os.path.join(dest_dir, src.split("/")[-1])
                shutil.copy2(src, dst)

    def _install_user_main(self):
        skeleton_dir = os.path.join(self.get_user_workspace(), "bricks", "skeleton")
        dest_dir = os.path.join(self.get_user_workspace(), "main", self.lab_name)

        if not os.path.exists(dest_dir):
            shutil.copytree(
                skeleton_dir, 
                dest_dir
            )

            # rename module
            shutil.move(
                os.path.join(dest_dir, "skeleton"), 
                os.path.join(dest_dir, self.lab_name)
            )

            # remove .git folder
            shutil.rmtree(os.path.join(dest_dir, ".git"))

        # update settings.json
        settings_file = os.path.join(dest_dir, "settings.json")
        with open(settings_file, 'r') as f:
            settings = json.load(f)
            settings["name"]                = self.config["lab"].get("name", "main")
            settings["uri"]                 = self.config["lab"].get("uri", "")
            settings["token"]               = self.config["lab"].get("token", "")
            settings["work_dir"]            = self.config["lab"].get("work_dir", "")
            settings["host"]                = self.config["lab"].get("host", "0.0.0.0")
            settings["virtual_host"]        = self.config["lab"].get("virtual_host", "lab.test.gencovery.io")
   
            settings["central"]             = {}
            settings["central"]["api_key"]  = self.config["lab"].get("central",{}).get("api_key", "")
            settings["central"]["api_url"]  = self.config["lab"].get("central",{}).get("api_url", "")

            settings["owner"]                = {}
            settings["owner"]["uri"]         = self.config["lab"]["owner"].get("uri", "")
            settings["owner"]["email"]       = self.config["lab"]["owner"].get("email", "admin@gencovery.com")
            settings["owner"]["first_name"]  = self.config["lab"]["owner"].get("first_name", "Owner")
            settings["owner"]["last_name"]   = self.config["lab"]["owner"].get("last_name", "")
            
            settings["admin"]                = {}
            settings["admin"]["uri"]         = self.config["lab"]["admin"].get("uri", "")
            settings["admin"]["email"]       = self.config["lab"]["admin"].get("email", "admin@gencovery.com")
            settings["admin"]["first_name"]  = self.config["lab"]["owner"].get("first_name", "Admin")
            settings["admin"]["last_name"]   = self.config["lab"]["owner"].get("last_name", "")
            
            dep = settings.get("dependencies",{})
            dep.update(self.config.get("dependencies",{}).get("gws",{}))
            dep.update(self.config.get("dependencies",{}).get("user",{}))
            settings["dependencies"] = dep

        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=4)

        #replace all words 'skeleton' in settings.json
        with open(settings_file, 'r') as f:
            text = f.read()
            text = text.replace("skeleton", self.lab_name)

        with open(settings_file, 'w') as f:
            f.write(text)

        #replace all words 'skeleton' in app.py
        app_file = os.path.join(dest_dir, self.lab_name, "./app.py")
        with open(app_file, 'r') as f:
            text = f.read()
            text = text.replace("skeleton", self.lab_name)

        with open(app_file, 'w') as f:
            f.write(text)

    def read_repo_type(self, repo_dir="", repo_name=""):
        if repo_dir != "":
            settings_file = os.path.join(repo_dir, "./settings.json")
        elif repo_name != "":
            repo_dir = self.get_repo_dir(repo_name)
            settings_file = os.path.join(repo_dir, "./settings.json")
        else:
            raise Exception("The repo_name or repo_dir is required")

        if os.path.exists(settings_file):
            with open(settings_file) as f:
                try:
                    settings = json.load(f)
                    #is_lab = settings.get("type", None) == "lab"
                    #if is_lab:
                    #    return "lab"
                    #else:
                    if not settings.get("name", None) is None:
                        return  "brick"
                except:
                    return "extern"
        else:
            return "extern"

    # -- L --

    def load_key(self):
        """
        Load the previously generated key
        """
        return open(self.__public_key_file_path, "rb").read()

    @property
    def lab_name(self):
        return self.config["lab"].get("name", "main")

    # -- R --

    def _read_config(self):
        with open( self.__config_file_path, 'r') as f:
            try:
                self.config = json.load(f)
                return
            except Exception as err:
                raise Exception("Cannot parse the config file. Please check file config file.") from err
        
        raise Exception("Cannot open the config file")
    
    # -- P -- 

    def get_gws_bricks(self) -> dict:
        return self.config["dependencies"].get("gws",{})
    
    def get_user_bricks(self) -> dict:
        return self.config["dependencies"].get("user", {})

    def pull(self, workspace_dir, repos={}):
        git_user = None
        git_pwd = None

        def _get_git_credentials():
            if os.path.exists(self.__public_file):
                with open(self.__public_file, 'r') as f:
                    private = json.load(f)
            else:
                raise Exception(f"File {self.__public_file} not found")

            git_user = private["git"]["login"]
            git_pwd = private["git"]["credentials"]
            
            if not git_pwd:
                raise Exception("The invalid git password")
            elif len(git_pwd) < 64:
                git_pwd = self.encrypt_message(git_pwd)
                private["git"]["credentials"] = git_pwd
                with open(self.__public_file, 'w') as f:
                    json.dump(private, f, indent=4)
            else:
                git_pwd = self.decrypt_message(git_pwd)

            git_pwd = urllib.parse.quote(git_pwd)

            return git_user, git_pwd

        git_user, git_pwd = _get_git_credentials()

        for repo_name in repos:
            origin = repos[repo_name]
            if origin == self.__default_git_origin_token:
                origin = self.__default_git_origin.strip("/") + "/" + repo_name + ".git"
                self._pull_repo(workspace_dir, repo_name, origin, user=git_user, pwd=git_pwd)
            else:
                self._pull_repo(workspace_dir, repo_name, origin)
            
            self.__is_pulled.append(repo_name)

            # pull sub repos
            repo_dir, _, _ = self.get_repo_dir(repo_name)
            settings_file = os.path.join(repo_dir, "./settings.json")
            if os.path.exists(settings_file):
                with open(settings_file) as f:
                    try:
                        settings = json.load(f)
                        deps = settings.get("dependencies",{})
                        deps.update(settings.get("externs",{}))
                        for name in deps:
                            is_already_pulled = (name in self.__is_pulled)
                            origin = deps[name]
                            if not is_already_pulled:
                                self.pull(workspace_dir, repos={name: origin})
                    except:
                        pass


    def _pull_repo(self, workspace_dir, repo_name, origin, user=None, pwd=None):

        if user:
            url = origin.strip("/")
            tab = url.split("://")
            if pwd:
                url = f"{tab[0]}://{user}:{pwd}@{tab[1]}"
            else:
                url = f"{tab[0]}://{user}@{tab[1]}"
        else:
            url = origin.strip("/")
        
        repo_dir, repo_type, wk = self.get_repo_dir(repo_name)
        alredy_exists = not repo_dir is None
        if alredy_exists:
            print(f"Git update {repo_type} {repo_name} (in {repo_dir}) from {origin}")
            git_repo = git.Repo(repo_dir)
            o = git_repo.remotes.origin
            saved_url = o.url
            o.set_url(url)
            o.pull()
            o.set_url(saved_url)
        else:
            print(f"Git clone {repo_name} from {tab[0]}://{tab[1]}")
            tmp_repo_dir = os.path.join(workspace_dir, "tmp", repo_name)
            
            if self.config["git"]["shallow"]:
                git_kwargs = {
                    "depth": 1,
                    "shallow_submodules": True
                }
            else:
                git_kwargs = {}
                
            git.Repo.clone_from(
                url, 
                tmp_repo_dir, 
                **git_kwargs
            )

            repo_type = self.read_repo_type(repo_dir=tmp_repo_dir)
            if repo_type == "brick":
                repo_dir = os.path.join(workspace_dir, "bricks", repo_name)
            elif repo_type == "lab":
                repo_dir = os.path.join(workspace_dir, "main", repo_name)
            else:
                repo_dir = os.path.join(workspace_dir, "externs", repo_name)

            shutil.move(tmp_repo_dir, repo_dir)
            git_repo = git.Repo(repo_dir)

        try:
            #set submodules pwd
            for sub in git_repo.submodules:
                sub_url = sub.config_reader().get_value("url")
                tab = re.split("://(.+@)?", sub_url)                
                sub_url = f"{tab[0]}://{user}:{pwd}@{tab[2]}" #tab[1] containt hypothetical "login"
                sub.config_writer().set_value("url", sub_url).release()
                print(f"Getting submodule {tab[0]}://{tab[2]}")

            #pull submodules
            git_repo.submodule_update(recursive=True)

            #restore submodule urls
            for sub in git_repo.submodules:
                sub_url = sub.config_reader().get_value("url")
                tab = re.split("://(.+@)?", sub_url)
                sub_url = f"{tab[0]}://{tab[2]}"   #tab[1] containt hypothetical "login"
                sub.config_writer().set_value("url", sub_url).release()
        except:
            pass

    # -- R --

    def repo_exists(self, repo_name):
        _repo_dir, _, _ = self.get_repo_dir(repo_name)
        return not _repo_dir is None

    # -- S --

    # -- U --

    # -- W --

    __is_pulled = []
    __config_file_path = "/lab/.sys/config.json"
    __public_key_file_path = os.path.join(__cdir__,".key.pub")
    __public_file = os.path.join(__cdir__,".public.json")
    __default_git_origin = "https://gitlab.com/gencovery/"
    __default_git_origin_token = "DEFAULT_ORIGIN"
    __structure = ["./bricks", "./data", "./main", "./logs", "./externs", "./notebooks", "./tmp"]

if __name__ == "__main__":
    g = GPM(
        gws_workspace="/lab/.gws",
        user_workspace="/lab/user",
        shallow=True
    )
    
    if g.is_ready():
        g.install_gws()
        g.install_user()