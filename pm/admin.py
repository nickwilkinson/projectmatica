from django.contrib import admin

from .models import Product, Category, Staff, Project, ProjectLogEntry

class CategoryAdmin(admin.ModelAdmin):
	extra = 1

class ProductAdmin(admin.ModelAdmin):
	extra = 1

class StaffAdmin(admin.ModelAdmin):
	extra = 1

class ProjectLogEntryAdmin(admin.ModelAdmin):
	list_display = ('entry_action', 'entry_text', 'entry_date')

class ProjectAdmin(admin.ModelAdmin):
	readonly_fields = ('redmine_project_url','redmine_project_id','redmine_project_name','total_hours_spent','recent_hours_spent', 'total_admin_hours_spent', 'total_analysis_hours_spent')
	fieldsets = [
		(None,					{'fields': ['redmine_project_url']}),
		(None,					{'fields': ['redmine_project_id']}),
		(None,					{'fields': ['redmine_project_name']}),
		(None,					{'fields': ['client_name']}),
		(None,					{'fields': ['project_desc']}),
		(None,					{'fields': ['budget']}),
		(None,					{'fields': ['tm_cap']}),
		(None,					{'fields': ['deadline']}),
		(None,					{'fields': ['analysis_pct']}),
		(None,					{'fields': ['admin_pct']}),
		(None,					{'fields': ['start_date']}),
		(None,					{'fields': ['completed_on']}),
		(None,					{'fields': ['total_hours_spent']}),
		(None,					{'fields': ['total_admin_hours_spent']}),
		(None,					{'fields': ['total_analysis_hours_spent']}),
		(None,					{'fields': ['recent_hours_spent']}),
		(None,					{'fields': ['product']}),
		(None,					{'fields': ['category']}),
		(None,					{'fields': ['team']}),
	]
	# inlines = [CategoryInline, ProductInline]
	# this is a list of fields displayed on the top-level Project page
	list_display = ('client_name', 'project_desc', 'product', 'category')
	list_filter = ['category', 'product']
	search_fields = ['client_name', 'redmine_project_name']

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Staff)
admin.site.register(ProjectLogEntry, ProjectLogEntryAdmin)
admin.site.register(Project, ProjectAdmin)