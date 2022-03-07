from calendar import timegm
from datetime import datetime

from django.conf import settings
from django.utils.functional import lazy
from django.utils.timezone import is_naive, make_aware, utc


def make_utc(dt):
    if settings.USE_TZ and is_naive(dt):
        return make_aware(dt, timezone=utc)

    return dt


def aware_utcnow():
    return make_utc(datetime.utcnow())


def datetime_to_epoch(dt):
    return timegm(dt.utctimetuple())


def datetime_from_epoch(ts):
    return make_utc(datetime.utcfromtimestamp(ts))


def format_lazy(s, *args, **kwargs):
    return s.format(*args, **kwargs)


format_lazy = lazy(format_lazy, str)

def get_user_model():
    """
    Return the User model that is active in this project.
    """
    try:
        return django_apps.get_model(settings.SIMPLE_JWT_AUTH_USER_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured("SIMPLE_JWT_AUTH_USER_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "SIMPLE_JWT_AUTH_USER_MODEL refers to model '%s' that has not been installed" % settings.SIMPLE_JWT_AUTH_USER_MODEL
        )
