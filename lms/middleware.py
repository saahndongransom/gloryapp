from django.shortcuts import render
from django.conf import settings

class LMSOfflineMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/lms/'):
            if getattr(settings, 'LMS_OFFLINE', False):
                # Allow staff through
                user = getattr(request, 'user', None)
                if user and user.is_authenticated and user.is_staff:
                    return self.get_response(request)
                return render(request, 'lms/offline.html', {
                    'message': getattr(settings, 'LMS_OFFLINE_MESSAGE', 'The student portal is temporarily offline.')
                })
        return self.get_response(request)
