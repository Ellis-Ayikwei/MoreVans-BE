from django.http import HttpResponsePermanentRedirect

# middleware.py in any of your apps
class ConditionalSlashMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for certain URL patterns that should not have trailing slashes
        if request.path.startswith('/api/v1/') and not request.path.endswith('/'):
            # Don't add slashes to API endpoints
            pass
        elif not request.path.endswith('/') and not request.path.startswith('/admin/'):
            # For non-API, non-admin URLs that don't end with slash, redirect
            return HttpResponsePermanentRedirect(request.path + '/')
            
        return self.get_response(request)