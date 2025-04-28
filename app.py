from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'KAPIBARA2025SKANAPP'

# In-memory storage for markers
markers = []
marker_id_counter = 1

# Default center coordinates
DEFAULT_CENTER = (51.1605, 71.4704)

CITY_COORDINATES = {
    # Города Казахстана
    "алматы": (43.238949, 76.889709),
    "алмата": (43.238949, 76.889709),
    "астана": (51.1605, 71.4704),
    "нур-султан": (51.1605, 71.4704),
    "нур султан": (51.1605, 71.4704),
    "шымкент": (42.3417, 69.5901),
    "караганда": (49.8065, 73.0871),
    "таразы": (42.9046, 71.3894),
    "уст-каменогорск": (49.9761, 82.6061),
    "павлодар": (52.2833, 76.9667),
    "костанай": (53.222, 63.619),
    "аттырау": (47.1308, 51.9234),
    "уральск": (51.2401, 51.2012),
    "актау": (44.9989, 51.8892),

    # Популярные города России
    "москва": (55.7558, 37.6176),
    "санкт-петербург": (59.9311, 30.3609),
    "новосибирск": (55.0084, 82.9357),
    "екатеринбург": (56.8389, 60.6057),
    "казань": (55.8304, 49.0661),
    "самара": (53.1959, 50.1000),
    "омск": (54.9893, 73.3682),
    "челябинск": (55.1644, 61.4368),
    "ростов-на-дону": (47.2357, 39.7015),
    "уфа": (54.7388, 55.9721),
    "волгоград": (48.7080, 44.5133),
    "краснодар": (45.0443, 38.9760),
    "воронеж": (51.6615, 39.2003),
    "нижний новгород": (56.2965, 43.9361),
    "пермь": (58.0000, 56.2500)
}


@app.route('/')
def root():
    return map_view()


@app.route('/map')
def map_view():
    return render_template('index.html', 
                         markers=[m for m in markers if m['deadline'] >= datetime.today().date()],
                         center_lat=DEFAULT_CENTER[0],
                         center_lng=DEFAULT_CENTER[1])


@app.route('/add_marker', methods=['POST'])
def add_marker():
    global marker_id_counter
    data = request.get_json()
    try:
        new_marker = {
            'id': marker_id_counter,
            'help_needed': data['help_needed'],
            'offer': data.get('offer', ''),
            'location_text': data['location'],
            'deadline': datetime.strptime(data['deadline'], '%Y-%m-%d').date(),
            'contact': data['contact'],
            'latitude': float(data['lat']),
            'longitude': float(data['lng']),
            'created_at': datetime.now()
        }
        markers.append(new_marker)
        marker_id_counter += 1
        return jsonify({'status': 'success', 'marker_id': new_marker['id']})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/edit_marker', methods=['POST'])
def edit_marker():
    data = request.get_json()
    try:
        marker = next((m for m in markers if m['id'] == int(data['marker_id'])), None)
        if marker:
            marker['help_needed'] = data.get('help_needed', marker['help_needed'])
            marker['offer'] = data.get('offer', marker['offer'])
            marker['location_text'] = data.get('location', marker['location_text'])
            marker['deadline'] = datetime.strptime(data['deadline'], '%Y-%m-%d').date()
            marker['contact'] = data.get('contact', marker['contact'])
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'error': 'Marker not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/delete_marker', methods=['POST'])
def delete_marker():
    data = request.get_json()
    try:
        marker_id = int(data['marker_id'])
        global markers
        markers = [m for m in markers if m['id'] != marker_id]
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/location', methods=['GET', 'POST'])
def location():
    if request.method == 'POST':
        city = request.form.get('city', '').strip().lower()
        coords = CITY_COORDINATES.get(city, DEFAULT_CENTER)
        return redirect(url_for('map_view'))
    return render_template('location.html')

@app.route('/rating')
def rating():
    # Simple counter for markers per location
    location_stats = {}
    for marker in markers:
        loc = marker['location_text'].lower()
        location_stats[loc] = location_stats.get(loc, 0) + 1
    top_locations = sorted(location_stats.items(), key=lambda x: x[1], reverse=True)[:100]
    return render_template('rating.html', top_locations=top_locations)

@app.route('/search')
def search():
    q = request.args.get('q', '')
    markers_found = []
    if q:
        q = q.lower()
        markers_found = [m for m in markers if q in m['location_text'].lower() 
                        or q in m['help_needed'].lower()]
    return render_template('search.html', q=q, markers_found=markers_found)

@app.route('/announcements')
def announcements():
    q = request.args.get('q', '')
    current_markers = [m for m in markers if m['deadline'] >= datetime.today().date()]
    if q:
        q = q.lower()
        current_markers = [m for m in current_markers 
                         if q in m['location_text'].lower() 
                         or q in m['help_needed'].lower()]
    return render_template('announcements.html', markers=current_markers, query=q)

@app.route('/announcement/<int:marker_id>')
def announcement(marker_id):
    marker = next((m for m in markers if m['id'] == marker_id), None)
    if marker:
        return render_template('announcement.html', marker=marker)
    return redirect(url_for('map_view'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
