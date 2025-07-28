from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required, current_user
from .models import Proyecto, Rubrica, Evaluacion, Evidencia, Notificacion
from .forms import EvaluacionForm
from . import db
from xhtml2pdf import pisa
from io import BytesIO

main = Blueprint('main', __name__)


# DASHBOARD (redireccionado por rol)
@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.rol == 'Estudiante':
        return render_template('dashboards/estudiante.html')
    elif current_user.rol == 'Evaluador':
        return render_template('dashboards/evaluador.html')
    elif current_user.rol == 'Coordinador':
        return render_template('dashboards/coordinador.html')
    elif current_user.rol == 'Administrador':
        return render_template('dashboards/admin.html')
    else:
        return "Rol no reconocido", 403


# SUBIR PROYECTO
@main.route('/upload_project', methods=['GET', 'POST'])
@login_required
def upload_project():
    if current_user.rol != 'estudiante':
        return "No autorizado", 403
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        archivo = request.files['archivo']
        archivo.save(f'app/static/{archivo.filename}')
        proyecto = Proyecto(titulo=titulo, descripcion=descripcion, archivo=archivo.filename, estudiante_id=current_user.id)
        db.session.add(proyecto)
        db.session.commit()
        return redirect(url_for('main.dashboard'))
    return render_template('upload_project.html')


# RUBRICA
@main.route('/rubric/<int:proyecto_id>', methods=['GET', 'POST'])
@login_required
def rubric(proyecto_id):
    if current_user.rol != 'evaluador':
        return "No autorizado", 403
    if request.method == 'POST':
        rubrica = Rubrica(
            originalidad=int(request.form['Originalidad']),
            relevancia=int(request.form['Relevancia']),
            metodologia=int(request.form['Metodologia']),
            resultados=int(request.form['Resultados']),
            evaluador_id=current_user.id,
            proyecto_id=proyecto_id
        )
        db.session.add(rubrica)
        db.session.commit()
        return redirect(url_for('main.upload_evidence', proyecto_id=proyecto_id))
    return render_template('rubric.html', proyecto_id=proyecto_id)


# EVIDENCIAS
@main.route('/upload_evidence/<int:proyecto_id>', methods=['GET', 'POST'])
@login_required
def upload_evidence(proyecto_id):
    if current_user.rol != 'evaluador':
        return "No autorizado", 403
    if request.method == 'POST':
        for f in request.files.getlist('archivos'):
            f.save(f'app/static/{f.filename}')
            evidencia = Evidencia(archivo=f.filename, proyecto_id=proyecto_id, evaluador_id=current_user.id)
            db.session.add(evidencia)
        db.session.commit()
        return redirect(url_for('main.evaluation', proyecto_id=proyecto_id))
    return render_template('evidences.html', proyecto_id=proyecto_id)


# GENERAR TEXTO AUTOMÁTICO PARA LA EVALUACIÓN
def generar_texto_evaluacion(rubrica):
    partes = []
    partes.append("El proyecto demuestra una alta originalidad." if rubrica.originalidad >= 4 else "La originalidad del proyecto es aceptable.")
    partes.append("El tema es altamente relevante." if rubrica.relevancia >= 4 else "El tema tiene relevancia moderada.")
    partes.append("Metodología sólida." if rubrica.metodologia >= 4 else "Metodología podría mejorarse.")
    partes.append("Resultados claros." if rubrica.resultados >= 4 else "Resultados necesitan más análisis.")
    return " ".join(partes)


