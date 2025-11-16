"""
Survey template definitions and insertion utilities.

This module contains all default survey templates provided to new customers
during deployment. Templates can be easily added, modified, or removed without
touching the deployment logic.

Usage:
    from utils.survey_templates import insert_all_default_templates
    insert_all_default_templates(db_path)

Adding new templates:
    1. Define a new template constant (e.g., SURVEY_EVENT_FEEDBACK_EN)
    2. Add it to the DEFAULT_TEMPLATES list
    3. All future deployments will include the new template
"""

import json
import sqlite3
from datetime import datetime, timezone
from utils.logging_config import log_operation_start, log_operation_end, log_validation_check
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# TEMPLATE DEFINITIONS
# ============================================================================

# Template 1: Simple Activity Survey (French, 8 questions)
# Used for collecting feedback after activities (golf tournaments, sports events, etc.)
# Estimated completion time: ~2 minutes
SURVEY_ACTIVITY_SIMPLE_FR = {
    "name": "Sondage d'Activité - Simple (questions)",
    "description": "Sondage simple en français pour recueillir les retours après une activité ponctuelle (tournoi de golf, événement sportif, etc.). Temps de réponse: ~2 minutes.",
    "status": "active",
    "questions": {
        "questions": [
            {
                "id": 1,
                "question": "Comment évaluez-vous votre satisfaction globale concernant cette activité?",
                "type": "rating",
                "required": True,
                "min_rating": 1,
                "max_rating": 5,
                "labels": {
                    "1": "Très insatisfait",
                    "2": "Insatisfait",
                    "3": "Neutre",
                    "4": "Satisfait",
                    "5": "Très satisfait"
                }
            },
            {
                "id": 2,
                "question": "Le prix demandé pour cette activité est-il justifié?",
                "type": "multiple_choice",
                "required": True,
                "options": [
                    "Trop cher",
                    "Un peu cher",
                    "Juste",
                    "Bon rapport qualité-prix",
                    "Excellent rapport qualité-prix"
                ]
            },
            {
                "id": 3,
                "question": "Recommanderiez-vous cette activité à un ami?",
                "type": "multiple_choice",
                "required": True,
                "options": [
                    "Certainement",
                    "Probablement",
                    "Peut-être",
                    "Probablement pas",
                    "Certainement pas"
                ]
            },
            {
                "id": 4,
                "question": "Comment évaluez-vous l'emplacement/les installations?",
                "type": "multiple_choice",
                "required": False,
                "options": [
                    "Excellent",
                    "Très bien",
                    "Bien",
                    "Moyen",
                    "Insuffisant"
                ]
            },
            {
                "id": 5,
                "question": "L'horaire de l'activité vous convenait-il?",
                "type": "multiple_choice",
                "required": False,
                "options": [
                    "Parfaitement",
                    "Bien",
                    "Acceptable",
                    "Peu pratique",
                    "Très peu pratique"
                ]
            },
            {
                "id": 6,
                "question": "Qu'avez-vous le plus apprécié de cette activité?",
                "type": "open_ended",
                "required": False,
                "max_length": 300
            },
            {
                "id": 7,
                "question": "Qu'est-ce qui pourrait être amélioré?",
                "type": "open_ended",
                "required": False,
                "max_length": 300
            },
            {
                "id": 8,
                "question": "Souhaiteriez-vous participer à nouveau à une activité similaire?",
                "type": "multiple_choice",
                "required": True,
                "options": [
                    "Oui, certainement",
                    "Oui, probablement",
                    "Peut-être",
                    "Probablement pas",
                    "Non"
                ]
            }
        ]
    }
}

# ============================================================================
# Future templates can be added here
# Examples:
#
# SURVEY_EVENT_FEEDBACK_FR = {
#     "name": "Sondage Post-Événement",
#     "description": "...",
#     "status": "active",
#     "questions": {...}
# }
#
# SURVEY_MEMBERSHIP_SATISFACTION_EN = {
#     "name": "Membership Satisfaction Survey",
#     "description": "...",
#     "status": "active",
#     "questions": {...}
# }
# ============================================================================

