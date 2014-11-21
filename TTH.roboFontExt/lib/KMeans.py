
import random
from os import urandom
from HelperFunc import mean

def square(x):
	return x*x

def swap(v,i,j):
	v[i], v[j] = v[j], v[i]

def init(values, nbSeeds):
	nv = len(values)
	ref = random.randint(0,nv-1)
	swap(values, 0, ref)
	for pos in range(1, nbSeeds):
		seedsRange = xrange(pos)
		vals = [(min([square(values[p]-values[i]) for p in seedsRange]), i) for i in xrange(pos, nv)]
		vals.sort()
		total = sum([d for (d,i) in vals])
		dice = random.random() * total
		total = 0.0
		i = pos
		for d, j in vals:
			total += d
			if total >= dice:
				i = j
				break
		swap(values, pos, i)

def kMeans(values, k):
	random.seed(urandom(16))
	if k <= 1: return ([mean(values)], [values])
	nv = len(values)
	if nv <= k: return (values, [[x] for x in values])
	init(values, k)
	seeds = values[0:k]
	changed = True
	workVals = [(v,-1) for v in values]
	iter = 0
	while changed:
		iter += 1
		changed = False
		clusters = []
		for i in seeds:
			clusters.append([])
		for i in xrange(nv):
			(v,vi) = workVals[i]
			minDist, closestSeedIndex = min([(square(s-v), si) for (si,s) in enumerate(seeds)])
			if vi != closestSeedIndex:
				changed = True
				workVals[i] = (v, closestSeedIndex)
			clusters[closestSeedIndex].append(v)
		seeds = [mean(cls) for cls in clusters]
	return seeds, clusters
