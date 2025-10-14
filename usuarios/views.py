from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Usuario, PerfilHijo, RecargaSaldo
from .forms import RecargaSaldoForm, PerfilHijoForm, TarjetaManualForm
from ventas.models import Venta, DetalleVenta
from productos.models import Producto

@login_required
def dashboard(request):
    """
    Vista principal del dashboard según el tipo de usuario
    """
    hoy = timezone.now().date()
    
    context = {
        'usuario': request.user,
        'fecha_actual': timezone.now(),
    }
    
    if request.user.tipo_usuario == 'administrador':
        # Dashboard para administrador
        ventas_hoy = Venta.objects.filter(fecha_venta__date=hoy, estado='pagada')
        total_ventas = ventas_hoy.aggregate(total=Sum('total'))['total'] or 0
        
                # Estadísticas generales para administrador
        ventas_hoy = Venta.objects.filter(fecha_venta__date=hoy, estado='pagada')
        total_ventas_hoy = ventas_hoy.aggregate(total=Sum('total'))['total'] or 0
        total_transacciones_hoy = ventas_hoy.count()
        
        # Calcular promedio de venta
        promedio_venta_hoy = 0
        if total_transacciones_hoy > 0:
            promedio_venta_hoy = total_ventas_hoy / total_transacciones_hoy
        
        # Comparativa con la semana anterior
        hace_una_semana = hoy - timedelta(days=7)
        ventas_semana_pasada = Venta.objects.filter(
            fecha_venta__date=hace_una_semana,
            estado='pagada'
        ).aggregate(total=Sum('total'))['total'] or 0
        
        # Cálculo de crecimiento
        if ventas_semana_pasada > 0:
            crecimiento = ((total_ventas - ventas_semana_pasada) / ventas_semana_pasada) * 100
        else:
            crecimiento = 100 if total_ventas > 0 else 0
        
        # Calcular promedio de venta
        total_transacciones_hoy = ventas_hoy.count()
        promedio_venta_hoy = 0
        if total_transacciones_hoy > 0:
            promedio_venta_hoy = total_ventas / total_transacciones_hoy

        context.update({
            'total_ventas_hoy': total_ventas,
            'total_transacciones_hoy': total_transacciones_hoy,
            'promedio_venta_hoy': promedio_venta_hoy,
            'total_usuarios': Usuario.objects.filter(activo=True).count(),
            'total_hijos': PerfilHijo.objects.filter(activo=True).count(),
            'productos_stock_bajo': Producto.objects.filter(
                stock_actual__lte=F('stock_minimo'),
                requiere_stock=True
            ).count(),
            'ventas_semana_pasada': ventas_semana_pasada,
            'crecimiento_ventas': crecimiento,
            
            # Últimas actividades
            'ultimas_ventas': Venta.objects.filter(
                estado='pagada', 
                fecha_venta__date=hoy
            ).select_related('cajero').order_by('-fecha_venta')[:8],
            'productos_populares': Producto.objects.annotate(
                total_vendido=Count('ventas_detalle')
            ).filter(total_vendido__gt=0).order_by('-total_vendido')[:4],
        })
        
    elif request.user.tipo_usuario == 'cajero':
        # Dashboard para cajero
        mis_ventas_hoy = Venta.objects.filter(
            cajero=request.user,
            fecha_venta__date=hoy,
            estado='pagada'
        )
        
        context.update({
            'mis_ventas_hoy': mis_ventas_hoy.aggregate(total=Sum('total'))['total'] or 0,
            'mis_transacciones_hoy': mis_ventas_hoy.count(),
            'mis_ultimas_ventas': mis_ventas_hoy.order_by('-fecha_venta')[:5],
        })
        
    elif request.user.tipo_usuario == 'padre':
        # Dashboard para padres
        mis_hijos = PerfilHijo.objects.filter(padre=request.user, activo=True)
        total_saldo = mis_hijos.aggregate(total=Sum('saldo_virtual'))['total'] or 0
        
        # Ultimas recargas
        ultimas_recargas = RecargaSaldo.objects.filter(
            hijo__padre=request.user
        ).order_by('-fecha_recarga')[:5]
        
        # Consumo del mes actual
        primer_dia_mes = hoy.replace(day=1)
        consumo_mes = Venta.objects.filter(
            hijo__padre=request.user,
            fecha_venta__date__gte=primer_dia_mes,
            estado='pagada'
        ).aggregate(total=Sum('total'))['total'] or 0
        
        context.update({
            'mis_hijos': mis_hijos,
            'total_saldo_hijos': total_saldo,
            'ultimas_recargas': ultimas_recargas,
            'consumo_mes_actual': consumo_mes,
            'hijos_saldo_bajo': mis_hijos.filter(saldo_virtual__lt=10000).count(),  # Menos de 10,000 Gs
        })
    
    return render(request, 'usuarios/dashboard.html', context)

