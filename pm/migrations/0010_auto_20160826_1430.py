# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-26 21:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pm', '0009_auto_20160826_1420'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='tm_cap',
            field=models.IntegerField(blank=True, default=0, verbose_name='Time and Materials cap'),
        ),
    ]
