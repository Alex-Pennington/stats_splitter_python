from flask import Flask, jsonify, render_template, request, send_from_directory
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
    
    @app.route('/api/production/complete-basket', methods=['POST'])
    def complete_basket():
        """Complete the current basket (simulates operator basket exchange signal)"""
        try:
            production_stats.handle_basket_exchange()
            logger.info("Basket completion triggered via web dashboard")
            return jsonify({'message': 'Basket completed successfully'})
        except Exception as e:
            logger.error(f"Error completing basket: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/production/start-break', methods=['POST'])
    def start_break():
        """Start an operator break"""
        try:
            if production_stats.current_basket:
                production_stats.current_basket.start_break()
                logger.info("Operator break started")
                return jsonify({'message': 'Break started successfully'})
            else:
                return jsonify({'error': 'No active basket to start break for'}), 400
        except Exception as e:
            logger.error(f"Error starting break: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/production/end-break', methods=['POST'])
    def end_break():
        """End an operator break"""
        try:
            if production_stats.current_basket:
                production_stats.current_basket.end_break()
                logger.info("Operator break ended")
                return jsonify({'message': 'Break ended successfully'})
            else:
                return jsonify({'error': 'No active basket to end break for'}), 400
        except Exception as e:
            logger.error(f"Error ending break: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/production/break-status', methods=['GET'])
    def break_status():
        """Get current break status"""
        try:
            if production_stats.current_basket:
                return jsonify({
                    'on_break': production_stats.current_basket.on_break,
                    'break_duration': production_stats.current_basket.get_current_break_time(),
                    'break_start_time': production_stats.current_basket.break_start_time
                })
            else:
                return jsonify({'on_break': False, 'break_duration': 0})
        except Exception as e:
            logger.error(f"Error getting break status: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/baskets')
    def basket_history():
        """Show detailed basket statistics page"""
        return render_template('basket_history.html')
    
    @app.route('/viewer')
    def data_viewer():
        """Show data viewer page for exported files"""
        return send_from_directory('.', 'data_viewer.html')
    
    @app.route('/api/baskets/history')
    def get_basket_history():
        """Get detailed basket history"""
        try:
            baskets = production_stats.get_basket_history()
            return jsonify(baskets)
        except Exception as e:
            logger.error(f"Error getting basket history: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/baskets/export')
    def export_basket_data():
        """Export comprehensive basket history and totals as JSON"""
        try:
            from flask import make_response
            import json
            from datetime import datetime
            
            # Get basket history data
            basket_data = production_stats.get_basket_history()
            
            # Get production summary for cumulative totals
            production_summary = production_stats.get_production_summary()
            
            # Create comprehensive export data
            export_data = {
                'export_info': {
                    'export_timestamp': datetime.now().isoformat(),
                    'export_date_formatted': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'system_uptime_hours': production_summary.get('uptime_seconds', 0) / 3600,
                    'data_version': '1.0'
                },
                'cumulative_totals': {
                    'total_baskets_completed': basket_data.get('total_baskets_completed', 0),
                    'total_splits': production_summary.get('total_splits', 0),
                    'total_cycles': production_summary.get('total_cycles', 0),
                    'total_fuel_consumed_gallons': basket_data.get('total_fuel_consumed', 0),
                    'average_fuel_per_basket': basket_data.get('average_fuel_per_basket', 0),
                    'overall_success_rate': (production_summary.get('total_splits', 0) / production_summary.get('total_cycles', 1) * 100) if production_summary.get('total_cycles', 0) > 0 else 0,
                    'system_uptime_seconds': production_summary.get('uptime_seconds', 0),
                    'completed_cycles': production_summary.get('completed_cycles', 0),
                    'aborted_cycles': production_summary.get('aborted_cycles', 0)
                },
                'production_rates': production_summary.get('production_rates', {}),
                'basket_history': basket_data,
                'current_basket': basket_data.get('current_basket'),
                'system_status': {
                    'current_stage': production_summary.get('current_stage', 'unknown'),
                    'system_status': production_summary.get('system_status', 'unknown'),
                    'last_activity': production_summary.get('idle_time_seconds', 0)
                }
            }
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'firewood_splitter_data_{timestamp}.json'
            
            # Create response with JSON data
            response_data = json.dumps(export_data, indent=2, default=str)
            response = make_response(response_data)
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            logger.info(f"Exported basket data: {len(basket_data.get('completed_baskets', []))} baskets, {export_data['cumulative_totals']['total_splits']} splits")
            return response
            
        except Exception as e:
            logger.error(f"Error exporting basket data: {e}")
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
    
    @app.route('/stats')
    def mqtt_stats_dashboard():
        """MQTT Statistics dashboard page"""
        return render_template('dashboard.html')
    
    @app.route('/monitor')
    def monitor_control():
        """Monitor control panel page"""
        return render_template('monitor_control.html')
    
    @app.route('/controller')
    def controller_control():
        """Controller control panel page"""
        return render_template('controller_control.html')
    
    @app.route('/api/monitor/status')
    def get_monitor_status():
        """Get current monitor readings (fuel, temperature)"""
        try:
            with production_stats.lock:
                return jsonify({
                    'fuel_level_gallons': production_stats._get_latest_fuel_level(),
                    'temperature_local_f': production_stats._get_latest_temperature('local'),
                    'temperature_remote_f': production_stats._get_latest_temperature('remote'),
                    'fuel_readings_count': len(production_stats.fuel_level_readings),
                    'temp_local_readings_count': len(production_stats.temperature_readings.get('local', [])),
                    'temp_remote_readings_count': len(production_stats.temperature_readings.get('remote', []))
                })
        except Exception as e:
            logger.error(f"Error getting monitor status: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/monitor/command', methods=['POST'])
    def send_monitor_command():
        """Send command to LogSplitter Monitor via MQTT"""
        try:
            data = request.get_json()
            if not data or 'command' not in data:
                return jsonify({'error': 'Command is required'}), 400
            
            command = data['command'].strip()
            if not command:
                return jsonify({'error': 'Command cannot be empty'}), 400
            
            # Get the MQTT client from the application context
            # Since we're using the Windows version, we need to access the global MQTT client
            mqtt_client = getattr(app, 'mqtt_client', None)
            if not mqtt_client:
                return jsonify({'error': 'MQTT client not available'}), 503
            
            # Publish command to monitor control topic
            try:
                mqtt_client.client.publish('monitor/control', command)
                logger.info(f"Sent monitor command: {command}")
                
                return jsonify({
                    'message': 'Command sent successfully',
                    'command': command,
                    'topic': 'monitor/control'
                })
                
            except Exception as e:
                logger.error(f"Failed to publish MQTT command: {e}")
                return jsonify({'error': f'Failed to send command: {str(e)}'}), 500
                
        except Exception as e:
            logger.error(f"Error sending monitor command: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/controller/command', methods=['POST'])
    def send_controller_command():
        """Send command to LogSplitter Controller via MQTT"""
        try:
            data = request.get_json()
            if not data or 'command' not in data:
                return jsonify({'error': 'Command is required'}), 400
            
            command = data['command'].strip()
            if not command:
                return jsonify({'error': 'Command cannot be empty'}), 400
            
            # Get the MQTT client from the application context
            mqtt_client = getattr(app, 'mqtt_client', None)
            if not mqtt_client:
                return jsonify({'error': 'MQTT client not available'}), 503
            
            # Publish command to controller control topic (controller/control)
            try:
                mqtt_client.client.publish('controller/control', command)
                logger.info(f"Sent controller command to controller/control: {command}")
                
                return jsonify({
                    'message': 'Command sent successfully',
                    'command': command,
                    'topic': 'controller/control',
                    'note': 'Controller response will be published to controller/control/resp'
                })
                
            except Exception as e:
                logger.error(f"Failed to publish controller MQTT command: {e}")
                return jsonify({'error': f'Failed to send command: {str(e)}'}), 500
                
        except Exception as e:
            logger.error(f"Error sending controller command: {e}")
            return jsonify({'error': str(e)}), 500
    
    # MQTT Statistics endpoints
    @app.route('/api/mqtt/stats')
    def get_mqtt_stats():
        """Get MQTT topic statistics"""
        try:
            # Get the MQTT stats engine from app context
            mqtt_stats_engine = getattr(app, 'mqtt_stats_engine', None)
            if not mqtt_stats_engine:
                return jsonify({
                    'total_topics': 0,
                    'total_messages': 0,
                    'uptime_seconds': 0,
                    'topics': {}
                })
            
            stats = mqtt_stats_engine.get_all_stats()
            
            # Add timestamp information for each topic
            for topic_name, topic_data in stats.get('topics', {}).items():
                if topic_data.get('last_updated'):
                    topic_data['last_timestamp'] = topic_data['last_updated']
            
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"Error getting MQTT stats: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Legacy endpoints for backward compatibility
    @app.route('/api/stats')
    def get_all_stats():
        """MQTT Statistics endpoint"""
        return get_mqtt_stats()
    
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