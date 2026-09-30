"""
Windows Event Log analyzer for FixIt AI
Analyzes system logs and identifies issues
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import Counter


class LogAnalyzer:
    """Analyzes Windows Event Logs"""

    # Common critical event IDs
    CRITICAL_EVENTS = {
        41: "Kernel-Power - System rebooted without cleanly shutting down",
        1074: "System has been shutdown by a process/user",
        6008: "Unexpected shutdown",
        4101: "Display driver stopped responding and has recovered",
        10016: "DCOM permission issue",
        1001: "Windows Error Reporting - Application crash",
        1000: "Application Error"
    }

    WARNING_EVENTS = {
        10010: "DCOM timeout",
        1014: "Name resolution timeout",
        1500: "Group Policy warning"
    }

    def __init__(self):
        self.events = []

    def parse_event_log_text(self, log_text: str) -> List[Dict]:
        """
        Parse Windows event log exported as text

        Args:
            log_text: Event log content as text

        Returns:
            List of parsed events
        """
        events = []

        # Split by event entries
        # This is a simplified parser - real implementation would need proper parsing
        lines = log_text.split('\n')

        current_event = {}
        for line in lines:
            line = line.strip()

            # Extract event ID
            if 'Event ID:' in line or 'EventID:' in line:
                match = re.search(r'(\d+)', line)
                if match:
                    current_event['event_id'] = int(match.group(1))

            # Extract level
            if 'Level:' in line:
                if 'Error' in line or 'Critical' in line:
                    current_event['level'] = 'Error'
                elif 'Warning' in line:
                    current_event['level'] = 'Warning'
                else:
                    current_event['level'] = 'Information'

            # Extract source
            if 'Source:' in line:
                source = line.split('Source:')[-1].strip()
                current_event['source'] = source

            # Extract timestamp
            if 'Date:' in line or 'Time Generated:' in line:
                # Try to parse datetime
                date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
                if date_match:
                    current_event['timestamp'] = date_match.group(1)

            # If we have enough data, save event
            if current_event.get('event_id') and current_event.get('level'):
                if current_event not in events:
                    events.append(current_event.copy())
                    current_event = {}

        self.events = events
        return events

    def analyze_events(self, events: List[Dict]) -> Dict:
        """
        Analyze event log entries and identify issues

        Args:
            events: List of parsed events

        Returns:
            Analysis results with findings
        """
        findings = []
        recommendations = []
        severity = "info"

        if not events:
            return {
                'findings': ["No events to analyze"],
                'recommendations': [],
                'severity': 'info',
                'summary': "No event log data available"
            }

        # Count event types
        error_count = sum(1 for e in events if e.get('level') == 'Error')
        warning_count = sum(1 for e in events if e.get('level') == 'Warning')

        # Analyze critical events
        critical_events = [e for e in events if e.get('event_id') in self.CRITICAL_EVENTS]

        if critical_events:
            severity = "warning"
            event_counter = Counter([e.get('event_id') for e in critical_events])

            for event_id, count in event_counter.most_common(5):
                description = self.CRITICAL_EVENTS.get(event_id, "Unknown event")
                findings.append(f"⚠ Event {event_id}: {description} ({count} occurrences)")

                # Add specific recommendations
                if event_id == 41:
                    recommendations.append("Check power settings and battery health")
                    recommendations.append("Verify system temperature and cooling")
                    recommendations.append("Update device drivers")
                    severity = "critical"

                elif event_id == 6008:
                    recommendations.append("Investigate unexpected shutdowns")
                    recommendations.append("Check Windows Reliability Monitor")
                    severity = "critical"

                elif event_id in [1000, 1001]:
                    recommendations.append("Identify crashing applications")
                    recommendations.append("Update or reinstall problematic software")

                elif event_id == 4101:
                    recommendations.append("Update graphics drivers")
                    recommendations.append("Check GPU temperature")

        # Check for patterns
        if error_count > 10:
            findings.append(f"⚠ High number of errors detected: {error_count}")
            severity = "warning"

        if warning_count > 20:
            findings.append(f"○ Many warnings detected: {warning_count}")

        # Source analysis
        sources = Counter([e.get('source', 'Unknown') for e in events if e.get('level') == 'Error'])
        if sources:
            top_source = sources.most_common(1)[0]
            findings.append(f"Most common error source: {top_source[0]} ({top_source[1]} errors)")

        summary = self._generate_summary(events, error_count, warning_count, critical_events)

        return {
            'findings': findings,
            'recommendations': recommendations,
            'severity': severity,
            'summary': summary,
            'stats': {
                'total_events': len(events),
                'errors': error_count,
                'warnings': warning_count,
                'critical_events': len(critical_events)
            }
        }

    def _generate_summary(self, events: List[Dict], error_count: int,
                         warning_count: int, critical_events: List[Dict]) -> str:
        """Generate summary of event log analysis"""
        summary = f"Analyzed {len(events)} events:\n"
        summary += f"- {error_count} errors\n"
        summary += f"- {warning_count} warnings\n"

        if critical_events:
            summary += f"\n{len(critical_events)} critical events detected that require attention."
        else:
            summary += "\nNo critical system events detected."

        return summary

    def get_shutdown_events(self, events: List[Dict]) -> List[Dict]:
        """Extract shutdown-related events"""
        shutdown_event_ids = [41, 1074, 6008]
        return [e for e in events if e.get('event_id') in shutdown_event_ids]

    def get_crash_events(self, events: List[Dict]) -> List[Dict]:
        """Extract application crash events"""
        crash_event_ids = [1000, 1001]
        return [e for e in events if e.get('event_id') in crash_event_ids]
