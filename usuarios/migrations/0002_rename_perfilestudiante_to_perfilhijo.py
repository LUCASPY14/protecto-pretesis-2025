# Generated manually for renaming PerfilEstudiante to PerfilHijo

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        # Renombrar tabla de PerfilEstudiante a PerfilHijo
        migrations.RenameModel(
            old_name='PerfilEstudiante',
            new_name='PerfilHijo',
        ),
        
        # Renombrar campo en RecargaSaldo
        migrations.RenameField(
            model_name='RecargaSaldo',
            old_name='estudiante',
            new_name='hijo',
        ),
    ]