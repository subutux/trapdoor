from .core import exceptions
import yaml
import os

import logging
log = logging.getLogger('trapdoor.config')
log.addHandler(logging.NullHandler())

DEFAULTS = {
    "db": {
        "host": "localhost",
        "user": "root",
        "password": "",
        "database": "trapdoor"
    },
    "web": {
        "transport": {
            "ipv4": {
                "enable": True,
                "listen": "0.0.0.0",
                "port": 8080
            }
        }
    },
    "traps": {
        "transport": {
            "ipv4": {
                "enable": True,
                "listen": "0.0.0.0",
                "port": 162,
            },
            "ipv6": {
                "enable": True,
                "listen": "::1",
                "port": 162,
            },
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
    },
    "mibs": {
        "locations": [
            "/usr/share/snmp/mibs",
            "/etc/trapdoor/mibs"
        ],
        "compiled": "/etc/trapdoor/mibs.compiled"

    }
}


class Config(object):
    """
    Simple config loader
    """

    def __init__(self, configfile="/etc/trapdoor/trapdoor.yaml"):
        if os.path.isfile(configfile):
            log.info("Got file {}".format(configfile))
            with open(configfile, 'r', encoding="utf-8") as cf:
                try:
                    cfg = yaml.load(cf)
                    log.debug("File parsed")
                except yaml.YAMLError as exc:
                    raise exceptions.ConfigNotParsedError(exc)
                self._config = self._merge_default(DEFAULTS, cfg)
        else:
            raise exceptions.ConfigNotFoundError(
                "Config file \"{}\" not found!".format(configfile))

    def get(self):
        return self._config

    def _merge_default(self, x, y):
        """
        Merge 2 dicts.

        Source: http://stackoverflow.com/a/26853961
        """
        z = x.copy()
        z.update(y)
        return z

    def __getitem__(self, attr):
        if attr in self._config:
            return self._config[attr]
        else:
            return None


def writeDefaults(configfile):
    """
    Helper function to write the DEFAULTS in yaml format
    to a config file
    """

    with open(configfile, 'w') as file:
        header = """# trapdoor configuration
# ----------------------
# These are the default settings for trapdoor.
# Please change them to your needs.

"""
        file.write(header)
        yaml.dump(DEFAULTS, file, default_flow_style=False)
        log.info("Saved defaults to file {}".format(configfile))
    return True
