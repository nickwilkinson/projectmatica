from django.shortcuts import get_object_or_404, render, render_to_response
from django.template import RequestContext
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.conf import settings
from collections import defaultdict

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

			
			# get most recent project log and timestamp
			if ProjectLogEntry.objects.filter(redmine_identifier = entry).exists():
				most_recent_log_entry_data = ProjectLogEntry.objects.filter(redmine_identifier = entry).order_by('-id')[0]
				all_projects_details[entry]["log_entry_text"] = most_recent_log_entry_data.entry_text
				all_projects_details[entry]["log_entry_date"] = most_recent_log_entry_data.entry_date.isoformat()
			else:
				all_projects_details[entry]["log_entry_text"] = "none"
				all_projects_details[entry]["log_entry_date"] = "---"


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

			# get most recent project log and timestamp
			if ProjectLogEntry.objects.filter(redmine_identifier = entry.redmine_project_id).exists():
				most_recent_log_entry_data = ProjectLogEntry.objects.filter(redmine_identifier = entry.redmine_project_id).order_by('-id')[0]
				log_entry_text = most_recent_log_entry_data.entry_text
				log_entry_date = most_recent_log_entry_data.entry_date.isoformat()
			else:
				log_entry_text = "none"
				log_entry_date = "---"


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
				"team_display": team_display,
				"log_entry_text": log_entry_text,
				"log_entry_date": log_entry_date
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

			# get most recent project log and timestamp
			if ProjectLogEntry.objects.filter(redmine_identifier = entry.redmine_project_id).exists():
				most_recent_log_entry_data = ProjectLogEntry.objects.filter(redmine_identifier = entry.redmine_project_id).order_by('-id')[0]
				log_entry_text = most_recent_log_entry_data.entry_text
				log_entry_date = most_recent_log_entry_data.entry_date.isoformat()
			else:
				log_entry_text = "none"
				log_entry_date = "---"


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
				"team_display": team_display,
				"log_entry_text": log_entry_text,
				"log_entry_date": log_entry_date
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
		"project_list": True,
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
	if request.method == "POST":
		form = PostForm(request.POST)
		post = form.save(commit=False)
		entry_text = request.POST.get('entry_text')
		entry_link = request.POST.get('entry_link')
		entry_action = request.POST.get('entry_action')
		entry_type = request.POST.get('entry_type')
		entry_date = request.POST.get('entry_date')
		redmine_identifier = request.POST.get('redmine_identifier')
		post.entry_author = request.user.username
		post.save()

		response_data = dict()
		response_data['entry_text'] = entry_text
		response_data['entry_link'] = entry_link
		response_data['entry_action'] = entry_action
		response_data['entry_type'] = entry_type
		response_data['entry_date'] = entry_date
		response_data['user'] = request.user.username
		response_data['redmine_identifier'] = redmine_identifier
		# return HttpResponse(response_data)
		return JsonResponse(response_data)

	else:
		form = PostForm()
		return render(request, 'pm/project_log_form.html', {'form': form})

@login_required
def project_details(request, pid):
	project_logs = ProjectLogEntry.objects.filter(redmine_identifier=pid).order_by('-entry_date').values()
	project_record = Project.objects.get(redmine_project_id = pid)

	# basic project info
	project_client = project_record.client_name
	project_desc = project_record.project_desc

	# get list of unique month/year pairs
	month_years = []
	for entry in project_logs:
		temp_date = entry['entry_date'].strftime('%B %Y')
		if temp_date not in month_years:
			month_years.append(temp_date)
		
	
	# get count of how many unique month/year paris there are
	month_groups = len(month_years)

	
	# store log entries in dict organized by month/year pairs
	project_logs_formatted = []
	for entry in project_logs:
		project_details = {
			"entry_text": entry['entry_text'],
			"entry_date_formatted": entry['entry_date'].strftime('%B %Y'),
			"entry_date": entry['entry_date'],
			"entry_action": entry['entry_action'],
			"entry_link": entry['entry_link'],
			"entry_author": entry['entry_author'],
			"entry_type": entry['entry_type']
		}
		project_logs_formatted.append(project_details)


	context = { 
		"redmine_project_id": pid,
		"show_menu" : True,
		"project_client": project_client,
		"project_desc": project_desc,
		"month_years": month_years,
		"month_groups": month_groups,
		"project_logs_formatted": project_logs_formatted
	}
	return render(request, 'pm/project_details.html', context)

