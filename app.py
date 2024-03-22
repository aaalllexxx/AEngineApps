import sys
from flask import Flask
from json_dict import JsonDict
import keyboard
from importlib import import_module
import webview

class App:
    def __init__(self, app_name=__name__):
        self.app_name = app_name
        self.flask = Flask(self.app_name)
        self.__config = {}
    
    def add_router(self, path: str, view_func: callable, **options):
        self.flask.add_url_rule(path, view_func=view_func, **options)
        
    def add_routers(self, rules: dict[str, callable]):
        for route, func in rules.items():
            self.add_router(route, func)
            
    def load_config(self, path):
        self.config = JsonDict(path)
    
    def run(self):
        webview.create_window(self.app_name, self.flask)
        webview.start(debug=self.config.get("debug") or False)
        
    def close(self):
        active_window = webview.active_window()
        if active_window:
            active_window.destroy()
        
    @property
    def config(self) -> dict:
        return self.__config
    
    @config.setter
    def config(self, value):
        if isinstance(value, dict):
            if value.get("routes"):
                for route, func in value["routes"].items():
                    if value.get("screen_path"):
                        prefix = value["screen_path"].replace("/", ".") + "."
                    cls = getattr(import_module(prefix + func), func)
                    options = {}
                    if hasattr(cls, "__options__"):
                        options = cls.__options__
                    call = cls()
                    self.add_router(route, call, **options)
            for prop, value in value.items():       
                self.__config[prop] = value
        
        elif isinstance(value, JsonDict):
            self.config = value.dictionary