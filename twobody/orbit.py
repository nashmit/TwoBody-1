# Third-party
import astropy.time as at
import astropy.units as u

# Project
from .core import rv_from_elements
from . import elements as elem
from .transforms import get_t0, a1_sini, mf


__all__ = ['KeplerOrbit']


class KeplerOrbit(object):

    def __init__(self, elements=None, elements_type='kepler', **kwargs):
        """

        Parameters
        ----------

        Examples
        --------


        """

        if elements is None:
            elements_cls = getattr(elem,
                                   "{0}Elements"
                                   .format(elements_type.capitalize()))

            # pass everything in kwargs to the class initializer
            elements = elements_cls(**kwargs)

        elif not isinstance(elements, elem.OrbitalElements):
            raise TypeError("'elements' must be an instance of an "
                            "OrbitalElements subclass.")

        self.elements = elements





    def t0(self, ref_mjd):
        """Un-mod the phase at pericenter, ``phi0``, to a time closest to the
        specified reference epoch.

        Parameters
        ----------
        ref_mjd : numeric
            Reference time in Barycentric MJD to get the pericenter time
            ``t0`` relative to.

        Returns
        -------
        t0 : `~astropy.time.Time`
            Pericenter time closest to input epoch.

        """
        return get_t0(self.phi0, self.P, ref_mjd)

    def _generate_rv_curve(self, t):
        if isinstance(t, at.Time):
            _t = t.tcb.mjd
        else:
            _t = t

        rv = rv_from_elements(times=_t,
                              P=self.P.to(u.day).value,
                              K=self.K.to(u.m/u.s).value,
                              e=self.ecc,
                              omega=self.omega.to(u.radian).value,
                              phi0=self.phi0.to(u.radian).value,
                              anomaly_tol=self.anomaly_tol)

        if self.trend is not None:
            v_trend = self.trend(_t).to(u.m/u.s).value
            rv += v_trend

        return rv

    def generate_rv_curve(self, t):
        """Generate a radial velocity curve evaluated at the specified times
        with the instantiated parameters.

        Parameters
        ----------
        t : array_like, `~astropy.time.Time`
            Time array. Either in BMJD or as an Astropy time.

        Returns
        -------
        rv : astropy.units.Quantity [speed]
        """
        rv = self._generate_rv_curve(t)
        return (rv*u.m/u.s).to(u.km/u.s)

    def __call__(self, t):
        return self.generate_rv_curve(t)

    def plot(self, t, ax=None, rv_unit=None, t_kwargs=None, plot_kwargs=None):
        """Plot the RV curve at the specified times.

        Parameters
        ----------
        t : array_like, `~astropy.time.Time`
            Time array. Either in BMJD or as an Astropy time.
        ax : `~matplotlib.axes.Axes`, optional
            The axis to draw on (default is to grab the current
            axes using `~matplotlib.pyplot.gca`).
        rv_unit : `~astropy.units.UnitBase`, optional
            Units to plot the radial velocities in (default is km/s).
        t_kwargs : dict, optional
            Keyword arguments passed to :class:`astropy.time.Time` with the
            input time array. For example, ``dict(format='mjd', scale='tcb')``
            for Barycentric MJD.
        plot_kwargs : dict, optional
            Any additional arguments or style settings passed to
            :func:`matplotlib.pyplot.plot`.

        Returns
        -------
        ax : `~matplotlib.axes.Axes`
            The matplotlib axes object that the RV curve was drawn on.

        """

        if ax is None:
            import matplotlib.pyplot as plt
            ax = plt.gca()

        if rv_unit is None:
            rv_unit = u.km/u.s

        if t_kwargs is None:
            t_kwargs = dict(format='mjd', scale='tcb')

        if plot_kwargs is None:
            plot_kwargs = dict()

        style = plot_kwargs.copy()
        style.setdefault('linestyle', '-')
        style.setdefault('alpha', 0.5)
        style.setdefault('marker', None)

        if not isinstance(t, at.Time):
            t = at.Time(t, **t_kwargs)
        rv = self.generate_rv_curve(t).to(rv_unit).value

        _t = getattr(getattr(t, t_kwargs['scale']), t_kwargs['format'])
        ax.plot(_t, rv, **style)

        return ax

    # --------------------------------------------------------------------------
    # Computed attributes

    @property
    def a1_sini(self):
        return a1_sini(self.P, self.K, self.ecc)

    @property
    def mf(self):
        return mf(self.P, self.K, self.ecc)
