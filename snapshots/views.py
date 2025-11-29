from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import SnapshotHistory
from inventory.models import Host, Group
from playbooks.models import Playbook


@login_required
def snapshot_history(request):
    """Display snapshot history with filters"""
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    host_filter = request.GET.get('host', '')
    group_filter = request.GET.get('group', '')
    playbook_filter = request.GET.get('playbook', '')
    search = request.GET.get('search', '')
    
    # Base queryset
    snapshots = SnapshotHistory.objects.select_related(
        'host', 'group', 'playbook', 'user'
    ).all()
    
    # Apply filters
    if status_filter:
        snapshots = snapshots.filter(status=status_filter)
    
    if host_filter:
        snapshots = snapshots.filter(host_id=host_filter)
    
    if group_filter:
        snapshots = snapshots.filter(group_id=group_filter)
    
    if playbook_filter:
        snapshots = snapshots.filter(playbook_id=playbook_filter)
    
    if search:
        snapshots = snapshots.filter(
            Q(snapshot_name__icontains=search) |
            Q(host__name__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Get statistics
    stats = {
        'total': SnapshotHistory.objects.count(),
        'active': SnapshotHistory.objects.filter(status='active').count(),
        'deleted': SnapshotHistory.objects.filter(status='deleted').count(),
        'failed': SnapshotHistory.objects.filter(status='failed').count(),
        'expired': SnapshotHistory.objects.filter(
            status='active',
            expires_at__lt=timezone.now()
        ).count(),
    }
    
    # Pagination
    paginator = Paginator(snapshots, 10)  # 10 snapshots per page
    page = request.GET.get('page')
    
    try:
        snapshots_page = paginator.page(page)
    except PageNotAnInteger:
        snapshots_page = paginator.page(1)
    except EmptyPage:
        snapshots_page = paginator.page(paginator.num_pages)
    
    # Get filter options
    hosts = Host.objects.filter(active=True).order_by('name')
    groups = Group.objects.all().order_by('name')
    playbooks = Playbook.objects.all().order_by('name')
    
    context = {
        'snapshots': snapshots_page,
        'paginator': paginator,
        'stats': stats,
        'hosts': hosts,
        'groups': groups,
        'playbooks': playbooks,
        'status_filter': status_filter,
        'host_filter': host_filter,
        'group_filter': group_filter,
        'playbook_filter': playbook_filter,
        'search': search,
    }
    
    return render(request, 'snapshots/history.html', context)


@login_required
def snapshot_detail(request, pk):
    """Display detailed information about a snapshot"""
    from django.shortcuts import get_object_or_404
    
    snapshot = get_object_or_404(SnapshotHistory, pk=pk)
    
    context = {
        'snapshot': snapshot,
    }
    
    return render(request, 'snapshots/detail.html', context)


@login_required
def delete_snapshot(request, pk):
    """Manually delete a snapshot from vCenter"""
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from deploy.vcenter_snapshot import get_vcenter_connection, delete_snapshot
    from settings.models import VCenterCredential
    from pyVim.connect import Disconnect
    import logging
    
    logger = logging.getLogger('snapshots')
    snapshot = get_object_or_404(SnapshotHistory, pk=pk)
    
    # Only allow deletion of active snapshots
    if snapshot.status != 'active':
        messages.warning(request, f'Snapshot "{snapshot.snapshot_name}" is already {snapshot.status}.')
        return redirect('snapshot_detail', pk=pk)
    
    try:
        # Get vCenter credentials
        vcenter_server = snapshot.host.vcenter_server
        if not vcenter_server:
            messages.error(request, 'Host does not have a vCenter server configured.')
            return redirect('snapshot_detail', pk=pk)
        
        # VCenterCredential.host matches Host.vcenter_server
        vcenter_cred = VCenterCredential.objects.filter(host=vcenter_server).first()
        if not vcenter_cred:
            messages.error(request, f'No credentials found for vCenter server: {vcenter_server}')
            return redirect('snapshot_detail', pk=pk)
        
        # Connect to vCenter
        si = get_vcenter_connection(vcenter_server, vcenter_cred.user, vcenter_cred.get_password())
        if not si:
            messages.error(request, 'Failed to connect to vCenter.')
            return redirect('snapshot_detail', pk=pk)
        
        try:
            # Delete snapshot from vCenter (returns tuple: success, message)
            success, message = delete_snapshot(si, snapshot.host.name, snapshot.snapshot_name)
            
            if success:
                # Mark as deleted in database
                snapshot.mark_as_deleted()
                messages.success(request, f'Snapshot "{snapshot.snapshot_name}" deleted successfully!')
                logger.info(f'[MANUAL-DELETE] Snapshot {snapshot.snapshot_name} deleted by {request.user.username}')
            else:
                # Even if vCenter deletion fails, mark as deleted in DB to avoid zombie records
                # This handles cases where snapshot was already deleted in vCenter
                if 'not found' in message.lower():
                    snapshot.mark_as_deleted()
                    messages.warning(request, f'Snapshot not found in vCenter (already deleted). Marked as deleted in database.')
                    logger.warning(f'[MANUAL-DELETE] Snapshot {snapshot.snapshot_name} not found in vCenter, marked as deleted in DB')
                else:
                    messages.error(request, f'Failed to delete snapshot: {message}')
                    logger.error(f'[MANUAL-DELETE] Failed to delete snapshot {snapshot.snapshot_name}: {message}')
        
        finally:
            Disconnect(si)
    
    except Exception as e:
        messages.error(request, f'Error deleting snapshot: {str(e)}')
        logger.error(f'[MANUAL-DELETE] Error deleting snapshot {snapshot.snapshot_name}: {str(e)}')
    
    return redirect('snapshot_detail', pk=pk)
