import trapdoor.core.mibs as mibs
import pkgutil
import importlib
import logging
log = logging.getLogger('trapdoor.core.handler')
log.addHandler(logging.NullHandler())
_HANDLERS = []
_HANDLERS_MODULES = {}
def load():
    _HANDLERS = []
    for item in pkgutil.iter_modules(__path__,'trapdoor.handlers.'):
        log.info("caching module {module}".format(module=item[1]))
        _HANDLERS.append(item[1])
        _HANDLERS_MODULES[item[1]] = importlib.import_module(item[1])
    return _HANDLERS


class Handler(object):
    """
    Base class for trap handlers
    """
    
    def __init__(self,config):
        self._config = config
        self._mibs = mibs.MibResolver()
    
    def _notification_callback(self, snmp_engine, stateReference, contextEngineId, contextName, varBinds, cbCtx):
        """
        Callback function for receiving notifications
        Borrowed from https://github.com/subutux/nagios-trapd/blob/master/src/nagios/snmp/receiver.py#L120
        """
        trap_oid = None
        trap_name = None
        trap_args = dict()

        try:
            # get the source address for this notification
            transportDomain, trap_source = snmp_engine.msgAndPduDsp.getTransportInfo(stateReference)
            log.debug("TrapReceiver: Notification received from %s, %s" % (trap_source[0], trap_source[1]))

            # read all the varBinds
            for oid, val in varBinds:
                # translate OID to mib symbol/modname
                (module, symbol) = self._mibs.lookup_oid(oid)

                if module == "SNMPv2-MIB" and symbol == "snmpTrapOID":
                    # the SNMPv2-MIB::snmpTrapOID value is the trap oid
                    trap_oid = val
                    # load the mib symbol/modname for the trap oid
                    (trap_symbol_name, trap_mod_name) = self._mibs.lookup_oid(trap_oid)
                else:
                    # all other values should be converted to mib symbol/modname
                    # and put in the trap_data dict

                    # trap_arg_oid = oid
                    # For the case the faultIndex was added into the OID, we have to lookup
                    # the original OID from MIB instead of using the OID in the received packet directly.
                    trap_arg_oid = self._mibs.lookup(module, symbol)
                    # convert value
                    trap_arg_value = self._mibs.lookup_value(module, symbol, val)
                    trap_args[trap_arg_oid] = trap_arg_value

                log.debug("Trap argument: %s, %s = %s" % (module, symbol, val))

            # get trap source info
            trap_source_address, trap_source_port = trap_source
            trap_source_hostname, trap_source_domain = get_hostname_from_address(trap_source_address)

            # set trap propreties
            trap_properties = dict()
            trap_properties['hostname'] = trap_source_hostname
            trap_properties['ipaddress'] = trap_source_address
            trap_properties['domain'] = trap_source_domain

            # Let the module do it's thing with this trap.
            self.trap(trap_oid, trap_args, trap_properties)

        except Exception as ex:
            log.exception("Error handling SNMP notification")
    
    def trap(self,trap_oid,trap_args,trap_properties):
        log.error("module not handling trap")
        pass
    