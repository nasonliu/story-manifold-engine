#!/usr/bin/env python3
"""API server for dashboard data"""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

PORT = 8081
DATA_DIR = Path(__file__).parent / "data" / "real_novels_skeletons"

class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            data = self.get_dashboard_data()
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())
        elif self.path == '/api/skeleton':
            # Get skeleton content
            filename = self.translate_path(self.path)
            self.serve_file(filename)
        elif self.path.startswith('/api/skeleton/'):
            # Serve skeleton file
            filepath = self.path[13:]  # Remove /api/skeleton/
            filepath = filepath.replace('%20', ' ')
            full_path = DATA_DIR
            
            # Find the file
            for root, dirs, files in os.walk(DATA_DIR):
                for f in files:
                    if f.replace('.json', '') == filepath.replace('.json', '') or f == filepath:
                        full_path = os.path.join(root, f)
                        break
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.wfile.write(content.encode())
            except:
                self.wfile.write(b'{}')
        else:
            super().do_GET()
    
    def get_dashboard_data(self):
        """Get all dashboard data"""
        skeletons = []
        source_stats = {}
        
        for root, dirs, files in os.walk(DATA_DIR):
            for f in files:
                if f.endswith('.json'):
                    filepath = os.path.join(root, f)
                    rel_path = os.path.relpath(filepath, DATA_DIR)
                    source = rel_path.split(os.sep)[0] if os.sep in rel_path else 'unknown'
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as fp:
                            content = json.load(fp)
                            skeletons.append({
                                'title': content.get('title', f.replace('.json', '')),
                                'author': content.get('author', 'Unknown'),
                                'language': content.get('language', source),
                                'genre': content.get('genre', ''),
                                'file': f.replace('.json', ''),
                                'path': rel_path
                            })
                    except:
                        skeletons.append({
                            'title': f.replace('.json', ''),
                            'author': 'Error',
                            'language': source,
                            'genre': '',
                            'file': f.replace('.json', ''),
                            'path': rel_path
                        })
                    
                    source_stats[source] = source_stats.get(source, 0) + 1
        
        # Language stats
        lang_stats = {'zh': 0, 'en': 0, 'classic': 0, 'other': 0}
        for s in skeletons:
            lang = s.get('language', 'other')
            if lang in ['zh', '中文']:
                lang_stats['zh'] += 1
            elif lang in ['en', '英文', 'English']:
                lang_stats['en'] += 1
            elif lang in ['classic', '经典']:
                lang_stats['classic'] += 1
            else:
                lang_stats['other'] += 1
        
        total = len(skeletons)
        
        return {
            'total': total,
            'target': 2000,
            'languages': lang_stats,
            'sources': source_stats,
            'skeletons': skeletons[:100]  # First 100 for list
        }

if __name__ == '__main__':
    os.chdir(Path(__file__).parent)
    server = HTTPServer(('0.0.0.0', PORT), DashboardHandler)
    print(f"API Server running on http://localhost:{PORT}")
    print(f"Data endpoint: http://localhost:{PORT}/api/data")
    server.serve_forever()
