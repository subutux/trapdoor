"""
Filter trap messages based on JavaScript functions
"""
import os
import js2py
from . import exceptions
from trapdoor import handlers

import logging
log = logging.getLogger('trapdoor.core.filter')
log.addHandler(logging.NullHandler())

HANDLERS = handlers.load()

FILTER_TEMPLATE='''// Trapdoor - filter
// This is an example filter you can use as a start.
// You always have to have a "Filter" function.
//
// the supplied trap is an object defining a recieved
// trap:
// ´´´
// { "timestamp": 123456789,
//   "oid": "1.2.3.4.5.6.7.8"
//   "translatedOid:"My.Trap.Translation"
//   "vars": {
//     "myVar" : "varValue",
//     "myVar1" : "varValue1",
//     "myVar2" : "varValue2"
//    }
// }
// ´´´
// Your trap shoud return an object like this:
// ```
// { "store": true,
//   "next": false
//   "handle": true,
//   "handler": "log"
//    "trap": `[trap object]`
// }

function Filter(Trap) {

    var filtered =  {
        "store": true,
        "next": false,
        "handle": false,
        "handle": null,
        "trap": Trap
    }
    
    // Do some magic here with Trap & filtered
    
    return filtered
}
'''


class FilterManager(object):
    def __init__(self,config):
        """
        A manager for filters. Allows us to save/apply/edit/remove
        filters saved at the configured location
        """
        self._location = config['filters']['location']
        self._filters = {}
        if os.path.exists(self._location) and os.path.isdir(self._location):
            pass
        else:
            log.error("Cannot access {}. Doesn't exit or is not a dir".format(self._location))
            raise exceptions.FilterPathError("Cannot access {}".format(self._location))

        try:
            for root, dirs, files in os.walk(self._location):
                for file in files:
                    if file.endswith('.js'):
                        f = os.path.join(root,file)
                        log.info('Loading {}'.format(f))
                        with open(f,'r') as reader:
                            self._filters[f] = Filter(f,reader.read(),HANDLERS)
                            log.debug("File {} Loaded".format(f))
        except Exception as e:
            log.error("Unable to load files: {} ".format(e))
            raise exceptions.FilterProcessError(e)
    

    def _test_file(self,js):
        """
        Test the file if its valid javascript
        """
        try:
            js2py.eval_js(js)
        except js2py.base.PyJsException as e:
            log.error("Cannot evaluate filter: {}".format(e))
            raise exceptions.FilterParseError(e)
        return True
    def _template(self,file):
        """
        store the template data into a new file
        """
    def new(self,path):
        """
        Create a new filter with template
        """
        filter_path = os.path.join(self._location,path)
        try:
            with open(filter_path,'w') as file:
                file.write(FILTER_TEMPLATE)
            self._filters[filter_path] = Filter(filter_path,FILTER_TEMPLATE,HANDLERS)
        except Exception as e:
            log.error("Unable to save/open file {}".format(path))
            raise exceptions.FilterSaveError(e)
        return True
    def save(self,path,new_data):
        """
        Save the filter after testing
        """
        
        filter_path = os.path.join(self._location,path)
        
        try:
            self._test_file(new_data)
        except exceptions.FilterParseError as e:
            log.error("Cannot save filter {}.Evaluation failed")
            raise exceptions.FilterSaveError(e)
        
        try:
            with open(filter_path,'w') as file:
                file.write(new_data)
            self._filters[filter_path] = Filter(filter_path,new_data,HANDLERS)
        except Exception as e:
            log.error("Unable to save/open file {}".format(path))
            raise exceptions.FilterSaveError(e)
        return True
    @property
    def filters(self):
        return self._filters
    
    def delete(self,path):
        try:
            if path in self._filters and os.path.exists(path) and os.path.isfile(path) and path.endswith(".js"):
                os.remove(os.path.join(self._location,path))
                self._filters.pop(path)
                return True
        except Exception as e:
            log.error("Unable to delete filter {}".format(path))

class Filter(object):
    """
    An filter instance
    """
    
    def __init__(self,name,js,handlers):
        """
        Evaluate the javascript and set some variables
        """

        self._name = name
        self._js = js
        self._handlers = handlers
        self._setContext()

    def _setContext(self):
        """
        Set the context for js. Add the handler function
        so javascript knows about the handlers.
        """
        
        def get_handlers():
            return self._handlers
        self._context = js2py.EvalJs({
            "handlers" : get_handlers
        })
        self._context.execute(self._js)
        
    def reset_handlers(self,handlers):
        """
        If we want to live add handlers,
        we can reset them here & reset the javascript context
        """
        self._handlers = handlers
        self._setContext()
    
    def evaluate(self,trap):
        """
        Evaluate the js "Filter() function"
        """

        return self._context.Filter(trap)
