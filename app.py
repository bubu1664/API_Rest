import os
import boto3
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Flask configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'  # Temp directory for uploads
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

# AWS Credentials and Bucket Configuration
AWS_ACCESS_KEY_ID = 'ASIA4E6YYM7RAYESJ26M'
AWS_SECRET_ACCESS_KEY = '/L0HOBwRTXyP0tE7IapNMZkCkkZRrbxh6qcbtgND'
AWS_SESSION_TOKEN ='IQoJb3JpZ2luX2VjEF0aCXVzLXdlc3QtMiJGMEQCIFSTSTIk0cOQRmv/AD6mcz6nJoq6M1k1eRb/gFH970r+AiBhHmCAfTqZJeVSl3yfWZabxPHnjkrI0run+1kYXN2+qCqtAgj2//////////8BEAAaDDgzNTI4ODg1MjQ1MCIMpdADrQZa3m+s4LSGKoECymu2XRqAH/NojysleqSgb3zLcVbz3XlUooDTFBcxamfmdzN0KHaG8/0uPQuWfeWqRzUGCTvXHBTDFpP6WEJks1MgNlMU/tqAgSPY0q+H5+UYfJemc1cyR52taSVJoaxZmsZpkLRbkN03SBmbwJDAyDGCeYFht08kDhx3e0nunwHLeF4FxIP7mKNLVTUCvG/7z3AHQIhFCvlCWdlGwqT7tDCHBp14g5CxvFituP2OkjTuSHHVgx/3QIgi30i35EnOJbcZbU+9ZOHPA37SNFeEf8cKQ/l4aSc2Bl9q2R8zGKv6NFNlJwIu1TrS+u8ReN+/EbQmBQgdA6fPur+cib/w+S0wiK2OugY6ngG5CA+2HTfEd02ZXDwk9S4dvUIQEB2FOW17oemAasAn8Yq9LZUVidSgBXeEWlN9y0JaA4mjfE/oqBroXVOCwce+1JG5dlTMWkBTXTd8hnrd2XeWURyzBlzQKLybtFBJ7pWHyC+UoOiYetZ9iw112bGZz+1NNUwEPKORPLdMJ7oXDBKh2gThMBNOwf3zURjtRMdwG/M0R1/maCsiO6O3XA=='
AWS_REGION = 'us-east-1'  # e.g., 'us-east-1'
BUCKET_NAME = 'mybucketawsapi'


# AWS S3 Configuration
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name=AWS_REGION
)

# MODELS
class Alumno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=True)
    matricula = db.Column(db.String(50), unique=True, nullable=False)
    promedio = db.Column(db.Float, nullable=True)
    password = db.Column(db.String(100), nullable=False)
    fotoPerfilUrl = db.Column(db.String(300), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nombres": self.nombres,
            "apellidos": self.apellidos,
            "matricula": self.matricula,
            "promedio": self.promedio,
            "password": self.password,
            "fotoPerfilUrl": self.fotoPerfilUrl
        }

# Helper function to check allowed file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


class Profesor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=True)
    numeroEmpleado = db.Column(db.Integer, unique=True, nullable=False)
    horasClase = db.Column(db.Integer, nullable=False)  # Changer en Integer

    def to_dict(self):
        return {
            "id": self.id,
            "nombres": self.nombres,
            "apellidos": self.apellidos,
            "numeroEmpleado": self.numeroEmpleado,
            "horasClase": int(self.horasClase),  # Convertir en entier si nécessaire
        }


# DATABASE INITIALIZATION
# Initialisation de la base après la configuration de l'application
with app.app_context():
    db.create_all()

# VALIDATION FUNCTIONS
def validate_alumno(data):
    return (
            isinstance(data.get('nombres'), str) and len(data['nombres']) > 0 and
            isinstance(data.get('matricula'), str) and len(data['matricula']) > 0 and
            (data.get('promedio') is None or isinstance(data['promedio'], (int, float))) and
            isinstance(data.get('password'), str) and len(data['password']) > 0
    )

def validate_profesor(data):
    return (
            isinstance(data.get('nombres'), str) and len(data['nombres']) > 0 and
            isinstance(data.get('numeroEmpleado'), int) and data['numeroEmpleado'] > 0 and
            isinstance(data.get('horasClase'), (int, float)) and data['horasClase'] >= 0
    )

# ROUTES FOR ALUMNOS
@app.route('/alumnos', methods=['GET'])
def get_alumnos():
    alumnos = Alumno.query.all()
    return jsonify([alumno.to_dict() for alumno in alumnos]), 200

@app.route('/alumnos/<int:id>', methods=['GET'])
def get_alumno(id):
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({"error": "Alumno not found"}), 404
    return jsonify(alumno.to_dict()), 200

@app.route('/alumnos', methods=['POST'])
def create_alumno():
    data = request.get_json()
    if not validate_alumno(data):
        return jsonify({"error": "Invalid data"}), 400
    alumno = Alumno(**data)
    db.session.add(alumno)
    db.session.commit()
    return jsonify(alumno.to_dict()), 201

