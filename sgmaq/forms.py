from django import forms
from django.forms import ModelForm
from .models import Task, PostImage

class UploadFileForm(forms.Form):
    file = forms.FileField()

class EmployeeTaskForm(ModelForm):
    class Meta:
        model = Task
        fields = ['windows', 'chassis', 'wheels', 'upholstery']
        labels = {
            'windows': 'Ventanas',
            'chassis': 'Carrocería', 
            'wheels': 'Llantas', 
            'upholstery': 'Tapicería'
        }

class TaskUploadImage(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['carimage']

# Formulario para usar el modelo de imagen del post
class PostImageForm(forms.ModelForm):
    class Meta:
        model = PostImage
        fields = ['images']


class TaskDeliveryClientForm(forms.ModelForm):
  task_id = forms.IntegerField(widget=forms.HiddenInput())
  class Meta:
    model = Task
    fields = ['task_id']


class TaskFormRechazoManager(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['vin', 'project']

class TaskFormRechazoCliente(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['vin', 'project']