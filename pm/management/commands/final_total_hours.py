#!/usr/bin/python
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from redmine import Redmine
from datetime import datetime, date, timedelta
from pm.models import Project

class Command(BaseCommand):
	help = 'Imports final tally of total hours spent on completed billable projects.'

	def handle(self, *args, **options):
		# Initialize redmine connection
		redmine = Redmine(settings.REDMINE_URL, version=settings.REDMINE_VER, key=settings.REDMINE_KEY)

		# Get all completed projects in the pm db
		completed_projects = Project.objects.filter(completed_on__isnull=False).values()
		completed_project_ids = []
		for completed_project in completed_projects:
			completed_project_ids.append(completed_project['redmine_project_id'])

		# Get total hours spent and total admin time spent per project from the Redmine db
		temp = []
		for project_id in completed_project_ids:
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

			# update data in the db
			pm_project = Project.objects.get(redmine_project_id=project_id)
			pm_project.total_hours_spent = total_project_hours
			pm_project.total_admin_hours_spent = total_admin_hours
			pm_project.total_analysis_hours_spent = total_analysis_hours
			pm_project.save()
			temp.append([project_id,total_project_hours,total_admin_hours])
			self.stdout.write('project_id: {0}'.format(project_id))

		self.stdout.write('project_id, total_project_hours, total_admin_hours: {0}'.format(temp))