from django.shortcuts import get_object_or_404, render, render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.conf import settings

# 'Redmine' is a dependency --> pip install python-redmine
from redmine import Redmine
from datetime import datetime, date, timedelta
import time
from operator import itemgetter, attrgetter, methodcaller
import json
from django.http import JsonResponse
import math
from .models import Category, Project, RecentWork
from .forms import ProjectForm
from django.shortcuts import redirect
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test

# 'requests' is a dependency --> pip install requests
# http://stackoverflow.com/questions/17309288/importerror-no-module-named-requests
import requests


@login_required
def project_list(request):

	# Configure Redmine reqest
	redmine = Redmine(settings.REDMINE_URL, version=settings.REDMINE_VER, key=settings.REDMINE_KEY)
	
	# Get time entries from the last X days from Redmine
	# date_N_days_ago = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
	# recent_time_entries = redmine.time_entry.filter(from_date=date_N_days_ago)

	# Add up the hours per project spent in the last X days
	# recent_project_hours = dict()
	# for entry in recent_time_entries:
	# 	if entry.project.id in recent_project_hours:
	# 		recent_project_hours[entry.project.id] += entry.hours
	# 	else:
	# 		recent_project_hours[entry.project.id] = entry.hours

	# make a list of all the project_ids in Redmine where work has been recorded in the last X days
	# recent_project_ids = list(recent_project_hours.keys())
	all_recent_projects = RecentWork.objects.all()
	recent_project_ids = []
	for entry in all_recent_projects:
		recent_project_ids.append(entry.redmine_project_id)

	# Get a list of all defined projects from the Projectmatica db that:
	#  - are categorized as Billable or Non-billable
	#  - don't have a completed_on date
	defined_projects = Project.objects.filter(category__category_name__in = ['Billable', 'Non-billable']).exclude(completed_on__isnull=False)

	defined_projects_details = dict()
	project_details = dict()
	for entry in defined_projects:
		project_details = {
			"client": entry.client_name,
			"deadline": entry.deadline,
			"project_desc": entry.project_desc,
			"budget": entry.budget,
			"identifier": entry.redmine_project_url,
			"total_hours": math.ceil(entry.total_hours_spent),
			"recent_hours": entry.recent_hours_spent,
			"tm_cap": entry.tm_cap,
			"category": entry.category.category_name
		}
		defined_projects_details[entry.redmine_project_id] = project_details

	# Make a list of project_ids for defined projects
	defined_project_ids = []
	for defined_project in defined_projects:
		defined_project_ids.append(defined_project.redmine_project_id)

	# Make a list of all project_ids in Projectmatica
	all_pm_project_ids = []
	all_pm_projects = Project.objects.all()
	for entry in all_pm_projects:
		all_pm_project_ids.append(entry.redmine_project_id)

	# Remove billable / non-billable projects from all_pm_projects list
	other_pm_project_ids = all_pm_project_ids
	for project_id in defined_project_ids:
		if project_id in all_pm_project_ids:
			other_pm_project_ids.remove(project_id)

	# Build a list of projects for display on the dashboard
	all_projects_details = dict()
	for entry in recent_project_ids:
		if entry in defined_project_ids:
			all_projects_details[entry] = defined_projects_details[entry]
			# all_projects_details[entry]["recent_hours"] = recent_project_hours[entry]
			
			# Calculate remaining hours for projects with a budget
			if all_projects_details[entry]["budget"] != 0:
				remaining_hours = all_projects_details[entry]["budget"] - all_projects_details[entry]["total_hours"]
				all_projects_details[entry]["remaining_hours"] = remaining_hours

				remaining_budget_pct = remaining_hours / all_projects_details[entry]["total_hours"]

				if remaining_budget_pct <= 0:
					all_projects_details[entry]["budget_status"] = 'text-danger'
				elif remaining_budget_pct <= 0.5:
					all_projects_details[entry]["budget_status"] = 'text-warning'
				else:
					all_projects_details[entry]["budget_status"] = ''

			# Calculate deadline status
			date_14_days_from_now = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
			if date.today().strftime('%Y-%m-%d') >= str(all_projects_details[entry]["deadline"]):
				all_projects_details[entry]["deadline_status"] = 'text-danger'
			elif date_14_days_from_now >= str(all_projects_details[entry]["deadline"]):
				all_projects_details[entry]["deadline_status"] = 'text-warning'
			else:
				all_projects_details[entry]["deadline_status"] = ''

			# Set Time and Materials indicator
			if all_projects_details[entry]["tm_cap"] != 0:
				all_projects_details[entry]["tm_status"] = '<span class="label label-info">Time and Materials</span>'
			else:
				all_projects_details[entry]["tm_status"] = ''

			# Set Non-billable indicator
			if all_projects_details[entry]["category"] == "Non-billable":
				all_projects_details[entry]["category_type"] = '<span class="label label-primary">Non-billable</span>'

		elif entry not in other_pm_project_ids:
			all_projects_details[entry] = {"project_id": entry, "deadline": ''}

	sorted_all_projects_details = sorted(all_projects_details.items(), key=lambda v: (v[1]['deadline'] == '', v[1]['deadline'] is None, v[1]['deadline']))

	context = {
		"show_menu" : True,
		"sorted_all_projects_details": sorted_all_projects_details
	}

	return render(request, 'pm/index.html', context)



