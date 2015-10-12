#!/usr/bin/python

import os

def parseImport(line, realNameOf):
	parts = line.split('import')
	if parts[0] != '':
		prefix = parts[0].split('from')[1].strip().replace('.', '/')
	else:
		prefix = ''
	imports = [s.strip().split() for s in parts[1].split(',')]
	for imp in imports:
		if 'as' in imp:
			if len(imp) != 3: exit(-1)
			if imp[1] != 'as': exit(-1)
			realName, abbrv = imp[0], imp[2]
		else:
			realName = imp[0]
			abbrv = realName
		realName = realName.replace('.', '/')
		if prefix != '':
			realName = '/'.join([prefix,realName])
		#print abbrv, " --> ", realName
		realNameOf[abbrv] = realName
def go():
	files = []
	for (dirpath, dirnames, filenames) in os.walk(os.getcwd()):
		if "freetype" in dirpath: continue
		base = os.path.split(dirpath)[1]
		for f in filenames:
			if f == 'dependencies.py': continue
			if f.endswith(".py"):
				n = f[:-3]
				if n == '__init__':
					shortname = base
				else:
					shortname = os.path.join(base, n)
				files.append((os.path.join(dirpath, f), shortname))
	reloadsOf = {}
	importsOf = {}
	for name, shortname in files:
		f = open(name)
		try:
			realNameOf = {}
			reloadsOf[shortname] = []
			#print "===================="
			#print shortname,':'
			#print "-------------------"
			fullLine = ''
			for line in f:
				l = fullLine + line.strip()
				if len(l) > 0 and l[-1] == '\\':
					fulLine = fullLine + l[:-1]
					continue
				else:
					fullLine = ''
				if l == '': continue
				if l[0] == '#': continue # remove commented line
				if 'import ' in l:
					parseImport(l, realNameOf)
				if 'reload(' in l:
					reloaded = l[7:-1].strip()
					reloadsOf[shortname].append(realNameOf[reloaded])
			importsOf[shortname] = realNameOf.values()
		finally:
			f.close()

	count = 1
	newCount = 2
	reloaded = ['lib/main']
	while newCount > count:
		count = newCount
		reloaded = set(sum([reloadsOf[x] for x in reloaded],list(reloaded)))
		newCount = len(reloaded)

	#for k,v in reloadsOf.iteritems():
	#	print k
	#	print v
	#	print ''

	print "When lib/main.py is reloaded, the following modules are reloaded:"
	for n in sorted(reloaded):
		print '\t',n

	filesThatImportUniqueInstance = [f for f in importsOf.keys() if 'models/TTHTool/uniqueInstance' in importsOf[f]]
	print "Files that import TTHTool::uniqueInstance :"
	for n in filesThatImportUniqueInstance:
		print '\t',n
	
	diff = set(filesThatImportUniqueInstance).difference(reloaded)
	print "Files that import TTHTool::uniqueInstance BUT are NOT reloaded:"
	for n in sorted(diff):
		print '\t',n

go()
