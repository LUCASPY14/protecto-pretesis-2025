from ventas.models import PuntoVenta

nuevos = [
    {'nombre': 'Caja Móvil', 'codigo': 'MOVIL01', 'ubicacion': 'Punto móvil para eventos', 'activo': True},
    {'nombre': 'Caja Express', 'codigo': 'EXP01', 'ubicacion': 'Sector Express', 'activo': True},
    {'nombre': 'Caja Patio', 'codigo': 'PATIO01', 'ubicacion': 'Patio Central', 'activo': True},
]
results = []
for punto in nuevos:
    obj, created = PuntoVenta.objects.get_or_create(codigo=punto['codigo'], defaults=punto)
    if not obj.activo:
        obj.activo = True
        obj.save()
    results.append((obj.codigo, obj.nombre, obj.activo, created))
print('Resultados:', results)
print('Todos los puntos de venta:', list(PuntoVenta.objects.values('codigo','nombre','activo')))