# List of templates to insert by default into new customer databases
DEFAULT_TEMPLATES = [
    SURVEY_ACTIVITY_SIMPLE_FR,
    # Add more templates here as needed
]


# ============================================================================
# INSERTION FUNCTIONS
# ============================================================================

def insert_survey_template(db_path, template_data, created_by=1):
    """
    Insert a single survey template into the customer database.

    Args:
        db_path (str): Path to the customer's SQLite database file
        template_data (dict): Survey template data with keys:
            - name (str): Template name
            - description (str): Template description
            - status (str): 'active' or 'archived'
            - questions (dict): Questions structure with nested question list
        created_by (int): Admin user ID (default: 1)

    Returns:
        int: The ID of the inserted template, or None on failure

    Raises:
        Exception: If database operations fail
    """
    log_operation_start(
        logger,
        "Insert Survey Template",
        db_path=db_path,
        template_name=template_data.get('name')
    )

    try:
        # Convert questions dict to JSON string (preserve French accents)
        questions_json = json.dumps(template_data['questions'], ensure_ascii=False)

        # Connect to database
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Defensive check: verify table exists
        cur.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='survey_template'
        """)

        if not cur.fetchone():
            error_msg = "survey_template table does not exist in database"
            logger.warning(f"⚠️ {error_msg}")
            log_validation_check(logger, "Table exists", False, error_msg)
            conn.close()
            log_operation_end(logger, "Insert Survey Template", success=False, error_msg=error_msg)
            return None

        log_validation_check(logger, "survey_template table exists", True, "Table found")

        # Insert template
        cur.execute("""
            INSERT INTO survey_template (name, description, questions, created_by, created_dt, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            template_data['name'],
            template_data['description'],
            questions_json,
            created_by,
            datetime.now(timezone.utc).isoformat(),
            template_data['status']
        ))

        template_id = cur.lastrowid

        # Commit changes
        conn.commit()
        conn.close()

        # Log success
        log_validation_check(
            logger,
            "Survey template inserted",
            True,
            f"Template ID: {template_id}, Name: '{template_data['name']}'"
        )
        log_operation_end(logger, "Insert Survey Template", success=True)

        return template_id

    except Exception as e:
        error_msg = f"Failed to insert survey template: {str(e)}"
        logger.error(f"❌ {error_msg}")
        log_operation_end(logger, "Insert Survey Template", success=False, error_msg=error_msg)
        raise


def insert_all_default_templates(db_path):
    """
    Insert all default survey templates into a new customer database.

    This function is called during customer deployment to provide pre-built
    survey templates that customers can use immediately.

    Args:
        db_path (str): Path to the customer's SQLite database file

    Returns:
        int: Number of templates successfully inserted

    Raises:
        Exception: If any template insertion fails
    """
    log_operation_start(
        logger,
        "Insert All Default Survey Templates",
        db_path=db_path,
        template_count=len(DEFAULT_TEMPLATES)
    )

    inserted_count = 0
    inserted_names = []

    try:
        for template in DEFAULT_TEMPLATES:
            template_id = insert_survey_template(db_path, template)
            if template_id:
                inserted_count += 1
                inserted_names.append(template['name'])
                logger.info(f"✅ Inserted template: '{template['name']}' (ID: {template_id})")
            else:
                logger.warning(f"⚠️ Failed to insert template: '{template['name']}'")

        # Final validation
        success = inserted_count == len(DEFAULT_TEMPLATES)
        log_validation_check(
            logger,
            "All templates inserted",
            success,
            f"{inserted_count}/{len(DEFAULT_TEMPLATES)} templates successfully added: {', '.join(inserted_names)}"
        )

        log_operation_end(
            logger,
            "Insert All Default Survey Templates",
            success=success
        )

        return inserted_count

    except Exception as e:
        error_msg = f"Error during template insertion: {str(e)}"
        logger.error(f"❌ {error_msg}")
        log_operation_end(
            logger,
            "Insert All Default Survey Templates",
            success=False,
            error_msg=error_msg
        )
        raise
