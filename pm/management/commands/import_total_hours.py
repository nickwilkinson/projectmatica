#!/usr/bin/python
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from redmine import Redmine
from datetime import datetime, date, timedelta
from pm.models import Category, Project, RecentWork

class Command(BaseCommand):
	help = 'Imports total hours spent on those billable projects that have been active in the last couple of weeks.'

	def handle(self, *args, **options):
		# Initialize redmine connection
		redmine = Redmine(settings.REDMINE_URL, version=settings.REDMINE_VER, key=settings.REDMINE_KEY)

		# Get time entries from the last X days from Redmine
		date_N_days_ago = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
		recent_time_entries = redmine.time_entry.filter(from_date=date_N_days_ago)

		# Add up the hours per project spent in the last X days
		recent_project_hours = dict()
		for entry in recent_time_entries:
			if entry.project.id in recent_project_hours:
				recent_project_hours[entry.project.id] += entry.hours
			else:
				recent_project_hours[entry.project.id] = entry.hours

		# make a list of all the project_ids in Redmine where work has been recorded in the last X days
		recent_project_ids = list(recent_project_hours.keys())

		# Delete any existig recent time entries from RecentWork table
		existing_recent_time_entries = RecentWork.objects.all().delete

		# Add project_ids to RecentWork table from the Redmine query
		for entry in recent_project_ids:
			e = RecentWork(redmine_project_id=entry)
			e.save()

		# for entry in existing_recent_time_entries:
		# 	entry.recent_hours_spent = 0.00
		# 	entry.save()

		# Save new recent time entries to pm db
		# all_pm_projects = Project.objects.all()
		# for entry in all_pm_projects:
		# 	if entry.redmine_project_id in recent_project_ids:


		# Get all deinfed projects in the pm db
		defined_projects = Project.objects.filter(category__category_name__in = ['Billable', 'Non-billable']).exclude(completed_on__isnull=False)
		defined_project_ids = []
		for defined_project in defined_projects:
			defined_project_ids.append(defined_project.redmine_project_id)

		# Get a list of unique projects where the total time spent needs to be updated in the pm db
		#  i.e. projects where 1) time has been spent in the last 14 days AND 2) they're defined in the pm db
		projects_to_update = []
		for entry in recent_time_entries:
			if entry.project.id in defined_project_ids:
				if entry.project.id not in projects_to_update:
					projects_to_update.append(entry.project.id)


		# Save total and recent hours to pm db
		temp = []
		for project_id in projects_to_update:
			project_time_entries = redmine.time_entry.filter(project_id=project_id)
			total_project_hours = 0
			total_admin_hours = 0
			total_analysis_hours = 0
			for entry in project_time_entries:
				total_project_hours += entry.hours
				if entry.activity.name == "Administration":
					total_admin_hours += entry.hours
				if entry.activity.name == "Analysis/Design":
					total_analysis_hours += entry.hours
			
			pm_project = Project.objects.get(redmine_project_id=project_id)
			pm_project.total_hours_spent = total_project_hours
			pm_project.total_admin_hours_spent = total_admin_hours
			pm_project.total_analysis_hours_spent = total_analysis_hours
			pm_project.recent_hours_spent = recent_project_hours[project_id]
			pm_project.save()
			temp.append([project_id,total_project_hours,recent_project_hours[project_id]])


		self.stdout.write('time: {0} -- [project_id, total_hours, recent_hours]: {1}'.format(datetime.now(), temp))

