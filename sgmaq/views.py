from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Q  # Import the Q object
from django.db.models import Count, Prefetch
from django.db import connection
from .decorators import unauthenticated_user, allowed_user
import plotly.express as px
import os
from django.conf import settings

from .models import Project
from .models import Client
from .models import CarBrand
from .models import CarModel
from .models import MotivoRechazo
from .models import PostImage
from .models import ChangeReason
from .models import ChangeLog
from .models import Task


from .forms import EmployeeTaskForm
from .forms import TaskUploadImage
from .forms import PostImageForm
from .forms import TaskDeliveryClientForm
from .forms import TaskFormRechazoManager
from .forms import TaskFormRechazoCliente
from .forms import UploadFileForm

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.platypus import Image as ImageReportlab
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

from datetime import datetime
import pandas as pd
from django.core.exceptions import ObjectDoesNotExist


def index(request):
    return render(request, 'global/index.html')

def about(request):
    return render(request, 'global/about.html')

@unauthenticated_user
def signup(request):
    if request.method == 'GET':
        return render(request, 'global/signup.html', {"form": UserCreationForm})
    else:

        if request.POST["password1"] == request.POST["password2"]:
            try:
                user = User.objects.create_user(
                    request.POST["username"], password=request.POST["password1"])
                user.save()
                login(request, user)
                return redirect('index')
            except IntegrityError:
                return render(request, 'global/signup.html', {"form": UserCreationForm, "error": "Username already exists."})

        return render(request, 'global/signup.html', {"form": UserCreationForm, "error": "Passwords did not match."})

@unauthenticated_user
def signin(request):
    if request.method == 'GET':
        return render(request, 'global/signin.html', {"form": AuthenticationForm})
    else:
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'global/signin.html', {"form": AuthenticationForm, "error": "Username or password is incorrect."})

        login(request, user)
        return redirect('index')
    
@allowed_user(allowed_roles=['admin', 'manager', 'employee', 'customer'])
def signout(request):
    logout(request)
    return redirect('index')

@login_required
@allowed_user(allowed_roles=['admin', 'manager', 'employee'])
def tasks(request):
    tasks = Task.objects.filter(Q(employee_user=request.user), datecompleted__isnull=True)
    pending_tasks_count = Task.objects.filter(datecompleted__isnull=True).count() # se mostrará para admins y managers
    pending_tasks_per_user = Task.objects.filter(datecompleted__isnull=True).values('employee_user_id__username').annotate(total=Count('id')) # 
    
    # Obtener la descripción del motivo de rechazo para cada tarea
    for task in tasks:
        if task.motivo_rechazo_manager:
            motivo_rechazo_id = task.motivo_rechazo_manager
            motivo_rechazo_desc = MotivoRechazo.objects.get(codigo=motivo_rechazo_id).descripcion
            task.motivo_rechazo_desc = motivo_rechazo_desc  # Añadir el campo de descripción al objeto de tarea


    return render(request, 'tasks/tasks.html', {
        'tasks': tasks,
        'pending_tasks_count': pending_tasks_count,
        'pending_tasks_per_user': pending_tasks_per_user
    })

@login_required
def task_search(request):
    # filtramos las tareas por usuario, por pendiente y por id (patente)
    query = request.GET.get('q')
    tasks = Task.objects.filter(employee_user=request.user, datecompleted__isnull=True, vin__icontains=query)
    return render(request, 'tasks/tasks.html', {
        'tasks': tasks
    })

