#!/usr/bin/env python3
"""
Generate test report for Quantum project
"""

import sys
import os
import json
import argparse
from datetime import datetime

class TestReportGenerator:
    """Generate test reports"""
    
    def __init__(self, test_results, output_dir):
        self.test_results = test_results
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_html_report(self):
        """Generate HTML test report"""
        report_path = os.path.join(self.output_dir, "test_report.html")
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test['status'] == 'passed')
        failed_tests = sum(1 for test in self.test_results if test['status'] == 'failed')
        skipped_tests = sum(1 for test in self.test_results if test['status'] == 'skipped')
        
        # Generate HTML
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Quantum Test Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #333;
            color: white;
            padding: 20px;
            border-radius: 5px;
        }}
        .summary {{
            background-color: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .test-result {{
            background-color: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .passed {{
            border-left: 5px solid #4CAF50;
        }}
        .failed {{
            border-left: 5px solid #f44336;
        }}
        .skipped {{
            border-left: 5px solid #ff9800;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-box {{
            flex: 1;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}
        .total {{
            background-color: #2196F3;
            color: white;
        }}
        .passed-box {{
            background-color: #4CAF50;
            color: white;
        }}
        .failed-box {{
            background-color: #f44336;
            color: white;
        }}
        .skipped-box {{
            background-color: #ff9800;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Quantum Test Report</h1>
        <p>Generated on: {timestamp}</p>
    </div>
    
    <div class="summary">
        <h2>Test Summary</h2>
        <div class="stats">
            <div class="stat-box total">
                <h3>Total Tests</h3>
                <p>{total_tests}</p>
            </div>
            <div class="stat-box passed-box">
                <h3>Passed</h3>
                <p>{passed_tests}</p>
            </div>
            <div class="stat-box failed-box">
                <h3>Failed</h3>
                <p>{failed_tests}</p>
            </div>
            <div class="stat-box skipped-box">
                <h3>Skipped</h3>
                <p>{skipped_tests}</p>
            </div>
        </div>
    </div>
    
    <h2>Test Results</h2>
"""
        
        # Add test results
        for test in self.test_results:
            status_class = test['status']
            html += f"""
    <div class="test-result {status_class}">
        <h3>{test['name']}</h3>
        <p><strong>Status:</strong> {test['status'].capitalize()}</p>
        <p><strong>Duration:</strong> {test['duration']:.2f}s</p>
        {f"<p><strong>Error:</strong> {test['error']}</p>" if 'error' in test else ''}
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        # Write HTML file
        with open(report_path, 'w') as f:
            f.write(html)
        
        return report_path
    
    def generate_json_report(self):
        """Generate JSON test report"""
        report_path = os.path.join(self.output_dir, "test_report.json")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.test_results),
            'passed_tests': sum(1 for test in self.test_results if test['status'] == 'passed'),
            'failed_tests': sum(1 for test in self.test_results if test['status'] == 'failed'),
            'skipped_tests': sum(1 for test in self.test_results if test['status'] == 'skipped'),
            'test_results': self.test_results
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report_path

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Generate test report')
    parser.add_argument('--results', required=True, help='Test results JSON file')
    parser.add_argument('--output', default='reports', help='Output directory')
    
    args = parser.parse_args()
    
    # Read test results
    with open(args.results, 'r') as f:
        test_results = json.load(f)
    
    # Generate reports
    generator = TestReportGenerator(test_results, args.output)
    html_report = generator.generate_html_report()
    json_report = generator.generate_json_report()
    
    print(f"HTML report generated: {html_report}")
    print(f"JSON report generated: {json_report}")

if __name__ == '__main__':
    main()
