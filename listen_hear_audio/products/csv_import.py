import csv
import io
from decimal import Decimal
from django.utils.text import slugify
from .models import PropertyType, Category, SubCategory, Package


def map_phase_name_to_installation_phase(phase_name, category_name):
    """
    Map labor_Phase_Name from CSV to installation_phase choices.

    Args:
        phase_name: The labor_Phase_Name from CSV (e.g., "Pre-Drywall")
        category_name: The category name for additional context

    Returns:
        One of: 'framing', 'rough_ins', 'insulation_drywall', 'trim_finishes'
    """
    phase_lower = phase_name.lower() if phase_name else ''
    category_lower = category_name.lower() if category_name else ''

    # Trim & Finish is trim_finishes
    if 'trim' in phase_lower or 'finish' in phase_lower:
        return 'trim_finishes'

    # Programming & Training happens after construction - trim_finishes
    if 'programming' in phase_lower or 'training' in phase_lower:
        return 'trim_finishes'

    # Pre-Drywall is rough_ins (wiring before drywall)
    if 'pre-drywall' in phase_lower or 'pre-wire' in category_lower:
        return 'rough_ins'

    # Post-Drywall - determine by category
    if 'post-drywall' in phase_lower:
        # Wiring, Security, Speaker Pre-Wire → rough_ins
        if any(word in category_lower for word in ['wiring', 'security', 'speaker', 'pre-wire']):
            return 'rough_ins'

        # Audio, Lighting, Automation systems → insulation_drywall or trim_finishes
        if 'audio' in category_lower or 'lighting' in category_lower or 'automation' in category_lower:
            return 'insulation_drywall'

        # Network infrastructure → insulation_drywall
        if 'network' in category_lower:
            return 'insulation_drywall'

        # Default for Post-Drywall
        return 'insulation_drywall'

    # Default fallback - rough-ins (most wiring/infrastructure)
    return 'rough_ins'


def detect_property_type_from_category(category_name):
    """
    Auto-detect property type from category name.

    Returns: 'Industrial', 'Commercial', or 'Residential'
    """
    category_lower = category_name.lower()

    # Industrial keywords
    if any(word in category_lower for word in ['industrial', 'factory', 'warehouse', 'plc', 'scada', 'process control']):
        return 'Industrial'

    # Commercial keywords
    if any(word in category_lower for word in ['commercial', 'building', 'enterprise', 'office', 'retail', 'business', 'access control']):
        return 'Commercial'

    # Default to Residential
    return 'Residential'


def import_packages_from_csv(csv_file, overwrite=False):
    """
    Import packages from CSV file. Property type is auto-detected from category names.

    CSV Format:
    category,type,item,labor_Phase_Name,Unit Price

    Args:
        csv_file: File object or file path
        overwrite: Whether to overwrite existing packages with same name

    Returns:
        dict with stats: {
            'created': int,
            'updated': int,
            'skipped': int,
            'errors': list of error messages,
            'property_types': dict of property type counts
        }
    """
    stats = {
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'errors': [],
        'property_types': {}
    }

    # Read CSV
    try:
        # Handle file object or string
        if hasattr(csv_file, 'read'):
            content = csv_file.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            csv_data = io.StringIO(content)
        else:
            # Assume it's a file path
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_data = io.StringIO(f.read())

        reader = csv.DictReader(csv_data)

        for row_num, row in enumerate(reader, start=2):  # Start at 2 because of header row
            try:
                # Extract data
                category_name = row.get('category', '').strip()
                type_name = row.get('type', '').strip()
                item_name = row.get('item', '').strip()
                phase_name = row.get('labor_Phase_Name', '').strip()
                price_str = row.get('Unit Price', '').strip()

                # Validate required fields
                if not category_name or not item_name:
                    stats['errors'].append(f"Row {row_num}: Missing category or item name")
                    stats['skipped'] += 1
                    continue

                # Parse price
                try:
                    price = Decimal(price_str) if price_str else Decimal('0.00')
                except:
                    stats['errors'].append(f"Row {row_num}: Invalid price '{price_str}' for {item_name}")
                    price = Decimal('0.00')

                # Auto-detect property type from category name
                property_type_name = detect_property_type_from_category(category_name)

                # Get or create PropertyType
                property_type, _ = PropertyType.objects.get_or_create(
                    name=property_type_name,
                    defaults={'slug': slugify(property_type_name)}
                )

                # Track property types
                stats['property_types'][property_type_name] = stats['property_types'].get(property_type_name, 0) + 1

                # Get or create Category
                category, _ = Category.objects.get_or_create(
                    property_type=property_type,
                    name=category_name,
                    defaults={'slug': slugify(category_name)}
                )

                # Get or create SubCategory (if type is provided)
                subcategory = None
                if type_name:
                    subcategory, _ = SubCategory.objects.get_or_create(
                        category=category,
                        name=type_name,
                        defaults={'slug': slugify(type_name)}
                    )

                # Determine installation phase
                installation_phase = map_phase_name_to_installation_phase(phase_name, category_name)

                # Check if package exists
                existing_package = Package.objects.filter(name=item_name).first()

                if existing_package and not overwrite:
                    stats['skipped'] += 1
                    continue

                # Create or update package
                package_defaults = {
                    'category': category,
                    'subcategory': subcategory,
                    'installation_phase': installation_phase,
                    'starting_price': price,
                    'slug': slugify(item_name),
                    'is_active': True,
                }

                if existing_package and overwrite:
                    # Update existing
                    for key, value in package_defaults.items():
                        setattr(existing_package, key, value)
                    existing_package.save()
                    stats['updated'] += 1
                else:
                    # Create new
                    Package.objects.create(
                        name=item_name,
                        **package_defaults
                    )
                    stats['created'] += 1

            except Exception as e:
                stats['errors'].append(f"Row {row_num}: {str(e)}")
                stats['skipped'] += 1

    except Exception as e:
        stats['errors'].append(f"CSV file error: {str(e)}")

    return stats
