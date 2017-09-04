# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-08-18 21:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pm', '0026_auto_20170725_1323'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entry_text', models.CharField(max_length=225)),
                ('entry_link', models.CharField(blank=True, default='', max_length=100)),
                ('entry_action', models.CharField(max_length=20)),
                ('entry_type', models.CharField(blank=True, max_length=20)),
                ('entry_date', models.DateField(verbose_name='Entry date')),
                ('project', models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='pm.Project')),
            ],
        ),
    ]