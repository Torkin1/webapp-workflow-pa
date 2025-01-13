from abc import ABC
from math import inf, sqrt

class WelfordEstimator():
    """
    Computes an estimate of the AVG and STD of a sequence of samples
    using the Welford's one-pass algorithm.
    > Lawrence M. Leemis_ Stephen K. Park - Discrete-Event Simulation_ A First Course-Prentice Hall (2004), Chapter 4. Statistics, p. 140, Algorithm 4.1.1
    """

    def __init__(self):
        self._n_samples = 0
        self._prev_n_samples = 0
        self._sum = 0
        
        self.avg = 0
        self.std = 0
        self.min = +inf
        self.max = -inf
    
    @property
    def n_samples(self):
        return self._n_samples
    
    @n_samples.setter
    def n_samples(self, value: float):
        if (value < self._n_samples):
            raise ValueError(f"New number of samples {value} cannot be less than current number of samples {self._n_samples}")
        self._prev_n_samples = self._n_samples
        self._n_samples = value
    
    def _update_avg(self, diff: float, delta: float):
        self.avg += diff * delta / self.n_samples
    
    def _update_std(self, diff: float, delta: float):
        self._sum += diff * diff * delta * self._prev_n_samples / self.n_samples
        self.std = sqrt(self._sum / self.n_samples)
    
    def _update_bounds(self, sample: float):
        if (sample > self.max):
            self.max = sample
        if (sample < self.min):
            self.min = sample
    
    def _update(self, sample: float):
        """
        Updates the statistics with a new sample. The delta parameter is
        the distance between the current sample and the previous one
        i.e. the distance can be in samples or in time units.
        """
        
        # inspired from pdsteele.des.uvs implementation
        if self.n_samples > 0:

            diff = sample - self.avg
            delta = self.n_samples - self._prev_n_samples

            self._update_avg(diff, delta)
            self._update_std(diff, delta)
            self._update_bounds(sample)
    
    def update(self, sample: float):
        self.n_samples += 1
        self._update(sample)
    
    def __str__(self):
        return "for a sample of size {0:d}\n".format(self._n_samples) \
            + "mean ................. = {0:7.8f}\n".format(self.avg) \
            + "standard deviation ... = {0:7.8f}\n".format(self.std) \
            + "minimum .............. = {0:7.8f}\n".format(self.min) \
            + "maximum .............. = {0:7.8f}\n".format(self.max) \

class WelfordTimeAveragedEstimator(WelfordEstimator):
    """
    A variant of the WelfordEstimator intended to be used to compute
    time-averaged statistics.
    > Lawrence M. Leemis_ Stephen K. Park - Discrete-Event Simulation_ A First Course-Prentice Hall (2004), Chapter 4. Statistics, p. 146, Theorem 4.1.4
    """

    def __init__(self):
        super().__init__()
    
    def update(self, sample: float, time: float):
        
        self.n_samples = time
        self._update(sample)

