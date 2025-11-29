from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)

def is_staff(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff)
def user_list(request):
    """List all users"""
    users = User.objects.all().order_by('-is_active', 'username')
    return render(request, 'users/user_list.html', {'users': users})

@login_required
@user_passes_test(is_staff)
def user_create(request):
    """Create a new user"""
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            password = request.POST.get('password')
            is_staff = request.POST.get('is_staff') == 'on'
            is_superuser = request.POST.get('is_superuser') == 'on'
            
            # Validate required fields
            if not all([username, password]):
                messages.error(request, 'Username and password are required')
                return redirect('user_create')
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()
            
            logger.info(f'User {username} created by {request.user.username}')
            messages.success(request, f'User "{username}" created successfully')
            return redirect('user_list')
            
        except IntegrityError:
            messages.error(request, f'Username "{username}" already exists')
            return redirect('user_create')
        except Exception as e:
            logger.error(f'Error creating user: {e}')
            messages.error(request, f'Error creating user: {str(e)}')
            return redirect('user_create')
    
    return render(request, 'users/user_form.html', {'action': 'Create'})

@login_required
@user_passes_test(is_staff)
def user_edit(request, user_id):
    """Edit an existing user"""
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        try:
            user.email = request.POST.get('email')
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.is_staff = request.POST.get('is_staff') == 'on'
            user.is_superuser = request.POST.get('is_superuser') == 'on'
            user.is_active = request.POST.get('is_active') == 'on'
            user.save()
            
            logger.info(f'User {user.username} updated by {request.user.username}')
            messages.success(request, f'User "{user.username}" updated successfully')
            return redirect('user_list')
            
        except Exception as e:
            logger.error(f'Error updating user: {e}')
            messages.error(request, f'Error updating user: {str(e)}')
            return redirect('user_edit', user_id=user_id)
    
    return render(request, 'users/user_form.html', {
        'action': 'Edit',
        'user_obj': user
    })

@login_required
@user_passes_test(is_staff)
def user_reset_password(request, user_id):
    """Reset user password"""
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        try:
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not new_password:
                messages.error(request, 'Password is required')
                return redirect('user_reset_password', user_id=user_id)
            
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match')
                return redirect('user_reset_password', user_id=user_id)
            
            user.set_password(new_password)
            user.save()
            
            logger.info(f'Password reset for user {user.username} by {request.user.username}')
            messages.success(request, f'Password reset successfully for user "{user.username}"')
            return redirect('user_list')
            
        except Exception as e:
            logger.error(f'Error resetting password: {e}')
            messages.error(request, f'Error resetting password: {str(e)}')
            return redirect('user_reset_password', user_id=user_id)
    
    return render(request, 'users/user_reset_password.html', {'user_obj': user})

@login_required
@user_passes_test(is_staff)
def user_toggle_active(request, user_id):
    """Toggle user active status"""
    user = get_object_or_404(User, pk=user_id)
    
    # Prevent deactivating yourself
    if user.id == request.user.id:
        messages.error(request, 'You cannot deactivate your own account')
        return redirect('user_list')
    
    user.is_active = not user.is_active
    user.save()
    
    status = 'activated' if user.is_active else 'deactivated'
    logger.info(f'User {user.username} {status} by {request.user.username}')
    messages.success(request, f'User "{user.username}" {status} successfully')
    
    return redirect('user_list')

@login_required
@user_passes_test(is_staff)
def user_delete(request, user_id):
    """Delete a user"""
    user = get_object_or_404(User, pk=user_id)
    
    # Prevent deleting yourself
    if user.id == request.user.id:
        messages.error(request, 'You cannot delete your own account')
        return redirect('user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        
        logger.info(f'User {username} deleted by {request.user.username}')
        messages.success(request, f'User "{username}" deleted successfully')
        return redirect('user_list')
    
    return render(request, 'users/user_confirm_delete.html', {'user_obj': user})
