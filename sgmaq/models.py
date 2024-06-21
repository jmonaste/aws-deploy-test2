from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name
    
class Client(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class CarBrand(models.Model):
    brandname = models.CharField(max_length=100)

    def __str__(self):
        return self.brandname

class CarModel(models.Model):
    model = models.CharField(max_length=100)
    brandname = models.ForeignKey(CarBrand, on_delete=models.CASCADE)

    def __str__(self):
        return self.model
    

class ChangeType(models.Model):
    changetype = models.CharField(max_length=100)

    def __str__(self):
        return self.changetype
    

class ChangeReason(models.Model):
    changereason = models.CharField(max_length=100)
    changetype = models.ForeignKey(ChangeType, on_delete=models.CASCADE)

    def __str__(self):
        return self.changereason        
    
class MotivoRechazo(models.Model):
    codigo = models.CharField(max_length=2, unique=True)
    descripcion = models.CharField(max_length=255)

    def __str__(self):
        return self.descripcion
    

    
class Task(models.Model):
    vin = models.CharField(max_length=100) # vehicle id num - número único de cada vehículo fabricado, por todas las marcas a nivel internacional - regulado por la norma ISO 3833
    project = models.ForeignKey(Project, on_delete=models.CASCADE) # campaña
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    carbrand = models.ForeignKey(CarBrand, on_delete=models.CASCADE)
    carmodel = models.ForeignKey(CarModel, on_delete=models.CASCADE) # la marca se saca con el modelo
    comment = models.TextField(blank=True)

    carimage = models.ImageField(upload_to = 'images/', blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(null=True, blank=True)
    datecompleted = models.DateTimeField(null=True, blank=True) # fecha en la que el employee termina el trabajo
    datecompleted_manager_approval = models.DateTimeField(null=True, blank=True) # fecha en la que el manager aprueba envío a cliente
    datecompleted_client_approval = models.DateTimeField(null=True, blank=True) # fecha en la que el cliente acepta el envío
    datecompleted_history = models.DateTimeField(null=True, blank=True) # fecha en la que se almacena en el histórico

    employee_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assigned_user_for_task")
    responsible_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="responsible_user_for_task")

    priority = models.CharField(max_length=1)
    description = models.TextField(blank=True)
    important = models.BooleanField(default=False)
    deniedbyclient = models.BooleanField(default=False)

    # Esto sólo debería rellenarlo el employee una vez vaya completando las tareas. a la hora de entregar, debe validarse que estas están completadas
    windows = models.BooleanField(default=False)
    chassis = models.BooleanField(default=False)
    wheels = models.BooleanField(default=False)
    upholstery = models.BooleanField(default=False)

    #AQUI VA LO BORRADO
    motivo_rechazo_manager = models.CharField(
        max_length=2,
        choices=MotivoRechazo.objects.values_list('codigo', 'descripcion'),
        null=True,
        blank=True,
    )
    comentario_rechazo_manager = models.TextField(blank=True, null=True)

    motivo_rechazo_cliente = models.CharField(
        max_length=2,
        choices=MotivoRechazo.objects.values_list('codigo', 'descripcion'),
        null=True,
        blank=True,
    )

    comentario_rechazo_cliente = models.TextField(blank=True, null=True)

    flag_rechazado = models.BooleanField(default=False)

    def __str__(self):
        #return self.vin + ' - ' + self.project.name + ' - ' + self.description
        return self.vin


class ChangeLog(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE) # VIN se obtiene con el ID del vehiuclo
    dateofchange = models.DateTimeField(auto_now_add=True) # se setea cuando se genera una fila o se añade una nueva task
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    descripcion_estado = models.TextField(blank=True, null=True)
    changereason = models.CharField(max_length=100, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    

    def __str__(self):
        return self.task

class Post(models.Model):
    title = models.CharField(max_length=250)
    description = models.TextField()
    image = models.FileField(blank=True)

    def __str__(self):
        return self.title
    


class PostImage(models.Model):
    task = models.ForeignKey(Task, default=None, on_delete=models.CASCADE)
    images = models.FileField(upload_to = 'images/')

    def __str__(self):
        return self.task.vin