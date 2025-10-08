"""
Test logging and analysis system
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

@dataclass
class TestResult:
    test_name: str
    category: str
    status: str  # "PASS", "FAIL", "SKIP", "ERROR"
    duration: float
    error_message: str = ""
    expected: str = ""
    actual: str = ""
    score: float = 0.0  # 0-100

class TestLogger:
    def __init__(self, output_dir: str = "tests/automated/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results: List[TestResult] = []
        
        # Setup file logger
        self.log_file = self.output_dir / f"test_run_{self.timestamp}.log"
        self.logger = logging.getLogger('test_logger')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # File handler
        file_handler = logging.FileHandler(self.log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def log_test_start(self, test_name: str, category: str):
        """Log test start"""
        self.logger.info(f"{'='*80}")
        self.logger.info(f"STARTING TEST: {test_name} [{category}]")
        self.logger.info(f"{'='*80}")
    
    def log_test_end(self, result: TestResult):
        """Log test end and store result"""
        self.results.append(result)
        status_color = {
            "PASS": "✓",
            "FAIL": "✗",
            "SKIP": "⊘",
            "ERROR": "⚠"
        }
        symbol = status_color.get(result.status, "?")
        
        self.logger.info(f"{symbol} {result.test_name}: {result.status} ({result.duration:.2f}s) - Score: {result.score:.1f}/100")
        
        if result.error_message:
            self.logger.error(f"   Error: {result.error_message}")
        
        self.logger.info(f"{'='*80}\n")
    
    def log_info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def log_error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def log_debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def generate_report(self):
        """Generate comprehensive test report"""
        report_file = self.output_dir / f"test_report_{self.timestamp}.txt"
        json_file = self.output_dir / f"test_results_{self.timestamp}.json"
        
        # Calculate statistics by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'errors': 0,
                    'skipped': 0,
                    'total_score': 0,
                    'tests': []
                }
            
            cat = categories[result.category]
            cat['total'] += 1
            cat['tests'].append(result)
            cat['total_score'] += result.score
            
            if result.status == 'PASS':
                cat['passed'] += 1
            elif result.status == 'FAIL':
                cat['failed'] += 1
            elif result.status == 'ERROR':
                cat['errors'] += 1
            elif result.status == 'SKIP':
                cat['skipped'] += 1
        
        # Generate text report
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write(f"WINDOWS-USE AGENT - COMPREHENSIVE TEST REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 100 + "\n\n")
            
            # Overall summary
            total_tests = len(self.results)
            total_passed = sum(1 for r in self.results if r.status == 'PASS')
            total_failed = sum(1 for r in self.results if r.status == 'FAIL')
            total_errors = sum(1 for r in self.results if r.status == 'ERROR')
            total_skipped = sum(1 for r in self.results if r.status == 'SKIP')
            overall_score = sum(r.score for r in self.results) / total_tests if total_tests > 0 else 0
            
            f.write("OVERALL SUMMARY\n")
            f.write("-" * 100 + "\n")
            f.write(f"Total Tests:    {total_tests}\n")
            f.write(f"Passed:         {total_passed} ({total_passed/total_tests*100:.1f}%)\n")
            f.write(f"Failed:         {total_failed} ({total_failed/total_tests*100:.1f}%)\n")
            f.write(f"Errors:         {total_errors} ({total_errors/total_tests*100:.1f}%)\n")
            f.write(f"Skipped:        {total_skipped} ({total_skipped/total_tests*100:.1f}%)\n")
            f.write(f"Overall Score:  {overall_score:.1f}/100 ({self._get_grade(overall_score)})\n")
            f.write("\n")
            
            # Category breakdown
            f.write("CATEGORY BREAKDOWN\n")
            f.write("=" * 100 + "\n\n")
            
            for category, stats in sorted(categories.items()):
                avg_score = stats['total_score'] / stats['total'] if stats['total'] > 0 else 0
                grade = self._get_grade(avg_score)
                
                f.write(f"Category: {category}\n")
                f.write("-" * 100 + "\n")
                f.write(f"Tests:          {stats['total']}\n")
                f.write(f"Passed:         {stats['passed']} ({stats['passed']/stats['total']*100:.1f}%)\n")
                f.write(f"Failed:         {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)\n")
                f.write(f"Errors:         {stats['errors']} ({stats['errors']/stats['total']*100:.1f}%)\n")
                f.write(f"Skipped:        {stats['skipped']} ({stats['skipped']/stats['total']*100:.1f}%)\n")
                f.write(f"Average Score:  {avg_score:.1f}/100 ({grade})\n")
                f.write("\n")
                
                # Individual test results
                f.write("Individual Tests:\n")
                for test in stats['tests']:
                    status_symbol = "✓" if test.status == "PASS" else "✗" if test.status == "FAIL" else "⚠" if test.status == "ERROR" else "⊘"
                    f.write(f"  {status_symbol} {test.test_name:<50} {test.score:>6.1f}/100 ({test.duration:.2f}s)\n")
                    if test.error_message:
                        f.write(f"     Error: {test.error_message}\n")
                
                f.write("\n" + "=" * 100 + "\n\n")
            
            # Grading scale
            f.write("GRADING SCALE\n")
            f.write("-" * 100 + "\n")
            f.write("A+ : 97-100  (Excellent)\n")
            f.write("A  : 93-96   (Excellent)\n")
            f.write("A- : 90-92   (Very Good)\n")
            f.write("B+ : 87-89   (Good)\n")
            f.write("B  : 83-86   (Good)\n")
            f.write("B- : 80-82   (Above Average)\n")
            f.write("C+ : 77-79   (Average)\n")
            f.write("C  : 73-76   (Average)\n")
            f.write("C- : 70-72   (Below Average)\n")
            f.write("D  : 60-69   (Poor)\n")
            f.write("F  : 0-59    (Failing)\n")
            f.write("\n" + "=" * 100 + "\n")
        
        # Generate JSON report
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': self.timestamp,
                'summary': {
                    'total': total_tests,
                    'passed': total_passed,
                    'failed': total_failed,
                    'errors': total_errors,
                    'skipped': total_skipped,
                    'overall_score': overall_score,
                    'grade': self._get_grade(overall_score)
                },
                'categories': {
                    cat: {
                        'stats': {k: v for k, v in stats.items() if k != 'tests'},
                        'average_score': stats['total_score'] / stats['total'] if stats['total'] > 0 else 0,
                        'grade': self._get_grade(stats['total_score'] / stats['total'] if stats['total'] > 0 else 0)
                    }
                    for cat, stats in categories.items()
                },
                'results': [asdict(r) for r in self.results]
            }, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"\n{'='*100}")
        self.logger.info(f"Test report generated: {report_file}")
        self.logger.info(f"JSON results saved: {json_file}")
        self.logger.info(f"Test log saved: {self.log_file}")
        self.logger.info(f"{'='*100}\n")
        
        return report_file
    
    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 97: return "A+"
        elif score >= 93: return "A"
        elif score >= 90: return "A-"
        elif score >= 87: return "B+"
        elif score >= 83: return "B"
        elif score >= 80: return "B-"
        elif score >= 77: return "C+"
        elif score >= 73: return "C"
        elif score >= 70: return "C-"
        elif score >= 60: return "D"
        else: return "F"

