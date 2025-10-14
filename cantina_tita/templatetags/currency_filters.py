from django import template

register = template.Library()

@register.filter
def guaranies(value):
    """
    Formatea un valor numérico como Guaraníes paraguayos
    Ejemplo: 15000 -> "Gs. 15.000"
    """
    if value is None or value == '':
        return "Gs. 0"
    
    try:
        # Convertir a entero (sin decimales)
        value = int(float(value))
        
        # Formatear con separador de miles
        formatted = f"{value:,}".replace(',', '.')
        
        return f"Gs. {formatted}"
    except (ValueError, TypeError):
        return "Gs. 0"

@register.filter
def guaranies_input(value):
    """
    Formatea un valor para mostrar en inputs sin el símbolo Gs.
    Ejemplo: 15000 -> "15.000"
    """
    if value is None or value == '':
        return "0"
    
    try:
        value = int(float(value))
        return f"{value:,}".replace(',', '.')
    except (ValueError, TypeError):
        return "0"