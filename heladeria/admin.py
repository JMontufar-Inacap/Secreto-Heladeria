from django.contrib import admin
from .models import Producto, Venta, DetalleVenta, Cliente

admin.site.site_header = "Heladería"
admin.site.site_title = "Heladería Admin"
admin.site.index_title = "Panel de administración principal"

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'telefono', 'email', 'fecha_registro')
    search_fields = ('nombre', 'email')
    list_filter = ('fecha_registro',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "stock", "state", "created_at", "updated_at")
    search_fields = ("nombre",)
    list_filter = ("state",)
    ordering = ("nombre",)
    list_select_related = ()

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    fields = ("producto", "cantidad", "subtotal")
    readonly_fields = ("subtotal",)

@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ("venta", "producto", "cantidad", "subtotal")
    search_fields = ("venta__id", "producto__nombre")
    list_filter = ("producto",)
    ordering = ("venta", "producto")
    list_select_related = ("venta", "producto")

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "fecha", "total")
    search_fields = ("usuario__username", "id")
    list_filter = ("fecha", "usuario")
    ordering = ("-fecha",)
    inlines = [DetalleVentaInline]
    list_select_related = ("usuario",)