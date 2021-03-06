B0;136;0c# -*- coding: latin-1 -*-
# Copyright (c) 2008 Pycircuit Development Team
# See LICENSE for details.

import pexpect
import skill
import re
import os, sys

def find_virtuoso():
	"""Find Cadence Virtuoso binary"""
	virtuosocmd = find_executable("icfb") or find_executable("virtuoso")
	if  virtuosocmd == None:
		raise ValueError("Cannot find virtuoso executable")
		
	cmd = virtuosocmd + " -nograph"
	return cmd

class CadenceSession(object):
	"""Class to handle a non-graphical cadence session

	>>> s = CadenceSession()
	>>> s.send("(list 1 2 3)")
	[1, 2, 3]
	>>> s.callfunc('list', 1,2,3)
	[1, 2, 3]
	>>> s.list(1,2,3)
	[1, 2, 3]
	
	"""
	def __init__(self, cmd=None, timeout=30, verbose=False):
		if cmd == None:
			cmd = find_virtuoso()
		self.verbose = verbose
		self.cds = pexpect.spawn(cmd, timeout=timeout)
		self.cds.setecho(False)
	    
		self.prompt = re.compile("^1?> ", re.MULTILINE)
	    
		self.startup = self.cds.before
		if verbose:
			print self.startup

	def callfunc(self, name, *args, **optargs):
		skillobject = skill.SkillObject(self)
		skillobject.eval(
			"(%s "%name + 
			" ".join(map(skill.toSkill, args) + 
				 ["?%s %s"%(k,skill.toSkill(v)) for k,v in optargs.items()])+
			")")
		return skillobject

	def _makeskillfunc(self, name):
		def func(*args, **optargs):
			return self.callfunc(name, *args, **optargs)
		return func
	
	def __getattr__(self, attr):
		"""Dynamically create a function that executes a skill function"""
		if not attr.startswith("_"):
			return self._makeskillfunc(attr)
		else:
			raise AttributeError()

	def send(self, expr):
		if self.verbose:
			print "Sending: "+expr
		self.cds.sendline(expr)
		self.cds.expect(self.prompt)
		if self.verbose:
			print "Got:", self.cds.before

		response = [s for s in re.split("[\r]\n",self.cds.before) if s != ""][-1]

		try:
		    result = skill.parse(response)
		except:
		    print response
		    raise Exception("Could not parse response")

		if response.find("*Error*") > 0:
			raise Exception(response)

		if self.verbose:
			print "Result:", result
		
		return result

	def __del__(self):
		if self.cds:
			self.cds.sendline("exit")
			self.cds.expect(pexpect.EOF)


def find_executable(executable, path=None):
    """Try to find 'executable' in the directories listed in 'path' (a
    string listing directories separated by 'os.pathsep'; defaults to
    os.environ['PATH']).  Returns the complete filename or None if not
    found
    """
    if path is None:
        path = os.environ['PATH']
    paths = path.split(os.pathsep)
    extlist = ['']
    if os.name == 'os2':
        (base, ext) = os.path.splitext(executable)
        # executable files on OS/2 can have an arbitrary extension, but
        # .exe is automatically appended if no dot is present in the name
        if not ext:
            executable = executable + ".exe"
    elif sys.platform == 'win32':
        pathext = os.environ['PATHEXT'].lower().split(os.pathsep)
        (base, ext) = os.path.splitext(executable)
        if ext.lower() not in pathext:
            extlist = pathext
    for ext in extlist:
        execname = executable + ext
        if os.path.isfile(execname):
            return execname
        else:
            for p in paths:
                f = os.path.join(p, execname)
                if os.path.isfile(f):
                    return f
    else:
	    return None

if __name__ == "__main__":
    import doctest
    doctest.testmod()