# EVALUACIÓN COMPLETA
@main.route('/evaluation/<int:proyecto_id>', methods=['GET', 'POST'])
@login_required
def evaluation(proyecto_id):
    if current_user.rol != 'evaluador':
        return "No autorizado", 403

    rubrica = Rubrica.query.filter_by(proyecto_id=proyecto_id, evaluador_id=current_user.id).first()
    if not rubrica:
        return "Debe completar la rúbrica primero", 400

    evaluacion = Evaluacion.query.filter_by(proyecto_id=proyecto_id, evaluador_id=current_user.id).first()
    form = EvaluacionForm(obj=evaluacion)

    if form.validate_on_submit():
        if not evaluacion:
            evaluacion = Evaluacion(proyecto_id=proyecto_id, evaluador_id=current_user.id)
            db.session.add(evaluacion)

        form.populate_obj(evaluacion)
        db.session.commit()
        flash('Evaluación guardada con éxito.', 'success')
        return redirect(url_for('main.result', proyecto_id=proyecto_id))

    texto = generar_texto_evaluacion(rubrica)
    return render_template('evaluation.html', form=form, evaluacion=evaluacion, proyecto_id=proyecto_id, proyecto=evaluacion.proyecto if evaluacion else None, texto=texto)


# RESULTADOS
@main.route('/result/<int:proyecto_id>')
@login_required
def result(proyecto_id):
    evaluacion = Evaluacion.query.filter_by(proyecto_id=proyecto_id, evaluador_id=current_user.id).first()
    if not evaluacion:
        return "Evaluación no encontrada", 404
    return render_template('result.html', evaluacion=evaluacion)


# CONFIRMAR EVALUACIÓN
@main.route('/evaluation/confirm/<int:proyecto_id>', methods=['POST'])
@login_required
def confirm_evaluation(proyecto_id):
    evaluacion = Evaluacion.query.filter_by(proyecto_id=proyecto_id, evaluador_id=current_user.id).first()
    if not evaluacion:
        return "Evaluación no encontrada", 404
    evaluacion.confirmada = True
    db.session.commit()
    return redirect(url_for('main.result', proyecto_id=proyecto_id))


# REVISIÓN POR COORDINADOR
@main.route('/revision/<int:proyecto_id>', methods=['GET', 'POST'])
@login_required
def revision(proyecto_id):
    if current_user.rol not in ['coordinador', 'director']:
        return "No autorizado", 403

    evaluacion = Evaluacion.query.filter_by(proyecto_id=proyecto_id).first()
    if not evaluacion or not evaluacion.confirmada:
        return "Evaluación no disponible", 404

    if request.method == 'POST':
        decision = request.form['decision']
        comentario = request.form.get('comentario')
        evaluacion.aprobada = (decision == 'aprobar')
        evaluacion.comentario_revision = comentario
        db.session.commit()
        return redirect(url_for('main.dashboard'))

    return render_template('revision.html', evaluacion=evaluacion, proyecto_id=proyecto_id)


# GENERAR PDF
@main.route('/reporte/<int:evaluacion_id>')
@login_required
def generar_reporte_pdf(evaluacion_id):
    evaluacion = Evaluacion.query.get_or_404(evaluacion_id)
    estudiante = evaluacion.proyecto.estudiante.nombre
    proyecto = evaluacion.proyecto.titulo
    evaluador = evaluacion.evaluador.nombre
    rubrica = {
        "Originalidad": evaluacion.originalidad,
        "Relevancia": evaluacion.relevancia,
        "Metodología": evaluacion.metodologia,
        "Resultados": evaluacion.resultados
    }
    total = sum(rubrica.values())

    html = render_template('reportes/reporte_final.html',
                           estudiante=estudiante,
                           proyecto=proyecto,
                           evaluador=evaluador,
                           rubrica=rubrica,
                           total=total)

    result = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)

    if pisa_status.err:
        return "Error al generar el PDF", 500

    response = make_response(result.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=reporte_final.pdf'
    return response


# NOTIFICACIONES
@main.route("/notificaciones")
@login_required
def notificaciones():
    notis = Notificacion.query.filter_by(usuario_id=current_user.id).order_by(Notificacion.fecha.desc()).all()
    return render_template("notificaciones.html", notis=notis)


# LISTADO DE EVALUACIONES (con filtro opcional)
@main.route('/evaluaciones')
@login_required
def ver_evaluaciones():
    estado = request.args.get('estado')
    query = Evaluacion.query.filter_by(evaluador_id=current_user.id)
    if estado:
        query = query.filter_by(estado=estado)
    evaluaciones = query.all()
    return render_template('evaluaciones/lista.html', evaluaciones=evaluaciones)
