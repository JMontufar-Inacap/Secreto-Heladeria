from django import template

register = template.Library()

@register.filter
def precio_cl(value):
    try:
        value = int(float(value))
        return f"{value:,}".replace(",", ".")
    except:
        return value

@register.filter
def formato_telefono(value):

    try:
        num = ''.join(filter(str.isdigit, str(value)))

        if len(num) == 9:
            return f"{num[0]} {num[1:5]} {num[5:9]}"

        elif len(num) == 11 and num.startswith("56"):
            return f"+56 {num[2]} {num[3:7]} {num[7:11]}"

        else:
            return value
    except:
        return value
    
@register.filter
def formato_rut(value):

    if not value:
        return ""

    # Convertir a string y limpiar
    rut = str(value).upper().replace(".", "").replace("-", "").strip()

    # Validar longitud mínima
    if len(rut) < 2:
        return value

    cuerpo = rut[:-1]
    dv = rut[-1]

    # Agregar puntos cada 3 dígitos
    cuerpo = cuerpo[::-1]                               # invertir
    cuerpo = ".".join(cuerpo[i:i+3] for i in range(0, len(cuerpo), 3))
    cuerpo = cuerpo[::-1]                               # revertir nuevamente

    return f"{cuerpo}-{dv}"