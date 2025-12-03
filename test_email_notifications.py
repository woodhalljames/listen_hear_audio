#!/usr/bin/env python
"""
Simple test script for email notifications

This script helps you test the email notification system for the builders app.
Run this after setting up your development environment to verify emails are working.

Usage:
    python test_email_notifications.py
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from listen_hear_audio.builders.models import Property, PurchasedPackage
from listen_hear_audio.products.models import Package
from listen_hear_audio.quotes.models import SiteConfiguration
from listen_hear_audio.builders.tasks import (
    send_property_creation_email,
    send_date_request_email,
    send_date_confirmation_email
)

User = get_user_model()


def check_site_configuration():
    """Check if site configuration exists"""
    print("\n1. Checking site configuration...")
    config = SiteConfiguration.get_config()
    if config:
        print(f"   ✓ Site configuration found")
        print(f"   - Business Name: {config.business_name}")
        print(f"   - Email: {config.email}")
        print(f"   - Notification Emails: {config.notification_emails}")
    else:
        print("   ✗ No site configuration found. Please create one in Django admin.")
        return False
    return True


def check_builder_user():
    """Check if builder users exist"""
    print("\n2. Checking for builder users...")
    builders = User.objects.filter(is_builder=True)
    if builders.exists():
        print(f"   ✓ Found {builders.count()} builder(s):")
        for builder in builders:
            print(f"      - {builder.email} ({builder.company_name or 'No company'})")
    else:
        print("   ✗ No builder users found.")
        print("   Create a builder user by:")
        print("   1. Going to /accounts/signup/")
        print("   2. Check 'I am a Builder/Contractor'")
        print("   3. Enter a company name")
        return False
    return True


def check_property_with_builder():
    """Check if properties with builders exist"""
    print("\n3. Checking for properties with assigned builders...")
    properties = Property.objects.filter(builders__isnull=False).distinct()
    if properties.exists():
        print(f"   ✓ Found {properties.count()} property/properties with builders:")
        for prop in properties[:3]:
            builders = prop.builders.all()
            print(f"      - {prop.name} ({builders.count()} builder(s))")
    else:
        print("   ✗ No properties with builders found.")
        print("   Create a property in Django admin and assign builders to it.")
        return False
    return True


def test_property_creation_email():
    """Test property creation email"""
    print("\n4. Testing property creation email...")
    try:
        # Find a property with builders
        property_obj = Property.objects.filter(builders__isnull=False).first()
        if not property_obj:
            print("   ✗ No property with builders to test")
            return False

        print(f"   Sending test email for property: {property_obj.name}")
        result = send_property_creation_email(property_obj.id)

        if result:
            print(f"   ✓ Property creation email sent successfully!")
            print(f"   Check your email (Mailpit at http://localhost:1025 in dev)")
        else:
            print("   ✗ Failed to send property creation email")
            return False
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False
    return True


def test_date_request_email():
    """Test date request email"""
    print("\n5. Testing date request email...")
    try:
        # Find a package with requested date
        package = PurchasedPackage.objects.filter(
            status='date_requested',
            requested_install_date__isnull=False
        ).first()

        if not package:
            print("   ⚠ No packages with requested dates found.")
            print("   Use the builder dashboard to request an installation date first.")
            return None

        print(f"   Sending test email for package: {package.package_name}")
        result = send_date_request_email(package.id)

        if result:
            print(f"   ✓ Date request email sent successfully!")
        else:
            print("   ✗ Failed to send date request email")
            return False
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False
    return True


def test_date_confirmation_email():
    """Test date confirmation email"""
    print("\n6. Testing date confirmation email...")
    try:
        # Find a package with confirmed date
        package = PurchasedPackage.objects.filter(
            status='scheduled',
            confirmed_install_date__isnull=False
        ).first()

        if not package:
            print("   ⚠ No packages with confirmed dates found.")
            print("   Use Django admin to confirm a date request first.")
            return None

        print(f"   Sending test email for package: {package.package_name}")
        result = send_date_confirmation_email(package.id)

        if result:
            print(f"   ✓ Date confirmation email sent successfully!")
        else:
            print("   ✗ Failed to send date confirmation email")
            return False
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False
    return True


def main():
    """Run all email notification tests"""
    print("=" * 60)
    print("Email Notification Test Suite")
    print("=" * 60)

    # Run checks
    checks = [
        check_site_configuration(),
        check_builder_user(),
        check_property_with_builder(),
    ]

    if not all(checks):
        print("\n" + "=" * 60)
        print("⚠ Pre-requisites not met. Please fix the issues above.")
        print("=" * 60)
        return

    # Run tests
    print("\n" + "-" * 60)
    print("Running Email Tests")
    print("-" * 60)

    test_property_creation_email()
    test_date_request_email()
    test_date_confirmation_email()

    print("\n" + "=" * 60)
    print("Test Suite Complete!")
    print("=" * 60)
    print("\nTo view sent emails in development:")
    print("1. Open http://localhost:1025 (Mailpit)")
    print("2. Check the inbox for test emails")
    print("\nNOTE: Make sure Celery is running to process email tasks:")
    print("  celery -A config.celery_app worker -l info")
    print("=" * 60)


if __name__ == '__main__':
    main()