def currency_formatter(amount):
    if amount >= 0:
        return '${:,.0f}'.format(amount)
    else:
        return '-${:,.0f}'.format(-amount)

def avg_colour_coding(numbers, field_type):
	if field_type == 'made_lost':
		if numbers <= -1000:
			return 'text-danger'
		elif numbers >= 1000:
			return 'text-success'
	elif field_type == 'budget':
		if numbers < 5:
			return 'text-success'
		elif numbers >= 10:
			return 'text-danger'
	elif field_type == 'schedule':
		if numbers >= 1.5:
			return 'text-danger'
		elif numbers <= 1:
			return 'text-success'
	elif field_type == 'overhead':
		if numbers > 10:
			return 'text-danger'


@login_required
def scorecard(request):
	# fake rate applied to all projects. use only until model has been updated to account for actual project rates
	chargeout_rate = 150
	
	# get a list of all billable projects with a completion date
	completed_projects = Project.objects.filter(category__category_name__in = ['Billable'], completed_on__isnull=False).values()

	# count of all projects
	completed_projects_count = len(completed_projects)

	# calculate stats for all completed projects
	completed_projects_details = []
	# counter = 0
	schedule_counter = 0
	budget_overage_total = 0
	made_lost_total = 0
	overhead_pct_total = 0
	schedule_overage_total = 0
	for entry in completed_projects:
		# get year from completed_on field
		year = entry['completed_on'].strftime('%Y')
		product = entry['product_id']
		# need to calculate made/lost, budget overage pct, schedule overage pct, overhead pct
		# counter += 1

		###### made/lost calc --> (budget - total_hours_spent) * rate
		made_lost_unformatted = (entry['budget'] - entry['total_hours_spent']) * chargeout_rate
		made_lost_total += made_lost_unformatted
		made_lost = currency_formatter(made_lost_unformatted)

		made_lost_indicator = ''
		if made_lost_unformatted >= 1000:
			made_lost_indicator = 'text-success'
		if made_lost_unformatted <= -1000:
			made_lost_indicator = 'text-danger'


		###### budget overage pct calc --> ((total_hours_spent / budget) - 1) * 100
		budget_overage_indicator = ''
		if entry['budget'] != 0:
			budget_overage_pct = round((((entry['total_hours_spent'] / entry['budget']) - 1) * 100),0)
			budget_overage_total += budget_overage_pct
			if budget_overage_pct < 5:
				budget_overage_indicator = 'text-success'
			elif budget_overage_pct >= 10:
				budget_overage_indicator = 'text-danger'
		else:
			budget_overage_pct = '---'

		###### schedule overage pct calc --> ((days between actual start and end) / (days between planned start and end) - 1) * 100
		actual_start_date = entry['start_date']
		deadline = entry['deadline']
		actual_end_date = entry['completed_on']

		schedule_overage_indicator = ''
		if actual_start_date:
			if deadline:
				schedule_counter += 1
				planned_days = (deadline - actual_start_date).days
				actual_days = (actual_end_date - actual_start_date).days
				if planned_days > 0:
					schedule_overage = float(format((actual_days / planned_days),'.1f'))
				else:
					schedule_overage = 0
				if schedule_overage >= 1.5:
					schedule_overage_indicator = 'text-danger'
				elif schedule_overage <= 1:
					schedule_overage_indicator = 'text-success'
				schedule_overage_total += schedule_overage
			else:
				schedule_overage = '---'
		else:
			schedule_overage = '---'


		###### overhead pct calc --> (total_admin_hours_spent / budget) * 100
		if entry['total_hours_spent'] > 0:
			overhead_pct = int(round(((entry['total_admin_hours_spent'] / entry['total_hours_spent']) * 100),0))
			overhead_pct_total += overhead_pct
		else:
			overhead_pct = 0

		overhead_indicator = ''
		if overhead_pct > 10:
			overhead_indicator = 'text-danger'

		if entry['budget'] <= 25:
			project_size = 'small'
		elif entry['budget'] > 25 and entry['budget'] <= 150:
			project_size = 'medium'
		elif entry['budget'] > 150:
			project_size = 'large'


		completed_project_details_list = {
			"redmine_project_url": entry['redmine_project_url'],
			"client_name": entry['client_name'],
			"project_desc": entry['project_desc'],
			"made_lost_unformatted": made_lost_unformatted,
			"made_lost": made_lost,
			"made_lost_indicator": made_lost_indicator,
			"budget_overage_pct": budget_overage_pct,
			"budget_overage_indicator": budget_overage_indicator,
			"overhead_pct": overhead_pct,
			"overhead_indicator": overhead_indicator,
			"schedule_overage": schedule_overage,
			"schedule_overage_indicator": schedule_overage_indicator,
			"year": year,
			"product": product,
			"project_size": project_size
		}
		completed_projects_details.append(completed_project_details_list)


	# get a list of every unique year of project completion
	years = []
	for entry in completed_projects_details:
		temp_date = entry['year']
		if temp_date not in years:
			years.append(temp_date)
	
	# sort years in reverse order
	years.sort(reverse=True)
	# get earliest and most recent years
	first_year = years[-1]
	most_recent_year = years[0]

	# make a list of all product types
	# AtoM == 1 | Archivematica == 2 | Binder == 3 | None == 4 | Combo == 5
	product_list = [1,2,5,3]

	# set completion year and total count of projects per year
	year_details = []
	year_counter = dict()
	product_count = dict()
	budget_overage_sum = dict()
	budget_overage_pct = dict()
	budget_avg_indicator = dict()
	made_lost_sum = dict()
	made_lost_avg = dict()
	made_lost_avg_indicator = dict()
	schedule_overage_sum = dict()
	schedule_overage_avg = dict()
	schedule_avg_indicator = dict()
	overhead_sum = dict()
	overhead_avg = dict()
	for year in years:
		year_counter = 0
		product_count = {'AtoM': 0, 'Archivematica': 0, 'Binder': 0, 'Combo': 0}
		budget_overage_sum = {'AtoM': 0, 'Archivematica': 0, 'Binder': 0, 'Combo': 0}
		made_lost_sum = {'AtoM': 0, 'Archivematica': 0, 'Binder': 0, 'Combo': 0}
		made_lost_avg = {'AtoM': 0, 'Archivematica': 0, 'Binder': 0, 'Combo': 0}
		made_lost_avg_unformatted = {'AtoM': 0, 'Archivematica': 0, 'Binder': 0, 'Combo': 0}
		made_lost_avg_indicator = {'AtoM': '', 'Archivematica': '', 'Binder': '', 'Combo': ''}
		schedule_overage_sum = {'AtoM': 0, 'Archivematica': 0, 'Binder': 0, 'Combo': 0}
		schedule_overage_avg = {'AtoM': 0, 'Archivematica': 0, 'Binder': 0, 'Combo': 0}
		schedule_avg_indicator = {'AtoM': '', 'Archivematica': '', 'Binder': '', 'Combo': ''}
		overhead_sum = {'AtoM': 0, 'Archivematica': 0, 'Binder': 0, 'Combo': 0}
		overhead_avg = {'AtoM': 0, 'Archivematica': 0, 'Binder': 0, 'Combo': 0}
		overhead_avg_indicator = {'AtoM': '', 'Archivematica': '', 'Binder': '', 'Combo': ''}
		budget_overage_pcts = []
		schedule_overages = []
		overhead_pcts = []
		budget_avg_indicator = {'AtoM': '', 'Archivematica': '', 'Binder': '', 'Combo': ''}
		budget_overage_pct['AtoM'] = 0
		# if year not in year_counter:
		# 	year_counter[year] = 0
		for project_detail in completed_projects_details:
			if project_detail['year'] == year:
				year_counter += 1
				
				# count products in this year
				if project_detail['product'] == 1:
					product_count['AtoM'] += 1
					if project_detail['made_lost'] != '---':
						made_lost_sum['AtoM'] += project_detail['made_lost_unformatted']
					if project_detail['budget_overage_pct'] != '---':
						budget_overage_sum['AtoM'] += project_detail['budget_overage_pct']
					if project_detail['schedule_overage'] != '---':
						schedule_overage_sum['AtoM'] += project_detail['schedule_overage']
					if project_detail['overhead_pct'] != '---':
						overhead_sum['AtoM'] += project_detail['overhead_pct']
				elif project_detail['product'] == 2:
					product_count['Archivematica'] += 1
					if project_detail['made_lost'] != '---':
						made_lost_sum['Archivematica'] += project_detail['made_lost_unformatted']
					if project_detail['budget_overage_pct'] != '---':
						budget_overage_sum['Archivematica'] += project_detail['budget_overage_pct']
					if project_detail['schedule_overage'] != '---':
						schedule_overage_sum['Archivematica'] += project_detail['schedule_overage']
					if project_detail['overhead_pct'] != '---':
						overhead_sum['Archivematica'] += project_detail['overhead_pct']
				elif project_detail['product'] == 3:
					product_count['Binder'] += 1
					if project_detail['made_lost'] != '---':
						made_lost_sum['Binder'] += project_detail['made_lost_unformatted']					
					if project_detail['budget_overage_pct'] != '---':
						budget_overage_sum['Binder'] += project_detail['budget_overage_pct']
					if project_detail['schedule_overage'] != '---':
						schedule_overage_sum['Binder'] += project_detail['schedule_overage']
					if project_detail['overhead_pct'] != '---':
						overhead_sum['Binder'] += project_detail['overhead_pct']				
				elif project_detail['product'] == 5:
					product_count['Combo'] += 1
					if project_detail['made_lost'] != '---':
						made_lost_sum['Combo'] += project_detail['made_lost_unformatted']
					if project_detail['budget_overage_pct'] != '---':
						budget_overage_sum['Combo'] += project_detail['budget_overage_pct']
					if project_detail['schedule_overage'] != '---':
						schedule_overage_sum['Combo'] += project_detail['schedule_overage']
					if project_detail['overhead_pct'] != '---':
						overhead_sum['Combo'] += project_detail['overhead_pct']


				# sum budget overages for the given year
				if project_detail['budget_overage_pct'] != '---':
					budget_overage_pcts.append(project_detail['budget_overage_pct'])

				# sum schedule overages for the given year
				if project_detail['schedule_overage'] != '---':
					schedule_overages.append(project_detail['schedule_overage'])

				# sum overheads for the given year
				if project_detail['overhead_pct'] != '---':
					overhead_pcts.append(project_detail['overhead_pct'])

		# calculate averages per product
		if product_count['AtoM'] > 0:
			made_lost_avg['AtoM'] = currency_formatter(round((made_lost_sum['AtoM'] / product_count['AtoM']),0))
			made_lost_avg_unformatted['AtoM'] = round((made_lost_sum['AtoM'] / product_count['AtoM']),0)
			budget_overage_pct['AtoM'] = int(round((budget_overage_sum['AtoM'] / product_count['AtoM']),0))
			schedule_overage_avg['AtoM'] = float(format((schedule_overage_sum['AtoM'] / product_count['AtoM']),'.1f'))
			overhead_avg['AtoM'] = int(round((overhead_sum['AtoM'] / product_count['AtoM']),1))
		else: 
			budget_overage_pct['AtoM'] = 0
		if product_count['Archivematica'] > 0:
			made_lost_avg['Archivematica'] = currency_formatter(round((made_lost_sum['Archivematica'] / product_count['Archivematica']),0))
			made_lost_avg_unformatted['Archivematica'] = round((made_lost_sum['Archivematica'] / product_count['Archivematica']),0)
			budget_overage_pct['Archivematica'] = int(round((budget_overage_sum['Archivematica'] / product_count['Archivematica']),0))
			schedule_overage_avg['Archivematica'] = float(format((schedule_overage_sum['Archivematica'] / product_count['Archivematica']),'.1f'))
			overhead_avg['Archivematica'] = int(round((overhead_sum['Archivematica'] / product_count['Archivematica']),1))
		else:
			budget_overage_pct['Archivematica'] = 0
		if product_count['Binder'] > 0:
			made_lost_avg['Binder'] = currency_formatter(round((made_lost_sum['Binder'] / product_count['Binder']),0))
			made_lost_avg_unformatted['Binder'] = round((made_lost_sum['Binder'] / product_count['Binder']),0)
			budget_overage_pct['Binder'] = int(round((budget_overage_sum['Binder'] / product_count['Binder']),0))
			schedule_overage_avg['Binder'] = float(format((schedule_overage_sum['Binder'] / product_count['Binder']),'.1f'))
			overhead_avg['Binder'] = int(round((overhead_sum['Binder'] / product_count['Binder']),1))
		else:
			budget_overage_pct['Binder'] = 0
		if product_count['Combo'] > 0:
			made_lost_avg['Combo'] = currency_formatter(round((made_lost_sum['Combo'] / product_count['Combo']),0))
			made_lost_avg_unformatted['Combo'] = round((made_lost_sum['Combo'] / product_count['Combo']),0)
			budget_overage_pct['Combo'] = int(round((budget_overage_sum['Combo'] / product_count['Combo']),0))
			schedule_overage_avg['Combo'] = float(format((schedule_overage_sum['Combo'] / product_count['Combo']),'.1f'))
			overhead_avg['Combo'] = int(round((overhead_sum['Combo'] / product_count['Combo']),1))
		else:
			budget_overage_pct['Combo'] = 0


		# calculate overall budget overage average for the given year
		# overall_budget_overage_avg = round((sum(budget_overage_pcts) / len(budget_overage_pcts)),0)
		# overall_budget_overage_avg = float(format((sum(budget_overage_pcts) / len(budget_overage_pcts)),'.0f'))
		overall_budget_overage_avg = int(round(sum(budget_overage_pcts) / len(budget_overage_pcts)))
		# set colour indicator
		if overall_budget_overage_avg > 10:
			overall_budget_overage_avg_indicator = 'text-danger'
		elif overall_budget_overage_avg <= 10:
			overall_budget_overage_avg_indicator = 'text-success'

		if overall_budget_overage_avg < 0:
			overall_budget_overage_avg_status = str(overall_budget_overage_avg) + '% under budget!'
		elif overall_budget_overage_avg > 0:
			overall_budget_overage_avg_status = str(overall_budget_overage_avg) + '% over budget'
		elif overall_budget_overage_avg == 0:
			overall_budget_overage_avg_status = str(overall_budget_overage_avg) + '% over budget!'


		# calculate overall schedule overage average for the given year
		overall_schedule_overage_avg = round((sum(schedule_overages) / len(schedule_overages)),1)

		# calculate overall overhead average for the given year
		overall_overhead_avg = round((sum(overhead_pcts) / len(overhead_pcts)),0)


		# set colour indicators for product averages
		made_lost_avg_indicator['AtoM'] = avg_colour_coding(made_lost_avg_unformatted['AtoM'], 'made_lost')
		made_lost_avg_indicator['Archivematica'] = avg_colour_coding(made_lost_avg_unformatted['Archivematica'], 'made_lost')
		made_lost_avg_indicator['Binder'] = avg_colour_coding(made_lost_avg_unformatted['Binder'], 'made_lost')
		made_lost_avg_indicator['Combo'] = avg_colour_coding(made_lost_avg_unformatted['Combo'], 'made_lost')

		budget_avg_indicator['AtoM'] = avg_colour_coding(budget_overage_pct['AtoM'], 'budget')
		budget_avg_indicator['Archivematica'] = avg_colour_coding(budget_overage_pct['Archivematica'], 'budget')
		budget_avg_indicator['Binder'] = avg_colour_coding(budget_overage_pct['Binder'], 'budget')
		budget_avg_indicator['Combo'] = avg_colour_coding(budget_overage_pct['Combo'], 'budget')

		schedule_avg_indicator['AtoM'] = avg_colour_coding(schedule_overage_avg['AtoM'], 'schedule')
		schedule_avg_indicator['Archivematica'] = avg_colour_coding(schedule_overage_avg['Archivematica'], 'schedule')
		schedule_avg_indicator['Binder'] = avg_colour_coding(schedule_overage_avg['Binder'], 'schedule')
		schedule_avg_indicator['Combo'] = avg_colour_coding(schedule_overage_avg['Combo'], 'schedule')

		overhead_avg_indicator['AtoM'] = avg_colour_coding(overhead_avg['AtoM'], 'overhead')
		overhead_avg_indicator['Archivematica'] = avg_colour_coding(overhead_avg['Archivematica'], 'overhead')
		overhead_avg_indicator['Binder'] = avg_colour_coding(overhead_avg['Binder'], 'overhead')
		overhead_avg_indicator['Combo'] = avg_colour_coding(overhead_avg['Combo'], 'overhead')

		year_details_list = {
			"completion_year": year,
			"projects_per_year": year_counter,
			"atom_projects": product_count['AtoM'],
			"am_projects": product_count['Archivematica'],
			"binder_projects": product_count['Binder'],
			"combo_projects": product_count['Combo'],
			"overall_budget_overage_avg": overall_budget_overage_avg,
			"overall_budget_overage_avg_indicator": overall_budget_overage_avg_indicator,
			"overall_budget_overage_avg_status": overall_budget_overage_avg_status,
			"atom_budget_overage": budget_overage_pct['AtoM'],
			"am_budget_overage": budget_overage_pct['Archivematica'],
			"binder_budget_overage": budget_overage_pct['Binder'],
			"combo_budget_overage": budget_overage_pct['Combo'],
			"atom_made_lost_avg": made_lost_avg['AtoM'],
			"am_made_lost_avg": made_lost_avg['Archivematica'],
			"binder_made_lost_avg": made_lost_avg['Binder'],
			"combo_made_lost_avg": made_lost_avg['Combo'],
			"overall_schedule_overage_avg": overall_schedule_overage_avg,
			"atom_schedule_overage_avg": schedule_overage_avg['AtoM'],
			"am_schedule_overage_avg": schedule_overage_avg['Archivematica'],
			"binder_schedule_overage_avg": schedule_overage_avg['Binder'],
			"combo_schedule_overage_avg": schedule_overage_avg['Combo'],
			"overall_overhead_avg": overall_overhead_avg,
			"atom_overhead_avg": overhead_avg['AtoM'],
			"am_overhead_avg": overhead_avg['Archivematica'],
			"binder_overhead_avg": overhead_avg['Binder'],
			"combo_overhead_avg": overhead_avg['Combo'],
			"made_lost_avg_indicator": made_lost_avg_indicator,
			"budget_avg_indicator": budget_avg_indicator,
			"schedule_avg_indicator": schedule_avg_indicator,
			"overhead_avg_indicator": overhead_avg_indicator
		}
		year_details.append(year_details_list)


	# for each year and product, calculate: avg made/lost, avg budget overage, avg schedule overage, avg overhead
	counter = dict()
	made_lost_total = dict()
	budget_overage_total = dict()
	overhead_pct_total = dict()
	schedule_overage_total = dict()
	year_product_key_list = [] 
	# add value totals
	for project_detail in completed_projects_details:
		year_product_key = project_detail['year'] + '-'+ str(project_detail['product'])
		year_product_key_list.append(project_detail['year'] + '-'+ str(project_detail['product']))
		if year_product_key not in counter:
			counter[year_product_key] = 0
			made_lost_total[year_product_key] = 0
			budget_overage_total[year_product_key] = 0
			overhead_pct_total[year_product_key] = 0
			schedule_overage_total[year_product_key] = 0

		made_lost_total[year_product_key] += project_detail['made_lost_unformatted']
		
		if project_detail['budget_overage_pct'] != '---':
			budget_overage_total[year_product_key] += project_detail['budget_overage_pct']
		
		overhead_pct_total[year_product_key] += project_detail['overhead_pct']
		
		if project_detail['schedule_overage'] != '---':
			schedule_overage_total[year_product_key] += project_detail['schedule_overage']
		
		# AVERAGES WILL BE WRONG SINCE VALUES SHOULD HAVE DIFFERENT COUNTERS
		counter[year_product_key] += 1

	# calculate value averages
	made_lost_avg = dict()
	budget_overage_avg = dict()
	overhead_pct_avg = dict()
	schedule_overage_avg = dict()
	for year_product_key in year_product_key_list:
		made_lost_avg_unformatted = made_lost_total[year_product_key] / counter[year_product_key]
		made_lost_avg[year_product_key] = currency_formatter(made_lost_avg_unformatted)
		budget_overage_avg[year_product_key] = round((budget_overage_total[year_product_key] / counter[year_product_key]), 0)
		overhead_pct_avg[year_product_key] = round((overhead_pct_total[year_product_key] / counter[year_product_key]), 0)
		schedule_overage_avg[year_product_key] = round((schedule_overage_total[year_product_key] / counter[year_product_key]), 1)

	##### JS chart stuff #####
	reversed_years = []
	reversed_years = sorted(years)
	year_data = ', '.join('"{0}"'.format(y) for y in reversed_years)
	year_data_str = 'labels: ['+year_data+']'

	# overall average budget
	chart_budget_data = []
	chart_schedule_data = []
	chart_overhead_data = []
	for year in reversed_years:
		for year_entry in year_details:
			if year_entry['completion_year'] == year:
				# budget chart data -- overall average
				chart_budget_data.append(str(year_entry['overall_budget_overage_avg']))
				chart_schedule_data.append(str(year_entry['overall_schedule_overage_avg']))
				chart_overhead_data.append(str(year_entry['overall_overhead_avg']))

	chart_overall_budget_data_str = ', '.join(chart_budget_data)
	chart_overall_schedule_data_str = ', '.join(chart_schedule_data)
	chart_overall_overhead_data_str = ', '.join(chart_overhead_data)

	# average budget performance -- small projects <= 25 hours
	# for every project with a budget <= 25 hours, add up (((spent / budget) - 1) * 100) / count
	# get project counts for all completed small, medium, and large projects
	overall_project_counts = {'small':0, 'medium':0, 'large':0}
	small_project_budget_overage_avg = []
	medium_project_budget_overage_avg = []
	large_project_budget_overage_avg = []
	small_project_schedule_overage_avg = []
	medium_project_schedule_overage_avg = []
	large_project_schedule_overage_avg = []
	small_project_overhead_avg = []
	medium_project_overhead_avg = []
	large_project_overhead_avg = []
	project_size_schedule_overage_avg = dict()
	all_small_project_count = dict()
	all_medium_project_count = dict()
	all_large_project_count = dict()
	chart_project_schedule_overage_avg_str = {'small':0, 'medium':0, 'large':0}
	chart_project_overhead_avg_str = {'small':0, 'medium':0, 'large':0}
	for year in reversed_years:
		small_project_count = 0
		medium_project_count = 0
		large_project_count = 0
		small_project_budget_overage_pct = 0
		medium_project_budget_overage_pct = 0
		large_project_budget_overage_pct = 0
		project_size_schedule_overage_sums = {'small':0, 'medium':0, 'large':0}
		project_size_overhead_sums = {'small':0, 'medium':0, 'large':0}
		for entry in completed_projects_details:
			if entry['year'] == year:
				if entry['project_size'] == 'small':
					small_project_count += 1
					overall_project_counts['small'] += 1
					if entry['budget_overage_pct'] != '---':
						small_project_budget_overage_pct += entry['budget_overage_pct']
					if entry['schedule_overage'] != '---':
						project_size_schedule_overage_sums['small'] += entry['schedule_overage']
					if entry['overhead_pct'] != '---':
						project_size_overhead_sums['small'] += entry['overhead_pct']
				elif entry['project_size'] == 'medium':
					medium_project_count += 1
					overall_project_counts['medium'] += 1
					if entry['budget_overage_pct'] != '---':
						medium_project_budget_overage_pct += entry['budget_overage_pct']
					if entry['schedule_overage'] != '---':
						project_size_schedule_overage_sums['medium'] += entry['schedule_overage']
					if entry['overhead_pct'] != '---':
						project_size_overhead_sums['medium'] += entry['overhead_pct']
				elif entry['project_size'] == 'large':
					large_project_count += 1
					overall_project_counts['large'] += 1
					if entry['budget_overage_pct'] != '---':
						large_project_budget_overage_pct += entry['budget_overage_pct']
					if entry['schedule_overage'] != '---':
						project_size_schedule_overage_sums['large'] += entry['schedule_overage']
					if entry['overhead_pct'] != '---':
						project_size_overhead_sums['large'] += entry['overhead_pct']

		small_project_budget_overage_avg.append(str(round((small_project_budget_overage_pct / small_project_count),0)))
		medium_project_budget_overage_avg.append(str(round((medium_project_budget_overage_pct / medium_project_count),0)))
		large_project_budget_overage_avg.append(str(round((large_project_budget_overage_pct / large_project_count),0)))

		small_project_schedule_overage_avg.append(str(round((project_size_schedule_overage_sums['small'] / small_project_count),1)))
		medium_project_schedule_overage_avg.append(str(round((project_size_schedule_overage_sums['medium'] / medium_project_count),1)))
		large_project_schedule_overage_avg.append(str(round((project_size_schedule_overage_sums['large'] / large_project_count),1)))

		small_project_overhead_avg.append(str(round((project_size_overhead_sums['small'] / small_project_count),0)))
		medium_project_overhead_avg.append(str(round((project_size_overhead_sums['medium'] / medium_project_count),0)))
		large_project_overhead_avg.append(str(round((project_size_overhead_sums['large'] / large_project_count),0)))

		# all_small_project_count[year] = small_project_count
		# all_medium_project_count[year] = medium_project_count
		# all_large_project_count[year] = large_project_count

	chart_small_project_budget_overage_avg_str = ', '.join(small_project_budget_overage_avg)
	chart_medium_project_budget_overage_avg_str = ', '.join(medium_project_budget_overage_avg)
	chart_large_project_budget_overage_avg_str = ', '.join(large_project_budget_overage_avg)

	chart_project_schedule_overage_avg_str['small'] = ', '.join(small_project_schedule_overage_avg)
	chart_project_schedule_overage_avg_str['medium'] = ', '.join(medium_project_schedule_overage_avg)
	chart_project_schedule_overage_avg_str['large'] = ', '.join(large_project_schedule_overage_avg)

	chart_project_overhead_avg_str['small'] = ', '.join(small_project_overhead_avg)
	chart_project_overhead_avg_str['medium'] = ', '.join(medium_project_overhead_avg)
	chart_project_overhead_avg_str['large'] = ', '.join(large_project_overhead_avg)


	context = {
		"scorecard" : True,
		"show_menu": True,
		"completed_projects_count": completed_projects_count,
		"completed_projects_details": completed_projects_details,
		"budget_overage_avg": budget_overage_avg,
		"made_lost_avg": made_lost_avg,
		"overhead_pct_avg": overhead_pct_avg,
		"schedule_overage_avg": schedule_overage_avg,
		"years": years,
		"product_list": product_list,
		"first_year": first_year,
		"year_details": year_details,
		"year_data_str": year_data_str,
		"chart_overall_budget_data_str": chart_overall_budget_data_str,
		"chart_overall_schedule_data_str": chart_overall_schedule_data_str,
		"chart_overall_overhead_data_str": chart_overall_overhead_data_str,
		"chart_small_project_budget_overage_avg_str": chart_small_project_budget_overage_avg_str,
		"chart_medium_project_budget_overage_avg_str": chart_medium_project_budget_overage_avg_str,
		"chart_large_project_budget_overage_avg_str": chart_large_project_budget_overage_avg_str,
		"overall_project_counts": overall_project_counts,
		"chart_project_schedule_overage_avg_str": chart_project_schedule_overage_avg_str,
		"chart_project_overhead_avg_str": chart_project_overhead_avg_str
	}

	return render(request, 'pm/scorecard.html', context)

