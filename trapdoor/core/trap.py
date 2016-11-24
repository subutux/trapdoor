from . import exceptions
import threading
import pysnmp.entity.config
import pysnmp.entity.engine
import pysnmp.entity.rfc3413.mibvar
import pysnmp.smi.builder
import pysnmp.smi.view
from pysnmp.carrier.asynsock.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv

import logging
log = logging.getLogger('trapdoor.core.trap')
log.addHandler(logging.NullHandler())

V3_AUTH = {
    "MD5": pysnmp.entity.config.usmHMACMD5AuthProtocol,
    "SHA": pysnmp.entity.config.usmHMACSHAAuthProtocol,
    "NONE": pysnmp.entity.config.usmNoAuthProtocol
}
V3_PRIV = {
    
    "DES": pysnmp.entity.config.usmDESPrivProtocol,
    "3DES": pysnmp.entity.config.usm3DESEDEPrivProtocol,
    "AES-128": pysnmp.entity.config.usmAesCfb128Protocol,
    "AES-192": pysnmp.entity.config.usmAesCfb192Protocol,
    "AES-256": pysnmp.entity.config.usmAesCfb256Protocol,
    "NONE": pysnmp.entity.config.usmNoPrivProtocol
}

class trapReciever(object):
    def __init__(self,config):
        self._config = config
        self._engine = pysnmp.entity.engine.SnmpEngine()
    
        if config["transport"]["ipv4"]:
            self._enable_transport_ipv4()
        
        if config["transport"]["ipv6"]:
            self._enable_transport_ipv6()
        
        if not config["transport"]["ipv6"] and not config["transport"]["ipv4"]:
            log.error(''.join(['No transport defined! specifiy at least',
                               ' one of ipv4,ipv6'])
                      )
            
            raise exceptions.ErrorTrapTransport("No transport defined")
        
        if config["v2c"]["enable"]:
            self._enable_v2c()
    
    
    def _enable_transport_ipv4(self):
        servermode = udp.UdpTransport().openServerMode(
            (self._config["listen"],int(self._config["port"]))
        )
        pysnmp.entity.config.addSocketTransport(self._engine,
                                                udp.domainName,
                                                servermode)
        log.info("Init UDP transport on {listen}:{port}".format(
            listen=self._config["listen"],
            port=self._config["port"]))
    
    def _enable_transport_ipv6(self):
        log.error("Not Implemented: IPv6 is not yet implemented")
        if self._config["transport"]["ipv4"]:
            log.error("Fallback to ipv4")
            self._enable_transport_ipv4()
    
    def _enable_v2c(self):
        log.info("Init v2c authentication")
        community = self._config["v2c"]["community"]
        pysnmp.entity.config.addV1System(self._engine, 'trapdoor', community)
    
    def _enable_v3(self):
        priv = self._config["v3"]["private"]
        priv_pass = self._config["v3"]["private"]
        auth = self._config["v3"]["auth"]
        user = self._config["v3"]["user"]
        user_pass = self._config["v3"]["pass"]
        
        log.info("init snmpv3 authentication")
        
        if auth not in V3_AUTH:
            log.error("Hashing of type '{}' not known!".format(auth))
            raise exceptions.ErrorTrapTransport("Unknown hashing '{}'".format(auth))
        
        if priv != "":
            
            if priv not in V3_PRIV:
                log.error("Encryption of type '{}' not known!".format(priv))
                raise exceptions.ErrorTrapTransport(
                    "Unknown encryption '{}'".format(priv)
                )
            
            pysnmp.entity.config.addV3User(self._engine,
                                           user,
                                           auth,
                                           user_pass,
                                           priv,
                                           priv_pass)
            log.info("Created SnmpV3 user {} using {} & private {}".format(
                user, auth, priv))
        else:
            pysnmp.entity.config.addV3User(self._engine,
                                           user,
                                           auth,
                                           user_pass)
            log.info("Created SnmpV3 user {} using {} & private None".format(
                user, auth))
            
