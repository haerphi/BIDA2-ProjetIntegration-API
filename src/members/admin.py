from django.contrib import admin
from .models import Member, Category

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('affiliation_number', 'first_name', 'last_name', 'email', 'birth_date', 'gender', 'is_active')
    search_fields = ('affiliation_number', 'first_name', 'last_name', 'email')
    list_filter = ('gender', 'is_active')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_age', 'max_age', 'gender')
    list_filter = ('gender',)