import logging

@app.route('/alumnos/<int:id>/fotoPerfil', methods=['POST'])
def upload_foto_alumno(id):
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({"error": "Alumno not found"}), 404

    if 'foto' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    files = request.files
    print(f"Files in request: {files}")

    # Si le champ 'foto' contient un tuple (ce qui ne devrait pas arriver normalement)
    if isinstance(files['foto'], tuple):
        return jsonify({"error": "Expected file, but got tuple instead"}), 400

    # Affichage du contenu de file pour débogage
    file = files['foto']
    print(f"File type: {type(file)}")
    print(f"File filename type: {type(file.filename)}")
    print(f"File filename: {file.filename}")
    print("1")

    if not file or not hasattr(file, 'filename') or not file.filename:
        return jsonify({"error": "Invalid file"}), 400
    print("2")

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400
    print("3")
    try:
        # Nom du fichier S3
        filename = f"alumnos/{id}/{file.filename}"
        print("4")

        # Téléchargement direct vers S3
        s3_client.upload_fileobj(
            file,
            BUCKET_NAME,
            filename,
            ExtraArgs={'ACL':'public-read'}
        )
        print("5")

        # URL publique
        fotoPerfilUrl = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{filename}"
        print("6")

    # Mise à jour dans la base de données
        alumno.fotoPerfilUrl = fotoPerfilUrl
        print("7")

        db.session.commit()
        print("8")

        return jsonify({"fotoPerfilUrl": fotoPerfilUrl}), 200

    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Error with AWS credentials: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/alumnos/<int:id>', methods=['PUT'])
def update_alumno(id):
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({"error": "Alumno not found"}), 404

    data = request.get_json()
    if not validate_alumno(data):
        return jsonify({"error": "Invalid data"}), 400

    # Mise à jour des champs
    alumno.nombres = data.get('nombres', alumno.nombres)
    alumno.apellidos = data.get('apellidos', alumno.apellidos)
    alumno.matricula = data.get('matricula', alumno.matricula)
    alumno.promedio = data.get('promedio', alumno.promedio)
    alumno.password = data.get('password', alumno.password)

    db.session.commit()
    return jsonify(alumno.to_dict()), 200

@app.route('/alumnos/<int:id>', methods=['DELETE'])
def delete_alumno(id):
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({"error": "Alumno not found"}), 404

    # Suppression de la photo de profil sur S3 si elle existe
    if alumno.fotoPerfilUrl:
        try:
            # Extraire le chemin du fichier à partir de l'URL S3
            filename = alumno.fotoPerfilUrl.split(f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/")[1]
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=filename)
        except Exception as e:
            return jsonify({"error": f"Failed to delete profile picture: {str(e)}"}), 500

    # Suppression de l'alumno
    db.session.delete(alumno)
    db.session.commit()
    return jsonify({"message": "Alumno deleted successfully"}), 200

# ROUTES FOR PROFESORES
@app.route('/profesores', methods=['GET'])
def get_profesores():
    profesores = Profesor.query.all()
    return jsonify([profesor.to_dict() for profesor in profesores]), 200

@app.route('/profesores/<int:id>', methods=['GET'])
def get_profesor(id):
    profesor = Profesor.query.get(id)
    if not profesor:
        return jsonify({"error": "Profesor not found"}), 404
    return jsonify(profesor.to_dict()), 200

@app.route('/profesores', methods=['POST'])
def create_profesor():
    data = request.get_json()
    if not validate_profesor(data):
        return jsonify({"error": "Invalid data"}), 400
    profesor = Profesor(**data)
    db.session.add(profesor)
    db.session.commit()
    return jsonify(profesor.to_dict()), 201

@app.route('/profesores/<int:id>', methods=['PUT'])
def update_profesor(id):
    profesor = Profesor.query.get(id)
    if not profesor:
        return jsonify({"error": "Profesor not found"}), 404
    data = request.get_json()
    if not validate_profesor(data):
        return jsonify({"error": "Invalid data"}), 400
    profesor.nombres = data['nombres']
    profesor.apellidos = data.get('apellidos', profesor.apellidos)
    profesor.numeroEmpleado = data['numeroEmpleado']
    profesor.horasClase = data['horasClase']
    db.session.commit()
    return jsonify(profesor.to_dict()), 200

@app.route('/profesores/<int:id>', methods=['DELETE'])
def delete_profesor(id):
    profesor = Profesor.query.get(id)
    if not profesor:
        return jsonify({"error": "Profesor not found"}), 404
    db.session.delete(profesor)
    db.session.commit()
    return jsonify({"message": "Profesor deleted"}), 200

# RUN THE APPLICATION
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crée les tables si elles n'existent pas
    app.run(host='0.0.0.0', port=5000, debug=True)
