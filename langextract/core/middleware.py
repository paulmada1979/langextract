"""
Minimal middleware for stateless API service.
"""

class StatelessMiddleware:
    """Minimal middleware that doesn't depend on Django's auth system."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Add any custom processing here if needed
        response = self.get_response(request)
        return response
    
    def process_request(self, request):
        # Process request if needed
        pass
    
    def process_response(self, request, response):
        # Process response if needed
        return response
