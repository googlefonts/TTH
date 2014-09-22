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
for i in range(len(funcs)):
	(l1, t1) = funcs[i]
	if i < n-1:
		(l2, t2) = funcs[i+1]
	else:
		(l2, t2) = l+1, "rien"
	funcs[i] = (l2-l1, t1)
funcs.sort(key = lambda (l1,t1): l1)#, reverse = True)
print "============", len(funcs), " functions =============="
for x in funcs:
	print x
print "============", len(funcs), " functions =============="
