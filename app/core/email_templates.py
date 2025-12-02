import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)

# Get the base directory (agent-app)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "app" / "templates" / "emails"

# Initialize Jinja2 environment
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True
)

def get_email_template(template_name: str, **kwargs) -> str:
    """
    Load and render an email template with the provided variables.
    
    Args:
        template_name: Name of the template file (e.g., 'welcome.html')
        **kwargs: Variables to pass to the template
    
    Returns:
        Rendered HTML string
    
    Raises:
        TemplateNotFound: If the template file doesn't exist
    """
    try:
        template = env.get_template(template_name)
        return template.render(**kwargs)
    except TemplateNotFound:
        logger.error(f"Email template '{template_name}' not found in {TEMPLATES_DIR}")
        raise
    except Exception as e:
        logger.error(f"Error rendering email template '{template_name}': {e}", exc_info=True)
        raise

