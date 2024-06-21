from django.contrib import admin
from .models import Project, Task, Client, CarBrand, CarModel, ChangeType, ChangeReason, Post, PostImage
from import_export.admin import ImportExportModelAdmin

class TaskAdmin(ImportExportModelAdmin):
    readonly_fields = ("created", )

# Register your models here.
admin.site.register(Project)

admin.site.register(Client)

admin.site.register(CarBrand)
admin.site.register(CarModel)

admin.site.register(ChangeType)
admin.site.register(ChangeReason)


admin.site.register(Task, TaskAdmin)
