# app/routes.py
from flask import render_template
from app import app # Import the app instance from __init__.py

# Define the route for the homepage (/)
@app.route('/')
@app.route('/index') # Optional: make /index work too
def home():
    """Renders the homepage."""
    # Data for the map could be passed here eventually
    # For now, just render the template
    # King County center coordinates (approximate)
    map_center_lat = 47.6062
    map_center_lon = -122.3321
    map_zoom = 9

    return render_template(
        'index.html',
        title='King County Real Estate Dashboard',
        map_center_lat=map_center_lat,
        map_center_lon=map_center_lon,
        map_zoom=map_zoom
    )

# @app.route('/property/<property_id>')
# def property_view(property_id):
#     # Logic to fetch and display property details
#     pass