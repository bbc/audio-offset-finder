from nose.tools import *
from offset_finder import *
from numpy.testing import *
import numpy as np

def test_truncate():
    a1 = np.array([])
    a2 = np.array([])
    r1, r2 = truncate(a1, a2)
    assert_array_equal(r1, a1)
    assert_array_equal(r2, a2)

    a1 = np.array([])
    a2 = np.array([0,1,2,3])
    r1, r2 = truncate(a1, a2)
    assert_array_equal(r1, a1)
    assert_array_equal(r2, np.array([1,2,3]))

    a1 = np.array([0,0,1,2])
    a2 = np.array([0,1,2,3])
    r1, r2 = truncate(a1, a2)
    assert_array_equal(r1, np.array([1,2]))
    assert_array_equal(r2, np.array([2,3]))

    a1 = np.array([1,2,3,4])
    a2 = np.array([2,3,4,5])
    r1, r2 = truncate(a1, a2)
    assert_array_equal(r1, a1)
    assert_array_equal(r2, a2)

def test_std_mfcc():
    m = np.array([[2,3,4], [4,5,5]])
    assert_array_equal(std_mfcc(m), np.array([[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]]))

def test_cross_correlation():
    m1 = np.array([[-0.5, -0.4, -0.4], [0.5, 0.5, 0.4], [0.1, -0.1, 0.1]])
    m2 = m1[1:]
    c = cross_correlation(m1, m2, 2)
    assert_equal(np.argmax(c), 1)

    m2 = m1
    c = cross_correlation(m1, m2, 2)
    assert_equal(np.argmax(c), 0)
