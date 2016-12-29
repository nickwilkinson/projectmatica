# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-26 22:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pm', '0010_auto_20160826_1430'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='tm_cap',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=8, verbose_name='Time and Materials cap'),
        ),
    ]
