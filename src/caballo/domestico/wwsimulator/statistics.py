from math import inf, sqrt


class WelfordEstimator():
    """
    Computes an estimate of the AVG and STD of a sequence of samples
    using the Welford's one-pass algorithm.
    > Lawrence M. Leemis_ Stephen K. Park - Discrete-Event Simulation_ A First Course-Prentice Hall (2004), Chapter 4. Statistics, p. 140, Algorithm 4.1.1
    """

    def __init__(self):
        self._n_samples = 0
        self._sum = 0
        
        self.avg = 0
        self.std = 0
        self.min = +inf
        self.max = -inf
    
    def update(self, sample: float):
        # inspired from pdsteele.des.uvs implementation
        self._n_samples += 1
        diff = sample - self.avg

        self._sum += diff * diff * (self._n_samples - 1.0) / self._n_samples
        self.avg += diff / self._n_samples
        if (sample > self.max):
            self.max = sample
        if (sample < self.min):
            self.min = sample
        self.std = sqrt(self._sum / self._n_samples)
    
    def __str__(self):
        return "for a sample of size {0:d}\n".format(self._n_samples) \
            + "mean ................. = {0:7.8f}\n".format(self.avg) \
            + "standard deviation ... = {0:7.8f}\n".format(self.std) \
            + "minimum .............. = {0:7.8f}\n".format(self.min) \
            + "maximum .............. = {0:7.8f}\n".format(self.max) \



