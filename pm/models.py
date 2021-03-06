import datetime

from django.db import models
from django.utils import timezone
from django import forms

# Define options for log entry action, to be displayed in the form select box
UPDATE = 'UP'
DECISION = 'DC'
ACTION_CHOICES = (
	(UPDATE, 'Update'),
	(DECISION, 'Decision'),
)


class Product(models.Model):
	product_name = models.CharField(max_length=20)
	
	def __str__(self):
		return self.product_name


class Category(models.Model):
	category_name = models.CharField(max_length=30)
	
	def __str__(self):
		return self.category_name


class Staff(models.Model):
	staff_abvr = models.CharField(max_length=4, blank=True, default="")
	staff_email = models.EmailField(blank=True, default="")
	staff_name = models.CharField(max_length=30, blank=True, default="")
	staff_position = models.CharField(max_length=20, blank=True, default="")
	
	def __str__(self):
		return self.staff_name


class Project(models.Model):
	redmine_project_url = models.CharField(max_length=100, blank=True, default="")
	redmine_project_id = models.IntegerField()
	redmine_project_name = models.CharField(max_length=200)
	client_name = models.CharField(max_length=75)
	project_desc = models.CharField('Project description', max_length=200)
	budget = models.IntegerField(default=0, blank=True)
	tm_cap = models.IntegerField('Time and Materials flag', default=0, blank=True)
	deadline = models.DateField(blank=True, null=True)
	analysis_pct = models.DecimalField('Analysis %', max_digits=3, decimal_places=2, default=0.00)
	admin_pct = models.DecimalField('Admin %', max_digits=3, decimal_places=2, default=0.00)
	start_date = models.DateField('Start date', blank=True, null=True)
	completed_on = models.DateField('Completion date', blank=True, null=True)
	total_hours_spent = models.DecimalField('Total hours spent', max_digits=8, decimal_places=2, default=0.00)
	total_admin_hours_spent = models.DecimalField('Total admin hours spent', max_digits=8, decimal_places=2, default=0.00)
	total_analysis_hours_spent = models.DecimalField('Total analysis hours spent', max_digits=8, decimal_places=2, default=0.00)
	recent_hours_spent = models.DecimalField('Recent hours spent', max_digits=8, decimal_places=2, default=0.00)
	product = models.ForeignKey(Product, on_delete=models.CASCADE, default=4) #defaults to "None" product
	category = models.ForeignKey(Category, on_delete=models.CASCADE, default=9) #defaults to "Uncategorized"
	team = models.ManyToManyField(Staff, blank=True)

	# https://stackoverflow.com/questions/4564086/django-display-content-of-a-manytomanyfield
	def staff_abvrs(self):
		return ', '.join([a.staff_abvr for a in self.team.all()])
	staff_abvrs.short_description = "Staff Abbreviations"

	def __str__(self):
		return self.redmine_project_name


class RecentWork(models.Model):
	redmine_project_id = models.IntegerField()

	def __str__(self):
		return '%s' % (self.redmine_project_id)


class ProjectLogEntry(models.Model):
	entry_action = models.CharField(max_length=2, choices=ACTION_CHOICES, default=UPDATE)
	entry_text = models.TextField(max_length=250)
	entry_link = models.URLField(blank=True, default="")
	entry_type = models.BooleanField('Meeting?', default=False)
	entry_date = models.DateTimeField(default=timezone.now)
	redmine_identifier = models.IntegerField()
	entry_author = models.CharField(max_length=20, default="")

	def __str__(self):
		return self.entry_action
