# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-26 18:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pm', '0007_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='category',
            field=models.ForeignKey(default=9, on_delete=django.db.models.deletion.CASCADE, to='pm.Category'),
        ),
    ]
