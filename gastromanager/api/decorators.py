from functools import wraps
from django.http import HttpResponseForbidden
from .models import Journal


def manager_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if the user's level is "Manager"
        if request.user.is_authenticated and request.user.level == "Manager":
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("No access")

    return _wrapped_view


def service_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if the user's level is "Service"
        if request.user.is_authenticated and request.user.level == "Service":
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("No access")

    return _wrapped_view


def production_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if the user's level is "Production"
        if request.user.is_authenticated and request.user.level == "Production":
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("No access")

    return _wrapped_view


# DONT TOUCH!
def register_activity(action_func):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Run the view and get the response
            response = view_func(request, *args, **kwargs)
            if request.method == "POST":
                # Get the description of the action
                action_description = action_func(request)
                if action_description is not None:
                    # Register the action in the "Journal" model
                    Journal.objects.create(user=request.user, action=action_description)
            return response  # Return the response obtained from running the view

        return _wrapped_view

    return decorator


# DONT TOUCH
