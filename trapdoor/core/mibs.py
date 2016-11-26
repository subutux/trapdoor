from . import exceptions
import pysnmp.smi.builder
import pysnmp.smi.view
import pysnmp.smi.compiler
import pysnmp.smi.error
import pysnmp.entity.rfc3413.mibvar
import pysnmp.proto.rfc1902

from pysmi.reader.url import getReadersFromUrls
from pysmi.searcher.pyfile import PyFileSearcher
from pysmi.searcher.pypackage import PyPackageSearcher
from pysmi.searcher.stub import StubSearcher
# from pysmi.borrower.pyfile import PyFileBorrower
from pysmi.writer.pyfile import PyFileWriter
from pysmi.parser.smi import parserFactory
from pysmi.parser.dialect import smiV1Relaxed
from pysmi.codegen.pysnmp import PySnmpCodeGen, defaultMibPackages
from pysmi.codegen.pysnmp import baseMibs, fakeMibs
from pysmi.compiler import MibCompiler

# from pysmi import debug as smiDebug
from pysmi import error as smiError

import os

import logging
log = logging.getLogger('trapdoor.core.mibs')
log.addHandler(logging.NullHandler())


class MibCollection(object):
    """
    A class that holds our loaded MIBs
    for easy management & lookups

    """

    def __init__(self, config):
        self.config = config
        log.info("Initializing smi.Builder")
        self.mibBuilder = pysnmp.smi.builder.MibBuilder()
        self.modules = []
        self.loadMibs()

    def loadMibs(self, config=None):
        """
        A function allowing us to reload the mibs
        while running
        """
        if config is not None:
            self.config = config
        if hasattr(config, 'mibs') and config["mibs"] != "":
            log.info("Adding custom mibs from: {}".format(
                ", ".join(self.config["mibs"])))
            pysnmp.smi.compiler.addMibCompiler(
                self.mibBuilder,
                sources=self.config["mibs"])
            log.info("Done")
            log.info("Indexing MIB objects")
            self.mibView = pysnmp.smi.view.MibViewController(self.mibBuilder)
            log.info("Done")

            self.modules = self._get_modules()

    def _get_modules(self):
        mibs = []
        modName = self.mibView.getFirstModuleName()
        while True:
            if modName:
                mibs.append(modName)
            try:
                modName = self.mibView.getNextModuleName(modName)
            except pysnmp.smi.error.SmiError:
                break
        return mibs


class MibResolver(object):
    DEFAULT_MIB_PATHS = []
    DEFAULT_MIB_LIST = ['SNMPv2-MIB', 'SNMP-COMMUNITY-MIB']

    def __init__(self, config, mib_paths=None, mib_list=None):
        if mib_paths is None:
            mib_paths = []
        if mib_list is None:
            mib_list = []
        self.config = config
        mib_paths.append(config["mibs"]["compiled"])
        # Initialize mib MibBuilder
        self._mib_builder = pysnmp.smi.builder.MibBuilder()

        # Configure MIB sources
        self._mib_sources = self._mib_builder.getMibSources()

        # Load default mib dirs
        for path in self.DEFAULT_MIB_PATHS + mib_paths:
            self.load_mib_dir(path)
        # Load default mibs
        for mib in self.DEFAULT_MIB_LIST + mib_list:
            self.load_mib(mib)

        self._detect_mibs_compiled()
        # Initialize MibViewController
        self._mib_view = pysnmp.smi.view.MibViewController(self._mib_builder)
        log.debug("MibResolver: Initialized")

    def _detect_mibs_compiled(self):
        try_again = []
        tries = {}
        for dirname, dirnames, filenames in os.walk(
                self.config["mibs"]["compiled"]):
            for filename in filenames:
                if filename.endswith(".py") and filename != "index.py":

                    mib = os.path.splitext(filename)[0]
                    try:
                        self.load_mib(mib)
                    except pysnmp.smi.error.MibLoadError as e:
                        log.info(
                            "Cannot load {}. I'll try again later.".format(e))
                        try_again.append(mib)

            if "__pycache__" in dirnames:
                dirnames.remove("__pycache__")

        # second try, tirth try ...
        while len(try_again) > 0:
            for mib in try_again:
                try:
                    self.load_mib(mib)
                    try_again.remove(mib)
                except pysnmp.smi.error.MibLoadError as e:
                    if mib in tries:
                        tries[mib] += 1
                    else:
                        tries[mib] = 1
                    if tries[mib] > 3:
                        log.error('Failed {}'.format(e))
                        try_again.remove(mib)
                    else:
                        log.info("failed {}. I'll try again.".format(e))

    def load_mib_dir(self, path):
        self._mib_sources += (pysnmp.smi.builder.DirMibSource(path),)
        log.debug("MibResolver: Loaded MIB source: %s" % path)
        self._mib_builder.setMibSources(*self._mib_sources)

    def load_mib(self, mib):
        self._mib_builder.loadModules(mib, )
        log.debug("MibResolver: Loaded MIB: %s" % mib)

    def lookup(self, module, symbol):
        name = ((module, symbol),)
        oid, suffix = pysnmp.entity.rfc3413.mibvar.mibNameToOid(
            self._mib_view, name)
        return pysnmp.proto.rfc1902.ObjectName(oid)

    def lookup_oid(self, oid):
        (symbol, module), indices = pysnmp.entity.rfc3413.mibvar.oidToMibName(
            self._mib_view, oid)
        return module, symbol

    def lookup_value(self, module, symbol, value):
        return pysnmp.entity.rfc3413.mibvar.cloneFromMibValue(self._mib_view,
                                                              module, symbol, value)


