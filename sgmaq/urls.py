from django.urls import path
from . import views
from django.contrib import admin
from django.conf import settings  # new
from django.urls import path, include  # new
from django.conf.urls.static import static  # new

urlpatterns = [    
    path('', views.index, name="index"),
    path('about/', views.about, name="about"),
    path('signin/', views.signin, name="signin"),
    path('signup/', views.signup, name="signup"),
    path('logout/', views.signout, name="logout"),

    path('tasks/', views.tasks, name="tasks"),
    path('tasks/task_search', views.task_search, name="task_search"),
    path('task_detail/<int:task_id>', views.task_detail, name="task_detail"),
    path('tasks_history/', views.tasks_history, name="tasks_history"),

    path('upload/', views.upload_file, name='upload_file'),

    path('task_delivery/<int:task_id>', views.task_delivery, name="task_delivery"),
    path('tasks/<int:task_id>/complete', views.complete_task, name="complete_task"),
    path('upload_image/<int:task_id>/', views.upload_image, name='upload_image'),

    path('task_manager_pending/', views.task_manager_pending, name="task_manager_pending"),
    path('task_manager_approval/<int:task_id>', views.task_manager_approval, name="task_manager_approval"), 
    path('task_manager_denial/<int:task_id>/', views.task_manager_denial, name="task_manager_denial"),  
    path('task_manager_client_pending/', views.task_manager_client_pending, name="task_manager_client_pending"),  

    path('task_client_pending/', views.task_client_pending, name="task_client_pending"),
    path('task_client_approval/<int:task_id>/', views.task_client_approval, name="task_client_approval"),    
    path('task_client_denial/<int:task_id>/', views.task_client_denial, name="task_client_denial"),    

    path('dashboard/', views.dashboard, name="dashboard"),

    path('download/', views.download_page, name='download_page'),
    path('download_pdf/', views.generate_pdf, name='generate_pdf'),
]  


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) #new