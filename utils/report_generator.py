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

    return report


def report_to_json(report):
    """Convert report to JSON string."""
    return json.dumps(report, indent=2, default=str)
