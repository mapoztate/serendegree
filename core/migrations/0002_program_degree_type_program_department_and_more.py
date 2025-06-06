# Generated by Django 4.2.21 on 2025-05-08 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='degree_type',
            field=models.CharField(choices=[('Associate', 'Associate'), ('Bachelor', 'Bachelor'), ('Master', 'Master'), ('Doctorate', 'Doctorate'), ('Certificate', 'Certificate')], default='Bachelor', max_length=20),
        ),
        migrations.AddField(
            model_name='program',
            name='department',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='program',
            name='elective_courses',
            field=models.ManyToManyField(blank=True, related_name='elective_for_programs', to='core.course'),
        ),
        migrations.AlterField(
            model_name='program',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='program',
            name='required_courses',
            field=models.ManyToManyField(related_name='required_for_programs', to='core.course'),
        ),
        migrations.AlterField(
            model_name='studentschedule',
            name='courses',
            field=models.ManyToManyField(to='core.course'),
        ),
    ]
