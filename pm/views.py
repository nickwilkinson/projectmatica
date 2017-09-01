from django.shortcuts import get_object_or_404, render, render_to_response
from django.template import RequestContext
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.conf import settings

# 'Redmine' is a dependency --> pip install python-redmine
from redmine import Redmine
from datetime import datetime, date, timedelta
import time
from operator import itemgetter, attrgetter, methodcaller
from django.http import JsonResponse
import math
from .models import Category, Project, RecentWork, ProjectLogEntry
from .forms import ProjectForm, PostForm
from django.shortcuts import redirect
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test

# 'requests' is a dependency --> pip install requests
# http://stackoverflow.com/questions/17309288/importerror-no-module-named-requests
import requests


@login_required
def project_list(request):

	# Configure Redmine reqest
	# redmine = Redmine(settings.REDMINE_URL, version=settings.REDMINE_VER, key=settings.REDMINE_KEY)
	
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
	#  - are categorized as Billable or Non-billable (don't get list of non-billable projects, yet!)
	#  - don't have a completed_on date
	# defined_projects = Project.objects.filter(category__category_name__in = ['Billable', 'Non-billable']).exclude(completed_on__isnull=False)
	defined_projects = Project.objects.filter(category__category_name__in = ['Billable']).exclude(completed_on__isnull=False)

	defined_projects_details = dict()
	project_details = dict()
	for entry in defined_projects:
		project_details = {
			"client": entry.client_name,
			"deadline": entry.deadline,
			"project_desc": entry.project_desc,
			"budget": entry.budget,
			"analysis_pct": entry.analysis_pct,
			"admin_pct": entry.admin_pct,
			"identifier": entry.redmine_project_url,
			"total_hours": math.ceil(entry.total_hours_spent),
			"total_admin_hours": math.ceil(entry.total_admin_hours_spent),
			"total_analysis_hours": math.ceil(entry.total_analysis_hours_spent),
			"recent_hours": entry.recent_hours_spent,
			"tm_cap": entry.tm_cap,
			"category": entry.category.category_name,
			"product": entry.product.product_name,
			"team": entry.staff_abvrs()
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

	
	# Build a list of projects for display on the dashboard [AtoM, Archivematica, Binder, Combo]
	product_count = [0, 0, 0, 0]
	all_projects_details = dict()
	for entry in recent_project_ids:
		if entry in defined_project_ids:
			all_projects_details[entry] = defined_projects_details[entry]
			# all_projects_details[entry]["recent_hours"] = recent_project_hours[entry]
			
			# Calculate remaining hours for projects with a budget
			if all_projects_details[entry]["budget"] != 0:
				if (all_projects_details[entry]["admin_pct"] == 0.0) and (all_projects_details[entry]["analysis_pct"] == 0.0):
					remaining_hours = all_projects_details[entry]["budget"] - all_projects_details[entry]["total_hours"]
					all_projects_details[entry]["remaining_hours"] = int(remaining_hours)
				else:
					tmp_total = all_projects_details[entry]["total_hours"] - all_projects_details[entry]["total_admin_hours"] - all_projects_details[entry]["total_analysis_hours"]
					remaining_hours = all_projects_details[entry]["budget"] - (tmp_total + (float(all_projects_details[entry]["total_admin_hours"]) * float(all_projects_details[entry]["admin_pct"])) + (float(all_projects_details[entry]["total_analysis_hours"]) * float(all_projects_details[entry]["analysis_pct"])))
					all_projects_details[entry]["remaining_hours"] = int(remaining_hours)

				remaining_budget_pct = float(remaining_hours / all_projects_details[entry]["budget"])

				# all_projects_details[entry]["budget_status"] = remaining_budget_pct
				if remaining_budget_pct <= 0.5:
					all_projects_details[entry]["budget_status"] = 'text-warning'
				else:
					all_projects_details[entry]["budget_status"] = ''
				
				if all_projects_details[entry]["remaining_hours"] <= 0:
					all_projects_details[entry]["budget_status"] = 'text-danger'


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


			# Determine if there are any projects for each product
			if all_projects_details[entry]["product"] == 'AtoM':
				product_count[0] = 1
			elif all_projects_details[entry]["product"] == 'Archivematica':
				product_count[1] = 1
			elif all_projects_details[entry]["product"] == 'Combo':
				product_count[2] = 1
			elif all_projects_details[entry]["product"] == 'Binder':
				product_count[3] = 1


			# Build team data for display
			if all_projects_details[entry]["team"] != '':
				all_projects_details[entry]["team_display"] = all_projects_details[entry]["team"].split(",")
			else:
				all_projects_details[entry]["team_display"] = ['<span>---</span>']


		# Add list of Uncategorized projects
		elif entry not in other_pm_project_ids:
			all_projects_details[entry] = {"project_id": entry, "deadline": ''}

	sorted_all_projects_details = sorted(all_projects_details.items(), key=lambda v: (v[1]['deadline'] == '', v[1]['deadline'] is None, v[1]['deadline']))


	# Build a list of non-billable projects
	all_non_billable_projects = Project.objects.filter(category__category_name__in = ['Non-billable']).exclude(completed_on__isnull=False)
	displayed_non_billable_projects = dict()
	non_billable_project_details = dict()
	non_billable_count = [0,0,0,0]
	for entry in all_non_billable_projects:
		if entry.redmine_project_id in recent_project_ids:
			
			remaining_hours = int(entry.budget - math.ceil(entry.total_hours_spent))
			
			# Set Time and Materials indicator
			if entry.tm_cap != 0:
				tm_status = '<span class="label label-info">Time and Materials</span>'
			else:
				tm_status = ''

			# Build team data for display
			if entry.staff_abvrs() != '':
				team_display = entry.staff_abvrs().split(",")
			else:
				team_display = ['<span>---</span>']

			non_billable_project_details = {
				"redmine_project_id": entry.redmine_project_id,
				"deadline": entry.deadline,
				"client": entry.client_name,
				"project_desc": entry.project_desc,
				"identifier": entry.redmine_project_url,
				"budget": entry.budget,
				"remaining_hours": remaining_hours,
				"recent_hours": entry.recent_hours_spent,
				"tm_status": tm_status,
				"product": entry.product.product_name,
				"total_hours": math.ceil(entry.total_hours_spent),
				"team_display": team_display
			}
			
			if entry.product.product_name == "AtoM":
				non_billable_count[0] += 1
			elif entry.product.product_name == "Archivematica":
				non_billable_count[1] += 1
			elif entry.product.product_name == "Binder":
				non_billable_count[2] += 1
			elif entry.product.product_name == "Combo":
				non_billable_count[3] += 1
			
			displayed_non_billable_projects[entry.redmine_project_id] = non_billable_project_details
	
	sorted_displayed_non_billable_projects = sorted(displayed_non_billable_projects.items(), key=lambda v: (v[1]['deadline'] == '', v[1]['deadline'] is None, v[1]['deadline']))


	# Build a list of inactivate projects
	all_billable_projects = Project.objects.filter(category__category_name__in = ['Billable']).exclude(completed_on__isnull=False)
	displayed_inactive_projects = dict()
	inactive_project_details = dict()
	inactive_count = [0,0,0,0]
	for entry in all_billable_projects:
		if entry.redmine_project_id not in recent_project_ids:
			
			remaining_hours = int(entry.budget - math.ceil(entry.total_hours_spent))
			
			# Set Time and Materials indicator
			if entry.tm_cap != 0:
				tm_status = '<span class="label label-info">Time and Materials</span>'
			else:
				tm_status = ''

			# Build team data for display
			if entry.staff_abvrs() != '':
				team_display = entry.staff_abvrs().split(",")
			else:
				team_display = ['<span>---</span>']


			inactive_project_details = {
				"redmine_project_id": entry.redmine_project_id,
				"deadline": entry.deadline,
				"client": entry.client_name,
				"project_desc": entry.project_desc,
				"identifier": entry.redmine_project_url,
				"budget": entry.budget,
				"remaining_hours": remaining_hours,
				"tm_status": tm_status,
				"product": entry.product.product_name,
				"total_hours": math.ceil(entry.total_hours_spent),
				"team_display": team_display
			}
			
			if entry.product.product_name == "AtoM":
				inactive_count[0] += 1
			elif entry.product.product_name == "Archivematica":
				inactive_count[1] += 1
			elif entry.product.product_name == "Binder":
				inactive_count[2] += 1
			elif entry.product.product_name == "Combo":
				inactive_count[3] += 1

			displayed_inactive_projects[entry.redmine_project_id] = inactive_project_details
	
	sorted_displayed_inactive_projects = sorted(displayed_inactive_projects.items(), key=lambda v: (v[1]['deadline'] == '', v[1]['deadline'] is None, v[1]['deadline']))

	# Build list of products to iterate through on the Dashboard
	product_list = ["Atom", "Archivematica", "Mixed projects", "Binder"]

	context = {
		"show_menu" : True,
		"sorted_all_projects_details": sorted_all_projects_details,
		"displayed_inactive_projects": sorted_displayed_inactive_projects,
		"displayed_non_billable_projects": sorted_displayed_non_billable_projects,
		"product_count": product_count,
		"non_billable_count": non_billable_count,
		"inactive_count": inactive_count,
		"dashboard": True,
		"product_list": product_list
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
			form.save_m2m()
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
		form.fields['start_date'].widget.attrs['placeholder'] = 'yyyy-mm-dd'
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
			project.save()
			# project.redmine_project_id = 1000
			# project.redmine_project_name = ''
			form.save_m2m()
			return redirect('project_list')
	else:
		form = ProjectForm(instance=project)
		form.fields['redmine_project_id'].widget.attrs['readonly'] = True
		form.fields['redmine_project_url'].widget.attrs['readonly'] = True
		form.fields['redmine_project_name'].widget.attrs['readonly'] = True
		form.fields['deadline'].widget.attrs['placeholder'] = 'yyyy-mm-dd'
		form.fields['start_date'].widget.attrs['placeholder'] = 'yyyy-mm-dd'
		form.fields['completed_on'].widget.attrs['placeholder'] = 'yyyy-mm-dd'

	context = {
		"show_menu" : True,
		"form" : form,
		"client_list": client_list,
		"autocomplete": True
	}
	return render(request, 'pm/project_edit.html', context)


def post_new(request):
    # form = PostForm()
    # return render(request, 'pm/project_log_form.html', {'form': form})

	# if request.method == 'POST':
	# 	# post_text = request.POST.get('the_entry')
	# 	response_data = {}

	# 	# post = Post(text=post_text)
	# 	# post.save()

	# 	response_data['result'] = 'Create post successful!'
	# 	# response_data['postpk'] = post.pk
	# 	# response_data['text'] = post.text
	# 	# response_data['created'] = post.created.strftime('%B %d, %Y %I:%M %p')
	# 	# response_data['author'] = post.author.username

	# 	return HttpResponse(
	# 		json.dumps(response_data),
	# 		content_type="application/json"
	# 	)
	# else:
	# 	return HttpResponse(
	# 		json.dumps({"nothing to see": "this isn't happening"}),
	# 		content_type="application/json"
	# 	)



	if request.method == "POST":
		form = PostForm(request.POST)
		post = form.save(commit=False)
		entry_text = request.POST.get('entry_text')
		entry_link = request.POST.get('entry_link')
		entry_action = request.POST.get('entry_action')
		entry_type = request.POST.get('entry_type')
		entry_date = request.POST.get('entry_date')
		redmine_identifier = request.POST.get('redmine_identifier')
		post.save()

		# post = form.save(commit=False)
		# post.entry_text = entry_text
		# post.entry_link = timezone.now()
		# post.save()
		# response_data = {}
		# response_data = form
		# response_data = [entry_text, entry_link, entry_action, entry_type, entry_date, redmine_project_id]
		response_data = dict()
		response_data['entry_text'] = entry_text
		response_data['entry_link'] = entry_link
		response_data['entry_action'] = entry_action
		response_data['entry_type'] = entry_type
		response_data['entry_date'] = entry_date
		response_data['redmine_identifier'] = redmine_identifier
		# return HttpResponse(response_data)
		return JsonResponse(response_data)

		# form = PostForm(request.POST)
		# if form.is_valid():
			# post = form.save()
			# entry_text = request.POST.get('entry_text')
			# entry_link = request.POST.get('entry_link')
			# entry_type = request.POST.get('entry_type')
			# entry_date = request.POST.get('entry_date')
			
			# response_data = {}
			# post = ProjectLogEntry(entry_text = text)
			# post.save()
			# post = form.save(commit=False)
			# post.entry_text = entry_text
			# post.published_date = timezone.now()
			# post.save()
			# return redirect('post_detail', pk=post.pk)
			# response_data['result'] = 'Create post successful!'
			# response_data['entry_text'] = entry_text
			# response_data['entry_link'] = entry_link
			# # response_data['entry_text'] = post.entry_text
			# return HttpResponse(json.dumps(response_data), content_type="application/json")
			# return JsonResponse(response_data)
	else:
		form = PostForm()
		return render(request, 'pm/project_log_form.html', {'form': form})

