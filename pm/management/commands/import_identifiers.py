from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from redmine import Redmine
from pm.models import Category, Project

class Command(BaseCommand):
	help = 'Imports project identifiers (ie URLs) from Redmine and updates the corresponding entry in the pm db.'

	def handle(self, *args, **options):
		defined_projects = Project.objects.filter(category__category_name__in = ['None'])
		redmine = Redmine(settings.REDMINE_URL, version=settings.REDMINE_VER, key=settings.REDMINE_KEY)
		all_defined_project_ids = []
		# redmine_project = redmine.project.get(422)		
		for entry in defined_projects:
			# all_defined_project_ids.append(entry.redmine_project_id)
			redmine_project = redmine.project.get(entry.redmine_project_id)
			pm_project = Project.objects.get(redmine_project_id=entry.redmine_project_id)
			all_defined_project_ids.append(redmine_project.identifier)
			pm_project.redmine_project_url = redmine_project.identifier
			pm_project.save()

		self.stdout.write('{}'.format(all_defined_project_ids))