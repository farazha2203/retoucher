from django.contrib import admin
from .models import *

admin.site.register(CustomerTier)
admin.site.register(CustomerProfile)
admin.site.register(StudioProfile)
admin.site.register(CustomerSubscription)
admin.site.register(PerformanceCommissionRule)
admin.site.register(OrderPricingSnapshot)
