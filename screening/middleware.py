from django.shortcuts import redirect
from django.urls import resolve, reverse

class BusinessUserMiddleware:
    """
    Middleware to redirect business users to business-specific pages
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Regular user pages that should redirect to business equivalents
        self.redirect_map = {
            'dashboard': 'business_dashboard',
            'profile': 'business_profile',
            'upload_resume': 'bulk_screening',
        }
        
    def __call__(self, request):
        # Process request
        if request.user.is_authenticated:
            # Check if user is a business user
            has_business_profile = hasattr(request.user, 'business_profile')
            
            if has_business_profile:
                # Get current URL name
                current_url_name = resolve(request.path_info).url_name
                
                # Check if current URL is in redirect map
                if current_url_name in self.redirect_map:
                    # Redirect to business equivalent
                    return redirect(self.redirect_map[current_url_name])
        
        # Continue with the request
        response = self.get_response(request)
        return response 