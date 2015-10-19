#!/usr/bin/python

import os, sys

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

def getPythonFiles(root):
	files = []
	for (dirpath, dirnames, filenames) in os.walk(root):
		if "freetype" in dirpath: continue
		base = os.path.split(dirpath)[1]
		for f in filenames:
			if f == 'go.py': continue
			if f.endswith(".py"):
				n = f[:-3]
				if n == '__init__':
					shortname = base
				else:
					shortname = os.path.join(base, n)
				files.append((os.path.join(dirpath, f), shortname))
	return files

def dependencies():
	files = getPythonFiles(os.getcwd())
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

	#print "When lib/main.py is reloaded, the following modules are reloaded:"
	#for n in sorted(reloaded):
	#	print '\t',n

	filesThatImportUniqueInstance = [f for f in importsOf.keys() if 'models/TTHTool/uniqueInstance' in importsOf[f]]
	#print "Files that import TTHTool::uniqueInstance :"
	#for n in filesThatImportUniqueInstance:
	#	print '\t',n
	
	diff = set(filesThatImportUniqueInstance).difference(reloaded)
	print "Files that import TTHTool::uniqueInstance BUT are NOT reloaded when lib/main.py is reloaded:"
	for n in sorted(diff):
		print '\t',n

# ===============================================================

def countFunctions():
	if len(sys.argv) > 2:
		f = open(sys.argv[2])
	else:
		f = sys.stdin
	funcs = []
	l = 1
	for line in f:
		if (-1) != line.find('def'):
			funcs.append((l, line))
		l += 1
	f.close()
	n = len(funcs)
	for i in range(n):
		(l1, t1) = funcs[i]
		if i < n-1:
			l2 = funcs[i+1][0]
		else:
			l2 = l+1
		funcs[i] = (l2-l1, t1)
	funcs.sort()
	print "============", n, " functions =============="
	for x in funcs: print x
	print "============", n, " functions =============="

# ===============================================================

def fileShouldBeReleased(f):
	if f[0] == '.': return False
	if f.endswith('.pyc'):
		if f in ['go.pyc']:
			return False
		return True
	if f.endswith('.py'):
		return f in ['main.py',
				'OpenAutoMatch.py',
				'OpenCompareFonts.py',
				'ClearAllTTHData.py',
				'CompileAllGlyphs.py',
				'ShipFont.py']
	if f == 'TODO': return False
	return True

def makeRelease():
	cwd = os.getcwd()
	extFullPath = os.path.split(cwd)[0]
	extPath, extDir = os.path.split(extFullPath)
	if extDir != 'TTH.roboFontExt':
		print "the release script should be executed from the lib/ directory."
		return
	try:
		# Prepare receiving hierarchy
		releaseDir = os.path.join(extPath,"_release")
		if not os.path.isdir(releaseDir): os.mkdir(releaseDir)
		releaseDir = os.path.join(releaseDir,'TTH.robofontExt')
		if not os.path.isdir(releaseDir): os.mkdir(releaseDir)
		if not os.path.isdir(releaseDir):
			print "RELEASE ERROR 1"
			return
		# cp stuff
		for (dirpath, dirnames, filenames) in os.walk(extFullPath):
			filenames[:] = [f for f in filenames if fileShouldBeReleased(f)]
			base = dirpath.replace('TTH.roboFontExt', '_release/TTH.roboFontExt')
			if not os.path.isdir(base): os.mkdir(base)
			print base,':'
			for f in filenames:
				src = os.path.join(dirpath,f)
				dst = os.path.join(base,f)
				cmd = "cp -f {} {}".format(src, dst)
				print '\t',f
				os.system(cmd)

	except Exception as inst:
		print "Exception during RELEASE:"
		print inst

# ===============================================================
# ===============================================================

command = sys.argv[1].upper()

if 'DEP' in command:
	dependencies()
elif 'COUNT' in command or 'FUN' in command:
	countFunctions()
elif 'RELEASE' in command:
	makeRelease()
else:
	print '''USAGE:
	./go.py dep
	./go.py (count|fun) [FILE] )
	./go.py release'''
