"""Main JIRA Activity Agent."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from jira_agent.activity_tracker import ActivityTracker
from jira_agent.models import StoryActivity, ActivityReport

logger = logging.getLogger(__name__)


class JIRAActivityAgent:
    """Main agent for JIRA activity tracking and analysis."""

    def __init__(self):
        """Initialize the JIRA Activity Agent."""
        self.tracker = ActivityTracker()
        logger.info("JIRA Activity Agent initialized")

    def get_story_activity(self, story_key: str) -> Optional[Dict]:
        """Get activity for a specific story."""
        activity = self.tracker.get_story_activity(story_key)
        return activity.to_dict() if activity else None

    def get_all_stories_with_activity(self) -> List[Dict]:
        """Get all stories with their activity information."""
        stories = self.tracker.get_all_stories_with_activity()
        return [s.to_dict() for s in stories]

    def get_story_contributors(self, story_key: str) -> Optional[List[str]]:
        """Get list of contributors for a story."""
        activity = self.tracker.get_story_activity(story_key)
        return activity.contributors if activity else None

    def get_phase_transitions(self, story_key: str) -> Optional[List[Dict]]:
        """Get phase transitions for a story."""
        activity = self.tracker.get_story_activity(story_key)
        if activity:
            return [t.to_dict() for t in activity.phase_transitions]
        return None

    def get_project_contributors_summary(self, project_key: str) -> Dict:
        """Get contributor summary for entire project."""
        return self.tracker.get_project_contributors_summary(project_key)

    def generate_activity_report(
        self,
        project_key: str,
        days: int = 7,
        include_details: bool = False,
    ) -> Dict:
        """Generate activity report for a project."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        report = self.tracker.generate_activity_report(
            project_key=project_key,
            start_date=start_date,
            end_date=end_date,
        )

        return report.to_dict()

    def export_report_to_csv(self, report: Dict, filename: str) -> bool:
        """Export activity report to CSV."""
        try:
            import csv
            
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow(["JIRA Activity Report"])
                writer.writerow(["Generated", report["generated_at"]])
                writer.writerow(["Project", report["project_key"]])
                writer.writerow(["Period", f"{report['period_start']} to {report['period_end']}"])
                writer.writerow([])
                
                # Summary
                writer.writerow(["Summary"])
                writer.writerow(["Total Stories", report["total_stories"]])
                writer.writerow(["Total Activities", report["total_activities"]])
                writer.writerow([])
                
                # Stories by phase
                writer.writerow(["Stories by Phase"])
                for phase, count in report["stories_by_phase"].items():
                    writer.writerow([phase, count])
                writer.writerow([])
                
                # Top contributors
                writer.writerow(["Top Contributors"])
                for user, count in report["top_contributors"]:
                    writer.writerow([user, count])
                writer.writerow([])
                
                # Phase times
                writer.writerow(["Average Phase Completion Times (days)"])
                for phase, days_avg in report["phase_completion_times"].items():
                    writer.writerow([phase, f"{days_avg:.1f}"])
                writer.writerow([])
                
                # Insights
                writer.writerow(["Insights"])
                for insight in report["insights"]:
                    writer.writerow([insight])
            
            logger.info(f"Report exported to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return False
