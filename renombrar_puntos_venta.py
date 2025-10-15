from ventas.models import PuntoVenta
nombres = [
    ('CAJA01', 'Caja 1 Principal'),
    ('CAJA02', 'Caja 2'),
    ('EXP01', 'Caja 3'),
    ('MOVIL01', 'Caja 4'),
    ('PATIO01', 'Caja 5'),
]
for codigo, nombre in nombres:
    try:
        obj = PuntoVenta.objects.get(codigo=codigo)
        obj.nombre = nombre
        obj.save()
        print(f"✅ Renombrado: {codigo} -> {nombre}")
    except PuntoVenta.DoesNotExist:
        print(f"❌ No existe: {codigo}")
print(list(PuntoVenta.objects.values('codigo','nombre','activo')))
