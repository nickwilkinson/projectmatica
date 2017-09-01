from django import forms
from .models import Product, Category, Staff, Project, ProjectLogEntry, ACTION_CHOICES
from django.forms import ModelMultipleChoiceField
from django.utils import timezone

class ProjectForm(forms.ModelForm):

	class StaffForm(forms.ModelForm):
	    team = ModelMultipleChoiceField(
	        queryset=Staff.objects,
	    )

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
			'category',
			'team')


class PostForm(forms.ModelForm):
# class PostForm(forms.Form):
	# entry_text = forms.CharField(widget=forms.Textarea())
	# entry_action = forms.CharField(max_length=2, widget=forms.Select(choices=ACTION_CHOICES))
	# entry_link = forms.URLField(required=False)
	# entry_type = forms.BooleanField(initial=False, required=False)
	# entry_date = forms.DateTimeField(required=False)
	# redmine_project_id = forms.IntegerField(widget=forms.HiddenInput(), initial=0)

	entry_type = forms.BooleanField(initial=False, required=False)
	# redmine_project_id = forms.IntegerField(initial=0)
	entry_action = forms.CharField(max_length=2, widget=forms.Select(choices=ACTION_CHOICES))

	class Meta:
		model = ProjectLogEntry
		# redmine_project_id = forms.IntegerField(widget=forms.HiddenInput(), initial=0)
		# entry_action = forms.CharField(max_length=2, widget=forms.Select(choices=ACTION_CHOICES))
		fields = ('entry_text', 'entry_action', 'entry_link', 'entry_type', 'entry_date', 'redmine_identifier')
		# entry_text = forms.CharField(widget=forms.Textarea())
		# entry_action = forms.CharField()
		# entry_link = forms.URLField()
		# entry_type = forms.BooleanField(initial=False, required=False)
		# entry_date = forms.DateTimeField()