@login_required
def upload_file(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        try:
            # Leer el archivo Excel usando pandas
            df = pd.read_excel(file)

            # Convertir las columnas de fecha a cadenas
            if 'deadline' in df.columns:
                df['deadline'] = df['deadline'].astype(str)

            # Procesar cada fila por separado
            results = []
            for index, row in df.iterrows():
                try:
                    vin = row['vin']
                    project_name = row['proyecto']
                    client_name = row['cliente']
                    carbrand = row['carbrand']
                    carmodel = row['carmodel']
                    comment = row['comment'] if pd.notnull(row['comment']) else None
                    created = datetime.now()  # Fecha y hora actual
                    deadline = row['deadline'] if pd.notnull(row['deadline']) else None
                    employee_user = row['employee']
                    responsible_user = row['responsible']
                    priority = row['priority']
                    description = row['description'] if pd.notnull(row['description']) else None
                    important = row['important']
                    deniedbyclient = False
                    windows = False
                    chassis = False
                    wheels = False
                    upholstery = False
                    flag_rechazado = False

                    # Validar el campo VIN
                    if Task.objects.filter(vin=vin).exists():
                        raise IntegrityError(f'El VIN "{vin}" ya existe en la base de datos.')
                    
                    # Validar el campo proyecto
                    try:
                        project = Project.objects.get(name=project_name)
                    except ObjectDoesNotExist:
                        raise ValueError(f'El proyecto "{project_name}" no existe en la base de datos.')
                    
                    # Validar el campo cliente
                    try:
                        client = Client.objects.get(name=client_name)
                    except ObjectDoesNotExist:
                        raise ValueError(f'El cliente "{client_name}" no existe en la base de datos.')

                    # Validar el campo carbrand
                    try:
                        car_brand = CarBrand.objects.get(brandname=carbrand)
                    except ObjectDoesNotExist:
                        raise ValueError(f'La marca de coches "{carbrand}" no existe en el sistema.')

                    # Validar el campo carmodel
                    try:
                        car_model = CarModel.objects.get(model=carmodel)
                    except ObjectDoesNotExist:
                        raise ValueError(f'El modelo "{carmodel}" no existe en el sistema.')

                    # Validar que la relación entre marca y modelo 
                    
                    # Validar campos de usuario
                    try:
                        responsible_user_info = User.objects.get(username=responsible_user)
                    except ObjectDoesNotExist:
                        raise ValueError(f'El usuario "{responsible_user}" no existe en el sistema.')

                    try:
                        employee_user_info = User.objects.get(username=employee_user)
                    except ObjectDoesNotExist:
                        raise ValueError(f'El usuario "{employee_user}" no existe en el sistema.')

                    # Validar del campo prioridad
                    if priority != 1 and priority != 0:
                        raise ValueError(f'El valor del campo "prioridad" en la fila {index + 2} no es válido. Sólo se permiten los valores 0 y 1.')

                    # Crear una nueva instancia de Task usando el método create
                    task = Task.objects.create(
                        vin=vin,
                        project=project,
                        client=client,
                        carbrand=car_brand,
                        carmodel=car_model,
                        comment=comment,
                        created=created,
                        deadline=deadline,
                        employee_user=employee_user_info,
                        responsible_user=responsible_user_info,
                        priority=priority,
                        description=description,
                        important=important,
                        deniedbyclient=deniedbyclient,
                        windows=windows,
                        chassis=chassis,
                        wheels=wheels,
                        upholstery=upholstery,
                        flag_rechazado=flag_rechazado
                    )

                    # Create changelog entry
                    ChangeLog.objects.create(
                        task=task,
                        dateofchange=created,
                        user=request.user,
                        descripcion_estado="Alta en el sistema",
                        changereason="Alta en el sistema",
                        comment="Alta en el sistema desde carga de fichero"
                    )

                    results.append({'index': index, 'status': 'success', 'message': f'{index + 2} - {vin} VIN insertado correctamente en el sistema.'})
                except Exception as e:
                    results.append({'index': index, 'status': 'error', 'message': f'Error en fila {index + 2}: {e}'})
            
            return JsonResponse({'results': results})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    else:
        form = UploadFileForm()
        return render(request, 'tasks/tasks_upload.html', {'form': form})




@login_required
def task_delivery(request, task_id):
    history = ChangeLog.objects.filter(task_id=task_id).order_by('-dateofchange') # Obtener el historial filtrado por task_id

    if history:
        user_ids = [h.user_id for h in history]
        users = User.objects.filter(pk__in=user_ids)
        # Combinar historiales con usuarios
        history = [(h, u) for h in history for u in users if u.pk == h.user_id]

    if request.method == 'GET':
        task = get_object_or_404(Task, pk=task_id, employee_user=request.user)
        images = PostImage.objects.filter(task=task)
        form = EmployeeTaskForm(instance=task)
        imageForm = TaskUploadImage(instance=task)

        return render(request, 'tasks/task_delivery.html', {
            'task': task,
            'form': form,
            'history': history,
            'imageForm': imageForm,
            'images': images
        })


    else:
        try:

            task = get_object_or_404(Task, pk=task_id, employee_user=request.user)
            field = request.POST.get('field')
            value = request.POST.get('value') == 'true'
            
            if hasattr(task, field):
                setattr(task, field, value)
                task.save()
                return redirect('tasks')
            else:
                return redirect('tasks')
        except ValueError:
                return render(request, 'tasks/task_delivery.html', {
                    'task': task,
                    'form': form,
                    'error': "Error actualizando task"
                })
        
@login_required    
def complete_task(request, task_id):
    # meter try
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=task_id, employee_user=request.user)
        form = EmployeeTaskForm(request.POST, instance=task)
        task.save()

        # Validation - para entregar, los checks deben estar marcados todos
        if all([task.windows, task.chassis, task.wheels, task.upholstery]):
            task.datecompleted = timezone.now()
            task.flag_rechazado = False
            task.save()

            # Create changelog entry
            ChangeLog.objects.create(
                task_id=task_id,
                dateofchange = timezone.now(),
                user_id=request.user.id,
                descripcion_estado = "Tarea completada",
                changereason="Tarea completada",
                comment="Entrada automática",
        
            )

            return redirect('tasks')
        
        return render(request, 'tasks/task_delivery.html', {
            'task': task,
            'form': form,
            'error': "Error - Antes de entregar debe completar todas las tareas"
            })

