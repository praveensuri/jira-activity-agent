"""Flask application server for JIRA Activity Agent."""
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from jira_agent.core import JIRAActivityAgent

# Configure logging
logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize agent
agent = JIRAActivityAgent()


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route("/api/stories", methods=["GET"])
def get_stories():
    """Get all stories with activity information."""
    try:
        stories = agent.get_all_stories_with_activity()
        return jsonify({
            "success": True,
            "count": len(stories),
            "data": stories,
        })
    except Exception as e:
        logger.error(f"Error fetching stories: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/stories/<story_key>", methods=["GET"])
def get_story(story_key):
    """Get activity for a specific story."""
    try:
        activity = agent.get_story_activity(story_key)
        if not activity:
            return jsonify({"success": False, "error": "Story not found"}), 404
        return jsonify({"success": True, "data": activity})
    except Exception as e:
        logger.error(f"Error fetching story {story_key}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/stories/<story_key>/activity", methods=["GET"])
def get_story_activity(story_key):
    """Get detailed activity for a specific story."""
    try:
        activity = agent.get_story_activity(story_key)
        if not activity:
            return jsonify({"success": False, "error": "Story not found"}), 404
        return jsonify({"success": True, "data": activity})
    except Exception as e:
        logger.error(f"Error fetching activity for {story_key}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/stories/<story_key>/transitions", methods=["GET"])
def get_transitions(story_key):
    """Get phase transitions for a story."""
    try:
        transitions = agent.get_phase_transitions(story_key)
        if transitions is None:
            return jsonify({"success": False, "error": "Story not found"}), 404
        return jsonify({"success": True, "data": transitions})
    except Exception as e:
        logger.error(f"Error fetching transitions for {story_key}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/stories/<story_key>/contributors", methods=["GET"])
def get_contributors(story_key):
    """Get contributors for a story."""
    try:
        contributors = agent.get_story_contributors(story_key)
        if contributors is None:
            return jsonify({"success": False, "error": "Story not found"}), 404
        return jsonify({"success": True, "data": contributors})
    except Exception as e:
        logger.error(f"Error fetching contributors for {story_key}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reports/activity", methods=["GET"])
def generate_report():
    """Generate activity report."""
    try:
        days = request.args.get("days", default=7, type=int)
        project_key = request.args.get("project", default=Config.JIRA_PROJECT_KEY, type=str)
        
        report = agent.generate_activity_report(
            project_key=project_key,
            days=days,
        )
        
        return jsonify({"success": True, "data": report})
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Analyze story activity with AI insights."""
    try:
        data = request.json
        story_key = data.get("story_key")
        
        if not story_key:
            return jsonify({"success": False, "error": "story_key is required"}), 400
        
        activity = agent.get_story_activity(story_key)
        
        if not activity:
            return jsonify({"success": False, "error": "Story not found"}), 404
        
        # Basic analysis
        analysis = {
            "story_key": story_key,
            "current_phase": activity["current_phase"],
            "total_activities": len(activity["activities"]),
            "unique_contributors": len(activity["contributors"]),
            "velocity_score": activity["velocity_score"],
            "phase_count": len(activity["phase_transitions"]),
            "insights": _generate_insights(activity),
        }
        
        return jsonify({"success": True, "data": analysis})
    except Exception as e:
        logger.error(f"Error analyzing story: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def _generate_insights(activity: dict) -> list:
    """Generate insights from activity data."""
    insights = []
    
    # Velocity insight
    if activity["velocity_score"] > 50:
        insights.append("High activity velocity on this story")
    elif activity["velocity_score"] < 20:
        insights.append("Low activity velocity - may need attention")
    
    # Contributor insight
    if activity["unique_contributors"] == 1:
        insights.append("Single contributor - consider collaboration")
    elif activity["unique_contributors"] > 5:
        insights.append("High collaboration - many contributors involved")
    
    # Phase insight
    if len(activity["phase_transitions"]) > 3:
        insights.append("Multiple phase transitions - possible blockers or rework")
    
    return insights


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info(f"Starting JIRA Activity Agent on port {Config.FLASK_PORT}")
    app.run(
        host="0.0.0.0",
        port=Config.FLASK_PORT,
        debug=Config.DEBUG,
    )
