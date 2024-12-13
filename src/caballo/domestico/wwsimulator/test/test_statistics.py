import os
import unittest

from caballo.domestico.wwsimulator.statistics import WelfordEstimator
from pdsteele import DES_DIR

class TestStatistics(unittest.TestCase):
    def test_welford(self):
        estimator = WelfordEstimator()
        with open(os.path.join(DES_DIR, "uvs.dat"), "r") as data:
            for line in data:
                estimator.update(float(line))
        print(estimator)
        self.assertAlmostEqual(estimator.avg, 3.042, places=3)
        self.assertAlmostEqual(estimator.std, 1.693, places=3)
        self.assertAlmostEqual(estimator.min, 0.207, places=3)
        self.assertAlmostEqual(estimator.max, 11.219, places=3)

if __name__ == "__main__":
    unittest.main()