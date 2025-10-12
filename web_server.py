from flask import Flask, jsonify, render_template, request
import logging

logger = logging.getLogger(__name__)

def create_app(production_stats):
    """Create and configure Flask application for production monitoring"""
    app = Flask(__name__)
    
    @app.route('/')
    def dashboard():
        """Main production dashboard page"""
        return render_template('production_dashboard.html')
    
    @app.route('/api/production/summary')
    def get_production_summary():
        """Get comprehensive production summary"""
        try:
            summary = production_stats.get_production_summary()
            return jsonify(summary)
        except Exception as e:
            logger.error(f"Error getting production summary: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/production/rates')
    def get_production_rates():
        """Get current production rates"""
        try:
            rates = production_stats.get_production_rates()
            return jsonify(rates)
        except Exception as e:
            logger.error(f"Error getting production rates: {e}")
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/production/current-basket')
    def get_current_basket():
        """Get current basket statistics"""
        try:
            basket_stats = production_stats.get_current_basket_stats()
            return jsonify(basket_stats)
        except Exception as e:
            logger.error(f"Error getting current basket stats: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/production/reset', methods=['POST'])
    def reset_production_stats():
        """Reset all production statistics"""
        try:
            production_stats.reset_stats()
            logger.info("Production statistics reset via API")
            return jsonify({'message': 'Production statistics reset successfully'})
        except Exception as e:
            logger.error(f"Error resetting production stats: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Legacy endpoints for backward compatibility
    @app.route('/api/stats')
    def get_all_stats():
        """Legacy endpoint - redirects to production summary"""
        return get_production_summary()
    
    @app.route('/api/summary')
    def get_summary():
        """Legacy endpoint - redirects to production summary"""
        return get_production_summary()
    
    @app.route('/api/reset', methods=['POST'])
    def reset_stats():
        """Legacy endpoint - redirects to production reset"""
        return reset_production_stats()
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'stats_splitter_python'
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app