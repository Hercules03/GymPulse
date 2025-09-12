#!/usr/bin/env python3
"""
Mock API Server to test frontend with real database data
Serves data from DynamoDB to verify frontend displays it correctly
"""

import json
import boto3
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='ap-east-1')
current_state_table = dynamodb.Table('gym-pulse-current-state')
aggregates_table = dynamodb.Table('gym-pulse-aggregates')

# Branch metadata
BRANCHES = {
    'hk-central': {'name': 'Central Branch', 'lat': 22.2819, 'lon': 114.1577},
    'hk-causeway': {'name': 'Causeway Bay Branch', 'lat': 22.2783, 'lon': 114.1747}
}

@app.route('/branches', methods=['GET'])
def get_branches():
    """Get all branches with current availability counts"""
    try:
        # Get all current machine states
        response = current_state_table.scan()
        machines = response['Items']
        
        # Aggregate by branch and category
        branches = []
        for branch_id, branch_info in BRANCHES.items():
            branch_machines = [m for m in machines if m.get('gymId') == branch_id]
            
            categories = {}
            for category in ['legs', 'chest', 'back']:
                cat_machines = [m for m in branch_machines if m.get('category') == category]
                free_count = len([m for m in cat_machines if m.get('status') == 'free'])
                total_count = len(cat_machines)
                
                categories[category] = {
                    'free': free_count,
                    'total': total_count
                }
            
            branches.append({
                'id': branch_id,
                'name': branch_info['name'],
                'coordinates': {
                    'lat': branch_info['lat'],
                    'lon': branch_info['lon']
                },
                'categories': categories
            })
        
        print(f"✅ Serving {len(branches)} branches with real data:")
        for branch in branches:
            print(f"   🏢 {branch['name']}: {sum(cat['free'] for cat in branch['categories'].values())}/{sum(cat['total'] for cat in branch['categories'].values())} machines free")
        return jsonify(branches)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/branches/<branch_id>/categories/<category>/machines', methods=['GET'])
def get_machines(branch_id, category):
    """Get machines for specific branch and category"""
    try:
        response = current_state_table.scan()
        machines = response['Items']
        
        # Filter by branch and category
        filtered_machines = [
            m for m in machines 
            if m.get('gymId') == branch_id and m.get('category') == category
        ]
        
        # Format for frontend
        machine_list = []
        for machine in filtered_machines:
            machine_list.append({
                'machineId': machine.get('machineId'),
                'name': machine.get('name', machine.get('machineId')),
                'status': machine.get('status'),
                'lastUpdate': machine.get('lastUpdate'),
                'lastChange': machine.get('lastChange', machine.get('lastUpdate')),
                'category': machine.get('category'),
                'gymId': machine.get('gymId'),
                'alertEligible': machine.get('status') == 'occupied'
            })
        
        result = {
            'machines': machine_list,
            'branchId': branch_id,
            'category': category,
            'totalCount': len(machine_list),
            'freeCount': len([m for m in machine_list if m['status'] == 'free']),
            'occupiedCount': len([m for m in machine_list if m['status'] == 'occupied'])
        }
        
        print(f"✅ Serving {len(machine_list)} {category} machines for {branch_id}")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'mock-api-server',
        'timestamp': int(datetime.now(timezone.utc).timestamp())
    })

if __name__ == '__main__':
    print("🚀 Starting Mock API Server with real database data...")
    print("📊 Will serve data from DynamoDB tables:")
    print("   - gym-pulse-current-state")
    print("   - gym-pulse-aggregates")
    print("🌐 Server will run on http://localhost:5000")
    print("🔄 Frontend can access via CORS-enabled endpoints")
    
    app.run(host='0.0.0.0', port=5001, debug=True)