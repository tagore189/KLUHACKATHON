"""Report generation module for damage assessment results."""
from datetime import datetime
import json


def generate_report(detection_result, severity_assessment, cost_estimate, image_filename=None):
    """
    Generate a comprehensive damage assessment report.
    Combines detection, severity, and cost data into a final report.
    """
    report = {
        'report_id': f"VCR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'generated_at': datetime.now().isoformat(),
        'image_file': image_filename,

        'vehicle_info': {
            'type': detection_result.get('vehicle_type', 'Unknown'),
            'color': detection_result.get('vehicle_color', 'Unknown'),
            'drivable': detection_result.get('drivable', True)
        },

        'damage_assessment': {
            'summary': detection_result.get('summary', ''),
            'overall_severity': severity_assessment.get('label', 'Unknown'),
            'severity_color': severity_assessment.get('color', '#888'),
            'severity_icon': severity_assessment.get('icon', ''),
            'severity_action': severity_assessment.get('action', ''),
            'damage_count': severity_assessment.get('damage_count', 0),
            'damages': severity_assessment.get('breakdown', [])
        },

        'cost_estimate': cost_estimate['summary'],
        'line_items': cost_estimate['line_items'],
        'recommendation': cost_estimate['recommendation'],
        'estimated_repair_days': cost_estimate['estimated_repair_days'],

        'disclaimer': 'This is an AI-generated pre-approval estimate. Final costs may vary based on in-person inspection. This estimate is valid for 30 days from the date of generation.'
    }

    # Enrich each damage entry with its corresponding cost information (if available)
    try:
        line_items_by_part = {}
        for item in cost_estimate.get('line_items', []):
            key = item.get('part_key')
            if not key:
                continue
            # If multiple damages map to same part, aggregate subtotals
            existing = line_items_by_part.get(key)
            if existing:
                existing['part_cost'] += item.get('part_cost', 0)
                existing['labor_cost'] += item.get('labor_cost', 0)
                existing['paint_cost'] += item.get('paint_cost', 0)
                existing['subtotal'] += item.get('subtotal', 0)
            else:
                line_items_by_part[key] = {
                    'part_cost': item.get('part_cost', 0),
                    'labor_cost': item.get('labor_cost', 0),
                    'paint_cost': item.get('paint_cost', 0),
                    'subtotal': item.get('subtotal', 0),
                }

        damages = report['damage_assessment'].get('damages', [])
        for dmg in damages:
            part_key = dmg.get('part')
            if not part_key:
                continue
            costs = line_items_by_part.get(part_key)
            if not costs:
                continue
            # Attach aggregated costs to the damage entry
            dmg['part_cost'] = round(costs['part_cost'], 2)
            dmg['labor_cost'] = round(costs['labor_cost'], 2)
            dmg['paint_cost'] = round(costs['paint_cost'], 2)
            dmg['total_cost'] = round(costs['subtotal'], 2)
    except Exception:
        # Cost enrichment is best-effort; never break report generation
        pass

    return report


def report_to_json(report):
    """Convert report to JSON string."""
    return json.dumps(report, indent=2, default=str)
