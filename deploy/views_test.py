"""
Test view for SSE
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def test_sse(request):
    """Simple test page for SSE"""
    return render(request, 'deploy/test_sse.html')
