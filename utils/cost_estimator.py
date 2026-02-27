"""Cost estimation module for vehicle damage repairs."""
import json
import os


def load_cost_data():
    """Load cost data from the JSON database."""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'cost_data.json')
    with open(db_path, 'r') as f:
        return json.load(f)


def estimate_costs(damages, severity_assessment):
    """
    Estimate repair costs based on detected damages and severity.
    Returns detailed cost breakdown with totals.
    """
    cost_data = load_cost_data()
    parts_db = cost_data['parts']
    labor_rate = cost_data['labor_rate_per_hour']
    paint_cost = cost_data['paint_cost_per_panel']
    severity_multipliers = cost_data['severity_multipliers']

    line_items = []
    total_parts_cost = 0
    total_labor_cost = 0
    total_paint_cost = 0

    for damage in damages:
        part_key = damage.get('part', '')
        severity = damage.get('severity', 'minor')
        damage_type = damage.get('damage_type', 'scratch')

        part_info = parts_db.get(part_key, None)
        if not part_info:
            # Default costs for unknown parts
            part_info = {
                'name': part_key.replace('_', ' ').title(),
                'repair_cost': {'min': 150, 'max': 500},
                'replacement_cost': {'min': 400, 'max': 1200},
                'labor_hours': {'repair': 2, 'replacement': 3}
            }

        multiplier = severity_multipliers.get(severity, 0.5)

        # Determine if repair or replacement
        needs_replacement = severity == 'severe' or damage_type in ['shatter', 'structural']

        if needs_replacement:
            cost_range = part_info['replacement_cost']
            labor_hours = part_info['labor_hours']['replacement']
            action = 'Replace'
        else:
            cost_range = part_info['repair_cost']
            labor_hours = part_info['labor_hours']['repair']
            action = 'Repair'

        # Calculate costs based on severity multiplier
        part_cost = cost_range['min'] + (cost_range['max'] - cost_range['min']) * multiplier
        labor_cost = labor_hours * labor_rate
        panel_paint_cost = paint_cost['min'] + (paint_cost['max'] - paint_cost['min']) * multiplier

        # Only add paint for visible damage
        needs_paint = damage_type not in ['shatter', 'crack'] or part_key not in ['headlight', 'taillight', 'windshield', 'side_mirror']

        item = {
            'part_name': part_info['name'],
            'part_key': part_key,
            'action': action,
            'damage_type': damage_type.replace('_', ' ').title(),
            'severity': severity,
            'part_cost': round(part_cost, 2),
            'labor_cost': round(labor_cost, 2),
            'labor_hours': labor_hours,
            'paint_cost': round(panel_paint_cost, 2) if needs_paint else 0,
            'subtotal': round(part_cost + labor_cost + (panel_paint_cost if needs_paint else 0), 2)
        }

        line_items.append(item)
        total_parts_cost += part_cost
        total_labor_cost += labor_cost
        if needs_paint:
            total_paint_cost += panel_paint_cost

    subtotal = total_parts_cost + total_labor_cost + total_paint_cost
    tax_rate = 0.08
    tax = subtotal * tax_rate
    total = subtotal + tax

    return {
        'line_items': line_items,
        'summary': {
            'total_parts': round(total_parts_cost, 2),
            'total_labor': round(total_labor_cost, 2),
            'total_paint': round(total_paint_cost, 2),
            'subtotal': round(subtotal, 2),
            'tax_rate': tax_rate,
            'tax': round(tax, 2),
            'total': round(total, 2),
            'currency': cost_data['currency']
        },
        'recommendation': get_recommendation(severity_assessment, total),
        'estimated_repair_days': estimate_repair_time(line_items)
    }


def get_recommendation(severity_assessment, total_cost):
    """Generate a recommendation based on severity and cost."""
    overall = severity_assessment.get('overall', 'minor')

    if overall == 'minor':
        return {
            'status': 'PRE-APPROVED',
            'status_color': '#22c55e',
            'message': f'This claim of ${total_cost:,.2f} is pre-approved for immediate processing.',
            'next_steps': [
                'Choose a certified repair shop from our network',
                'Schedule your repair appointment',
                'Repairs will begin upon vehicle drop-off'
            ]
        }
    elif overall == 'moderate':
        return {
            'status': 'PRE-APPROVED',
            'status_color': '#22c55e',
            'message': f'This claim of ${total_cost:,.2f} is pre-approved. A brief review may be conducted.',
            'next_steps': [
                'Select a certified repair facility',
                'An adjuster may contact you within 24 hours',
                'Repairs can proceed after brief verification'
            ]
        }
    else:
        return {
            'status': 'REVIEW REQUIRED',
            'status_color': '#f59e0b',
            'message': f'This claim of ${total_cost:,.2f} requires adjuster review due to severity.',
            'next_steps': [
                'An adjuster will be assigned within 2 hours',
                'In-person inspection may be required',
                'Estimated review completion: 24-48 hours'
            ]
        }


def estimate_repair_time(line_items):
    """Estimate total repair time in business days."""
    total_hours = sum(item['labor_hours'] for item in line_items)
    # Assume 6 productive hours per day
    days = max(1, round(total_hours / 6))
    # Add buffer for parts ordering
    if any(item['action'] == 'Replace' for item in line_items):
        days += 2
    return days
