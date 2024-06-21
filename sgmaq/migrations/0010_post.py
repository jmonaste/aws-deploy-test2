# Generated by Django 4.2.2 on 2024-06-11 10:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sgmaq', '0009_changelog'),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=250)),
                ('description', models.TextField()),
                ('image', models.FileField(blank=True, upload_to='')),
            ],
        ),
    ]
