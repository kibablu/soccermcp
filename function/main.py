"""
Python code to retrieve cloud run token.
Deployed to a cloud function
"""

import functions_framework
from google.auth.transport.requests import Request
from google.oauth2 import id_token
import google.auth
from flask import jsonify

@functions_framework.http
def get_oidc_token(request):
    # Get the target audience from the query parameter or JSON body
    request_json = request.get_json(silent=True)
    target_audience = None

    if request.args and 'target_audience' in request.args:
        target_audience = request.args.get('target_audience')
    elif request_json and 'target_audience' in request_json:
        target_audience = request_json.get('target_audience')

    if not target_audience:
        return jsonify({"error": "Missing 'target_audience' parameter"}), 400

    try:
        # Use Application Default Credentials (ADC) to get the identity
        auth_req = Request()
        # This fetches an ID token specifically for the target audience (your Soccer MCP URL)
        token = google.oauth2.id_token.fetch_id_token(auth_req, target_audience)
        
        return jsonify({"id_token": token})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500