from flask import Blueprint, render_template, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from ..models.book import Book
from ..models.reading import Reading
from ..models.inventory import Inventory
from ..core.database import db

# Create blueprint with a URL prefix
bp = Blueprint('web', __name__, url_prefix='')

@bp.route('/')
def index():
    """Main page"""
    return render_template('entry_editor/index.html')

@bp.route('/entry-editor')
def entry_editor():
    """Entry editor page"""
    return render_template('entry_editor/index.html')

@bp.route('/api/entries/<table>', methods=['GET'])
def get_entries(table):
    """Get entries for a specific table"""
    try:
        search = request.args.get('search', '')
        
        model_map = {
            'books': Book,
            'read': Reading,
            'inv': Inventory
        }
        
        model = model_map.get(table)
        if not model:
            return jsonify({
                'error': 'Invalid table',
                'debug': {
                    'requested_table': table,
                    'available_tables': list(model_map.keys())
                }
            }), 400
        
        query = model.query
        
        if search:
            if hasattr(model, 'title'):
                query = query.filter(model.title.ilike(f'%{search}%'))
            elif hasattr(model, 'id'):
                try:
                    query = query.filter(model.id == int(search))
                except ValueError:
                    pass
        
        entries = query.limit(100).all()
        
        return jsonify({
            'status': 'success',
            'entries': [entry.to_dict() for entry in entries],
            'debug': {
                'table': table,
                'search': search,
                'entry_count': len(entries),
                'route': request.path,
                'method': request.method
            }
        })

    except SQLAlchemyError as e:
        return jsonify({
            'error': 'Database error',
            'debug': {
                'error_type': str(type(e).__name__),
                'error_message': str(e)
            }
        }), 500
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'debug': {
                'error_type': str(type(e).__name__),
                'error_message': str(e)
            }
        }), 500

@bp.route('/api/entries/<table>/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def manage_entry(table, id):
    """Manage individual entries"""
    model_map = {
        'books': Book,
        'read': Reading,
        'inv': Inventory
    }
    
    model = model_map.get(table)
    if not model:
        return jsonify({'error': 'Invalid table'}), 400

    entry = db.session.get(model, id)
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404

    if request.method == 'GET':
        return jsonify(entry.to_dict())
    
    elif request.method == 'PUT':
        data = request.json
        for key, value in data.items():
            setattr(entry, key, value)
        db.session.commit()
        return jsonify(entry.to_dict())
    
    elif request.method == 'DELETE':
        db.session.delete(entry)
        db.session.commit()
        return jsonify({'status': 'success'})