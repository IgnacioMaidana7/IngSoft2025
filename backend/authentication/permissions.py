from rest_framework.permissions import BasePermission
from authentication.models import EmpleadoUser


class IsSupermercadoAdmin(BasePermission):
    """
    Permiso que permite acceso solo a administradores de supermercado.
    """
    
    def has_permission(self, request, view):
        # Verificar que el usuario esté autenticado
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Verificar que NO sea un empleado (debe ser administrador)
        return not isinstance(request.user, EmpleadoUser)


class IsEmpleado(BasePermission):
    """
    Permiso base que permite acceso solo a empleados autenticados.
    """
    
    def has_permission(self, request, view):
        # Verificar que el usuario esté autenticado y sea un empleado
        return (
            request.user and 
            request.user.is_authenticated and 
            isinstance(request.user, EmpleadoUser) and
            request.user.is_active
        )


class IsReponedor(BasePermission):
    """
    Permiso que permite acceso solo a empleados con puesto de Reponedor.
    Tienen acceso a Productos e Inventario.
    """
    
    def has_permission(self, request, view):
        # Verificar que sea empleado autenticado
        if not (request.user and request.user.is_authenticated and isinstance(request.user, EmpleadoUser)):
            return False
        
        # Verificar que el puesto sea REPONEDOR
        return request.user.puesto == 'REPONEDOR' and request.user.is_active


class IsCajero(BasePermission):
    """
    Permiso que permite acceso solo a empleados con puesto de Cajero.
    Tienen acceso a Ventas.
    """
    
    def has_permission(self, request, view):
        # Verificar que sea empleado autenticado
        if not (request.user and request.user.is_authenticated and isinstance(request.user, EmpleadoUser)):
            return False
        
        # Verificar que el puesto sea CAJERO
        return request.user.puesto == 'CAJERO' and request.user.is_active


class IsReponedorOrAdmin(BasePermission):
    """
    Permiso que permite acceso a Reponedores o Administradores de supermercado.
    Para acceso a Productos e Inventario.
    """
    
    def has_permission(self, request, view):
        # Verificar que el usuario esté autenticado
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Si es administrador de supermercado, permitir acceso
        if not isinstance(request.user, EmpleadoUser):
            return True
        
        # Si es empleado, debe ser Reponedor
        return request.user.puesto == 'REPONEDOR' and request.user.is_active


class IsCajeroOrAdmin(BasePermission):
    """
    Permiso que permite acceso a Cajeros o Administradores de supermercado.
    Para acceso a Ventas.
    """
    
    def has_permission(self, request, view):
        # Verificar que el usuario esté autenticado
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Si es administrador de supermercado, permitir acceso
        if not isinstance(request.user, EmpleadoUser):
            return True
        
        # Si es empleado, debe ser Cajero
        return request.user.puesto == 'CAJERO' and request.user.is_active


class IsEmployeeOwner(BasePermission):
    """
    Permiso que verifica que el empleado pertenezca al supermercado correcto.
    """
    
    def has_object_permission(self, request, view, obj):
        # Si es administrador, verificar que el objeto pertenezca a su supermercado
        if not isinstance(request.user, EmpleadoUser):
            return hasattr(obj, 'supermercado') and obj.supermercado == request.user
        
        # Si es empleado, verificar que pertenezca al mismo supermercado que el objeto
        if hasattr(obj, 'supermercado'):
            return obj.supermercado == request.user.supermercado
        
        return True