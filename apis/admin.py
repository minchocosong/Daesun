from django.contrib import admin
from . import models


admin.site.register(models.Scraps, models.ScrapsAdmin)
admin.site.register(models.Pledge, models.PledgeAdmin)
admin.site.register(models.Keywords, models.KeywordsAdmin)
admin.site.register(models.ApprovalRating, models.ApprovalRatingAdmin)
admin.site.register(models.LoveOrHate, models.LoveOrHateAdmin)
