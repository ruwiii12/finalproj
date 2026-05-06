# Migration to add Account model and link Employee to Account

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payroll_app', '0002_alter_employee_id_number_payslip'),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=100, unique=True)),
                ('password', models.CharField(max_length=100)),
                ('is_admin', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='employee',
            name='account_id',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='payroll_app.account',
            ),
        ),
    ]
