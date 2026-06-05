"""Activity tracking and analysis for JIRA stories."""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from jira_agent.jira_connector import JIRAConnector
from jira_agent.models import (
    UserActivity,
    PhaseTransition,
    StoryActivity,
    ActivityReport,
    IssuePhase,
)

logger = logging.getLogger(__name__)


class ActivityTracker:
    """Tracks and analyzes user activity for JIRA stories."""

    def __init__(self):
        """Initialize activity tracker."""
        self.connector = JIRAConnector()
        self.phase_order = [IssuePhase.BACKLOG, IssuePhase.IN_PROGRESS, IssuePhase.IN_REVIEW, IssuePhase.DONE]

    def get_story_activity(self, story_key: str) -> Optional[StoryActivity]:
        """Get complete activity information for a story."""
        try:
            story_details = self.connector.get_story_details(story_key)
            if not story_details:
                return None

            changelog = self.connector.get_story_changelog(story_key)
            comments = self.connector.get_story_comments(story_key)
            worklogs = self.connector.get_story_worklogs(story_key)

            # Extract activities
            activities = self._extract_activities(story_key, changelog, comments, worklogs)

            # Extract phase transitions
            phase_transitions = self._extract_phase_transitions(story_key, changelog)

            # Get contributors
            contributors = list(set(
                [a.user for a in activities] +
                [pt.user for pt in phase_transitions]
            ))

            # Calculate velocity score
            velocity_score = self._calculate_velocity_score(activities, phase_transitions)

            return StoryActivity(
                story_key=story_key,
                story_title=story_details["summary"],
                current_phase=story_details["status"],
                created_at=datetime.fromisoformat(story_details["created"].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(story_details["updated"].replace('Z', '+00:00')),
                activities=activities,
                phase_transitions=phase_transitions,
                contributors=contributors,
                velocity_score=velocity_score,
            )
        except Exception as e:
            logger.error(f"Error getting activity for {story_key}: {e}")
            return None

    def _extract_activities(self, story_key: str, changelog: List, comments: List, worklogs: List) -> List[UserActivity]:
        """Extract all user activities from various sources."""
        activities = []

        # Add changelog activities
        for entry in changelog:
            activities.append(UserActivity(
                user=entry["author"],
                action=f"Modified {entry['field']}",
                timestamp=datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00')),
                details={
                    "field": entry["field"],
                    "from": entry["from_value"],
                    "to": entry["to_value"],
                },
            ))

        # Add comments
        for comment in comments:
            activities.append(UserActivity(
                user=comment["author"],
                action="Commented",
                timestamp=datetime.fromisoformat(comment["timestamp"].replace('Z', '+00:00')),
                details={"comment_length": len(comment["body"])},
            ))

        # Add worklogs
        for worklog in worklogs:
            activities.append(UserActivity(
                user=worklog["author"],
                action="Logged time",
                timestamp=datetime.fromisoformat(worklog["timestamp"].replace('Z', '+00:00')),
                details={"time_spent": worklog["time_spent"]},
            ))

        # Sort by timestamp
        activities.sort(key=lambda x: x.timestamp)
        return activities

    def _extract_phase_transitions(self, story_key: str, changelog: List) -> List[PhaseTransition]:
        """Extract phase transitions from changelog."""
        transitions = []
        status_changes = [entry for entry in changelog if entry["field"] == "status"]

        for i, change in enumerate(status_changes):
            from_phase = change["from_value"] or "Start"
            to_phase = change["to_value"]
            timestamp = datetime.fromisoformat(change["timestamp"].replace('Z', '+00:00'))

            # Calculate duration in phase (from this transition to the next)
            duration = None
            if i < len(status_changes) - 1:
                next_timestamp = datetime.fromisoformat(
                    status_changes[i + 1]["timestamp"].replace('Z', '+00:00')
                )
                duration = (next_timestamp - timestamp).days

            transitions.append(PhaseTransition(
                from_phase=from_phase,
                to_phase=to_phase,
                timestamp=timestamp,
                user=change["author"],
                duration_in_phase=duration,
            ))

        return transitions

    def _calculate_velocity_score(self, activities: List[UserActivity], transitions: List[PhaseTransition]) -> float:
        """Calculate velocity score based on activity and transitions."""
        score = 0.0
        score += len(activities) * 0.5  # Activity count
        score += len(transitions) * 1.0  # Transitions
        return min(score, 100.0)  # Cap at 100

    def get_all_stories_with_activity(self) -> List[StoryActivity]:
        """Get all stories with their activity information."""
        stories_data = self.connector.get_all_stories()
        stories_activity = []

        for story in stories_data:
            activity = self.get_story_activity(story["key"])
            if activity:
                stories_activity.append(activity)

        return stories_activity

    def get_project_contributors_summary(self, project_key: str) -> Dict[str, Dict[str, int]]:
        """Get summary of contributions by user for all stories."""
        stories = self.connector.get_all_stories()
        contributors_summary = defaultdict(lambda: defaultdict(int))

        for story in stories:
            activity = self.get_story_activity(story["key"])
            if activity:
                for contrib in activity.contributors:
                    activity_count = len([a for a in activity.activities if a.user == contrib])
                    contributors_summary[story["key"]][contrib] = activity_count

        return dict(contributors_summary)

    def generate_activity_report(
        self,
        project_key: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> ActivityReport:
        """Generate comprehensive activity report for a project."""
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)

        stories = self.get_all_stories_with_activity()

        # Filter by date range
        filtered_stories = [
            s for s in stories
            if start_date <= s.updated_at <= end_date
        ]

        # Calculate metrics
        stories_by_phase = Counter([s.current_phase for s in filtered_stories])
        total_activities = sum(len(s.activities) for s in filtered_stories)
        
        # Top contributors
        all_contributors = Counter()
        for story in filtered_stories:
            for activity in story.activities:
                all_contributors[activity.user] += 1
        top_contributors = all_contributors.most_common(10)

        # Phase completion times
        phase_times = defaultdict(list)
        for story in filtered_stories:
            for transition in story.phase_transitions:
                if transition.duration_in_phase:
                    phase_times[transition.to_phase].append(transition.duration_in_phase)
        
        phase_completion_times = {
            phase: sum(times) / len(times)
            for phase, times in phase_times.items()
            if times
        }

        # Generate insights
        insights = self._generate_insights(filtered_stories, phase_completion_times)

        return ActivityReport(
            project_key=project_key,
            generated_at=datetime.now(),
            period_start=start_date,
            period_end=end_date,
            total_stories=len(filtered_stories),
            total_activities=total_activities,
            stories_by_phase=dict(stories_by_phase),
            top_contributors=top_contributors,
            phase_completion_times=phase_completion_times,
            insights=insights,
        )

    def _generate_insights(self, stories: List[StoryActivity], phase_times: Dict[str, float]) -> List[str]:
        """Generate insights from activity data."""
        insights = []

        if not stories:
            insights.append("No stories found in the specified period.")
            return insights

        # Activity insights
        avg_velocity = sum(s.velocity_score for s in stories) / len(stories)
        insights.append(f"Average story velocity: {avg_velocity:.1f}")

        # Phase insights
        for phase, days in sorted(phase_times.items(), key=lambda x: x[1], reverse=True):
            insights.append(f"Average time in {phase}: {days:.1f} days")

        # Contributor insights
        all_users = set()
        for story in stories:
            all_users.update(story.contributors)
        insights.append(f"Total unique contributors: {len(all_users)}")

        return insights
