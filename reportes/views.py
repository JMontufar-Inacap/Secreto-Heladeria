from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.db.models import Sum, F, DecimalField, Case, When, Q, Count
from django.db.models.functions import Coalesce
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from heladeria.models import DetalleVenta, Venta, Producto
from decimal import Decimal
import json


def calcular_porcentaje(actual, anterior):
    actual_float = float(actual) if isinstance(actual, Decimal) else float(actual)
    anterior_float = float(anterior) if isinstance(anterior, Decimal) else float(anterior)
    
    if anterior_float == 0 and actual_float == 0:
        return 0
    
    if anterior_float == 0:
        return 100 if actual_float > 0 else -100
    
    return round(((actual_float - anterior_float) / anterior_float) * 100, 1)


@login_required
def reporte_dashboard(request):
    hoy = now().date()
    
    estado_filtro = request.GET.get('estado', 'COMPLETED')
    periodo_filtro = request.GET.get('periodo', '12meses')
    productos_ids_str = request.GET.getlist('productos')

    productos_ids = []
    for pid in productos_ids_str:
        if pid and pid.isdigit():
            productos_ids.append(int(pid))
    
    if len(productos_ids) > 3:
        productos_ids = productos_ids[:3]
    
    if estado_filtro == 'COMPLETED':
        estados = ['COMPLETED']
    elif estado_filtro == 'PENDING':
        estados = ['PENDING']
    elif estado_filtro == 'BOTH':
        estados = ['COMPLETED', 'PENDING']
    else:
        estados = ['COMPLETED']
    
    # ========================================================================
    # SEPARAR PERÍODOS: Uno para TARJETAS (corto) y otro para GRÁFICOS (largo)
    # ========================================================================
    
    if periodo_filtro == '12meses':
        # PARA GRÁFICO: últimos 12 meses completos
        inicio_grafico = hoy - relativedelta(months=12)
        fin_grafico = hoy
        
        # PARA TARJETAS: solo mes actual vs mes anterior
        inicio_periodo_actual = hoy.replace(day=1)  # Primer día del mes actual
        fin_periodo_actual = hoy
        
        # Mes anterior completo
        primer_dia_mes_anterior = (hoy.replace(day=1) - timedelta(days=1)).replace(day=1)
        ultimo_dia_mes_anterior = hoy.replace(day=1) - timedelta(days=1)
        inicio_periodo_anterior = primer_dia_mes_anterior
        fin_periodo_anterior = ultimo_dia_mes_anterior
        
        periodo_label = '12 meses'
        usar_meses = True
        num_periodos = 12
        
    elif periodo_filtro == '10semanas':
        # PARA GRÁFICO: últimas 10 semanas completas
        inicio_grafico = hoy - timedelta(weeks=10)
        fin_grafico = hoy
        
        # PARA TARJETAS: semana actual vs semana anterior
        inicio_periodo_actual = hoy - timedelta(days=hoy.weekday())  # Lunes de esta semana
        fin_periodo_actual = hoy
        
        # Semana anterior (lunes a domingo)
        inicio_periodo_anterior = inicio_periodo_actual - timedelta(weeks=1)
        fin_periodo_anterior = inicio_periodo_actual - timedelta(days=1)
        
        periodo_label = '10 semanas'
        usar_meses = False
        num_periodos = 10
        
    elif periodo_filtro == '7dias':
        # PARA GRÁFICO: últimos 7 días
        inicio_grafico = hoy - timedelta(days=7)
        fin_grafico = hoy
        
        # PARA TARJETAS: hoy vs ayer
        inicio_periodo_actual = hoy
        fin_periodo_actual = hoy
        
        inicio_periodo_anterior = hoy - timedelta(days=1)
        fin_periodo_anterior = hoy - timedelta(days=1)
        
        periodo_label = '7 días'
        usar_meses = False
        num_periodos = 7
        
    else:
        inicio_grafico = hoy - relativedelta(months=12)
        fin_grafico = hoy
        inicio_periodo_actual = hoy.replace(day=1)
        fin_periodo_actual = hoy
        primer_dia_mes_anterior = (hoy.replace(day=1) - timedelta(days=1)).replace(day=1)
        ultimo_dia_mes_anterior = hoy.replace(day=1) - timedelta(days=1)
        inicio_periodo_anterior = primer_dia_mes_anterior
        fin_periodo_anterior = ultimo_dia_mes_anterior
        periodo_label = '12 meses'
        usar_meses = True
        num_periodos = 12

    # DEBUG
    print(f"\n{'='*60}")
    print(f"PERIODO: {periodo_filtro}")
    print(f"HOY: {hoy}")
    print(f"{'='*60}")
    print(f"GRÁFICO (visualización larga):")
    print(f"  {inicio_grafico} → {fin_grafico}")
    print(f"\nTARJETAS - Período actual:")
    print(f"  {inicio_periodo_actual} → {fin_periodo_actual}")
    print(f"\nTARJETAS - Período anterior:")
    print(f"  {inicio_periodo_anterior} → {fin_periodo_anterior}")
    print(f"{'='*60}\n")
    
    def get_base_queryset(fecha_inicio, fecha_fin):
        qs = DetalleVenta.objects.filter(
            venta__estado__in=estados,
            venta__fecha__date__range=(fecha_inicio, fecha_fin)
        )
        if productos_ids:
            qs = qs.filter(producto_id__in=productos_ids)
        return qs
    
    # ========================================================================
    # CÁLCULO DE TARJETAS (usa períodos cortos)
    # ========================================================================
    
    if productos_ids:
        cards = []
        for producto_id in productos_ids:
            try:
                producto = Producto.objects.get(id=producto_id)
            except Producto.DoesNotExist:
                continue
            
            # Período actual (corto)
            detalles_actual = DetalleVenta.objects.filter(
                venta__estado__in=estados,
                venta__fecha__date__range=(inicio_periodo_actual, fin_periodo_actual),
                producto_id=producto_id
            )
            
            unidades_actual = detalles_actual.aggregate(
                total=Coalesce(Sum('cantidad'), 0)
            )['total']
            
            dinero_actual = detalles_actual.aggregate(
                total=Coalesce(
                    Sum(
                        F('cantidad') * Case(
                            When(precio_unitario__isnull=False, then=F('precio_unitario')),
                            default=F('producto__precio'),
                            output_field=DecimalField()
                        ),
                        output_field=DecimalField()
                    ),
                    Decimal('0')
                )
            )['total']
            
            # Período anterior (corto)
            detalles_anterior = DetalleVenta.objects.filter(
                venta__estado__in=estados,
                venta__fecha__date__range=(inicio_periodo_anterior, fin_periodo_anterior),
                producto_id=producto_id
            )
            
            unidades_anterior = detalles_anterior.aggregate(
                total=Coalesce(Sum('cantidad'), 0)
            )['total']
            
            dinero_anterior = detalles_anterior.aggregate(
                total=Coalesce(
                    Sum(
                        F('cantidad') * Case(
                            When(precio_unitario__isnull=False, then=F('precio_unitario')),
                            default=F('producto__precio'),
                            output_field=DecimalField()
                        ),
                        output_field=DecimalField()
                    ),
                    Decimal('0')
                )
            )['total']
            
            print(f"Producto: {producto.nombre}")
            print(f"  Unidades actual: {unidades_actual}, anterior: {unidades_anterior}")
            print(f"  Dinero actual: {dinero_actual}, anterior: {dinero_anterior}")
            print(f"  % Unidades: {calcular_porcentaje(unidades_actual, unidades_anterior)}")
            print(f"  % Dinero: {calcular_porcentaje(dinero_actual, dinero_anterior)}")
            
            cards.append({
                'titulo': f'{producto.nombre} - Unidades',
                'valor': unidades_actual,
                'moneda': False,
                'porcentaje': calcular_porcentaje(unidades_actual, unidades_anterior)
            })
            
            cards.append({
                'titulo': f'{producto.nombre} - Ventas',
                'valor': dinero_actual,
                'moneda': True,
                'porcentaje': calcular_porcentaje(dinero_actual, dinero_anterior)
            })
    else:
        # Período actual (corto) - TARJETAS
        ventas_actual = Venta.objects.filter(
            estado__in=estados,
            fecha__date__range=(inicio_periodo_actual, fin_periodo_actual)
        )
        
        detalles_actual = get_base_queryset(inicio_periodo_actual, fin_periodo_actual)
        
        unidades_actual = detalles_actual.aggregate(
            total=Coalesce(Sum('cantidad'), 0)
        )['total']
        
        ordenes_actual = ventas_actual.count()
        
        dinero_actual = detalles_actual.aggregate(
            total=Coalesce(
                Sum(
                    F('cantidad') * Case(
                        When(precio_unitario__isnull=False, then=F('precio_unitario')),
                        default=F('producto__precio'),
                        output_field=DecimalField()
                    ),
                    output_field=DecimalField()
                ),
                Decimal('0')
            )
        )['total']
        
        clientes_actual = ventas_actual.filter(
            cliente__isnull=False
        ).values('cliente').distinct().count()
        
        # Período anterior (corto) - TARJETAS
        ventas_anterior = Venta.objects.filter(
            estado__in=estados,
            fecha__date__range=(inicio_periodo_anterior, fin_periodo_anterior)
        )
        
        detalles_anterior = get_base_queryset(inicio_periodo_anterior, fin_periodo_anterior)
        
        unidades_anterior = detalles_anterior.aggregate(
            total=Coalesce(Sum('cantidad'), 0)
        )['total']
        
        ordenes_anterior = ventas_anterior.count()
        
        dinero_anterior = detalles_anterior.aggregate(
            total=Coalesce(
                Sum(
                    F('cantidad') * Case(
                        When(precio_unitario__isnull=False, then=F('precio_unitario')),
                        default=F('producto__precio'),
                        output_field=DecimalField()
                    ),
                    output_field=DecimalField()
                ),
                Decimal('0')
            )
        )['total']
        
        clientes_anterior = ventas_anterior.filter(
            cliente__isnull=False
        ).values('cliente').distinct().count()
        
        # DEBUG
        print("=== CARDS GENERALES ===")
        print(f"Unidades actual: {unidades_actual}, anterior: {unidades_anterior}")
        print(f"Órdenes actual: {ordenes_actual}, anterior: {ordenes_anterior}")
        print(f"Dinero actual: {dinero_actual}, anterior: {dinero_anterior}")
        print(f"Clientes actual: {clientes_actual}, anterior: {clientes_anterior}")
        
        cards = [
            {
                'titulo': 'Unidades vendidas',
                'valor': unidades_actual,
                'moneda': False,
                'porcentaje': calcular_porcentaje(unidades_actual, unidades_anterior)
            },
            {
                'titulo': 'Órdenes realizadas',
                'valor': ordenes_actual,
                'moneda': False,
                'porcentaje': calcular_porcentaje(ordenes_actual, ordenes_anterior)
            },
            {
                'titulo': 'Dinero recibido',
                'valor': dinero_actual,
                'moneda': True,
                'porcentaje': calcular_porcentaje(dinero_actual, dinero_anterior)
            },
            {
                'titulo': 'Clientes con pedido',
                'valor': clientes_actual,
                'moneda': False,
                'porcentaje': calcular_porcentaje(clientes_actual, clientes_anterior)
            }
        ]
    
    # ========================================================================
    # CÁLCULO DE GRÁFICOS (usa períodos largos)
    # ========================================================================
    
    if usar_meses:
        base_mes = hoy.replace(day=1)
        periodos = [base_mes - relativedelta(months=i) for i in range(11, -1, -1)]
        chart_labels = [m.strftime("%b %Y") for m in periodos]
    else:
        if periodo_filtro == '10semanas':
            periodos = []
            for i in range(9, -1, -1):
                inicio_semana = hoy - timedelta(weeks=i, days=hoy.weekday())
                periodos.append(inicio_semana)
            chart_labels = [f"Sem {p.strftime('%d/%m')}" for p in periodos]
        else:
            periodos = [hoy - timedelta(days=i) for i in range(6, -1, -1)]
            chart_labels = [d.strftime("%d/%m") for d in periodos]
    
    # Gráfico de ganancias
    chart_data = []
    
    for idx, periodo in enumerate(periodos):
        if usar_meses:
            if periodo.month == 12:
                siguiente = periodo.replace(year=periodo.year + 1, month=1)
            else:
                siguiente = periodo.replace(month=periodo.month + 1)
        elif periodo_filtro == '10semanas':
            siguiente = periodo + timedelta(days=7)
        else:
            siguiente = periodo + timedelta(days=1)
        
        ganancias = DetalleVenta.objects.filter(
            venta__estado__in=estados,
            venta__fecha__date__gte=periodo,
            venta__fecha__date__lt=siguiente,
            precio_compra__isnull=False,
            precio_unitario__isnull=False
        )
        
        if productos_ids:
            ganancias = ganancias.filter(producto_id__in=productos_ids)
        
        total_ganancias = ganancias.aggregate(
            total=Coalesce(
                Sum(
                    (F('precio_unitario') - F('precio_compra')) * F('cantidad'),
                    output_field=DecimalField()
                ),
                Decimal('0')
            )
        )['total']
        
        chart_data.append(float(total_ganancias))
    
    # Gráfico de órdenes
    ordenes_chart_labels = chart_labels
    ordenes_chart_data = []
    
    for idx, periodo in enumerate(periodos):
        if usar_meses:
            if periodo.month == 12:
                siguiente = periodo.replace(year=periodo.year + 1, month=1)
            else:
                siguiente = periodo.replace(month=periodo.month + 1)
        elif periodo_filtro == '10semanas':
            siguiente = periodo + timedelta(days=7)
        else:
            siguiente = periodo + timedelta(days=1)
        
        ordenes = Venta.objects.filter(
            estado__in=estados,
            fecha__date__gte=periodo,
            fecha__date__lt=siguiente
        )
        
        if productos_ids:
            ordenes = ordenes.filter(detalleventa__producto_id__in=productos_ids).distinct()
        
        ordenes_chart_data.append(ordenes.count())
    
    # ========================================================================
    # MÉTRICAS ADICIONALES (usan período largo del gráfico)
    # ========================================================================
    
    top_productos = Producto.objects.filter(
        id__in=get_base_queryset(inicio_grafico, fin_grafico)
            .values_list('producto_id', flat=True)
    ).annotate(
        total_vendidos=Sum('detalleventa__cantidad', filter=Q(detalleventa__venta__fecha__date__range=(inicio_grafico, fin_grafico)))
    ).order_by('-total_vendidos')[:5]

    
    ordenes_periodo = Venta.objects.filter(
        estado__in=estados,
        fecha__date__range=(inicio_grafico, fin_grafico)
    )
    
    if productos_ids:
        ordenes_periodo = ordenes_periodo.filter(detalleventa__producto_id__in=productos_ids).distinct()
    
    ordenes_total = ordenes_periodo.count()
    
    # Período anterior para crecimiento de órdenes (mismo tamaño que el gráfico)
    if periodo_filtro == '12meses':
        inicio_grafico_anterior = inicio_grafico - relativedelta(months=12)
        fin_grafico_anterior = inicio_grafico - timedelta(days=1)
    elif periodo_filtro == '10semanas':
        inicio_grafico_anterior = inicio_grafico - timedelta(weeks=10)
        fin_grafico_anterior = inicio_grafico - timedelta(days=1)
    else:
        inicio_grafico_anterior = inicio_grafico - timedelta(days=7)
        fin_grafico_anterior = inicio_grafico - timedelta(days=1)
    
    ordenes_periodo_anterior = Venta.objects.filter(
        estado__in=estados,
        fecha__date__range=(inicio_grafico_anterior, fin_grafico_anterior)
    )
    
    if productos_ids:
        ordenes_periodo_anterior = ordenes_periodo_anterior.filter(
            detalleventa__producto_id__in=productos_ids
        ).distinct()
    
    ordenes_anterior_total = ordenes_periodo_anterior.count()
    
    crecimiento_ordenes = calcular_porcentaje(ordenes_total, ordenes_anterior_total)
    
    # Ticket promedio
    detalles_periodo = get_base_queryset(inicio_grafico, fin_grafico)
    
    total_ventas = detalles_periodo.aggregate(
        total=Coalesce(
            Sum(
                F('cantidad') * Case(
                    When(precio_unitario__isnull=False, then=F('precio_unitario')),
                    default=F('producto__precio'),
                    output_field=DecimalField()
                ),
                output_field=DecimalField()
            ),
            Decimal('0')
        )
    )['total']
    
    ticket_promedio = total_ventas / ordenes_total if ordenes_total > 0 else 0
    
    # Producto estrella
    producto_top_obj = get_base_queryset(inicio_grafico, fin_grafico).values(
        'producto__nombre'
    ).annotate(
        total=Sum('cantidad')
    ).order_by('-total').first()
    
    producto_top = producto_top_obj['producto__nombre'] if producto_top_obj else 'N/A'
    
    productos_disponibles = Producto.objects.filter(state='ACTIVE').order_by('nombre')
    
    total_cards = len(cards)
    if total_cards == 1:
        col_md = 12
    elif total_cards == 2:
        col_md = 6
    elif total_cards == 3:
        col_md = 4
    elif total_cards == 4:
        col_md = 3
    elif total_cards == 6:
        col_md = 2
    else:
        col_md = 3
    
    context = {
        'cards': cards,
        'col_md': col_md,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'ordenes_chart_labels': json.dumps(ordenes_chart_labels),
        'ordenes_chart_data': json.dumps(ordenes_chart_data),
        'top_productos': top_productos,
        'ordenes_12_meses': ordenes_total,
        'crecimiento_ordenes': crecimiento_ordenes,
        'ticket_promedio': ticket_promedio,
        'producto_top': producto_top,
        'productos_disponibles': productos_disponibles,
        'productos_seleccionados': productos_ids,
        'estado_filtro': estado_filtro,
        'periodo_filtro': periodo_filtro,
        'periodo_label': periodo_label,
    }

    return render(request, 'reportes/dashboard.html', context)