import inspect

from calendar import timegm
from datetime import datetime

from django.apps import apps as django_apps
from django.conf import settings
from django.contrib.auth import _clean_credentials
from django.contrib.auth.signals import user_login_failed
from django.utils.functional import lazy
from django.utils.timezone import is_naive, make_aware, utc
from django.views.decorators.debug import sensitive_variables
from django.contrib.auth import load_backend

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
    Return the User model that is active for SimpleJWT.
    """
    try:
        return django_apps.get_model(settings.SIMPLE_JWT_AUTH_USER_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured("SIMPLE_JWT_AUTH_USER_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "SIMPLE_JWT_AUTH_USER_MODEL refers to model '%s' that has not been installed" % settings.SIMPLE_JWT_AUTH_USER_MODEL
        )

def _get_backends(return_tuples=False):
    backends = []
    for backend_path in settings.SIMPLE_JWT_AUTHENTICATION_BACKENDS:
        backend = load_backend(backend_path)
        backends.append((backend, backend_path) if return_tuples else backend)
    if not backends:
        raise ImproperlyConfigured(
            'No authentication backends have been defined. Does '
            'SIMPLE_JWT_AUTHENTICATION_BACKENDS contain anything?'
        )
    return backends

@sensitive_variables('credentials')
def authenticate(request=None, **credentials):
    """
    If the given credentials are valid, return a User object.
    """
    for backend, backend_path in _get_backends(return_tuples=True):
        backend_signature = inspect.signature(backend.authenticate)
        try:
            backend_signature.bind(request, **credentials)
        except TypeError:
            # This backend doesn't accept these credentials as arguments. Try the next one.
            continue
        try:
            user = backend.authenticate(request, **credentials)
        except PermissionDenied:
            # This backend says to stop in our tracks - this user should not be allowed in at all.
            break
        if user is None:
            continue
        # Annotate the user object with the path of the backend.
        user.backend = backend_path
        return user

    # The credentials supplied are invalid to all backends, fire signal
    user_login_failed.send(sender=__name__, credentials=_clean_credentials(credentials), request=request)
