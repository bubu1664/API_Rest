from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# In-memory data storage
alumnos = []
profesores = []

# Helper functions for validation
def validate_alumno(data):
    required_fields = ["id", "nombres", "apellidos", "matricula", "promedio"]
    for field in required_fields:
        if field not in data or data[field] == "":
            abort(400, description=f"The field '{field}' is required and cannot be empty.")
    if not isinstance(data["promedio"], (int, float)):
        abort(400, description="The field 'promedio' must be a number.")

def validate_profesor(data):
    required_fields = ["id", "numeroEmpleado", "nombres", "apellidos", "horasClase"]
    for field in required_fields:
        if field not in data or data[field] == "":
            abort(400, description=f"The field '{field}' is required and cannot be empty.")
    if not isinstance(data["horasClase"], int):
        abort(400, description="The field 'horasClase' must be an integer.")

# Endpoints for alumnos (students)
@app.route('/alumnos', methods=['GET'])
def get_alumnos():
    return jsonify(alumnos), 200

@app.route('/alumnos/<int:id>', methods=['GET'])
def get_alumno(id):
    alumno = next((a for a in alumnos if a['id'] == id), None)
    if alumno is None:
        abort(404, description="Alumno not found.")
    return jsonify(alumno), 200

@app.route('/alumnos', methods=['POST'])
def create_alumno():
    if not request.json:
        abort(400, description="Data is required.")
    validate_alumno(request.json)
    nuevo_alumno = {
        'id': request.json['id'],
        'nombres': request.json['nombres'],
        'apellidos': request.json['apellidos'],
        'matricula': request.json['matricula'],
        'promedio': request.json['promedio']
    }
    alumnos.append(nuevo_alumno)
    return jsonify(nuevo_alumno), 201

@app.route('/alumnos/<int:id>', methods=['PUT'])
def update_alumno(id):
    alumno = next((a for a in alumnos if a['id'] == id), None)
    if alumno is None:
        abort(404, description="Alumno not found.")
    if not request.json:
        abort(400, description="Data is required.")
    for field in ["nombres", "apellidos", "matricula", "promedio"]:
        if field in request.json and request.json[field] != "":
            alumno[field] = request.json[field]
    return jsonify(alumno), 200

@app.route('/alumnos/<int:id>', methods=['DELETE'])
def delete_alumno(id):
    alumno = next((a for a in alumnos if a['id'] == id), None)
    if alumno is None:
        abort(404, description="Alumno not found.")
    alumnos.remove(alumno)
    return jsonify({}), 200

# Endpoints for profesores (teachers)
@app.route('/profesores', methods=['GET'])
def get_profesores():
    return jsonify(profesores), 200

@app.route('/profesores/<int:id>', methods=['GET'])
def get_profesor(id):
    profesor = next((p for p in profesores if p['id'] == id), None)
    if profesor is None:
        abort(404, description="Profesor not found.")
    return jsonify(profesor), 200

@app.route('/profesores', methods=['POST'])
def create_profesor():
    if not request.json:
        abort(400, description="Data is required.")
    validate_profesor(request.json)
    nuevo_profesor = {
        'id': request.json['id'],
        'numeroEmpleado': request.json['numeroEmpleado'],
        'nombres': request.json['nombres'],
        'apellidos': request.json['apellidos'],
        'horasClase': request.json['horasClase']
    }
    profesores.append(nuevo_profesor)
    return jsonify(nuevo_profesor), 201

@app.route('/profesores/<int:id>', methods=['PUT'])
def update_profesor(id):
    profesor = next((p for p in profesores if p['id'] == id), None)
    if profesor is None:
        abort(404, description="Profesor not found.")
    if not request.json:
        abort(400, description="Data is required.")
    for field in ["numeroEmpleado", "nombres", "apellidos", "horasClase"]:
        if field in request.json and request.json[field] != "":
            profesor[field] = request.json[field]
    return jsonify(profesor), 200

@app.route('/profesores/<int:id>', methods=['DELETE'])
def delete_profesor(id):
    profesor = next((p for p in profesores if p['id'] == id), None)
    if profesor is None:
        abort(404, description="Profesor not found.")
    profesores.remove(profesor)
    return jsonify({}), 200



from werkzeug.exceptions import HTTPException

# Global error handler for HTTP exceptions
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Handles standard HTTP exceptions and returns a JSON response."""
    return jsonify({"error": e.description}), e.code

# General error handler for unexpected exceptions
@app.errorhandler(Exception)
def handle_general_exception(e):
    """Handles any unexpected exceptions and returns a generic error response."""
    return jsonify({"error": "An unexpected error occurred"}), 500



# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
