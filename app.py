import os
import boto3
import uuid
import time
import random
import string
from boto3.dynamodb.conditions import Key
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Flask configuration
app = Flask(__name__)

BASE_URL = "http://127.0.0.1:5000"

# Database
endpoint = "database-2-instance-1.chaiyymsqn0u.us-east-1.rds.amazonaws.com"
username = "admin"
password = "imolecys"
database_name = "rest_db"


app.config['SQLALCHEMY_DATABASE_URI'] = (
  f'mysql+pymysql://{username}:{password}@{endpoint}:3306/{database_name}'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

# AWS Credentials and Bucket Configuration
AWS_ACCESS_KEY_ID = 'ASIA4E6YYM7RGJZTBFT2'
AWS_SECRET_ACCESS_KEY = 'lqGoC2t6YQ5HujNvj9+R6W6Qvi5u7ztyBkFFtlGR'
AWS_SESSION_TOKEN = 'IQoJb3JpZ2luX2VjEDgaCXVzLXdlc3QtMiJHMEUCIQDKsh3AoIN0G1O1CS4m+APO7yvPk+XjpK8DxZwzyb+eOAIgalKWbFS89J9pB/6SHPjMOTuywHRjTePNgjsw5RkK614qrQII4f//////////ARAAGgw4MzUyODg4NTI0NTAiDPUld6sNJ8yHmtM1oiqBAm4Rr6xtT7YqACndTFO6qQK0pSfUEIefFM2Ad8VJRiNWDxWjR8t8IbtULOdpXcmAjrdV2CQ3dh+s/8k4RAeK6Asm37w593s6+E0c2d/iMk7irMv52Trp8bJ8+HoIZ4SZp5wIps3NZk23JsXJmMKt8gfg5gNEk+F57iuEGiGgkewuFg9jtPGmwH+nbClw07US6f9rfi0CUzGxDumdPdaoWj0K1gCaa2hUkt9A0tG3InmJCjMD+sb5aO5SkhvqO5EoaXrAkaou95rrMSV2Y5hFI6+RQhB4NcqguyWS0a3aACAA/7fkvHqJpvQKy6hbcwoxB7F/jt1RhDk+XnoF5dtNlsUuMKu/vroGOp0BG3umiJQ2Ngn1QQZJ1AX1htt1X0u4iUqeSjQBlQkkSdMx9bU2hDDPEwUGiVugYUevkbe7L08AM+IgVIUMqfMXI8CGz1g47D85md0+PmdxossSD3DVlpzsVIS2rV+2NyAWalp3dlGLoYnQTIoIqidtqP3yw4bUab8BCesgwjYb7dY43hx3HPahn1olrTpaXdU6AT9lrY/fP33PQ6UdWg=='
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

# Initialisation client DynamoDB
dynamodb_client = boto3.resource(
    'dynamodb',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
    region_name=AWS_REGION
)
dynamodb_table = dynamodb_client.Table('sesiones-alumnos')
def generate_session_string(length=128):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))



# Configuration SNS
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:835288852450:AlumnoNotifications'

# Initialisation du client SNS
sns_client = boto3.client(
    'sns',
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
    horasClase = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "nombres": self.nombres,
            "apellidos": self.apellidos,
            "numeroEmpleado": self.numeroEmpleado,
            "horasClase": int(self.horasClase),  # Convertir en entier si nécessaire
        }


# DATABASE INITIALIZATION
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
    if isinstance(files['foto'], tuple):
        return jsonify({"error": "Expected file, but got tuple instead"}), 400

    # Affichage du contenu de file pour débogage
    file = files['foto']

    if not file or not hasattr(file, 'filename') or not file.filename:
        return jsonify({"error": "Invalid file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400
    try:
        # Nom du fichier S3
        filename = f"alumnos/{id}/{file.filename}"

        # Téléchargement direct vers S3
        s3_client.upload_fileobj(
            file,
            BUCKET_NAME,
            filename,
            ExtraArgs={'ACL':'public-read'}
        )

        # URL publique
        fotoPerfilUrl = f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"

    # Mise à jour dans la base de données
        alumno.fotoPerfilUrl = fotoPerfilUrl

        db.session.commit()

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

@app.route('/alumnos/<int:id>/session/login', methods=['POST'])
def session_login(id):
    data = request.get_json()
    password = data.get('password')

    # Vérifier que l'élève existe dans la base
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({"error": "Alumno not found"}), 404

    # Vérifier le mot de passe
    if alumno.password != password:
        return jsonify({"error": "Invalid password"}), 400

    # Générer les informations de session
    session_id = str(uuid.uuid4())
    session_string = generate_session_string()
    timestamp = int(time.time())

    # Enregistrer la session dans DynamoDB
    try:
        dynamodb_table.put_item(
            Item={
                "id": session_id,
                "fecha": timestamp,
                "alumnoId": id,
                "active": True,
                "sessionString": session_string
            }
        )
        return jsonify({"session_id": session_id, "sessionString": session_string}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to create session: {str(e)}"}), 500

@app.route('/alumnos/<int:id>/session/verify', methods=['POST'])
def session_verify(id):
    data = request.get_json()
    session_string = data.get('sessionString')

    # Rechercher la session dans DynamoDB
    try:
        response = dynamodb_table.scan(
            FilterExpression=Key('alumnoId').eq(id) & Key('sessionString').eq(session_string)
        )
        if not response['Items']:
            return jsonify({"error": "Invalid session"}), 400

        session = response['Items'][0]
        if session['active']:
            return jsonify({"message": "Session is valid"}), 200
        else:
            return jsonify({"error": "Session is inactive"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to verify session: {str(e)}"}), 500

@app.route('/alumnos/<int:id>/session/logout', methods=['POST'])
def session_logout(id):
    data = request.get_json()
    session_string = data.get('sessionString')

    try:
        response = dynamodb_table.scan(
            FilterExpression=Key('alumnoId').eq(id) & Key('sessionString').eq(session_string)
        )
        if not response['Items']:
            return jsonify({"error": "Invalid session"}), 400

        session_id = response['Items'][0]['id']
        dynamodb_table.update_item(
            Key={'id': session_id},
            UpdateExpression="SET active = :inactive",
            ExpressionAttributeValues={':inactive': False}
        )
        return jsonify({"message": "Session terminated"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to logout: {str(e)}"}), 500


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


@app.route('/alumnos/<int:id>/email', methods=['POST'])
def send_email_to_alumno(id):
    alumno = Alumno.query.get(id)
    if not alumno:
        return jsonify({"error": "Alumno not found"}), 404
    message = (
        f"Información del Alumno:\n"
        f"Nombre: {alumno.nombres} {alumno.apellidos}\n"
        f"Matrícula: {alumno.matricula}\n"
        f"Promedio: {alumno.promedio}\n"
    )

    try:
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject=f"Notificación para {alumno.nombres} {alumno.apellidos}"
        )
        return jsonify({"message": "Notificación enviada exitosamente", "response": response}), 200
    except Exception as e:
        return jsonify({"error": f"No se pudo enviar la notificación: {str(e)}"}), 500

# RUN THE APPLICATION
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
