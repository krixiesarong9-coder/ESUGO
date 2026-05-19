from .models import Cart, Profile


def user_profile(request):
    """Make user profile and cart available in all templates"""
    profile = None
    cart = None
    if request.user.is_authenticated:
        profile, created = Profile.objects.get_or_create(user=request.user)
        cart = Cart.objects.filter(user=request.user).first()
    return {
        'user_profile': profile,
        'cart': cart,
    }
