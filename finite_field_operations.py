

n = 8
alpha = 285

# Q = 2^n - 1
Q = pow(2, n) - 1

logf = dict()
expf = dict()


def precompute_logf_expf():
    for i in xrange(1, pow(2,n)):
        print i

        expf = 0
        logf = 0

        expf[i] = expf
        logf[i] = logf


precompute_logf_expf()


def mul(x, y):

    if x == 0 or y == 0:
        return 0

    return expf[(logf[x] + logf[y]) % Q]
