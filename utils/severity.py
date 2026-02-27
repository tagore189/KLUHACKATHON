"""Severity assessment module for damage classification."""


SEVERITY_LEVELS = {
    'minor': {
        'label': 'Minor',
        'description': 'Cosmetic damage, no structural impact',
        'color': '#22c55e',
        'icon': '🟢',
        'action': 'Repair recommended within 30 days'
    },
    'moderate': {
        'label': 'Moderate',
        'description': 'Significant damage requiring professional repair',
        'color': '#f59e0b',
        'icon': '🟡',
        'action': 'Repair recommended within 7 days'
    },
    'severe': {
        'label': 'Severe',
        'description': 'Major structural damage, may affect safety',
        'color': '#ef4444',
        'icon': '🔴',
        'action': 'Immediate professional assessment required'
    }
}


def assess_severity(damages):
    """
    Assess overall severity based on individual damage items.
    Returns severity level and detailed breakdown.
    """
    if not damages:
        return {
            'overall': 'none',
            'label': 'No Damage',
            'description': 'No visible damage detected',
            'color': '#22c55e',
            'score': 0,
            'breakdown': []
        }

    severity_scores = {'minor': 1, 'moderate': 2, 'severe': 3}
    total_score = 0
    breakdown = []

    for damage in damages:
        severity = damage.get('severity', 'minor')
        score = severity_scores.get(severity, 1)
        total_score += score

        severity_info = SEVERITY_LEVELS.get(severity, SEVERITY_LEVELS['minor'])
        breakdown.append({
            'part': damage.get('part', 'unknown'),
            'damage_type': damage.get('damage_type', 'unknown'),
            'severity': severity,
            'severity_label': severity_info['label'],
            'color': severity_info['color'],
            'icon': severity_info['icon'],
            'confidence': damage.get('confidence', 0),
            'description': damage.get('description', '')
        })

    # Calculate average severity
    avg_score = total_score / len(damages)

    if avg_score <= 1.3:
        overall = 'minor'
    elif avg_score <= 2.3:
        overall = 'moderate'
    else:
        overall = 'severe'

    # Upgrade if any single damage is severe
    if any(d.get('severity') == 'severe' for d in damages):
        if overall == 'minor':
            overall = 'moderate'

    severity_info = SEVERITY_LEVELS[overall]

    return {
        'overall': overall,
        'label': severity_info['label'],
        'description': severity_info['description'],
        'color': severity_info['color'],
        'icon': severity_info['icon'],
        'action': severity_info['action'],
        'score': round(avg_score, 2),
        'damage_count': len(damages),
        'breakdown': breakdown
    }
