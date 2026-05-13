"""
Hormulse AI - Main Application Entry Point

A multi-AI chat platform supporting Gemini, GPT-4, Claude, DeepSeek, and more.
"""

import os
import logging
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# ============================================
# CONFIGURATION
# ============================================

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'sqlite:///hormulse.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', True)
app.config['JSON_SORT_KEYS'] = False

# Upload Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize Database
db = SQLAlchemy(app)

# ============================================
# LOGGING SETUP
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# MODELS
# ============================================

class Chat(db.Model):
    """Chat message model"""
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            'id': self.id,
            'provider': self.provider,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'timestamp': self.timestamp.isoformat()
        }


# ============================================
# ROUTES - PAGE ROUTES
# ============================================

@app.route('/')
def index():
    """Homepage"""
    return render_template('index.html')


@app.route('/chat')
def chat():
    """Chat interface"""
    return render_template('chat.html')


# ============================================
# ROUTES - API ROUTES
# ============================================

@app.route('/api/providers', methods=['GET'])
def get_providers():
    """Get list of available AI providers"""
    providers = [
        {
            'id': 'gemini',
            'name': 'Google Gemini',
            'icon': '🌐',
            'status': 'active' if os.getenv('GEMINI_API_KEY') else 'inactive'
        },
        {
            'id': 'gpt4',
            'name': 'GPT-4',
            'icon': '🤖',
            'status': 'active' if os.getenv('OPENAI_API_KEY') else 'inactive'
        },
        {
            'id': 'claude',
            'name': 'Claude',
            'icon': '💫',
            'status': 'active' if os.getenv('CLAUDE_API_KEY') else 'inactive'
        },
        {
            'id': 'deepseek',
            'name': 'DeepSeek',
            'icon': '🔍',
            'status': 'active' if os.getenv('DEEPSEEK_API_KEY') else 'inactive'
        },
    ]
    return jsonify(providers)


@app.route('/api/chat', methods=['POST'])
def send_message():
    """Send message to selected AI provider"""
    try:
        data = request.get_json()
        provider = data.get('provider', 'gemini')
        message = data.get('message', '')

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # TODO: Implement actual AI provider communication
        response = f"Response from {provider}: {message}"

        # Save to database
        chat = Chat(
            provider=provider,
            user_message=message,
            ai_response=response
        )
        db.session.add(chat)
        db.session.commit()

        return jsonify({
            'success': True,
            'provider': provider,
            'message': message,
            'response': response,
            'id': chat.id
        })

    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_image():
    """Analyze image with AI"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        provider = request.form.get('provider', 'gemini')

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # TODO: Implement image analysis
        analysis = f"Image analysis from {provider}: [Analysis pending]"

        return jsonify({
            'success': True,
            'provider': provider,
            'filename': file.filename,
            'analysis': analysis
        })

    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get chat history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        chats = Chat.query.order_by(Chat.timestamp.desc()).limit(limit).all()
        return jsonify([chat.to_dict() for chat in chats])
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """Clear chat history"""
    try:
        Chat.query.delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'History cleared'})
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


# ============================================
# CONTEXT PROCESSORS
# ============================================

@app.context_processor
def inject_config():
    """Inject config into templates"""
    return {
        'app_name': 'Hormulse AI',
        'app_version': '1.0.0'
    }


# ============================================
# MAIN APPLICATION ENTRY POINT
# ============================================

if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("Database initialized")

    # Run the application
    host = os.getenv('HOST', 'localhost')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', True)

    logger.info(f"Starting Hormulse AI on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
