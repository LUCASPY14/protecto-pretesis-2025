# Cambios recientes (Octubre 2025)

## Mejoras en permisos y roles
- **Recarga de saldo virtual**: Solo usuarios con tipo `administrador` o `cajero` pueden acceder a la funcionalidad de recarga de saldo virtual. Los padres no ven ni pueden usar esta opción.
- **Agregar hijos (PerfilHijo)**: Solo usuarios con tipo `administrador` pueden agregar nuevos hijos. Los padres no ven ni pueden usar esta opción.
- **Scripts de gestión**:
  - `activar_puntos_venta.py`: Activa los puntos de venta.
  - `renombrar_puntos_venta.py`: Renombra los puntos de venta.
  - `usuarios/management/commands/cargar_datos_demo.py`: Carga datos de prueba (padres, hijos, tarjetas, productos).

### Cómo probar las nuevas restricciones

1. **Recarga de saldo virtual**
   - Inicia sesión como `administrador` o `cajero` y verifica que puedes ver y usar la opción de recarga de saldo virtual en el detalle de cada hijo.
   - Inicia sesión como `padre` y verifica que NO aparece la opción de recarga de saldo virtual.

2. **Agregar hijos**
   - Inicia sesión como `administrador` y verifica que puedes agregar nuevos hijos desde la gestión de usuarios.
   - Inicia sesión como `padre` y verifica que NO aparece la opción para agregar hijos.

### Notas técnicas
- Se agregó un `.gitignore` para evitar subir archivos compilados, bases de datos locales y backups.
- Se limpiaron archivos `.pyc` y `__pycache__` del repositorio.
- Las migraciones de Django han sido actualizadas y compactadas.

### Sugerencias de mejora
- Añadir pruebas unitarias para las vistas y permisos.
- Documentar los scripts de gestión en mayor detalle.
- Considerar un sistema de logs para acciones administrativas.

---
# protecto-pretesis-2025
proyecto pretesis 2025 version 1 (falta mejorar el pos)

# Sistema de Gestión de Cantina "La Cantina de Tita"

Sistema integral de gestión para cantinas escolares desarrollado con Django y Tailwind CSS.

## 📋 Información del Proyecto

- **Cliente**: La Cantina de Tita
- **Ubicación**: Asunción, Paraguay
- **Contacto Admin**: admin@tita.com | WhatsApp: +595981934107
- **Desarrollado por**: LGservice | WhatsApp: +595985350656

## 🚀 Características Principales

### ✅ Completadas

1. **Sistema de Usuarios Multi-Rol**
   - Administradores: Control total del sistema
   - Cajeros: Gestión de ventas y punto de venta
   - Padres: Monitoreo de consumo y recarga de saldo

2. **Gestión de Estudiantes**
   - Perfiles de estudiantes vinculados a padres
   - Sistema de saldo virtual con tarjeta exclusiva
   - Control de saldo negativo con autorización
   - Historial de recargas y consumos

3. **Múltiples Métodos de Pago**
   - Efectivo (0% comisión)
   - Transferencia bancaria (0% comisión)
   - Giros Tigo (0% comisión)
   - Tarjeta Débito/QR (4% comisión)
   - Tarjeta Crédito/QR (6% comisión)
   - Tarjeta exclusiva de la cantina (saldo virtual)
   - Pagos mixtos permitidos

4. **Sistema de Facturación Inteligente**
   - Facturación automática solo para métodos que lo requieren
   - Evita doble facturación con saldo virtual
   - Facturas físicas y digitales/electrónicas

5. **Gestión de Productos e Inventario**
   - Control de stock en tiempo real
   - Categorización de productos
   - Alertas de stock bajo
   - Historial de movimientos de inventario
   - Gestión de proveedores

6. **Múltiples Puntos de Venta**
   - Sistema POS optimizado para cantinas
   - Asignación de cajeros por punto de venta
   - Control de transacciones por cajero

7. **Diseño Responsive**
   - Interfaz optimizada para desktop y móviles
   - Tailwind CSS para diseño moderno
   - Experiencia de usuario intuitiva

### 🔄 En Desarrollo

1. **Sistema de Reportes Avanzados**
   - Consumo por estudiante
   - Productos más vendidos
   - Ingresos por método de pago
   - Análisis de comisiones
   - Reportes automáticos programables

2. **Sistema POS Completo**
   - Interfaz de venta táctil
   - Búsqueda rápida de productos
   - Calculadora de pagos mixtos
   - Impresión de tickets

3. **Generación de Facturas PDF**
   - Templates personalizados
   - Códigos QR para facturas digitales
   - Envío automático por email

