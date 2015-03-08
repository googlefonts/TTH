
import random
from os import urandom
from HelperFunc import mean

def square(x):
	return x*x

def swap(v,i,j):
	v[i], v[j] = v[j], v[i]

def uniques(values):
	#values.sort()
	uniq = []
	prev = values[0]-1
	for v in values:
		if v != prev:
			prev = v
			uniq.append(v)
	return uniq

def init(values, nbSeeds):
	nv = len(values)
	ref = random.randint(0,nv-1)
	swap(values, 0, ref)
	for pos in range(1, nbSeeds):
		seedsRange = xrange(pos)
		vals = [(min([square(values[p]-values[i]) for p in seedsRange]), i) for i in xrange(pos, nv)]
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

def partScore(clusters, means):
	return sum([sum([square(means[ci]-v) for v in c]) for (ci,c) in enumerate(clusters)])

def iterative(values, k):
	random.seed(urandom(16))
	uniqValues = uniques(values)
	if k <= 1:
		return [mean(values)], partScore([values], [mean(values)]), [values]
	if len(uniqValues) <= k: return uniqValues, 0.0, [[x] for x in uniqValues]
	init(uniqValues, k)
	seeds = uniqValues[0:k]
	changed = True
	nv = len(values)
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
	return seeds, partScore(clusters, seeds), clusters

def optimal(values, k): # In 1D, optimal clustering is possible with dynamic programming
	uniqValues = uniques(values)
	if k <= 1:
		m = mean(values)
		return partScore([values], [m]), [m], [values]
	if len(uniqValues) <= k: return 0.0, uniqValues, [uniqValues]
	#values.sort()
	nv = len(values)
	cumSqSum = []
	cumSum = []
	sqSum = sum = 0.0
	for v in values:
		sqSum += v*v
		cumSqSum.append(sqSum)
		sum += v
		cumSum.append(sum)
	cumSum.append(0)
	cumSqSum.append(0)
	def score(i,j): # i, j included
		return (cumSqSum[j]-cumSqSum[i-1]) - square(cumSum[j]-cumSum[i-1]) / float(j-i+1)
	table = [[None for _ in xrange(nv)] for _ in range(k)]
	row = table[0]
	for i in xrange(nv):
		row[i] = score(0,i), 0
	for m in range(1,k-1):
		prev = table[m-1]
		row = table[m]
		for i in range(m,nv):
			row[i] = min([(prev[j][0] + score(j+1,i), j+1) for j in range(m-1,i)])
	prev = table[k-2]
	table[k-1][nv-1] = min([(prev[j][0] + score(j+1,i), j+1) for j in range(k-2,i)])

	pos = nv-1
	lefts = []
	for m in range(k-1, -1, -1):
		lefts.append(table[m][pos][1])
		pos = lefts[-1]-1
	lefts.reverse()
	lefts.append(nv)
	clusters = [values[lefts[m]:lefts[m+1]] for m in range(k)]
	return table[k-1][nv-1][0], [mean(c) for c in clusters], clusters
