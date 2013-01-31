# coding=UTF-8
'''
Startup script for Control System Web.
'''

import sys, os.path, glob

# Setup python search path before importing modules from 'csw' #
csweb_home = os.path.dirname(os.path.abspath(os.path.dirname(sys.argv[0])))
sys.path.append(csweb_home)


# Execute configuration scripts from '$(csweb_home)/config' directory.
config_path = os.path.join(csweb_home, 'config')
if not os.path.isdir(config_path):
	sys.exit('Configuration directory not found: %s' % (config_path,))

config_glob = os.path.join(config_path, '*.py')
config_paths = glob.glob(config_glob)
config_paths.sort()

try:
	for config_script in config_paths:
		execfile(config_script)
except Exception as e:
	sys.exit('Error while running config script: %s: %s' % (os.path.basename(config_script), str(e)))


# Start the reactor #
log.msg('start.py: Run the reactor', logLevel=_DEBUG)
reactor.run()
# Wait for reactort #
log.msg('start.py: Reactor stopped.', logLevel=_DEBUG)
