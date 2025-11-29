from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.contrib import messages
from settings.models import VCenterCredential
from .vcenter_service import VCenterService
import csv
import logging

logger = logging.getLogger(__name__)


@login_required
def vm_list(request):
    """
    Vista principal para listar VMs desde vCenter.
    Permite seleccionar vCenter, buscar y paginar resultados.
    """
    # Obtener todos los vCenters disponibles
    vcenters = VCenterCredential.objects.all().order_by('name')
    
    # Obtener parámetros de la solicitud
    vcenter_id = request.GET.get('vcenter')
    vlan_filter = request.GET.get('vlan', '').strip()
    search_query = request.GET.get('search', '').strip()
    search_field = request.GET.get('search_field', 'all')
    page_number = request.GET.get('page', 1)
    
    vms = []
    all_vlans = []
    selected_vcenter = None
    error_message = None
    
    # Si se seleccionó un vCenter, obtener las VMs
    if vcenter_id:
        try:
            selected_vcenter = VCenterCredential.objects.get(id=vcenter_id)
            
            # Conectar a vCenter y obtener VMs
            service = VCenterService(
                host=selected_vcenter.host,
                port=443,  # Puerto por defecto
                user=selected_vcenter.user,
                pwd=selected_vcenter.get_password(),
                disable_ssl_verification=not selected_vcenter.ssl_verify
            )
            
            try:
                service.connect()
                
                # Buscar o listar todas
                if search_query:
                    vms = service.search_vms(search_query, search_field)
                else:
                    vms = service.get_all_vms()
                
                logger.info(f"Retrieved {len(vms)} VMs from vCenter {selected_vcenter.name}")
                
                # Extraer todas las VLANs únicas
                vlans_set = set()
                for vm in vms:
                    for network in vm.get('networks', []):
                        if network and network != 'Unknown':
                            vlans_set.add(network)
                all_vlans = sorted(list(vlans_set))
                
                # Filtrar por VLAN si se seleccionó una
                if vlan_filter:
                    vms = [vm for vm in vms if vlan_filter in vm.get('networks', [])]
                    logger.info(f"Filtered to {len(vms)} VMs in VLAN {vlan_filter}")
                
            except Exception as e:
                error_message = f"Error al conectar a vCenter: {str(e)}"
                logger.error(error_message)
                messages.error(request, error_message)
            finally:
                service.disconnect()
                
        except VCenterCredential.DoesNotExist:
            error_message = "vCenter no encontrado"
            messages.error(request, error_message)
        except Exception as e:
            error_message = f"Error inesperado: {str(e)}"
            logger.error(error_message)
            messages.error(request, error_message)
    
    # Paginar resultados
    paginator = Paginator(vms, 50)  # 50 VMs por página
    page_obj = paginator.get_page(page_number)
    
    context = {
        'vcenters': vcenters,
        'selected_vcenter': selected_vcenter,
        'vms': page_obj,
        'all_vlans': all_vlans,
        'vlan_filter': vlan_filter,
        'search_query': search_query,
        'search_field': search_field,
        'total_vms': len(vms),
        'error_message': error_message,
    }
    
    return render(request, 'addressing/vm_list.html', context)


@login_required
def export_csv(request):
    """
    Exporta la lista de VMs a CSV.
    """
    vcenter_id = request.GET.get('vcenter')
    vlan_filter = request.GET.get('vlan', '').strip()
    search_query = request.GET.get('search', '').strip()
    search_field = request.GET.get('search_field', 'all')
    
    if not vcenter_id:
        messages.error(request, "Debe seleccionar un vCenter")
        return redirect('vm_list')
    
    try:
        selected_vcenter = VCenterCredential.objects.get(id=vcenter_id)
        
        # Conectar a vCenter y obtener VMs
        service = VCenterService(
            host=selected_vcenter.host,
            port=443,
            user=selected_vcenter.user,
            pwd=selected_vcenter.get_password(),
            disable_ssl_verification=not selected_vcenter.ssl_verify
        )
        
        try:
            service.connect()
            
            # Buscar o listar todas
            if search_query:
                vms = service.search_vms(search_query, search_field)
            else:
                vms = service.get_all_vms()
            
            # Filtrar por VLAN si se seleccionó una
            if vlan_filter:
                vms = [vm for vm in vms if vlan_filter in vm.get('networks', [])]
            
            # Crear respuesta CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="vms_{selected_vcenter.name}.csv"'
            response.write('\ufeff')  # BOM para Excel UTF-8
            
            writer = csv.writer(response)
            
            # Encabezados
            writer.writerow([
                'VM Name',
                'Hostname',
                'IP Address',
                'MAC Address',
                'VLAN/Network',
                'Operating System',
                'Power State',
                'Additional IPs',
                'Additional MACs',
                'Additional VLANs'
            ])
            
            # Datos
            for vm in vms:
                # IPs adicionales (después de la primera)
                additional_ips = ', '.join(vm.get('ips', [])[1:]) if len(vm.get('ips', [])) > 1 else ''
                # MACs adicionales (después de la primera)
                additional_macs = ', '.join(vm.get('macs', [])[1:]) if len(vm.get('macs', [])) > 1 else ''
                # VLANs adicionales (después de la primera)
                additional_vlans = ', '.join(vm.get('networks', [])[1:]) if len(vm.get('networks', [])) > 1 else ''
                
                writer.writerow([
                    vm.get('vm_name', ''),
                    vm.get('hostname', ''),
                    vm.get('ip_primary', ''),
                    vm.get('mac_primary', ''),
                    vm.get('network_primary', 'Unknown'),
                    vm.get('os', ''),
                    vm.get('power_state', ''),
                    additional_ips,
                    additional_macs,
                    additional_vlans
                ])
            
            logger.info(f"Exported {len(vms)} VMs to CSV from vCenter {selected_vcenter.name}")
            return response
            
        except Exception as e:
            error_message = f"Error al obtener VMs: {str(e)}"
            logger.error(error_message)
            messages.error(request, error_message)
            return redirect('vm_list')
        finally:
            service.disconnect()
            
    except VCenterCredential.DoesNotExist:
        messages.error(request, "vCenter no encontrado")
        return redirect('vm_list')
    except Exception as e:
        logger.error(f"Error en exportación CSV: {str(e)}")
        messages.error(request, f"Error al exportar: {str(e)}")
        return redirect('vm_list')