@user_passes_test(lambda u: u.is_superuser)
def project_new(request, pid):
	redmine = Redmine(settings.REDMINE_URL, version=settings.REDMINE_VER, key=settings.REDMINE_KEY)
	project_details = redmine.project.get(pid)

	# Create client list for autocomplete
	client_list = []
	all_pm_projects = Project.objects.all()
	for entry in all_pm_projects:
		if entry.client_name not in client_list:
			client_list.append(entry.client_name)

	# POST request (saving data)
	if request.method == "POST":
		form = ProjectForm(request.POST)
		if form.is_valid():
			project_time_entries = redmine.time_entry.filter(project_id=pid)
			total_project_hours = 0
			for entry in project_time_entries:
				total_project_hours += entry.hours

			project = form.save(commit=False)
			project.redmine_project_url = project_details.identifier
			project.redmine_project_id = project_details.id
			project.redmine_project_name = project_details.name
			project.total_hours_spent = total_project_hours
			project.save()
			return redirect('project_list')
	# GET request (loading data)
	else:
		form = ProjectForm(initial={
			'redmine_project_url': project_details.identifier, 
			'redmine_project_id': project_details.id,
			'redmine_project_name': project_details.name,
			'client_name': project_details.parent.name
			})
		form.fields['redmine_project_id'].widget.attrs['readonly'] = True
		form.fields['redmine_project_url'].widget.attrs['readonly'] = True
		form.fields['redmine_project_name'].widget.attrs['readonly'] = True
		form.fields['deadline'].widget.attrs['placeholder'] = 'yyyy-mm-dd'
		form.fields['completed_on'].widget.attrs['placeholder'] = 'yyyy-mm-dd'

	context = {
		"show_menu" : True,
		"form" : form,
		"client_list": client_list,
		"autocomplete": True
	}
	return render(request, 'pm/project_edit.html', context)


@user_passes_test(lambda u: u.is_superuser)
def project_edit(request, pid):
	project = get_object_or_404(Project, redmine_project_id=pid)

	# Create client list for autocomplete
	client_list = []
	all_pm_projects = Project.objects.all()
	for entry in all_pm_projects:
		if entry.client_name not in client_list:
			client_list.append(entry.client_name)

	if request.method == "POST":
		form = ProjectForm(request.POST, instance=project)
		if form.is_valid():
			project = form.save(commit=False)
			# project.redmine_project_id = 1000
			# project.redmine_project_name = ''
			project.save()
			return redirect('project_list')
	else:
		form = ProjectForm(instance=project)
		form.fields['redmine_project_id'].widget.attrs['readonly'] = True
		form.fields['redmine_project_url'].widget.attrs['readonly'] = True
		form.fields['redmine_project_name'].widget.attrs['readonly'] = True
		form.fields['deadline'].widget.attrs['placeholder'] = 'yyyy-mm-dd'
		form.fields['completed_on'].widget.attrs['placeholder'] = 'yyyy-mm-dd'

	context = {
		"show_menu" : True,
		"form" : form,
		"client_list": client_list,
		"autocomplete": True
	}
	return render(request, 'pm/project_edit.html', context)