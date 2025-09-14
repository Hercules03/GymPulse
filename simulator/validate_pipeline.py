#!/usr/bin/env python3
"""
GymPulse Data Pipeline Validation Script
Validates data flow from IoT simulation → AWS backend → frontend display
"""

import json
import time
import requests
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Any

class DataPipelineValidator:
    def __init__(self):
        self.api_base = "https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod"
        self.results = {}
        
    def print_header(self, title: str):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        
    def print_step(self, step: str, status: str = ""):
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "🔍"
        print(f"{status_icon} {step}" + (f" - {status}" if status else ""))
        
    def test_api_endpoints(self) -> Dict[str, Any]:
        """Test API endpoints and validate data structure"""
        self.print_header("STEP 1: API Endpoint Validation")
        
        results = {
            "branches_endpoint": {"status": "FAIL", "data": None, "error": None},
            "data_structure": {"status": "FAIL", "issues": []},
            "machine_counts": {"status": "FAIL", "expected": 19, "actual": 0}
        }
        
        try:
            # Test branches endpoint
            self.print_step("Testing GET /branches endpoint")
            response = requests.get(f"{self.api_base}/branches", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results["branches_endpoint"]["status"] = "PASS"
                results["branches_endpoint"]["data"] = data
                self.print_step(f"API Response: {response.status_code}", "PASS")
                
                # Validate data structure
                self.print_step("Validating data structure")
                issues = []
                
                if not isinstance(data, list):
                    issues.append("Response is not a list")
                else:
                    total_machines = 0
                    for branch in data:
                        # Check required fields
                        required_fields = ['id', 'name', 'coordinates', 'categories']
                        for field in required_fields:
                            if field not in branch:
                                issues.append(f"Missing field '{field}' in branch {branch.get('id', 'unknown')}")
                        
                        # Count machines
                        if 'categories' in branch:
                            for category, stats in branch['categories'].items():
                                if 'total' in stats:
                                    total_machines += stats['total']
                    
                    results["machine_counts"]["actual"] = total_machines
                    if total_machines == 19:
                        results["machine_counts"]["status"] = "PASS"
                        self.print_step(f"Machine count validation: {total_machines}/19", "PASS")
                    else:
                        self.print_step(f"Machine count validation: {total_machines}/19 (mismatch)", "FAIL")
                
                if not issues:
                    results["data_structure"]["status"] = "PASS"
                    self.print_step("Data structure validation", "PASS")
                else:
                    results["data_structure"]["issues"] = issues
                    self.print_step("Data structure validation", "FAIL")
                    for issue in issues:
                        print(f"    ⚠️  {issue}")
                        
            else:
                results["branches_endpoint"]["error"] = f"HTTP {response.status_code}"
                self.print_step(f"API Response: {response.status_code}", "FAIL")
                
        except Exception as e:
            results["branches_endpoint"]["error"] = str(e)
            self.print_step(f"API connection failed: {e}", "FAIL")
            
        return results
    
    def check_simulator_status(self) -> Dict[str, Any]:
        """Check IoT simulator status and capability"""
        self.print_header("STEP 2: IoT Simulator Status")
        
        results = {
            "simulator_available": {"status": "FAIL", "error": None},
            "configuration": {"status": "FAIL", "machines": 0},
            "certificates": {"status": "FAIL", "error": None}
        }
        
        try:
            # Check simulator status
            self.print_step("Checking simulator availability")
            result = subprocess.run(['python', 'main.py', '--status'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                results["simulator_available"]["status"] = "PASS"
                self.print_step("Simulator command available", "PASS")
                
                # Check configuration
                self.print_step("Checking machine configuration")
                try:
                    with open('config/machines.json', 'r') as f:
                        config = json.load(f)
                        machine_count = len(config.get('machines', []))
                        results["configuration"]["machines"] = machine_count
                        if machine_count > 0:
                            results["configuration"]["status"] = "PASS"
                            self.print_step(f"Configuration: {machine_count} machines", "PASS")
                        else:
                            self.print_step("No machines in configuration", "FAIL")
                except Exception as e:
                    self.print_step(f"Configuration read error: {e}", "FAIL")
                
                # Check certificates
                self.print_step("Checking certificate directory")
                try:
                    import os
                    cert_files = [f for f in os.listdir('certs') if f.endswith('.pem')]
                    if cert_files:
                        results["certificates"]["status"] = "PASS" 
                        self.print_step(f"Certificates: {len(cert_files)} files found", "PASS")
                    else:
                        self.print_step("No certificate files found", "FAIL")
                except Exception as e:
                    results["certificates"]["error"] = str(e)
                    self.print_step(f"Certificate check failed: {e}", "FAIL")
                    
            else:
                results["simulator_available"]["error"] = result.stderr
                self.print_step("Simulator command failed", "FAIL")
                
        except Exception as e:
            results["simulator_available"]["error"] = str(e)
            self.print_step(f"Simulator check failed: {e}", "FAIL")
            
        return results
    
    def test_real_time_simulation(self) -> Dict[str, Any]:
        """Test real-time data flow with short simulation"""
        self.print_header("STEP 3: Real-Time Data Flow Test")
        
        results = {
            "baseline_data": None,
            "simulation_run": {"status": "FAIL", "error": None},
            "data_change_detected": {"status": "FAIL", "changes": []}
        }
        
        try:
            # Get baseline data
            self.print_step("Getting baseline API data")
            baseline_response = requests.get(f"{self.api_base}/branches")
            if baseline_response.status_code == 200:
                results["baseline_data"] = baseline_response.json()
                self.print_step("Baseline data captured", "PASS")
                
                # Run short simulation
                self.print_step("Running 30-second simulation test")
                sim_result = subprocess.run([
                    'python', 'main.py', 
                    '--duration', '0.5',  # 30 seconds
                    '--verbose'
                ], capture_output=True, text=True, timeout=60)
                
                if sim_result.returncode == 0:
                    results["simulation_run"]["status"] = "PASS"
                    self.print_step("Simulation completed successfully", "PASS")
                    
                    # Check for data changes
                    time.sleep(5)  # Wait for propagation
                    self.print_step("Checking for data changes")
                    
                    updated_response = requests.get(f"{self.api_base}/branches")
                    if updated_response.status_code == 200:
                        updated_data = updated_response.json()
                        changes = self.compare_branch_data(results["baseline_data"], updated_data)
                        
                        if changes:
                            results["data_change_detected"]["status"] = "PASS"
                            results["data_change_detected"]["changes"] = changes
                            self.print_step("Data changes detected", "PASS")
                            for change in changes:
                                print(f"    📊 {change}")
                        else:
                            self.print_step("No data changes detected", "FAIL")
                            print("    ⚠️  This could indicate pipeline issues or timing delays")
                    else:
                        self.print_step("Failed to get updated data", "FAIL")
                        
                else:
                    results["simulation_run"]["error"] = sim_result.stderr
                    self.print_step("Simulation failed", "FAIL")
                    print(f"    ⚠️  Error: {sim_result.stderr}")
                    
            else:
                self.print_step("Failed to get baseline data", "FAIL")
                
        except Exception as e:
            self.print_step(f"Real-time test failed: {e}", "FAIL")
            
        return results
    
    def compare_branch_data(self, baseline: List[Dict], updated: List[Dict]) -> List[str]:
        """Compare two sets of branch data and identify changes"""
        changes = []
        
        for i, (base_branch, updated_branch) in enumerate(zip(baseline, updated)):
            branch_id = base_branch.get('id', f'branch_{i}')
            
            for category in ['legs', 'chest', 'back']:
                base_cat = base_branch.get('categories', {}).get(category, {})
                updated_cat = updated_branch.get('categories', {}).get(category, {})
                
                base_free = base_cat.get('free', 0)
                updated_free = updated_cat.get('free', 0)
                
                if base_free != updated_free:
                    changes.append(f"{branch_id}/{category}: {base_free} → {updated_free} free machines")
                    
        return changes
    
    def validate_frontend_integration(self) -> Dict[str, Any]:
        """Validate frontend integration by checking console logs"""
        self.print_header("STEP 4: Frontend Integration Validation")
        
        results = {
            "api_integration": {"status": "UNKNOWN", "note": "Manual verification required"},
            "websocket": {"status": "UNKNOWN", "note": "Manual verification required"},
            "real_time_updates": {"status": "UNKNOWN", "note": "Manual verification required"}
        }
        
        self.print_step("Frontend integration requires manual verification")
        print(f"    📋 Open: http://localhost:3001")
        print(f"    🔍 Check browser console for 'Loaded branches from AWS API'")
        print(f"    🔄 Verify dashboard shows 19 total machines")
        print(f"    ⏱️  Run simulation and watch for real-time updates")
        
        return results
    
    def generate_report(self, all_results: Dict[str, Any]):
        """Generate comprehensive validation report"""
        self.print_header("VALIDATION REPORT")
        
        # Count passes/fails
        total_tests = 0
        passed_tests = 0
        
        for step_results in all_results.values():
            for test_name, test_result in step_results.items():
                if isinstance(test_result, dict) and 'status' in test_result:
                    total_tests += 1
                    if test_result['status'] == 'PASS':
                        passed_tests += 1
        
        print(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed")
        print(f"✅ Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "No tests completed")
        
        # Detailed findings
        print(f"\n📋 Key Findings:")
        api_results = all_results.get('api_tests', {})
        machine_count = api_results.get('machine_counts', {}).get('actual', 0)
        print(f"  • API Endpoint: {'✅ Working' if api_results.get('branches_endpoint', {}).get('status') == 'PASS' else '❌ Issues'}")
        print(f"  • Machine Count: {machine_count}/19 machines")
        print(f"  • Data Structure: {'✅ Valid' if api_results.get('data_structure', {}).get('status') == 'PASS' else '❌ Issues'}")
        
        simulator_results = all_results.get('simulator_tests', {})
        print(f"  • Simulator: {'✅ Available' if simulator_results.get('simulator_available', {}).get('status') == 'PASS' else '❌ Issues'}")
        
        realtime_results = all_results.get('realtime_tests', {})
        changes = realtime_results.get('data_change_detected', {}).get('changes', [])
        print(f"  • Real-time Flow: {'✅ Working' if changes else '⚠️ Needs verification'}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        if machine_count != 19:
            print("  • Check DynamoDB current-state table for missing machines")
            print("  • Run simulator to populate machine data")
            
        if not changes:
            print("  • Run longer simulation to verify real-time updates")
            print("  • Check AWS CloudWatch logs for Lambda execution")
            
        print("  • Monitor frontend console during simulation for real-time updates")
        print("  • Test WebSocket connections for live tile updates")
        
    def run_full_validation(self):
        """Run complete validation suite"""
        print("🚀 GymPulse Data Pipeline Validation")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_results = {}
        
        # Run validation steps
        all_results['api_tests'] = self.test_api_endpoints()
        all_results['simulator_tests'] = self.check_simulator_status()
        all_results['realtime_tests'] = self.test_real_time_simulation()
        all_results['frontend_tests'] = self.validate_frontend_integration()
        
        # Generate report
        self.generate_report(all_results)
        
        return all_results

def main():
    validator = DataPipelineValidator()
    
    # Allow running specific tests
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        if test_type == "api":
            validator.test_api_endpoints()
        elif test_type == "simulator":
            validator.check_simulator_status()
        elif test_type == "realtime":
            validator.test_real_time_simulation()
        elif test_type == "frontend":
            validator.validate_frontend_integration()
        else:
            print("Usage: python validate_pipeline.py [api|simulator|realtime|frontend]")
    else:
        # Run full validation
        validator.run_full_validation()

if __name__ == "__main__":
    main()