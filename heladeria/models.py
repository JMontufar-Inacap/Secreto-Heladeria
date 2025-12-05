from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class BaseModel(models.Model):
    STATE_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]
    state = models.CharField(max_length=10, choices=STATE_CHOICES, default="ACTIVE")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

class Producto(BaseModel):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(
        upload_to='productos/', 
        blank=True, 
        null=True
    )

    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'devices_producto'

class Venta(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    cliente = models.ForeignKey('Cliente', on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(
        max_length=10,
        choices=[('CART', 'En carrito'), ('PENDING', 'Pendiente'), ('COMPLETED', 'Completada'),  ('CANCELLED', 'Cancelada'),],
        default='PENDING'
    )
    fecha = models.DateTimeField(default=timezone.now)

    def total(self):
        return sum(detalle.subtotal() for detalle in self.detalleventa_set.all())

    def __str__(self):
        cliente_info = f" ({self.cliente.nombre})" if self.cliente else ""
        return f"Venta #{self.id} - {self.usuario.username}{cliente_info}"
    
    class Meta:
        db_table = 'devices_venta'

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=0)

    def subtotal(self):
        return self.producto.precio * self.cantidad

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
    
    class Meta:
        db_table = 'devices_detalleventa'

class Cliente(models.Model):
    rut = models.CharField(max_length=12, unique=True, null=False)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, null=True)
    telefono = models.CharField(max_length=20, null=True)
    email = models.EmailField(null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'devices_cliente'