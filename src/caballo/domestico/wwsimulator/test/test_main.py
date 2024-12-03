import unittest
import caballo.domestico.wwsimulator.main as main
import caballo.domestico.wwsimulator.des.rng as rng
import caballo.domestico.wwsimulator.des.rvgs as rvgs
import blist


class TestGreet(unittest.TestCase):
    def testGreet(self):
        self.assertEqual(main.greet(), "Hello, World!")

if __name__ == "__main__":
    unittest.main()