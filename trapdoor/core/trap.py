from . import exceptions
import trapdoor.core.mibs as mibs
import threading
import datetime
import pysnmp.entity.config
import pysnmp.entity.engine
import pysnmp.entity.rfc3413.mibvar
import pysnmp.smi.builder
import pysnmp.smi.view
from pysnmp.carrier.asyncio.dgram import udp,udp6
from pysnmp.entity.rfc3413 import ntfrcv
import asyncio
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
    def __init__(self,config,Q,loop=None):
        self._config = config
        self._engine = pysnmp.entity.engine.SnmpEngine()
        self._mibs = mibs.MibResolver(config)
        self.transports = []
        self.Q = Q
        if loop == None:
            self.loop = asyncio.get_event_loop()
    
        if config["traps"]["transport"]["ipv4"]["enable"]:
            self._enable_transport_ipv4()
        
        if config["traps"]["transport"]["ipv6"]["enable"]:
            self._enable_transport_ipv6()
        
        if not config["traps"]["transport"]["ipv6"]["enable"] and not config["traps"]["transport"]["ipv4"]["enable"]:
            log.error(''.join(['No transport enabled! specifiy at least',
                               ' one of ipv4,ipv6'])
                      )
            
            raise exceptions.ErrorTrapTransport("No transport enabled")
        
        if config["traps"]["v2c"]["enable"]:
            self._enable_v2c()
    
    
    def _enable_transport_ipv4(self):
        servermode = udp.UdpTransport().openServerMode(
            (self._config["traps"]["transport"]["ipv4"]["listen"],
             int(self._config["traps"]["transport"]["ipv4"]["port"]))
        )
        self.transports.append(servermode)
        pysnmp.entity.config.addTransport(self._engine,
                                                udp.domainName,
                                                servermode)
        log.info("Init UDP[ipv4] transport on {listen}:{port}".format(
            listen=self._config["traps"]["transport"]["ipv4"]["listen"],
            port=self._config["traps"]["transport"]["ipv4"]["port"]))
    
    def _enable_transport_ipv6(self):
        servermode = udp6.Udp6Transport().openServerMode(
            (self._config["traps"]["transport"]["ipv6"]["listen"],
             int(self._config["traps"]["transport"]["ipv6"]["port"]))
        )
        self.transports.append(servermode)
        pysnmp.entity.config.addTransport(self._engine,
                                                udp6.domainName,
                                                servermode)
        log.info("Init UDP[ipv6] transport on {listen}:{port}".format(
            listen=self._config["traps"]["transport"]["ipv6"]["listen"],
            port=self._config["traps"]["transport"]["ipv6"]["port"]))
    
    def _enable_v2c(self):
        log.info("Init v2c authentication")
        community = self._config["traps"]["v2c"]["community"]
        pysnmp.entity.config.addV1System(self._engine, 'trapdoor', community)
    
    def _enable_v3(self):
        priv = self._config["traps"]["v3"]["private"]
        priv_pass = self._config["traps"]["v3"]["private"]
        auth = self._config["traps"]["v3"]["auth"]
        user = self._config["traps"]["v3"]["user"]
        user_pass = self._config["traps"]["v3"]["pass"]
        
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
        
    def _notification_callback(self, snmpEngine, stateReference, contextEngineId, contextName, varBinds,cbCtx):
        """
        Callback function for receiving notifications
        Borrowed from https://github.com/subutux/nagios-trapd/blob/master/src/nagios/snmp/receiver.py#L120
        """
        
        trap_oid = None
        trap_name = None
        trap_args = dict()

        try:
            # get the source address for this notification
            transportDomain, trap_source =      snmpEngine.msgAndPduDsp.getTransportInfo(stateReference)
            #transportDomain, transportAddress = snmpEngine.msgAndPduDsp.getTransportInfo(stateReference)
            log.debug("Notification received from %s, %s" % (trap_source[0], trap_source[1]))

            # read all the varBinds
            for oid, val in varBinds:
                # translate OID to mib symbol/modname
                (module, symbol) = self._mibs.lookup_oid(oid)

                if module == "SNMPv2-MIB" and symbol == "snmpTrapOID":
                    # the SNMPv2-MIB::snmpTrapOID value is the trap oid
                    trap_oid = val
                    # load the mib symbol/modname for the trap oid
                    (trap_symbol_name, trap_mod_name) = self._mibs.lookup_oid(trap_oid)
                    trap_name = "{}::{}".format(trap_symbol_name,trap_mod_name)
                    val = '::'.join(self._mibs.lookup_oid(val))
                    log.debug("TRAP: %s::%s = %s" % (module, symbol, val))
                else:
                    # all other values should be converted to mib symbol/modname
                    # and put in the trap_data dict

                    # trap_arg_oid = oid
                    # For the case the faultIndex was added into the OID, we have to lookup
                    # the original OID from MIB instead of using the OID in the received packet directly.
                    trap_arg_oid = self._mibs.lookup(module, symbol)
                    # convert value
                    trap_arg_value = self._mibs.lookup_value(module, symbol, val)
                    
                    trap_args[trap_arg_oid] = {"oid": oid,
                                               "module": module,
                                               "symbol": symbol,
                                               "var":trap_arg_oid,
                                               "val":val,
                                               "try_trans_val":trap_arg_value
                                               }

                    log.debug("Trap argument: %s::%s = %s" % (module, symbol, val))

            # get trap source info
            trap_source_address, trap_source_port = trap_source
            #trap_source_hostname, trap_source_domain = get_hostname_from_address(trap_source_address)

            # set trap propreties
            trap_properties = dict()
            trap_properties['ipaddress'] = trap_source_address
            
            trap = {
                "timestamp": datetime.date.today(),
                "oid": trap_oid,
                "translateOid":trap_name,
                "vars": trap_args
            }
            
            # Let the module do it's thing with this trap.
            #self.trap(trap_oid, trap_args, trap_properties)
            # Add the trap to the queue
            self.Q.async_q.put(Trap(trap))

        except Exception as ex:
            log.exception("Error handling SNMP notification: {}".format(ex))
        return True
    def cbFun(self,snmpEngine,
          stateReference,
          contextEngineId, contextName,
          varBinds,
          cbCtx):
        transportDomain, transportAddress = snmpEngine.msgAndPduDsp.getTransportInfo(stateReference)
        print('Notification from %s, SNMP Engine %s, Context %s' % (transportAddress,
                                                                    contextEngineId.prettyPrint(),
                                                                    contextName.prettyPrint()))
        for name, val in varBinds:
            print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))
        
    @asyncio.coroutine
    def register(self):
        """
        registers the engine & callback
        """
        ntfrcv.NotificationReceiver(self._engine,self._notification_callback)
        log.info('Registered callback')
        return True
    @asyncio.coroutine
    def stop(self):
        if self._config["traps"]["transport"]["ipv4"]["enable"]:
            log.info("Closing {} transport".format(str("UDP[ipv4]")))
            pysnmp.entity.config.delTransport(self._engine,udp.domainName)
            log.info("Closed {} transport".format(str("UDP[ipv4]")))
        if self._config["traps"]["transport"]["ipv6"]["enable"]:
            log.info("Closing {} transport".format(str("UDP[ipv6]")))
            pysnmp.entity.config.delTransport(self._engine,udp6.domainName)
            log.info("Closed {} transport".format(str("UDP[ipv6]")))

        log.info("trapReciever stopped.")
class Trap(object):
    """
    an object defining a trap.
    """
    
    def __init__(self,trapdata):
        self._trapdata = trapdata
        self._history = []
        #extract the history from the trap
        if "history" in trapdata:
            self._history.extend(trapdata['history'])
            del self._trapdata['history']
    
    
    @property
    def oid(self):
        return self._trapdata['oid']
    @property
    def translateOid(self):
        return self._trapdata['translatedOid']
    @property
    def timestamp(self):
        return self._trapdata['timestamp']
    def get_var(self,var):
        if var in self._trapdata['vars']:
            return self._trapdata['vars'][var]
    def set_var(self,var,val):
        if var in self._trapdata['vars']:
            self._trapdata['vars'][var] = val
    
    @property
    def history(self):
        return self._history
    @history.setter
    def history(self,hist):
        self._history = hist
        
    def to_dict(self):
        data = {}
        data.update(self._trapdata)
        data['history'] = self._history
        return data
