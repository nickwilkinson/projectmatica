# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-26 17:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pm', '0005_auto_20160826_1021'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='product',
            field=models.ForeignKey(default=4, on_delete=django.db.models.deletion.CASCADE, to='pm.Product'),
        ),
    ]
