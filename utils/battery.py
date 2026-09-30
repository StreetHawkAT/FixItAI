"""
Battery report analyzer for FixIt AI
Parses and analyzes Windows battery reports
"""

import re
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from bs4 import BeautifulSoup


class BatteryAnalyzer:
    """Analyzes Windows battery reports"""

    def __init__(self):
        self.report_data = None

    def parse_battery_report(self, file_path: str) -> Dict:
        """
        Parse Windows battery report HTML file

        Args:
            file_path: Path to battery-report.html

        Returns:
            Dictionary containing parsed battery data
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract key battery information
            data = {
                'report_date': datetime.now(),
                'design_capacity': self._extract_capacity(soup, 'DESIGN CAPACITY'),
                'full_charge_capacity': self._extract_capacity(soup, 'FULL CHARGE CAPACITY'),
                'cycle_count': self._extract_cycle_count(soup),
                'battery_health_percent': 0.0,
                'recent_usage': self._extract_recent_usage(soup),
                'battery_history': self._extract_battery_history(soup),
                'raw_html': html_content
            }

            # Calculate battery health
            if data['design_capacity'] and data['full_charge_capacity']:
                data['battery_health_percent'] = (
                    data['full_charge_capacity'] / data['design_capacity'] * 100
                )

            self.report_data = data
            return data

        except Exception as e:
            raise Exception(f"Failed to parse battery report: {str(e)}")

    def _extract_capacity(self, soup, label: str) -> Optional[int]:
        """Extract capacity value from report"""
        try:
            # Look for the label in the HTML
            text = soup.get_text()
            pattern = f"{label}\\s+(\\d+)\\s+mWh"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        except:
            pass
        return None

    def _extract_cycle_count(self, soup) -> Optional[int]:
        """Extract battery cycle count"""
        try:
            text = soup.get_text()
            pattern = r"CYCLE COUNT\\s+(\\d+)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        except:
            pass
        return None

    def _extract_recent_usage(self, soup) -> List[Dict]:
        """Extract recent battery usage data"""
        usage_data = []
        try:
            # Find tables with recent usage information
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        usage_data.append({
                            'period': cells[0].get_text(strip=True),
                            'active_time': cells[1].get_text(strip=True),
                            'drain_rate': cells[2].get_text(strip=True)
                        })
        except:
            pass
        return usage_data

    def _extract_battery_history(self, soup) -> List[Dict]:
        """Extract battery capacity history"""
        history = []
        try:
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        history.append({
                            'date': cells[0].get_text(strip=True),
                            'capacity': cells[1].get_text(strip=True)
                        })
        except:
            pass
        return history

    def analyze_battery_health(self, data: Dict) -> Dict:
        """
        Analyze battery health and provide recommendations

        Args:
            data: Parsed battery report data

        Returns:
            Analysis results with findings and recommendations
        """
        findings = []
        recommendations = []
        severity = "info"

        battery_health = data.get('battery_health_percent', 0)

        # Analyze battery health percentage
        if battery_health >= 80:
            findings.append("✓ Battery health is good ({:.1f}%)".format(battery_health))
            severity = "success"
        elif battery_health >= 60:
            findings.append("⚠ Battery health is moderate ({:.1f}%)".format(battery_health))
            recommendations.append("Consider calibrating the battery")
            recommendations.append("Monitor battery drain patterns")
            severity = "warning"
        else:
            findings.append("⚠ Battery health is poor ({:.1f}%)".format(battery_health))
            recommendations.append("Battery may need replacement soon")
            recommendations.append("Avoid deep discharges")
            recommendations.append("Keep laptop plugged in when possible")
            severity = "critical"

        # Analyze cycle count
        cycle_count = data.get('cycle_count')
        if cycle_count:
            if cycle_count < 300:
                findings.append(f"✓ Low battery cycle count: {cycle_count}")
            elif cycle_count < 500:
                findings.append(f"○ Moderate battery cycle count: {cycle_count}")
            else:
                findings.append(f"⚠ High battery cycle count: {cycle_count}")
                recommendations.append("Battery is approaching end of life")

        # Analyze recent usage patterns
        recent_usage = data.get('recent_usage', [])
        if recent_usage:
            # Check for unusual drain rates
            for usage in recent_usage[:3]:
                drain_rate_str = usage.get('drain_rate', '')
                # Extract numeric value if present
                drain_match = re.search(r'(\d+)', drain_rate_str)
                if drain_match:
                    drain_rate = int(drain_match.group(1))
                    if drain_rate > 15000:  # 15W+
                        findings.append(f"⚠ High power consumption detected: {drain_rate}mW")
                        recommendations.append("Check for resource-intensive background processes")
                        recommendations.append("Reduce screen brightness")
                        recommendations.append("Close unnecessary applications")

        return {
            'findings': findings,
            'recommendations': recommendations,
            'severity': severity,
            'summary': self._generate_summary(data, findings)
        }

    def _generate_summary(self, data: Dict, findings: List[str]) -> str:
        """Generate a human-readable summary"""
        battery_health = data.get('battery_health_percent', 0)
        design_cap = data.get('design_capacity', 0)
        current_cap = data.get('full_charge_capacity', 0)

        summary = f"Battery Health: {battery_health:.1f}% "
        summary += f"({current_cap:,} mWh / {design_cap:,} mWh design capacity)\n\n"

        if battery_health >= 80:
            summary += "Your battery is in good condition. "
        elif battery_health >= 60:
            summary += "Your battery shows moderate wear. "
        else:
            summary += "Your battery shows significant degradation. "

        return summary

    def compare_reports(self, report1: Dict, report2: Dict) -> Dict:
        """
        Compare two battery reports to track changes over time

        Args:
            report1: Earlier battery report
            report2: Later battery report

        Returns:
            Comparison analysis
        """
        comparison = {
            'health_change': 0.0,
            'capacity_change': 0,
            'findings': []
        }

        # Compare health percentages
        health1 = report1.get('battery_health_percent', 0)
        health2 = report2.get('battery_health_percent', 0)
        health_change = health2 - health1

        comparison['health_change'] = health_change

        if health_change < -5:
            comparison['findings'].append(
                f"⚠ Battery health decreased by {abs(health_change):.1f}%"
            )
        elif health_change < -2:
            comparison['findings'].append(
                f"○ Battery health slightly decreased by {abs(health_change):.1f}%"
            )
        else:
            comparison['findings'].append(
                f"✓ Battery health stable (change: {health_change:+.1f}%)"
            )

        # Compare capacities
        cap1 = report1.get('full_charge_capacity', 0)
        cap2 = report2.get('full_charge_capacity', 0)
        cap_change = cap2 - cap1

        comparison['capacity_change'] = cap_change

        if cap_change < -1000:
            comparison['findings'].append(
                f"⚠ Full charge capacity decreased by {abs(cap_change):,} mWh"
            )

        return comparison
