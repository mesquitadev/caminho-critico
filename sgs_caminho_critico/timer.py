import itertools, time

from urllib3.connectionpool import xrange


class Timer(object):
    def __init__(self, name=None):
        self.name = name

    def __enter__(self):
        self.tstart = time.time()

    def __exit__(self, type, value, traceback):
        if self.name:
            print('[%s]' % self.name, end=' ')
        print('Elapsed: %s' % (time.time() - self.tstart))


k = [[1, 2], [4], [5, 6, 2], [1, 2], [3], [5, 2], [6], [8], [9]] * 5
N = 100000

print(len(k))

with Timer('set'):
    for i in xrange(N):
        kt = [tuple(i) for i in k]
        skt = set(kt)
        kk = [list(i) for i in skt]


with Timer('sort'):
    for i in xrange(N):
        ks = sorted(k)
        dedup = [ks[i] for i in xrange(len(ks)) if i == 0 or ks[i] != ks[i-1]]


with Timer('groupby'):
    for i in xrange(N):
        k = sorted(k)
        dedup = list(k for k, _ in itertools.groupby(k))

with Timer('loop in'):
    for i in xrange(N):
        new_k = []
        for elem in k:
            if elem not in new_k:
                new_k.append(elem)