def storeMib(config, mib, mibdir=None, fetchRemote=False):
    """
    A function to compile, store new mibs

    Mostly got the code from
    https://raw.githubusercontent.com/etingof/pysmi/master/scripts/mibdump.py
    """
    cacheDir = '/tmp/'
    log.debug("Collecting MIB resources")
    mibSearchers = defaultMibPackages
    log.debug("Searches")
    mibStubs = [x for x in baseMibs if x not in fakeMibs]
    log.debug("Stubs")
    mibSources = ["file://{}".format(x) for x in config["mibs"]["locations"]]
    log.debug("MIB sources from config")
    if mibdir != None:
        mibSources.append("file://{}".format(mibdir))

    log.debug("MIB source from param")
    # if "mib" is a path, add it to the sources.
    if os.path.sep in mib:
        mibSources.append(os.path.abspath(os.path.dirname(mib)))
        log.debug("MIB source from '{}'".format(mib))
    if fetchRemote:
        mibSources.append('http://mibs.snmplabs.com/asn1/@mib@')
        log.debug("Added remote mib source.")
    log.info("Using MIB sources: [{}]".format(
        ", ".join(mibSources)))
    log.info("Using dest: {}".format(config['mibs']['compiled']))
    log.info("Initialize compiler")
    try:
        mibCompiler = MibCompiler(
            parserFactory(**smiV1Relaxed)(tempdir=cacheDir),
            PySnmpCodeGen(),
            PyFileWriter(config['mibs']['compiled']).setOptions(
                pyCompile=True, pyOptimizationLevel=0
            )
        )
        print(mibSources)
    except Exception as e:
        log.error("Exception! {}".format(e))
    log.debug("Adding sources to compiler")
    try:
        mibCompiler.addSources(
            *getReadersFromUrls(
                *mibSources, **dict(
                    fuzzyMatching=True
                )
            )
        )
        mibCompiler.addSearchers(PyFileSearcher(config['mibs']['compiled']))
        for mibSearcher in mibSearchers:
            mibCompiler.addSearchers(PyPackageSearcher(mibSearcher))
        mibCompiler.addSearchers(StubSearcher(*mibStubs))

        log.debug("Starting compilation of {}".format(mib))
        processed = mibCompiler.compile(*[mib],
                                        **dict(noDeps=False,
                                               rebuild=False,
                                               dryRun=False,
                                               genTexts=False,
                                               ignoreErrors=False))
        mibCompiler.buildIndex(
            processed,
            dryRun=False,
            ignoreErrors=False
        )
    except smiError.PySmiError as e:
        log.error("Compilation failed: {}".format(e))
        raise exceptions.MibCompileError(e)

    errors = [(x, processed[x].error)
              for x in sorted(processed) if processed[x] == 'failed']
    compiled = [(x, processed[x].alias)
                for x in sorted(processed) if processed[x] == 'compiled']
    missing = [x for x in sorted(processed) if processed[x] == 'missing']
    for mib in compiled:
        log.info("Compiled {} ({})".format(mib[0], mib[1]))
    if len(errors) > 0 or len(missing) > 0:
        for error in errors:
            log.error("Could not process {} MIB: {}".format(
                error[0], error[1]))
        for mis in missing:
            log.error("Could not find {}".format(mis))

        raise exceptions.MibCompileFailed(errors)
    log.info("Done without errors")
    print(processed)
