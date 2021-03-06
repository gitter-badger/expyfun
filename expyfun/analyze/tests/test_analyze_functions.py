from nose.tools import assert_raises, assert_equal, assert_true
from numpy.testing import assert_allclose, assert_array_equal
try:
    from scipy.special import logit as splogit
except ImportError:
    splogit = None
import numpy as np
import warnings

import expyfun.analyze as ea

warnings.simplefilter('always')


def test_presses_to_hmfc():
    """Test converting press times to HMFC"""
    # Simple example
    targets = [0., 1.]
    foils = [0.5, 1.5]
    tmin, tmax = 0.1, 0.6

    presses = [0.25, 1.25]
    hmfco = [2, 0, 0, 2, 0]
    out = ea.press_times_to_hmfc(presses, targets, foils, tmin, tmax)
    assert_array_equal(out, hmfco)

    presses = [0.75, 1.601]  # just past the boundary
    hmfco = [0, 2, 2, 0, 0]
    out = ea.press_times_to_hmfc(presses, targets, foils, tmin, tmax)
    assert_array_equal(out, hmfco)

    presses = [0.75, 1.55]  # smaller than tmin
    hmfco = [1, 1, 1, 1, 0]
    out = ea.press_times_to_hmfc(presses, targets, foils, tmin, tmax)
    assert_array_equal(out, hmfco)

    presses = [0.75, 2.11]  # greater than tmax
    hmfco = [0, 2, 1, 1, 1]
    out = ea.press_times_to_hmfc(presses, targets, foils, tmin, tmax)
    assert_array_equal(out, hmfco)

    # A complicated example
    targets = [0, 2, 3]
    foils = [1, 4]
    tmin, tmax = 0., 0.5

    presses = [0.1, 1.2, 1.3, 2.1, 2.7, 5.]  # multiple presses to same targ
    hmfco = [2, 1, 1, 1, 2]

    out = ea.press_times_to_hmfc(presses, targets, foils, tmin, tmax)
    assert_array_equal(out, hmfco)

    presses = []  # no presses
    hmfco = [0, 3, 0, 2, 0]
    out = ea.press_times_to_hmfc(presses, targets, foils, tmin, tmax)
    assert_array_equal(out, hmfco)

    presses = [-1, 7, 8]  # all errant presses
    hmfco = [0, 3, 0, 2, 3]
    out = ea.press_times_to_hmfc(presses, targets, foils, tmin, tmax)
    assert_array_equal(out, hmfco)

    # Bad inputs
    assert_raises(ValueError, ea.press_times_to_hmfc,
                  presses, targets, foils, tmin, 1.1)


def test_dprime():
    """Test dprime and dprime_2afc accuracy
    """
    assert_raises(TypeError, ea.dprime, 'foo', 0, 0, 0)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        ea.dprime((1.1, 0, 0, 0))
    assert_equal(len(w), 1)
    assert_equal(0, ea.dprime((1, 0, 1, 0)))
    assert_equal(np.inf, ea.dprime((1, 0, 2, 1), False))
    assert_equal(ea.dprime((5, 0, 1, 0)), ea.dprime_2afc((5, 1)))
    assert_raises(ValueError, ea.dprime, np.ones((5, 4, 3)))
    assert_raises(ValueError, ea.dprime, (1, 2, 3))
    assert_raises(ValueError, ea.dprime_2afc, (1, 2, 3))
    assert_equal(np.sum(ea.dprime_2afc([[5, 1], [1, 5]])), 0)
    # test simple larger dimensionality support
    assert_equal(ea.dprime((5, 0, 1, 0)), ea.dprime([[[5, 0, 1, 0]]])[0][0])


def test_logit():
    """Test logit calculations
    """
    assert_raises(ValueError, ea.logit, 2)
    # On some versions, this throws warnings about divide-by-zero
    with warnings.catch_warnings(record=True):
        warnings.simplefilter('always')
        assert_equal(ea.logit(0), -np.inf)
        assert_equal(ea.logit(1), np.inf)
    assert_true(ea.logit(1, max_events=1) < np.inf)
    assert_equal(ea.logit(0.5), 0)
    if splogit is not None:
        # Travis doesn't support scipy.special.logit, but this passes locally:
        foo = np.random.rand(5)
        assert_allclose(ea.logit(foo), splogit(foo))
    foo = np.array([[0, 0.5, 1], [1, 0.5, 0]])
    bar = np.ones_like(foo).astype(int)
    assert_true(np.all(np.equal(ea.logit(foo, 1), np.zeros_like(foo))))
    assert_true(np.all(np.equal(ea.logit(foo, [1, 1, 1]), np.zeros_like(foo))))
    assert_true(np.all(np.equal(ea.logit(foo, bar), np.zeros_like(foo))))
    assert_raises(ValueError, ea.logit, foo, [1, 1])  # can't broadcast


def test_sigmoid():
    """Test sigmoidal fitting and generation
    """
    n_pts = 1000
    x = np.random.randn(n_pts)
    p0 = (0., 1., 0., 1.)
    y = ea.sigmoid(x, *p0)
    assert_true(np.all(np.logical_and(y <= 1, y >= 0)))
    p = ea.fit_sigmoid(x, y)
    assert_allclose(p, p0, atol=1e-4, rtol=1e-4)
    p = ea.fit_sigmoid(x, y, (0, 1, None, None), ('upper', 'lower'))
    assert_allclose(p, p0, atol=1e-4, rtol=1e-4)

    y += np.random.rand(n_pts) * 0.01
    p = ea.fit_sigmoid(x, y)
    assert_allclose(p, p0, atol=0.1, rtol=0.1)


def test_rt_chisq():
    """Test reaction time chi-square fitting
    """
    # 1D should return single float
    foo = np.random.rand(30)
    assert_raises(ValueError, ea.rt_chisq, foo - 1.)
    assert_equal(np.array(ea.rt_chisq(foo)).shape, ())
    # 2D should return array with shape of input but without ``axis`` dimension
    foo = np.random.rand(30).reshape((2, 3, 5))
    for axis in range(-1, foo.ndim):
        bar = ea.rt_chisq(foo, axis=axis)
        assert_true(np.all(np.equal(np.delete(foo.shape, axis),
                                    np.array(bar.shape))))
    foo_bad = np.concatenate((np.random.rand(30), [100.]))
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        bar = ea.rt_chisq(foo_bad)
    assert_equal(len(w), 1)  # warn that there was a likely bad value
