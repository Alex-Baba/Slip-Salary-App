from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_revokedtoken_alter_attendance_month_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='idempotencyrecord',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.employee'),
        ),
        migrations.AlterUniqueTogether(
            name='idempotencyrecord',
            unique_together={('endpoint', 'key', 'owner')},
        ),
    ]
