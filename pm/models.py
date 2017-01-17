import datetime

from django.db import models
from django.utils import timezone

class Product(models.Model):
	product_name = models.CharField(max_length=20)
	
	def __str__(self):
		return self.product_name


class Category(models.Model):
	category_name = models.CharField(max_length=30)
	
	def __str__(self):
		return self.category_name


class Project(models.Model):
	redmine_project_url = models.CharField(max_length=100, blank=True, default="")
	redmine_project_id = models.IntegerField()
	redmine_project_name = models.CharField(max_length=200)
	client_name = models.CharField(max_length=75)
	project_desc = models.CharField('Project description', max_length=200)
	budget = models.IntegerField(default=0, blank=True)
	tm_cap = models.IntegerField('Time and Materials cap', default=0, blank=True)
	deadline = models.DateField(blank=True, null=True)
	analysis_pct = models.DecimalField('Analysis %', max_digits=3, decimal_places=2, default=0.00)
	admin_pct = models.DecimalField('Admin %', max_digits=3, decimal_places=2, default=0.00)
	start_date = models.DateField('Start date', blank=True, null=True)
	completed_on = models.DateField('Completion date', blank=True, null=True)
	total_hours_spent = models.DecimalField('Total hours spent', max_digits=8, decimal_places=2, default=0.00)
	total_admin_hours_spent = models.DecimalField('Total admin hours spent', max_digits=8, decimal_places=2, default=0.00)
	total_analysis_hours_spent = models.DecimalField('Total analysis hours spent', max_digits=8, decimal_places=2, default=0.00)
	recent_hours_spent = models.DecimalField('Recent hours spent', max_digits=8, decimal_places=2, default=0.00)
	product = models.ForeignKey(Product, on_delete=models.CASCADE, default=4) #defauls to "None" product
	category = models.ForeignKey(Category, on_delete=models.CASCADE, default=9) #defauls to "Uncategorized"
	
	def __str__(self):
		return self.redmine_project_name


class RecentWork(models.Model):
	redmine_project_id = models.IntegerField()

	def __str__(self):
		return '%s' % (self.redmine_project_id)