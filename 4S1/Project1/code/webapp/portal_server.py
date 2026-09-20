"""Serve the static portal and archived result APIs on localhost.

Numerical analysis is read from the cenara70hx export, never recomputed locally.
Image overlays only visualize saved predictions. This viewer never loads a model.
Run: code/.venv311/Scripts/python.exe code/webapp/portal_server.py --port 8767
"""
import argparse
import json
from pathlib import Path
from flask import jsonify
import server as legacy

app = legacy.app
cache = Path(__file__).with_name('cache') / 'legacy-analysis.json'
analysis = json.loads(cache.read_text(encoding='utf-8'))
# These are existing archived summaries, not newly calculated evaluation scores.
for task in ('reasonseg', 'drone'):
    analysis['summary'][task] = legacy.load_summary(task)
    analysis['counts'][task] = len(legacy.load_rows(task))
legacy.ANALYSIS = analysis

def viewer_status():
    return jsonify(viewer_only=True, cuda=False, model_loaded=False, busy=False,
                   message='Saved results viewer. Model inference runs separately on cenara70hx.')

def no_local_inference():
    return jsonify(error='This archive viewer displays saved experiments only. New inference must run on cenara70hx; no local model is loaded.'), 409

app.view_functions['api_status'] = viewer_status
app.view_functions['api_segment'] = no_local_inference

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8767)
    args = parser.parse_args()
    app.run(host='127.0.0.1', port=args.port, debug=False, threaded=True)
