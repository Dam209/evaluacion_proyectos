from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional

class EvaluacionForm(FlaskForm):
    originalidad = SelectField(
        'Originalidad',
        choices=[(1, 'Baja'), (2, 'Media'), (3, 'Alta')],
        coerce=int,
        validators=[DataRequired()]
    )

    relevancia = SelectField(
        'Relevancia',
        choices=[(1, 'Baja'), (2, 'Media'), (3, 'Alta')],
        coerce=int,
        validators=[DataRequired()]
    )

    metodologia = SelectField(
        'Metodología',
        choices=[(1, 'Débil'), (2, 'Aceptable'), (3, 'Sólida')],
        coerce=int,
        validators=[DataRequired()]
    )

    resultados = SelectField(
        'Resultados',
        choices=[(1, 'Pobres'), (2, 'Moderados'), (3, 'Excelentes')],
        coerce=int,
        validators=[DataRequired()]
    )

    comentarios = TextAreaField(
        'Comentarios Generales',
        validators=[Optional()]
    )

    confirmada = BooleanField('Confirmar evaluación')

    aprobada = BooleanField('Proyecto Aprobado')

    comentario_revision = TextAreaField(
        'Comentarios del Revisor',
        validators=[Optional()]
    )

    submit = SubmitField('Enviar Evaluación')
