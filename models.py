from . import db
from flask_login import UserMixin
from datetime import datetime

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    rol = db.Column(db.String(50))  # estudiante, evaluador, coordinador, admin

    # Relaciones inversas
    proyectos = db.relationship('Proyecto', backref='estudiante', lazy=True)
    evaluaciones_realizadas = db.relationship('Evaluacion', backref='evaluador', lazy=True)
    notificaciones = db.relationship('Notificacion', backref='usuario', lazy=True)


class Proyecto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150))
    descripcion = db.Column(db.Text)
    archivo = db.Column(db.String(100))
    estudiante_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

    evaluaciones = db.relationship('Evaluacion', backref='proyecto', lazy=True)
    evidencias = db.relationship('Evidencia', backref='proyecto', lazy=True)


class Rubrica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    originalidad = db.Column(db.Integer)
    relevancia = db.Column(db.Integer)
    metodologia = db.Column(db.Integer)
    resultados = db.Column(db.Integer)
    evaluador_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyecto.id'))


class Evidencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    archivo = db.Column(db.String(100))
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyecto.id'))
    evaluador_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))


class Evaluacion(db.Model):
    __tablename__ = 'evaluacion'

    id = db.Column(db.Integer, primary_key=True)

    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyecto.id'), nullable=False)
    evaluador_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    rubrica_json = db.Column(db.Text, nullable=True)   # Rúbrica serializada en JSON
    nota_final = db.Column(db.Float, nullable=True)
    comentarios = db.Column(db.Text, nullable=True)

    confirmada = db.Column(db.Boolean, default=False)
    aprobada = db.Column(db.Boolean, default=None)
    comentario_revision = db.Column(db.Text, nullable=True)

    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_confirmacion = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Evaluacion {self.id} - Proyecto {self.proyecto_id} - Evaluador {self.evaluador_id}>'


class Notificacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    mensaje = db.Column(db.String(200))
    leido = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
