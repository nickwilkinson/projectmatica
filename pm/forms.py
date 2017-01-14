from django import forms
from .models import Product, Category, Project

class ProjectForm(forms.ModelForm):

	class Meta:
		model = Project
		fields = (
			'redmine_project_id',
			'redmine_project_url',
			'redmine_project_name',
			'client_name',
			'project_desc',
			'budget',
			'tm_cap',
			'deadline',
			'analysis_pct',
			'admin_pct',
			'start_date',
			'completed_on',
			'product',
			'category')