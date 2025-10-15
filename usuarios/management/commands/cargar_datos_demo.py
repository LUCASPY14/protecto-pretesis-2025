from django.core.management.base import BaseCommand
from usuarios.models import Usuario, PerfilHijo, TransaccionTarjeta
from productos.models import Producto, Categoria
from django.db import transaction

class Command(BaseCommand):
    help = 'Carga padres, hijos, tarjetas, saldos y productos de ejemplo.'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Crear padre
            padre, _ = Usuario.objects.get_or_create(username='padre1', defaults={
                'email': 'padre1@example.com',
                'tipo_usuario': 'padre',
                'is_active': True,
            })
            padre.set_password('Padre12345')
            padre.save()

            # Crear hijos y tarjetas
            hijos_data = [
                {'nombre_completo': 'Juan', 'saldo': 100000, 'numero_tarjeta': '5555000000000001'},
                {'nombre_completo': 'Ana', 'saldo': 80000, 'numero_tarjeta': '5555000000000002'},
            ]
            for h in hijos_data:
                hijo, _ = PerfilHijo.objects.get_or_create(
                    nombre_completo=h['nombre_completo'],
                    padre=padre,
                    defaults={'saldo_virtual': h['saldo'], 'numero_tarjeta': h['numero_tarjeta'], 'tarjeta_activa': True}
                )
                hijo.saldo_virtual = h['saldo']
                hijo.numero_tarjeta = h['numero_tarjeta']
                hijo.tarjeta_activa = True
                hijo.save()

            # Crear productos
            productos = [
                # nombre, precio_costo, precio_venta
                ("Coca Cola 500ml", 5000, 7000),
                ("Pulp Naranja 250ml", 3000, 4500),
                ("Sprite 500ml", 5000, 7000),
                ("Jugo Watts 200ml Naranja", 2500, 4000),
                ("Jugo Watts 200ml Manzana", 2500, 4000),
                ("Jugo Watts 200ml Durazno", 2500, 4000),
                ("Empanada Frita Carne", 2500, 4000),
                ("Empanada Frita Pollo", 2500, 4000),
                ("Empanada Frita JyQ", 2500, 4000),
                ("Sandwich de Miga JyQ", 3000, 5000),
                ("Sandwich de Miga Pollo", 3000, 5000),
                ("Sandwich de Miga Verduras", 3000, 5000),
                ("Pollo Árabe", 4000, 6000),
                ("Pave de Oreo", 3500, 5000),
                ("Pororo", 2000, 3500),
                ("Empanada al Horno Carne", 2500, 4000),
                ("Empanada al Horno Pollo", 2500, 4000),
                ("Empanada al Horno JyQ", 2500, 4000),
                ("Café Corto", 1500, 2500),
                ("Café Medio", 2000, 3000),
                ("Café Largo", 2500, 3500),
            ]
            categoria, _ = Categoria.objects.get_or_create(nombre="General")
            for idx, (nombre, costo, venta) in enumerate(productos, start=1):
                Producto.objects.get_or_create(
                    nombre=nombre,
                    codigo=f"PROD{idx:03}",
                    defaults={
                        'precio_costo': costo,
                        'precio_venta': venta,
                        'categoria': categoria,
                        'requiere_stock': False,
                    }
                )

        self.stdout.write(self.style.SUCCESS('Datos de ejemplo cargados correctamente.'))
