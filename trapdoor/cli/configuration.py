import logging
log = logging.getLogger('trapdoor.cli.configuration')
log.addHandler(logging.NullHandler())

def init_config(conf,args):
    try:
        conf.writeDefaults(args.config)
    except Exception as e:
        log.error('Unable to write config! {}'.format(e))
        exit(1)
    exit(0)