@login_required
def perfil(request):
    """
    Vista del perfil del usuario
    """
    return render(request, 'usuarios/perfil.html', {
        'usuario': request.user
    })

@login_required
def lista_hijos(request):
    """
    Lista de hijos (para padres muestran sus hijos, para admin/cajeros todos)
    """
    if request.user.tipo_usuario == 'padre':
        hijos = PerfilHijo.objects.filter(
            padre=request.user,
            activo=True
        ).order_by('nombre_completo')
    else:
        hijos = PerfilHijo.objects.filter(
            activo=True
        ).order_by('nombre_completo')
    
    return render(request, 'usuarios/lista_hijos.html', {
        'hijos': hijos
    })

@login_required
def detalle_hijo(request, pk):
    """
    Detalle de un hijo
    """
    hijo = get_object_or_404(PerfilHijo, pk=pk)
    
    # Verificar permisos
    if request.user.tipo_usuario == 'padre' and hijo.padre != request.user:
        messages.error(request, 'No tienes permisos para ver este hijo.')
        return redirect('usuarios:lista_hijos')
    
    # Obtener historial de compras y recargas
    compras_recientes = Venta.objects.filter(
        hijo=hijo,
        estado='pagada'
    ).order_by('-fecha_venta')[:10]
    
    recargas_recientes = RecargaSaldo.objects.filter(
        hijo=hijo
    ).order_by('-fecha_recarga')[:10]
    
    return render(request, 'usuarios/detalle_hijo.html', {
        'hijo': hijo,
        'compras_recientes': compras_recientes,
        'recargas_recientes': recargas_recientes,
    })

