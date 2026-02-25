from django.core.management.base import BaseCommand
from listen_hear_audio.products.models import Category, Package


class Command(BaseCommand):
    help = 'Diagnose and optionally fix category builder_section assignments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Actually apply the fixes (otherwise just show diagnostics)',
        )

    def handle(self, *args, **options):
        fix_mode = options['fix']

        self.stdout.write(self.style.WARNING('='*80))
        self.stdout.write(self.style.WARNING('CATEGORY DIAGNOSTICS'))
        self.stdout.write(self.style.WARNING('='*80))

        categories = Category.objects.all()
        self.stdout.write(f'\nTotal categories: {categories.count()}\n')

        # Check categories with no builder_section
        categories_no_section = categories.filter(builder_section='')
        self.stdout.write(self.style.WARNING(
            f'Categories with NO builder_section: {categories_no_section.count()}'
        ))

        # Auto-assign builder sections based on category names
        section_mappings = {
            # Network & Automation
            'network': 'network_automation',
            'automation': 'network_automation',
            'control': 'network_automation',
            'lighting': 'network_automation',
            'climate': 'network_automation',
            'shades': 'network_automation',
            'hvac': 'network_automation',

            # Security
            'security': 'security',
            'camera': 'security',
            'surveillance': 'security',
            'access': 'security',
            'alarm': 'security',
            'door': 'security',
            'lock': 'security',

            # Audio
            'audio': 'audio',
            'speaker': 'audio',
            'sound': 'audio',
            'music': 'audio',

            # Entertainment
            'video': 'entertainment',
            'tv': 'entertainment',
            'display': 'entertainment',
            'theater': 'entertainment',
            'media': 'entertainment',
            'entertainment': 'entertainment',
            'streaming': 'entertainment',
        }

        self.stdout.write('\n' + self.style.SUCCESS('Categories needing builder_section:'))

        fixed_count = 0
        for category in categories_no_section:
            package_count = category.packages.count()
            suggested_section = None

            # Try to determine section from category name
            cat_name_lower = category.name.lower()
            for keyword, section in section_mappings.items():
                if keyword in cat_name_lower:
                    suggested_section = section
                    break

            if suggested_section:
                section_display = dict(Category.BUILDER_SECTION_CHOICES).get(suggested_section, suggested_section)
                self.stdout.write(
                    f'  - {category.name} '
                    f'({package_count} packages) -> {self.style.SUCCESS(section_display)}'
                )

                if fix_mode:
                    category.builder_section = suggested_section
                    category.save()
                    fixed_count += 1
            else:
                self.stdout.write(
                    f'  - {category.name} '
                    f'({package_count} packages) -> {self.style.WARNING("UNKNOWN - needs manual assignment")}'
                )

        # Show summary by section
        self.stdout.write('\n' + self.style.WARNING('='*80))
        self.stdout.write(self.style.WARNING('BUILDER SECTION SUMMARY'))
        self.stdout.write(self.style.WARNING('='*80))

        for section_value, section_label in Category.BUILDER_SECTION_CHOICES:
            categories_in_section = Category.objects.filter(
                builder_section=section_value,
                is_active=True
            )
            packages_in_section = Package.objects.filter(
                category__builder_section=section_value,
                category__is_active=True,
                is_active=True
            )

            self.stdout.write(
                f'\n{section_label}:\n'
                f'  Categories: {categories_in_section.count()}\n'
                f'  Packages: {packages_in_section.count()}'
            )

            for cat in categories_in_section:
                pkg_count = cat.packages.filter(is_active=True).count()
                self.stdout.write(f'    - {cat.name} ({pkg_count} packages)')

        # Check catalog visibility
        self.stdout.write('\n' + self.style.WARNING('='*80))
        self.stdout.write(self.style.WARNING('CATALOG VISIBILITY'))
        self.stdout.write(self.style.WARNING('='*80))

        catalog_visible = categories.filter(show_in_catalog=True, is_active=True).count()
        catalog_hidden = categories.filter(show_in_catalog=False, is_active=True).count()

        self.stdout.write(f'\nVisible in catalog: {catalog_visible}')
        self.stdout.write(f'Hidden from catalog: {catalog_hidden}')

        if fix_mode:
            self.stdout.write('\n' + self.style.SUCCESS('='*80))
            self.stdout.write(self.style.SUCCESS(f'FIXED {fixed_count} categories!'))
            self.stdout.write(self.style.SUCCESS('='*80))
        else:
            self.stdout.write('\n' + self.style.WARNING('='*80))
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes made'))
            self.stdout.write(self.style.WARNING('Run with --fix to apply changes'))
            self.stdout.write(self.style.WARNING('='*80))