## 🛠️ Tecnologías Utilizadas

- **Backend**: Django 4.2+ (Python)
- **Frontend**: Tailwind CSS 3.3+
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Autenticación**: Sistema integrado de Django
- **Reportes**: ReportLab, OpenPyXL
- **Archivos Estáticos**: WhiteNoise

## 📦 Instalación y Configuración

### Prerrequisitos
- Python 3.8+
- Node.js 18+ (para Tailwind CSS)
- Git

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd proyectodepretesis2025
```

2. **Configurar entorno Python**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows
```

3. **Instalar dependencias Python**
```bash
pip install -r requirements.txt
```

4. **Instalar dependencias Node.js**
```bash
npm install
```

5. **Compilar CSS con Tailwind**
```bash
npm run build-css
```

6. **Configurar base de datos**
```bash
python manage.py makemigrations
python manage.py migrate
```

7. **Cargar datos iniciales**
```bash
python manage.py cargar_datos_iniciales
```

8. **Crear superusuario**
```bash
python manage.py createsuperuser
```

9. **Ejecutar servidor de desarrollo**
```bash
python manage.py runserver
```

## 👥 Usuarios de Prueba

### Administrador
- **Usuario**: admin
- **Email**: admin@tita.com
- **Contraseña**: admin123
- **Tipo**: Administrador

## 🗂️ Estructura del Proyecto

```
cantina_tita/
├── cantina_tita/          # Configuración principal
├── usuarios/              # Gestión de usuarios y estudiantes
├── productos/             # Inventario y productos
├── ventas/               # Sistema de ventas y POS
├── reportes/             # Generación de reportes
├── templates/            # Templates HTML
├── static/               # Archivos estáticos
├── media/                # Archivos subidos
└── requirements.txt      # Dependencias Python
```

## 🔧 Configuración del Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
DEBUG=True
SECRET_KEY=tu-clave-secreta-aqui
DATABASE_URL=sqlite:///db.sqlite3

# Información de contacto
ADMIN_EMAIL=admin@tita.com
ADMIN_WHATSAPP=+595981934107
DEVELOPER_WHATSAPP=+595985350656

# Configuración de facturación
TAX_RATE=10.0
DEBIT_CARD_FEE=4.0
CREDIT_CARD_FEE=6.0
```

## 📊 Funcionalidades del Sistema

### Dashboard por Tipo de Usuario

#### Administrador
- Estadísticas de ventas diarias
- Control de usuarios y estudiantes
- Alertas de stock bajo
- Acceso a todos los módulos

#### Cajero
- Resumen de ventas propias
- Acceso al POS
- Historial de transacciones

#### Padre
- Saldo de hijos
- Historial de consumos
- Sistema de recargas

### Métodos de Pago Configurados

| Método | Comisión | Genera Factura |
|--------|----------|----------------|
| Efectivo | 0% | ✅ |
| Transferencia | 0% | ✅ |
| Giros Tigo | 0% | ✅ |
| Tarjeta Débito/QR | 4% | ✅ |
| Tarjeta Crédito/QR | 6% | ✅ |
| Saldo Virtual | 0% | ❌ |

## 🔒 Seguridad

- Autenticación requerida para todas las vistas
- Permisos por tipo de usuario
- Validación de datos en formularios
- Protección CSRF habilitada

## 📱 Responsive Design

El sistema está optimizado para:
- Dispositivos móviles (smartphones)
- Tablets
- Computadoras de escritorio
- Puntos de venta táctiles

## 🐛 Solución de Problemas

### CSS no se carga
```bash
python manage.py collectstatic
npm run build-css
```

### Error de migraciones
```bash
python manage.py makemigrations --empty <app_name>
python manage.py migrate
```

### Problemas con Node.js
```bash
npm install
npm run build-css
```

## 🚀 Deployment (Producción)

### Variables de Entorno Requeridas
- `DEBUG=False`
- `SECRET_KEY=clave-secreta-fuerte`
- `DATABASE_URL=postgresql://usuario:password@host:puerto/db`
- `ALLOWED_HOSTS=tu-dominio.com`

### Comandos de Deployment
```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn cantina_tita.wsgi:application
```

## 📞 Soporte Técnico

Para soporte técnico, contactar a:
- **LGservice**
- **WhatsApp**: +595985350656
- **Email**: Disponible bajo solicitud

## 📄 Licencia

Proyecto desarrollado exclusivamente para "La Cantina de Tita". Todos los derechos reservados.

---


**Desarrollado con ❤️ por LGservice para La Cantina de Tita**
