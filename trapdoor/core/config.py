import yaml
import os

import logging
log = logging.getLogger('trapdoor.core.config')
log.addHandler(logging.NullHandler())

DEFAULTS = {
    "db" : {
        "host": "localhost",
        "user": "root",
        "password": "",
        "database": "trapdoor"
        },
    "traps" : {
        "port": 162,
        "listen": "0.0.0.0",
        "transport":{
            "ipv4": True,
            "ipv6": False
        },
        "v2c": {
            "enable": True,
            "community": "public"
        },
        "v3": {
            "enable": True,
            "auth": "MD5",
            "private": "AES-128",
            "user": "public",
            "password": "public",
            "private_password": "public"
        }
    },
    "filters": {
        "location": "/etc/trapdoor/filters.d/"
    }
}

class ConfigNotFoundError(Exception):
    pass

class ConfigNotParsedError(Exception):
    pass

class Config(object):
    """
    Simple config loader
    """
    def __init__(self,configfile="/etc/trapdoor/trapdoor.yaml"):
        if os.path.isfile(configfile):
            log.info("Got file {}".format(configfile))
            with open(configfile,'r',encoding="utf-8") as cf:
                try:
                    cfg = yaml.load(cf)
                    log.debug("File parsed: {}".format(cfg))
                except yaml.YAMLError as exc:
                    raise ConfigNotParsedError(exc)
                self.config = self._merge_default(DEFAULTS, cfg)
        else:
            raise ConfigNotFoundError("Config file \"{}\" not found!".format(configfile))
    def get(self):
        return self.config
    def _merge_default(self,x,y):
        """
        Merge 2 dicts.
        
        Source: http://stackoverflow.com/a/26853961
        """
        z = x.copy()
        z.update(y)
        return z
    
        