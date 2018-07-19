from django.contrib import admin

from .models import *

admin.site.register(Bill)
admin.site.register(Legislator)
admin.site.register(Action)
admin.site.register(Sponsorship)
admin.site.register(CoSponsorship)
admin.site.register(Representative)
admin.site.register(Senator)
admin.site.register(State)
admin.site.register(BillSummary)
admin.site.register(Committee)
