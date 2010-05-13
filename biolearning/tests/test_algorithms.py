import numpy as np
import scipy.io as sio

from nose.tools import *
from nose.plugins.attrib import attr

from biolearning.algorithms import *
from biolearning.algorithms import _soft_thresholding

class TestAlgorithms(object):
    """
    Results generated with the original matlab code
    """

    def setup(self):
        data = sio.loadmat('tests/toy_dataA.mat', struct_as_record=False)
        self.X = data['X']
        self.Y = data['Y']

    def test_data(self):
        assert_equals((30, 40), self.X.shape)
        assert_equals((30, 1), self.Y.shape)

    def test_rls(self):
        # case n >= d
        for penalty in np.linspace(0.0, 1.0, 5):
            value = ridge_regression(self.X, self.Y, penalty)
            assert_equal(value.shape, (self.X.shape[1], 1))

        expected = ridge_regression(self.X, self.Y, 0.0)
        value = ridge_regression(self.X, self.Y)
        assert_true(np.allclose(expected, value))

        # case d > n
        X = self.X.T
        Y = self.X[0:1,:].T
        for penalty in np.linspace(0.0, 1.0, 5):
            value = ridge_regression(X, Y, penalty)
            assert_equal(value.shape, (X.shape[1], 1))

        expected = ridge_regression(X, Y, 0.0)
        value = ridge_regression(X, Y)
        assert_true(np.allclose(expected, value))

    def test_l1l2_regularization(self):
        from itertools import product
        n, m = self.X.shape

        values = np.linspace(0.1, 1.0, 5)
        for mu, tau in product(values, values):
            beta, k1 = l1l2_regularization(self.X, self.Y, mu, tau,
                                           returns_iterations=True)
            assert_equal(beta.shape, (self.X.shape[1], 1))

            beta, k2 = l1l2_regularization(self.X, self.Y, mu, tau,
                                           tolerance=1e-3,
                                           returns_iterations=True)
            assert_true(k2 <= k1)

            beta, k3 = l1l2_regularization(self.X, self.Y, mu, tau,
                                           tolerance=1e-3, kmax=100,
                                           returns_iterations=True)
            assert_true(k3 <= k2)
            assert_true(k3 == 100)

            beta1, k1 = l1l2_regularization(self.X, self.Y, mu, tau,
                                            returns_iterations=True)
            beta2, k2 = l1l2_regularization(self.X, self.Y, mu, tau,
                                            beta=beta1,
                                            returns_iterations=True)
            assert_true(k2 <= k1)

    def test_l1l2_path(self):
        values = np.linspace(0.1, 1.0, 5)
        beta_path = l1l2_path(self.X, self.Y, 0.1, values)

        assert_true(len(beta_path) <= len(values))
        for i in xrange(1, len(beta_path)):

            b = beta_path[i]
            b_prev = beta_path[i-1]

            selected_prev = len(b_prev[b_prev != 0.0])
            selected = len(b[b != 0.0])
            assert_true(selected <= selected_prev)

    def test_l1l2_path_saturation(self):
        values = [0.1, 1e1, 1e3, 1e4]
        beta_path = l1l2_path(self.X, self.Y, 0.1, values)
        assert_equals(len(beta_path), 2)

        for i in xrange(2):
            b = beta_path[i]
            selected = len(b[b != 0.0])

            assert_true(selected <= len(b))
            
    def test_l1_bounds(self):
        out = l1_bounds(self.X, self.Y)
        
        assert_equals(2, len(out))
        assert_true(out[0] < out[1])
        
        out_ = l1_bounds(self.X, self.Y, 1e0)
        assert_true(out[0] < out_[0])
        assert_true(out[1] > out_[1])    
        assert_true(out_[0] < out_[1])
        
        assert_raises(ValueError, l1_bounds, self.X, self.Y, out[1])
        assert_raises(ValueError, l1_bounds, self.X, self.Y, -out[0]*2)
        assert_raises(ValueError, l1_bounds, self.X, self.Y, out[1]*2)
        
    def test_soft_thresholding(self):
        beta = ridge_regression(self.X, self.Y)
        for th in np.linspace(0.0, 10.0, 50):
            out = _soft_thresholding(beta, th)
    
            # Verbose and slow version
            out_exp = beta - (np.sign(beta) * th/2.0)
            out_exp[np.abs(beta) <= th/2.0] = 0.0
            
            assert_true(np.allclose(out, out_exp))