import os
import re
import glob
import requests


class SnowflakeRunner:
   
    def __init__(self): 
        self.is_debug_mode = None
        self.path = None
        self.script_list = None
        self.script_conn_list = None
        self.script_mod = None
        self.check_words = None
        self.replace_words = None

    def execute_locally(self): 
        if self.is_debug_mode is None or self.script_mod is None:
            print("Run a prepare script first!")
        comment_code_regex = re.compile(r"(?<!:)//.*")
        retScript=""
        for line in self.script_mod.splitlines():
            for check, replace in zip(self.check_words, self.replace_words):
                line = line.replace('<'+check+'>', replace)
                line = re.sub(comment_code_regex, '', line)
            retScript+=line+'\r\n'
        return retScript

    def prepare_deployment(self,is_debug_mode,varDict,script_mod):
        check_words = varDict.keys()
        replace_words = varDict.values()
        self.is_debug_mode = is_debug_mode
        self.script_mod=script_mod
        self.check_words = check_words
        self.replace_words = replace_words

    