from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Review
from .forms import ReviewForm
from screening.models import BusinessProfile

def home(request):
    reviews = Review.objects.filter(is_approved=True).order_by('-created_at')[:3]
    is_business_user = False
    
    if request.user.is_authenticated:
        try:
            business_profile = BusinessProfile.objects.get(user=request.user)
            is_business_user = True
        except BusinessProfile.DoesNotExist:
            pass
            
    context = {
        'reviews': reviews,
        'is_business_user': is_business_user
    }
    return render(request, 'home.html', context)

@login_required
def add_review(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            messages.success(request, 'Your review has been submitted and is pending approval.')
            return redirect('home')
    else:
        form = ReviewForm()
    return render(request, 'add_review.html', {'form': form})

@login_required
def my_reviews(request):
    reviews = Review.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_reviews.html', {'reviews': reviews}) 