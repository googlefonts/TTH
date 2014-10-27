#!/usr/bin/python

import sys, fileinput

if len(sys.argv) > 1:
	f = open(sys.argv[1])
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
