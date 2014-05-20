cdef class IntercalObjective:
    # Memoryviews - all are 1D, length n_terms
    cdef long [:] from_index
    cdef long [:] to_index
    cdef double[:] delta
    cdef double [:] weight

    # Number of terms in obj func (edges in network)
    cdef long n_terms

    def __init__(self, long[:] from_index,
                       long[:] to_index,
                       double[:] delta,
                       double[:] weight,
                       long n_terms):
        self.from_index = from_index
        self.to_index = to_index
        self.delta = delta
        self.weight = weight
        self.n_terms = n_terms

    def __call__(self, double[:] x):
        cdef long i
        cdef double F = 0.
        cdef double f
        for i in xrange(self.n_terms):
            f = self.weight[i] * (self.delta[i]
                                  + x[self.from_index[i]]
                                  - x[self.to_index[i]])
            F += f * f
        return F
