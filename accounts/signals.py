from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from django.shortcuts import redirect

# If user doesn't have a role yet, redirect to choose role
@receiver(user_signed_up)
def social_user_signed_up(request, user, **kwargs):
    if not user.role:
        request.session['role_pending'] = True