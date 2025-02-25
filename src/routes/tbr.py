from flask import Blueprint, render_template, request, jsonify

tbr = Blueprint('tbr', __name__)

@tbr.route('/')
@tbr.route('/manager')
def manager():
    """Render the TBR manager page"""
    return render_template('tbr/tbr_manager.html')

@tbr.route('/api/reorder_chain', methods=['POST'])
def reorder_chain():
    """Handle chain reordering"""
    try:
        data = request.get_json()
        reading_id = data.get('reading_id')
        chain_type = data.get('chain_type')
        target_id = data.get('target_id')

        # TODO: Implement your database logic here
        # For now, just return success to test the frontend
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tbr.route('/api/chains', methods=['GET'])
def get_chains():
    """Get all reading chains"""
    try:
        # TODO: Replace this with actual database queries
        # For now, return dummy data for testing
        chains = [
            {
                'media': 'kindle',
                'books': [
                    {
                        'id': '1',
                        'title': 'The Hobbit',
                        'author': 'J.R.R. Tolkien',
                        'progress': 75,
                        'current': True,
                        'date_started': '2025-02-01'
                    }
                ]
            },
            {
                'media': 'hardcover',
                'books': [
                    {
                        'id': '2',
                        'title': 'Dune',
                        'author': 'Frank Herbert',
                        'progress': 30,
                        'current': False,
                        'date_started': '2025-02-15'
                    }
                ]
            },
            {
                'media': 'audio',
                'books': [
                    {
                        'id': '3',
                        'title': 'Project Hail Mary',
                        'author': 'Andy Weir',
                        'progress': 50,
                        'current': False,
                        'date_started': '2025-02-10'
                    }
                ]
            }
        ]
        return jsonify({'chains': chains})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
