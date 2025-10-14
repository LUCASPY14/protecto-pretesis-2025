from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Producto, Categoria, MovimientoStock, Proveedor

@login_required
def lista_productos(request):
    """Lista de productos"""
    productos = Producto.objects.all().order_by('categoria__nombre', 'nombre')
    return render(request, 'productos/lista_productos.html', {'productos': productos})

@login_required
def crear_producto(request):
    """Crear nuevo producto"""
    if request.method == 'POST':
        try:
            # Crear el producto
            producto = Producto.objects.create(
                nombre=request.POST['nombre'],
                codigo=request.POST.get('codigo', ''),
                descripcion=request.POST.get('descripcion', ''),
                categoria_id=request.POST['categoria'],
                precio_costo=request.POST['precio_costo'],
                precio_venta=request.POST['precio_venta'],
                stock_actual=request.POST.get('stock_actual', 0),
                stock_minimo=request.POST.get('stock_minimo', 0),
                stock_maximo=request.POST.get('stock_maximo', None),
                requiere_stock=bool(request.POST.get('requiere_stock')),
                disponible=bool(request.POST.get('disponible')),
                imagen=request.FILES.get('imagen')
            )
            
            # Crear movimiento de stock inicial si hay stock
            if int(request.POST.get('stock_actual', 0)) > 0:
                MovimientoStock.objects.create(
                    producto=producto,
                    tipo='entrada',
                    cantidad=producto.stock_actual,
                    motivo='Stock inicial',
                    usuario=request.user
                )
            
            messages.success(request, f'Producto "{producto.nombre}" creado exitosamente.')
            return redirect('productos:lista_productos')
            
        except Exception as e:
            messages.error(request, f'Error al crear el producto: {str(e)}')
    
    # GET request o error en POST
    categorias = Categoria.objects.filter(activo=True).order_by('nombre')
    context = {
        'categorias': categorias,
    }
    return render(request, 'productos/crear_producto.html', context)

@login_required
def detalle_producto(request, pk):
    """Detalle de un producto"""
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, 'productos/detalle_producto.html', {'producto': producto})

@login_required
def editar_producto(request, pk):
    """Editar producto"""
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, 'productos/editar_producto.html', {'producto': producto})

@login_required
def lista_categorias(request):
    """Lista de categorías"""
    categorias = Categoria.objects.all().order_by('nombre')
    return render(request, 'productos/lista_categorias.html', {'categorias': categorias})

@login_required
def crear_categoria(request):
    """Crear nueva categoría"""
    return render(request, 'productos/crear_categoria.html')

@login_required
def control_stock(request):
    """Control de stock"""
    productos = Producto.objects.all().order_by('stock_actual')
    return render(request, 'productos/control_stock.html', {'productos': productos})

@login_required
def movimiento_stock(request, pk):
    """Registrar movimiento de stock"""
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, 'productos/movimiento_stock.html', {'producto': producto})

@login_required
def lista_proveedores(request):
    """Lista de proveedores"""
    proveedores = Proveedor.objects.all().order_by('nombre')
    return render(request, 'productos/lista_proveedores.html', {'proveedores': proveedores})

@login_required
def crear_proveedor(request):
    """Crear nuevo proveedor"""
    return render(request, 'productos/crear_proveedor.html')