@login_required       
def upload_image(request, task_id):
    if request.method == 'POST':
        task = Task.objects.get(pk=task_id)
        images = request.FILES.getlist('images')  # Nombre del campo en el formulario
        
        if not images:
            return JsonResponse({'status': 'error', 'message': 'No images uploaded'})

        errors = []
        for image in images:
            image_form = PostImageForm({'task': task.id}, {'images': image})
            if image_form.is_valid():
                post_image = image_form.save(commit=False)
                post_image.task = task
                post_image.save()
            else:
                errors.append(image_form.errors)
        
        if errors:
            return JsonResponse({'status': 'error', 'errors': errors})
        
        return JsonResponse({'status': 'success', 'message': 'Images uploaded successfully'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@allowed_user(allowed_roles=['admin', 'manager'])
def task_manager_pending(request):
    # Mostrar todas las tareas entregadas por employee, independientemente del usuario
    tasks = Task.objects.filter(datecompleted__isnull=False, datecompleted_manager_approval__isnull=True).order_by('-datecompleted')
    return render(request, 'tasks/task_manager_pending.html', {
        'tasks': tasks
    })

@login_required
def task_manager_approval(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if request.method == 'POST':
        try:
            form = TaskDeliveryClientForm(request.POST)
            if form.is_valid():
                task.datecompleted_manager_approval = timezone.now()
                task.save()
                # Create changelog entry
                ChangeLog.objects.create(
                    task_id=task_id,
                    dateofchange = timezone.now(),
                    user_id=request.user.id,
                    descripcion_estado = "Tarea Aprobada por manager",
                    changereason= "Tarea Aprobada por manager",
                    comment="Entrada automática",
                )                
            return redirect('task_manager_pending')
        except ValueError:
                return redirect('task_manager_pending')

@login_required
@allowed_user(allowed_roles=['admin', 'manager'])
def task_manager_denial(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if request.method == 'GET':
        print('task_manager_denial - get')
        return render(request, 'tasks/task_manager_denial.html', {
            'task': task,
            'form': TaskFormRechazoManager
        })
    else:
        print('task_manager_denial - post')
        try:
            form = TaskFormRechazoManager(request.POST)
            if form.is_valid():
                task.datecompleted = None
                task.datecompleted_manager_approval = None
                task.datecompleted_client_approval = None
                task.motivo_rechazo_manager = form.cleaned_data['motivo_rechazo_manager']
                task.comentario_rechazo_manager = form.cleaned_data['comentario_rechazo_manager']
                task.flag_rechazado = True
                task.save()
                # Create changelog entry
                ChangeLog.objects.create(
                    task_id=task_id,
                    dateofchange = timezone.now(),
                    user_id=request.user.id,
                    descripcion_estado = "Tarea Rechazada por manager",
                    changereason= MotivoRechazo.objects.get(codigo=task.motivo_rechazo_manager).descripcion,
                    comment=task.comentario_rechazo_manager,
                )
            return redirect('task_manager_pending')
        except ValueError:
            return redirect('task_manager_pending')

@login_required
def task_detail(request, task_id):
    if request.method == 'GET':
        history = ChangeLog.objects.filter(task_id=task_id).order_by('-dateofchange') # Obtener el historial filtrado por task_id

        if history:
            user_ids = [h.user_id for h in history]
            users = User.objects.filter(pk__in=user_ids)
            # Combinar historiales con usuarios
            history = [(h, u) for h in history for u in users if u.pk == h.user_id]

        task = get_object_or_404(Task, pk=task_id)
        form = EmployeeTaskForm(instance=task)
        imageForm = TaskUploadImage(instance=task)
        return render(request, 'tasks/task_detail.html', {
            'task': task,
            'form': form,
            'history': history,
            'imageForm': imageForm
        })

@login_required
@allowed_user(allowed_roles=['admin', 'manager'])
def task_manager_client_pending(request):
    # fecha de compeltada, y manager rellena, cliente vacía
    tasks = Task.objects.filter(datecompleted__isnull=False, datecompleted_manager_approval__isnull=False, datecompleted_client_approval__isnull=True)

    return render(request, 'tasks/task_manager_client_pending.html', {
        'tasks': tasks
    })

@login_required
@allowed_user(allowed_roles=['admin', 'manager'])
def tasks_history(request):
    tasks = Task.objects.all() # todas las tareas
    return render(request, 'tasks/tasks_history.html', {
        'tasks': tasks
    })

@login_required
@allowed_user(allowed_roles=['customer'])
def task_client_pending(request):
    # Mostrar todas las tareas entregadas por employee, independientemente del usuario
    tasks = Task.objects.filter(datecompleted__isnull=False, datecompleted_manager_approval__isnull=False, datecompleted_client_approval__isnull=True).order_by('-datecompleted')
    return render(request, 'tasks/task_client_pending.html', {
        'tasks': tasks
    })

@login_required
@allowed_user(allowed_roles=['customer'])
def task_client_approval(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if request.method == 'POST':
        try:

            form = TaskDeliveryClientForm(request.POST)
            if form.is_valid():
                task.datecompleted_client_approval = timezone.now()
                task.save()

                # Create changelog entry
                ChangeLog.objects.create(
                    task_id=task_id,
                    dateofchange = timezone.now(),
                    user_id=request.user.id,
                    descripcion_estado = "Tarea Aprobada por cliente",
                    changereason= "Tarea Aprobada por cliente",
                    comment="Entrada automática",
            
                )                
                
            return redirect('task_client_pending')
        except ValueError:
                return redirect('task_client_pending')

@login_required
@allowed_user(allowed_roles=['customer'])
def task_client_denial(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if request.method == 'GET':
        return render(request, 'tasks/task_client_denial.html', {
            'task': task,
            'form': TaskFormRechazoCliente
        })
    else:
        try:
            form = TaskFormRechazoCliente(request.POST)
            if form.is_valid():
                task.datecompleted = None
                task.datecompleted_manager_approval = None
                task.datecompleted_client_approval = None
                task.motivo_rechazo_cliente = form.cleaned_data['motivo_rechazo_cliente']
                task.comentario_rechazo_cliente = form.cleaned_data['comentario_rechazo_cliente']
                task.flag_rechazado = True
                task.save()

                # Create changelog entry
                ChangeLog.objects.create(
                    task_id=task_id,
                    dateofchange = timezone.now(),
                    user_id=request.user.id,
                    descripcion_estado = "Tarea Rechazada por cliente",
                    changereason= MotivoRechazo.objects.get(codigo=task.motivo_rechazo_cliente).descripcion,
                    comment=task.comentario_rechazo_cliente,
                )

            return redirect('task_client_pending')
        except ValueError:
            return redirect('task_client_pending')



@login_required
@allowed_user(allowed_roles=['admin', 'manager'])
def dashboard(request):
    # Obtener todas las altas en el sistema agrupadas por año y mes
    altas_por_mes = ChangeLog.objects.filter(changereason='Alta en el sistema') \
        .extra(select={'year_month': "strftime('%%Y-%%m', dateofchange)"}) \
        .values('year_month') \
        .annotate(num_altas=Count('id'))

    # Convertir a DataFrame
    df_altas = pd.DataFrame(list(altas_por_mes))

    if not df_altas.empty:
        fig = px.bar(
            df_altas,
            x='year_month',
            y='num_altas',
            labels={'year_month': 'Año-Mes', 'num_altas': 'Número de Altas'},
            title='Número de Altas en el Sistema por Mes',
            color_discrete_sequence=['#FFD700']  # Amarillo
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='black')
        )
        chart = fig.to_html()
    else:
        chart = "<p>No data available for altas por mes.</p>"

    # Obtener todos los rechazos por mes
    rechazos_por_mes = ChangeLog.objects.filter(descripcion_estado__icontains='Rechazada') \
        .extra(select={'year_month': "strftime('%%Y-%%m', dateofchange)"}) \
        .values('year_month') \
        .annotate(num_altas=Count('id'))

    # Convertir a DataFrame
    df_rechazos = pd.DataFrame(list(rechazos_por_mes))

    if not df_rechazos.empty:
        fig = px.bar(
            df_rechazos,
            x='year_month',
            y='num_altas',
            labels={'year_month': 'Año-Mes', 'num_altas': 'Número de Rechazos'},
            title='Número de Rechazos en el Sistema por Mes',
            color_discrete_sequence=['#D3D3D3']  # Gris
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='black')
        )
        chart_rechazos_por_mes = fig.to_html()
    else:
        chart_rechazos_por_mes = "<p>No data available for rechazos por mes.</p>"

    # Consulta para obtener los motivos de rechazo
    sql_query = """
        SELECT t.changereason, COUNT(t.task_id) AS cuenta_rechazos
        FROM (
            SELECT task_id, descripcion_estado, changereason 
            FROM sgmaq_changelog
            WHERE descripcion_estado LIKE '%Rechaz%'
        ) AS t
        GROUP BY t.changereason
    """

    # Ejecutar la consulta SQL
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        resultados = cursor.fetchall()

    # Convertir resultados a DataFrame
    df_resultados = pd.DataFrame(resultados, columns=['changereason', 'cuenta_rechazos'])

    if not df_resultados.empty:
        fig = px.bar(
            df_resultados,
            x='changereason',
            y='cuenta_rechazos',
            labels={'changereason': 'Motivo de Rechazo', 'cuenta_rechazos': 'Cantidad de Rechazos'},
            title='Número de Rechazos en el Sistema',
            color_discrete_sequence=['#000000']  # Negro
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='black')
        )
        chart_rechazos_por_empleado = fig.to_html()
    else:
        chart_rechazos_por_empleado = "<p>No data available for rechazos por empleado.</p>"

    return render(request, 'tasks/dashboard.html', {
        'chart': chart,
        'chart_rechazos_por_mes': chart_rechazos_por_mes,
        'chart_rechazos_por_empleado': chart_rechazos_por_empleado
    })


@login_required
def generate_pdf(request):
    # Crear un objeto HttpResponse con las cabeceras PDF.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="task_list.pdf"'

    # Crear el objeto PDF
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    # Agregar el logo
    logo_path = os.path.join(settings.BASE_DIR, 'sgmaq', 'static', 'logo-footer.png')
    elements.append(ImageReportlab(logo_path, width=2*inch, height=1*inch))

    # Añadir el título del documento
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.alignment = 1
    elements.append(Paragraph("Task List", title_style))

    # Encabezado y pie de página
    def add_header_footer(canvas, doc):
        canvas.saveState()
        header = "Task List"
        footer = "Page %d" % doc.page
        canvas.setFont('Helvetica-Bold', 12)
        canvas.drawString(inch, 10.5*inch, header)
        canvas.setFont('Helvetica', 10)
        canvas.drawString(inch, 0.75*inch, footer)
        canvas.restoreState()

    # Añadir los datos de la tabla
    data = [["VIN", "Fecha", "Responsable"]]
    tasks = Task.objects.all()
    for task in tasks:
        formatted_date = task.created.strftime("%d/%m/%Y %H:%M")
        data.append([task.vin, formatted_date, task.employee_user_id])

    # Crear la tabla y añadirla al PDF
    table = Table(data, colWidths=[2*inch, 2*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    # Construir el PDF
    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

    return response

@login_required
def download_page(request):
    return render(request, 'tasks/download.html')






