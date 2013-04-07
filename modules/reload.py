#!/usr/bin/env python
"""
Code Copyright (C) 2012-2013 Liam Stanley
Credits: Sean B. Palmer, Michael Yanovich
reload.py - Code Module Reloader Module
http://code.liamstanley.net/
"""

import sys, os.path, time, imp
import irc

def f_reload(code, input): 
   """Reloads a module, for use by admins only.""" 
   if not input.admin: return

   name = input.group(2)
   if name == code.config.owner: 
      return code.reply('What?')

   if (not name) or (name == '*'): 
      code.variables = None
      code.commands = None
      code.setup()
      return code.reply('done')

   if not sys.modules.has_key(name): 
      return code.reply('%s: no such module!' % name)

   # Thanks to moot for prodding me on this
   path = sys.modules[name].__file__
   if path.endswith('.pyc') or path.endswith('.pyo'): 
      path = path[:-1]
   if not os.path.isfile(path): 
      return code.reply('Found %s, but not the source file' % name)

   module = imp.load_source(name, path)
   sys.modules[name] = module
   if hasattr(module, 'setup'): 
      module.setup(code)

   mtime = os.path.getmtime(module.__file__)
   modified = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(mtime))

   code.register(vars(module))
   code.bind_commands()

   code.reply('%r (version: %s)' % (module, modified))
f_reload.name = 'reload'
f_reload.rule = ('$nick', ['reload'], r'(\S+)?')
f_reload.priority = 'low'
f_reload.thread = False

if __name__ == '__main__': 
   print __doc__.strip()