"""
Function for querying Patchs
"""
from dascore.constants import PatchType
from dascore.utils.patch import _AttrsCoordsMixer, _get_history_str, patch_function
from dascore.utils.time import get_select_time


def _prepare_kwargs(patch, kwargs):
    """Maybe convert times to datetime, get min/max values."""
    if "time" in kwargs:
        tmin = patch.attrs.time_min
        tmax = patch.attrs.time_max
        times = tuple(
            get_select_time(x, tmin, tmax) if x is not None else x
            for x in kwargs["time"]
        )
        kwargs["time"] = times
    # convert (start, end) to slice(start, end)
    kwargs = {
        i: slice(v[0], v[1]) if isinstance(v, (list, tuple)) else v
        for i, v in kwargs.items()
    }
    return kwargs


@patch_function(history=None)
def select(patch: PatchType, *, copy=False, **kwargs) -> PatchType:
    """
    Return a subset of the trace based on query parameters.

    Any dimension of the data can be passed as key, and the values
    should either be a Slice or a tuple of (min, max) for that
    dimension.

    The time dimension is handled specially in that either floats,
    datetime64 or datetime objects can be used to specify relative
    or absolute times, respectively.

    Parameters
    ----------
    copy
        If True, copy the resulting data. This is needed so the old
        array can get gc'ed and memory freed.
    **kwargs
        Used to specify the dimension and slices to select on.

    Examples
    --------
    >>> # select meters 50 to 300
    >>> import numpy as np
    >>> from dascore.examples import get_example_patch
    >>> tr = get_example_patch()
    >>> new = tr.select(distance=(50,300))
    """
    kwargs = _prepare_kwargs(patch, kwargs)
    # convert tuples into slices
    new = patch._data_array.sel(**kwargs)
    # no slicing was performed, just return original.
    if new.data.shape == patch.data.shape:
        return patch
    # prepare outputs
    data = new.data if not copy else new.data.copy()
    attrs = dict(new.attrs)
    attrs["history"] = _get_history_str(patch, select, **kwargs)
    attrs, coords = _AttrsCoordsMixer(attrs, new.coords, new.dims)()
    return patch.__class__(data, attrs=attrs, coords=coords, dims=patch.dims)
