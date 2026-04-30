from django.contrib import admin
from .models import User, BloodBank, BloodInventory, DonationRequest, BloodRequest

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # Matches your custom role-based User model
    list_display = ('username', 'email', 'role', 'phone', 'blood_group', 'is_staff')
    list_filter = ('role', 'blood_group', 'is_staff')
    search_fields = ('username', 'email', 'phone')

@admin.register(BloodBank)
class BloodBankAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'contact')
    search_fields = ('name', 'location')

@admin.register(BloodInventory)
class BloodInventoryAdmin(admin.ModelAdmin):
    list_display = ('blood_bank', 'blood_group', 'units_available')
    list_filter = ('blood_group', 'blood_bank')
    # Allows you to update stock levels directly from the list view
    list_editable = ('units_available',)

@admin.register(DonationRequest)
class DonationRequestAdmin(admin.ModelAdmin):
    # This matches the "my_donations" logic in your donor_dashboard
    list_display = ('donor', 'blood_bank', 'blood_group', 'status', 'created_at')
    list_filter = ('status', 'blood_group')
    list_editable = ('status',)
    date_hierarchy = 'created_at'

@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    # This matches the hospital request logic
    list_display = ('hospital', 'blood_group', 'units_needed', 'status', 'created_at')
    list_filter = ('status', 'blood_group')
    list_editable = ('status',)
    search_fields = ('hospital__username', 'location')