@login_required
def crear_hijo(request):
    """
    Crear nuevo hijo (solo para padres o administradores)
    """
    if request.user.tipo_usuario not in ['padre', 'administrador']:
        messages.error(request, 'No tienes permisos para crear hijos.')
        return redirect('usuarios:dashboard')
    
    # Determinar el padre
    padre = None
    if request.user.tipo_usuario == 'padre':
        padre = request.user
    
    if request.method == 'POST':
        form = PerfilHijoForm(request.POST, padre=padre)
        
        # Si es administrador, obtener el padre seleccionado
        if request.user.tipo_usuario == 'administrador':
            padre_id = request.POST.get('padre_id')
            if padre_id:
                padre = get_object_or_404(Usuario, pk=padre_id, tipo_usuario='padre')
                form.padre = padre
        
        if form.is_valid():
            try:
                hijo = form.save()
                messages.success(request, f'Hijo {hijo.nombre_completo} creado exitosamente.')
                return redirect('usuarios:detalle_hijo', pk=hijo.pk)
            except Exception as e:
                messages.error(request, f'Error al crear el hijo: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = PerfilHijoForm(padre=padre)
    
    # Para administradores, mostrar lista de padres
    padres = None
    if request.user.tipo_usuario == 'administrador':
        padres = Usuario.objects.filter(tipo_usuario='padre', activo=True).order_by('first_name', 'last_name')
    
    return render(request, 'usuarios/crear_hijos.html', {
        'form': form,
        'padres': padres
    })

@login_required
def recarga_saldo(request, pk):
    """
    Recargar saldo virtual a un hijo
    """
    hijo = get_object_or_404(PerfilHijo, pk=pk)
    
    # Verificar permisos
    if request.user.tipo_usuario == 'padre' and hijo.padre != request.user:
        messages.error(request, 'No tienes permisos para recargar saldo a este hijo.')
        return redirect('usuarios:lista_hijos')
    
    # Obtener recargas recientes para mostrar en el sidebar
    recargas_recientes = RecargaSaldo.objects.filter(
        hijo=hijo
    ).order_by('-fecha_recarga')[:5]
    
    if request.method == 'POST':
        form = RecargaSaldoForm(request.POST, hijo=hijo)
        if form.is_valid():
            try:
                recarga = form.save(realizada_por=request.user)
                messages.success(request, f'Recarga de {recarga.monto:,.0f} Gs. realizada exitosamente.')
                return redirect('usuarios:detalle_hijo', pk=hijo.pk)
            except Exception as e:
                messages.error(request, f'Error al realizar la recarga: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RecargaSaldoForm(hijo=hijo)
    
    return render(request, 'usuarios/recarga_saldo.html', {
        'hijo': hijo,
        'form': form,
        'recargas_recientes': recargas_recientes,
    })

@login_required
def lista_usuarios(request):
    """
    Lista de usuarios del sistema con filtros de búsqueda (solo para administradores)
    """
    if request.user.tipo_usuario != 'administrador':
        messages.error(request, 'No tienes permisos para ver esta página.')
        return redirect('usuarios:dashboard')
    
    # Filtros de búsqueda
    usuarios = Usuario.objects.all()
    
    # Filtro por búsqueda de texto
    search = request.GET.get('search')
    if search:
        usuarios = usuarios.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Filtro por tipo de usuario
    tipo = request.GET.get('tipo')
    if tipo:
        usuarios = usuarios.filter(tipo_usuario=tipo)
    
    # Filtro por estado activo/inactivo
    activo = request.GET.get('activo')
    if activo == 'true':
        usuarios = usuarios.filter(activo=True)
    elif activo == 'false':
        usuarios = usuarios.filter(activo=False)
    
    # Ordenar usuarios
    usuarios = usuarios.order_by('tipo_usuario', 'first_name', 'last_name')
    
    # Estadísticas para el dashboard
    total_usuarios = Usuario.objects.count()
    usuarios_activos = Usuario.objects.filter(activo=True).count()
    
    # Usuarios que han accedido hoy
    from django.utils import timezone
    hoy = timezone.now().date()
    accesos_hoy = Usuario.objects.filter(
        last_login__date=hoy
    ).count()
    
    return render(request, 'usuarios/lista_usuarios.html', {
        'usuarios': usuarios,
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'accesos_hoy': accesos_hoy,
    })

@login_required
def crear_usuario(request):
    """
    Crear nuevo usuario (solo para administradores)
    """
    if request.user.tipo_usuario != 'administrador':
        messages.error(request, 'No tienes permisos para crear usuarios.')
        return redirect('usuarios:dashboard')
    
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            tipo_usuario = request.POST.get('tipo_usuario')
            password = request.POST.get('password')
            
            # Validaciones
            if not all([username, email, first_name, last_name, tipo_usuario, password]):
                messages.error(request, 'Todos los campos son requeridos.')
                return render(request, 'usuarios/crear_usuario.html')
            
            if Usuario.objects.filter(username=username).exists():
                messages.error(request, 'El nombre de usuario ya existe.')
                return render(request, 'usuarios/crear_usuario.html')
            
            if Usuario.objects.filter(email=email).exists():
                messages.error(request, 'El email ya está registrado.')
                return render(request, 'usuarios/crear_usuario.html')
            
            # Crear usuario
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                tipo_usuario=tipo_usuario
            )
            
            messages.success(request, f'Usuario {username} creado exitosamente.')
            return redirect('usuarios:lista_usuarios')
            
        except Exception as e:
            messages.error(request, f'Error al crear el usuario: {str(e)}')
    
    return render(request, 'usuarios/crear_usuario.html')

@login_required
def detalle_usuario(request, pk):
    """
    Vista de detalle de usuario
    """
    if request.user.tipo_usuario != 'administrador':
        messages.error(request, 'No tienes permisos para ver esta página.')
        return redirect('usuarios:dashboard')
    
    usuario = get_object_or_404(Usuario, pk=pk)
    
    # Estadísticas del usuario si es padre
    context = {'usuario': usuario}
    
    if usuario.tipo_usuario == 'padre':
        hijos = PerfilHijo.objects.filter(padre=usuario, activo=True)
        context.update({
            'hijos': hijos,
            'total_saldo': hijos.aggregate(total=Sum('saldo_virtual'))['total'] or 0,
        })
    
    # Si es cajero, mostrar estadísticas de ventas
    if usuario.tipo_usuario == 'cajero':
        ventas_cajero = Venta.objects.filter(cajero=usuario, estado='pagada')
        context.update({
            'total_ventas': ventas_cajero.aggregate(total=Sum('total'))['total'] or 0,
            'total_transacciones': ventas_cajero.count(),
        })
    
    return render(request, 'usuarios/detalle_usuario.html', context)

@login_required 
def editar_usuario(request, pk):
    """
    Vista para editar usuario (solo administradores)
    """
    if request.user.tipo_usuario != 'administrador':
        messages.error(request, 'No tienes permisos para editar usuarios.')
        return redirect('usuarios:dashboard')
    
    usuario = get_object_or_404(Usuario, pk=pk)
    
    # No permitir que el admin se edite a sí mismo
    if usuario.pk == request.user.pk:
        messages.error(request, 'No puedes editar tu propio usuario.')
        return redirect('usuarios:lista_usuarios')
    
    if request.method == 'POST':
        try:
            # Actualizar campos básicos
            usuario.first_name = request.POST.get('first_name', '')
            usuario.last_name = request.POST.get('last_name', '')
            usuario.email = request.POST.get('email', '')
            usuario.telefono = request.POST.get('telefono', '')
            usuario.activo = request.POST.get('activo') == 'on'
            
            # Solo permitir cambiar tipo de usuario si no es administrador
            if usuario.tipo_usuario != 'administrador':
                nuevo_tipo = request.POST.get('tipo_usuario')
                if nuevo_tipo in ['cajero', 'padre']:
                    usuario.tipo_usuario = nuevo_tipo
            
            # Cambiar contraseña si se proporciona
            nueva_password = request.POST.get('password')
            if nueva_password:
                usuario.set_password(nueva_password)
            
            usuario.save()
            messages.success(request, f'Usuario {usuario.username} actualizado correctamente.')
            return redirect('usuarios:detalle_usuario', pk=usuario.pk)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar usuario: {str(e)}')
    
    return render(request, 'usuarios/editar_usuario.html', {'usuario': usuario})

def logout_view(request):
    """
    Vista personalizada para logout que maneja GET y POST
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'Has cerrado sesión exitosamente. ¡Hasta pronto, {username}!')
    
    return redirect('login')


@login_required
def asignar_tarjeta(request, pk):
    """
    Asignar tarjeta exclusiva a un hijo
    """
    hijo = get_object_or_404(PerfilHijo, pk=pk)
    
    # Verificar permisos
    if request.user.tipo_usuario == 'padre' and hijo.padre != request.user:
        messages.error(request, 'No tienes permisos para asignar tarjeta a este hijo.')
        return redirect('usuarios:lista_hijos')
    
    if request.user.tipo_usuario not in ['padre', 'administrador']:
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('usuarios:dashboard')
    
    if request.method == 'POST':
        try:
            if hijo.numero_tarjeta:
                messages.warning(request, f'{hijo.nombre_completo} ya tiene una tarjeta asignada.')
            else:
                hijo.asignar_tarjeta()
                messages.success(request, f'Tarjeta asignada exitosamente a {hijo.nombre_completo}.')
                
                # Crear registro de transacción
                from .models import TransaccionTarjeta
                TransaccionTarjeta.objects.create(
                    hijo=hijo,
                    numero_tarjeta_utilizada=hijo.numero_tarjeta,
                    tipo_transaccion='ajuste',
                    monto=0,
                    saldo_anterior=hijo.saldo_virtual,
                    saldo_posterior=hijo.saldo_virtual,
                    estado='exitosa',
                    realizada_por=request.user,
                    observaciones='Asignación inicial de tarjeta'
                )
                
        except Exception as e:
            messages.error(request, f'Error al asignar tarjeta: {str(e)}')
    
    return redirect('usuarios:detalle_hijo', pk=hijo.pk)


@login_required
def activar_desactivar_tarjeta(request, pk):
    """
    Activar o desactivar tarjeta de un hijo
    """
    hijo = get_object_or_404(PerfilHijo, pk=pk)
    
    # Solo administradores pueden activar/desactivar tarjetas
    if request.user.tipo_usuario != 'administrador':
        messages.error(request, 'Solo los administradores pueden activar/desactivar tarjetas.')
        return redirect('usuarios:detalle_hijo', pk=hijo.pk)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        try:
            if accion == 'activar':
                hijo.tarjeta_activa = True
                mensaje = f'Tarjeta de {hijo.nombre_completo} activada exitosamente.'
                observaciones = 'Tarjeta activada por administrador'
            elif accion == 'desactivar':
                hijo.tarjeta_activa = False
                mensaje = f'Tarjeta de {hijo.nombre_completo} desactivada exitosamente.'
                observaciones = 'Tarjeta desactivada por administrador'
            else:
                messages.error(request, 'Acción no válida.')
                return redirect('usuarios:detalle_hijo', pk=hijo.pk)
            
            hijo.save()
            messages.success(request, mensaje)
            
            # Crear registro de transacción
            from .models import TransaccionTarjeta
            TransaccionTarjeta.objects.create(
                hijo=hijo,
                numero_tarjeta_utilizada=hijo.numero_tarjeta or 'N/A',
                tipo_transaccion='ajuste',
                monto=0,
                saldo_anterior=hijo.saldo_virtual,
                saldo_posterior=hijo.saldo_virtual,
                estado='exitosa',
                realizada_por=request.user,
                observaciones=observaciones
            )
            
        except Exception as e:
            messages.error(request, f'Error al actualizar tarjeta: {str(e)}')
    
    return redirect('usuarios:detalle_hijo', pk=hijo.pk)


@login_required
def regenerar_tarjeta(request, pk):
    """
    Regenerar número y código de tarjeta de un hijo
    """
    hijo = get_object_or_404(PerfilHijo, pk=pk)
    
    # Solo administradores pueden regenerar tarjetas
    if request.user.tipo_usuario != 'administrador':
        messages.error(request, 'Solo los administradores pueden regenerar tarjetas.')
        return redirect('usuarios:detalle_hijo', pk=hijo.pk)
    
    if request.method == 'POST':
        try:
            numero_anterior = hijo.numero_tarjeta
            
            # Regenerar número y código
            hijo.numero_tarjeta = None
            hijo.codigo_tarjeta = None
            hijo.asignar_tarjeta()
            
            messages.success(request, f'Tarjeta regenerada exitosamente para {hijo.nombre_completo}.')
            
            # Crear registro de transacción
            from .models import TransaccionTarjeta
            TransaccionTarjeta.objects.create(
                hijo=hijo,
                numero_tarjeta_utilizada=numero_anterior or 'N/A',
                tipo_transaccion='ajuste',
                monto=0,
                saldo_anterior=hijo.saldo_virtual,
                saldo_posterior=hijo.saldo_virtual,
                estado='exitosa',
                realizada_por=request.user,
                observaciones=f'Tarjeta regenerada. Número anterior: {numero_anterior}'
            )
            
        except Exception as e:
            messages.error(request, f'Error al regenerar tarjeta: {str(e)}')
    
    return redirect('usuarios:detalle_hijo', pk=hijo.pk)


@login_required
def gestionar_tarjeta_manual(request, pk):
    """
    Vista para gestionar tarjetas de forma manual (solo administradores)
    """
    # Verificar permisos de administrador
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para realizar esta acción')
        return redirect('usuarios:dashboard')
    
    hijo = get_object_or_404(PerfilHijo, pk=pk)
    
    if request.method == 'POST':
        form = TarjetaManualForm(request.POST, hijo=hijo)
        if form.is_valid():
            try:
                resultado = form.aplicar_accion()
                messages.success(request, resultado)
                
                # Registrar transacción para auditoría
                from .models import TransaccionTarjeta
                TransaccionTarjeta.objects.create(
                    hijo=hijo,
                    numero_tarjeta_utilizada=hijo.numero_tarjeta or 'N/A',
                    tipo_transaccion='ajuste',
                    monto=0,
                    saldo_anterior=hijo.saldo_virtual,
                    saldo_posterior=hijo.saldo_virtual,
                    estado='exitosa',
                    realizada_por=request.user,
                    observaciones=f'Gestión manual de tarjeta: {resultado}'
                )
                
                return redirect('usuarios:detalle_hijo', pk=hijo.pk)
            except Exception as e:
                messages.error(request, f'Error en la operación: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = TarjetaManualForm(hijo=hijo)
    
    context = {
        'titulo': f'Gestionar Tarjeta - {hijo.nombre_completo}',
        'hijo': hijo,
        'form': form,
    }
    
    return render(request, 'usuarios/gestionar_tarjeta.html', context)


@login_required
def editar_hijo(request, pk):
    """
    Editar información de un hijo
    """
    hijo = get_object_or_404(PerfilHijo, pk=pk)
    
    # Verificar permisos
    if request.user.tipo_usuario == 'padre' and hijo.padre != request.user:
        messages.error(request, 'No tienes permisos para editar este hijo.')
        return redirect('usuarios:lista_hijos')
    elif request.user.tipo_usuario not in ['padre', 'administrador']:
        messages.error(request, 'No tienes permisos para editar hijos.')
        return redirect('usuarios:dashboard')
    
    if request.method == 'POST':
        form = PerfilHijoForm(request.POST, instance=hijo, padre=hijo.padre)
        
        if form.is_valid():
            try:
                hijo = form.save()
                messages.success(request, f'Información de {hijo.nombre_completo} actualizada exitosamente.')
                return redirect('usuarios:detalle_hijo', pk=hijo.pk)
            except Exception as e:
                messages.error(request, f'Error al actualizar el hijo: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PerfilHijoForm(instance=hijo, padre=hijo.padre)
    
    context = {
        'titulo': f'Editar - {hijo.nombre_completo}',
        'hijo': hijo,
        'form': form,
        'editando': True,
    }
    
    return render(request, 'usuarios/editar_hijo.html', context)


@login_required
def eliminar_hijo(request, pk):
    """
    Eliminar un hijo (solo para administradores o con confirmación especial)
    """
    hijo = get_object_or_404(PerfilHijo, pk=pk)
    
    # Verificar permisos estrictos para eliminar
    if request.user.tipo_usuario == 'padre' and hijo.padre != request.user:
        messages.error(request, 'No tienes permisos para eliminar este hijo.')
        return redirect('usuarios:lista_hijos')
    elif request.user.tipo_usuario not in ['padre', 'administrador']:
        messages.error(request, 'No tienes permisos para eliminar hijos.')
        return redirect('usuarios:dashboard')
    
    # Verificar si el hijo tiene saldo o transacciones
    tiene_saldo = hijo.saldo_virtual != 0
    tiene_transacciones = hasattr(hijo, 'ventas') and hijo.ventas.exists()
    
    if request.method == 'POST':
        confirmacion = request.POST.get('confirmacion')
        
        if confirmacion == 'ELIMINAR':
            try:
                nombre_hijo = hijo.nombre_completo
                
                # Si tiene saldo positivo, advertir
                if hijo.saldo_virtual > 0:
                    messages.warning(request, f'ATENCIÓN: Se eliminará el hijo {nombre_hijo} con saldo de {hijo.saldo_virtual:,.0f} Gs.')
                
                # Eliminar el hijo
                hijo.delete()
                messages.success(request, f'Hijo {nombre_hijo} eliminado exitosamente.')
                return redirect('usuarios:lista_hijos')
                
            except Exception as e:
                messages.error(request, f'Error al eliminar el hijo: {str(e)}')
        else:
            messages.error(request, 'Confirmación incorrecta. Debes escribir "ELIMINAR" exactamente.')
    
    context = {
        'titulo': f'Eliminar - {hijo.nombre_completo}',
        'hijo': hijo,
        'tiene_saldo': tiene_saldo,
        'tiene_transacciones': tiene_transacciones,
    }
    
    return render(request, 'usuarios/eliminar_hijo.html', context)
