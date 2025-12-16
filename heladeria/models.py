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

class Categoria(BaseModel):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'devices_categoria'

        
class Producto(BaseModel):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=0)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos'
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
        cliente_info = f" ({self.cliente.nombre_completo})" if self.cliente else ""
        return f"Venta #{self.id} - {self.usuario.username}{cliente_info}"
    
    class Meta:
        db_table = 'devices_venta'

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=0)

    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True
    )
    precio_compra = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True
    )

    def subtotal(self):
        precio = self.precio_unitario or self.producto.precio
        return precio * self.cantidad

    def ganancia(self):
        if self.precio_compra is None:
            return 0
        precio = self.precio_unitario or self.producto.precio
        return (precio - self.precio_compra) * self.cantidad

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
    
    class Meta:
        db_table = 'devices_detalleventa'

class Cliente(models.Model):
    TIPO_CLIENTE_CHOICES = [
        ('PERSONA', 'Persona natural'),
        ('EMPRESA', 'Empresa'),
    ]
    IDIOMA_CHOICES = [
        ('es', 'Español'),
        ('en', 'English'),
    ]
    DOCUMENTO_CHOICES = [
        ('BOLETA', 'Boleta'),
        ('FACTURA', 'Factura'),
    ]

    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=30)
    apellido = models.CharField(max_length=50)

    tipo_cliente = models.CharField(max_length=10, choices=TIPO_CLIENTE_CHOICES, default='PERSONA')

    direccion = models.CharField(max_length=100)
    pais = models.CharField(max_length=50, default='Chile')
    region = models.CharField(max_length=50)
    comuna = models.CharField(max_length=50)
    telefono = models.CharField(max_length=14)
    email = models.EmailField(unique=True)

    idioma_preferido = models.CharField(max_length=5, choices=IDIOMA_CHOICES, default='es')
    documento_preferido = models.CharField(max_length=10, choices=DOCUMENTO_CHOICES, default='BOLETA')
    enviar_comprobante_email = models.BooleanField(default=True)
    recibe_promociones = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"
    
    class Meta:
        db_table = 'devices_cliente'