@login_required
def scorecard_csv(request):
	# fake rate applied to all projects. use only until model has been updated to account for actual project rates
	chargeout_rate = 150
	# get a list of all billable projects with a completion date
	completed_projects = Project.objects.filter(category__category_name__in = ['Billable'], completed_on__isnull=False).values()

	# count of all projects
	completed_projects_count = len(completed_projects)

	# calculate stats for all completed projects
	csv_export = []
	schedule_counter = 0
	budget_overage_total = 0
	made_lost_total = 0
	overhead_pct_total = 0
	schedule_overage_total = 0
	for entry in completed_projects:
		# get year from completed_on field
		year = entry['completed_on'].strftime('%Y')
		product = entry['product_id']
		# need to calculate made/lost, budget overage pct, schedule overage pct, overhead pct

		###### made/lost calc --> (budget - total_hours_spent) * rate
		made_lost_unformatted = (entry['budget'] - entry['total_hours_spent']) * chargeout_rate
		made_lost_total += made_lost_unformatted
		made_lost = currency_formatter(made_lost_unformatted)

		###### budget overage pct calc --> ((total_hours_spent / budget) - 1) * 100
		budget_overage_indicator = ''
		if entry['budget'] != 0:
			budget_overage_pct = round((((entry['total_hours_spent'] / entry['budget']) - 1) * 100),0)
			budget_overage_total += budget_overage_pct
		else:
			budget_overage_pct = '---'

		###### schedule overage pct calc --> ((days between actual start and end) / (days between planned start and end) - 1) * 100
		actual_start_date = entry['start_date']
		deadline = entry['deadline']
		actual_end_date = entry['completed_on']

		if actual_start_date:
			if deadline:
				schedule_counter += 1
				planned_days = (deadline - actual_start_date).days
				actual_days = (actual_end_date - actual_start_date).days
				if planned_days > 0:
					schedule_overage = round((actual_days / planned_days),1)
				else:
					schedule_overage = 0
				schedule_overage_total += schedule_overage
			else:
				schedule_overage = '---'
		else:
			schedule_overage = '---'


		###### overhead pct calc --> (total_admin_hours_spent / budget) * 100
		if entry['total_hours_spent'] > 0:
			overhead_pct = round(((entry['total_admin_hours_spent'] / entry['total_hours_spent']) * 100),0)
			overhead_pct_total += overhead_pct
		else:
			overhead_pct = 0

		if entry['budget'] <= 25:
			project_size = 'small'
		elif entry['budget'] > 25 and entry['budget'] <= 150:
			project_size = 'medium'
		elif entry['budget'] > 150:
			project_size = 'large'


		csv_project_details_list = {
			"redmine_project_url": entry['redmine_project_url'],
			"client_name": entry['client_name'],
			"project_desc": entry['project_desc'],
			"made_lost_unformatted": made_lost_unformatted,
			"budget_overage_pct": budget_overage_pct,
			"overhead_pct": overhead_pct,
			"schedule_overage": schedule_overage,
			"year": year,
			"product": product,
			"project_size": project_size
		}
		csv_export.append(csv_project_details_list)

	context = { "csv_export": csv_export }

	return render(request, 'pm/scorecard_csv.html', context)	

