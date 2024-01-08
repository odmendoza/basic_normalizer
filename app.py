#!/usr/bin/python3.11.6

# -*- coding: utf-8 -*-
import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask_heroku import Heroku

UPLOAD_FOLDER = 'files/'
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

# Settings
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('universal_table',
                                    filename=filename))
    return render_template('upload_file.html')


@app.route('/universal_table<filename>', )
def universal_table(filename):
    path = 'files/'
    file = pd.ExcelFile(path + filename)

    sheets = file.sheet_names
    table = file.parse(sheets[0])

    table_attributes = table.columns.values

    dataframe = pd.DataFrame.to_html(table, index=False)
    dataframe = dataframe.replace(
        'class="dataframe"', 'class="table table-sm"')

    return render_template('universal_table.html', dataframe=dataframe, attributes=table_attributes, document=filename)


@app.route('/1_nf', methods=['GET', 'POST'])
def first_nf():
    if request.method == 'POST':
        table_pk = request.form.getlist('attribute')
        if len(table_pk) == 0:
            return '''
                <h3> No ha seleccionado una clave primaria </h3>
                <button type="button" class="btn btn-primary" onclick="goBack()">Volver atrás</button>
                <script>
                    function goBack() {
                      window.history.back();
                      }
                      </script>'''
        else:
            attributes = request.form.get('attributes')
            attributes = attributes.replace(' ', ', ')
            attributes = attributes.replace('\n', '')
            attributes = attributes.replace('\r', '')
            original_table = request.form.get('original_table')
            document = request.form.get('original_table')

            attributes = attributes.replace('[', '')
            attributes = attributes.replace(']', '')
            attributes = attributes.replace("'", '')
            attributes = attributes.replace(' ', '')
            attributes = list(attributes.split(','))
            not_key = attributes
            for i in table_pk:
                not_key.remove(i)

            data = pd.read_html(original_table, header=0)[0]
            data = pd.DataFrame(data)

            pk_is_valid = any(data.duplicated(subset=table_pk))
            if not pk_is_valid:
                return render_template('1_nf.html',
                                       primary_key=table_pk,
                                       table=original_table,
                                       attributes=attributes,
                                       not_key=not_key,
                                       data=[{'name': 'Coma'}, {'name': 'Punto y coma'}])
            else:
                return '''
                <h3> Su clave primaria no es válida </h3>
                <button type="button" class="btn btn-primary" onclick="goBack()">Volver atrás</button>
                <script>
                    function goBack() {
                      window.history.back();
                      }
                </script>'''


@app.route('/2_nf', methods=['GET', 'POST'])
def second_nf():
    if request.method == 'POST':
        primary_key = request.form.get('primary_key')
        primary_key = primary_key.replace('[', '')
        primary_key = primary_key.replace(']', '')
        primary_key = primary_key.replace("'", '')
        primary_key = primary_key.replace(' ', '')
        primary_key = list(primary_key.split(','))

        not_key = request.form.get('not_key')
        not_key = not_key.replace('[', '')
        not_key = not_key.replace(']', '')
        not_key = not_key.replace("'", '')
        not_key = not_key.replace(' ', '')
        not_key = list(not_key.split(','))

        attributes = request.form.get('attributes')
        attributes = attributes.replace('[', '')
        attributes = attributes.replace(']', '')
        attributes = attributes.replace("'", '')
        attributes = attributes.replace(' ', '')
        attributes = list(attributes.split(','))

        separator = request.form.get('comp_select')
        if separator == 'Coma':
            sep_val = ','
        if separator == 'Punto y coma':
            sep_val = ';'

        not_atomic = request.form.getlist('attribute')

        table = request.form.get('table')
        table = table.replace('class="table table-sm"', 'class="dataframe"')

        data = pd.read_html(table, header=0)[0]
        data = pd.DataFrame(data)

        tables = []

        table_without_not_atomic = data
        table_without_not_atomic = table_without_not_atomic.drop(
            columns=not_atomic)
        table_without_not_atomic = pd.DataFrame.to_html(
            table_without_not_atomic, index=False)
        table_without_not_atomic = table_without_not_atomic.replace(
            'class="dataframe"', 'class="table table-sm"')
        # tables.append(table_without_not_atomic)

        # data_pk = data[primary_key] # Asigna columnas vacias de la clave primaria
        # Asigna columnas vacias de la clave primaria
        data_pk = data[primary_key + attributes]

        for i in not_atomic:
            table_1nf = data_pk
            table_1nf[i] = data[i]
            # table_1nf = table_1nf.dropna()
            length = table_1nf[i].count()
            j = 0
            while j < length:
                split_row = table_1nf.iloc[j][i].split(sep_val)
                if len(split_row) > 1:
                    for k in split_row:
                        row_rp = table_1nf.iloc[j]
                        row_rp[i] = k
                        table_1nf = table_1nf.append(row_rp, ignore_index=True)
                    table_1nf = table_1nf.drop(table_1nf.index[j])
                j = j + 1
            table_1nf = pd.DataFrame.to_html(table_1nf, index=False)
            table_1nf = table_1nf.replace(
                'class="dataframe"', 'class="table table-sm"')
            tables.append(table_1nf)

        attributes_not_key = not_key
        for nt in not_atomic:
            attributes_not_key.remove(nt)

        return render_template('2_nf.html', tables=tables, primary_key=primary_key, attributes_not_key=attributes_not_key,
                               data=[{'name': 'SI'}, {'name': 'NO'}])
    else:
        return '<h3> No ha seleccionado atributos no clave con datos no atómicos </h3>'


@app.route('/3_nf', methods=['GET', 'POST'])
def thrid_nf():
    if request.method == 'POST':
        parcial_dependence = request.form.get('comp_select')
        tables = request.form.get('tables')
        tables = tables.replace("[", '')
        tables = tables.replace("]", '')
        tables = tables.replace('\n', '')
        tables = tables.replace('\\n', '')
        tables = tables.replace("'", '')
        tables = list(tables.split(','))

        p_k = request.form.get('primary_key')
        p_k = p_k.replace('[', '')
        p_k = p_k.replace(']', '')
        p_k = p_k.replace("'", '')
        p_k = p_k.replace(' ', '')
        p_k = list(p_k.split(','))

        n_k = request.form.get('attributes_not_key')
        n_k = n_k.replace('[', '')
        n_k = n_k.replace(']', '')
        n_k = n_k.replace("'", '')
        n_k = n_k.replace(' ', '')
        n_k = list(n_k.split(','))

        if parcial_dependence == 'NO':
            return render_template('3_nf.html', tables=tables, p_k=p_k, n_k=n_k, data=[{'name': 'SI'}, {'name': 'NO'}])
        else:
            table = request.form.get('tables')
            table = table.replace(
                'class="table table-sm"', 'class="dataframe"')
            i = 0
            all_tables = {}
            while i < len(tables):
                data = pd.read_html(table, header=0)[i]
                data = pd.DataFrame(data)
                all_tables[i] = data
                if i == 0:
                    table_1rt = data
                i = i + 1

            partial_pk = request.form.getlist('pk')
            attr_partial_pk = request.form.getlist('ank')
            new_table = pd.DataFrame()
            for ppk in partial_pk:
                new_table[ppk] = table_1rt[ppk]
            for appk in attr_partial_pk:
                new_table[appk] = table_1rt[appk]
            all_tables[i] = new_table
            final_tables = []
            for j in all_tables:
                if j == 0:
                    all_tables[j] = all_tables[j].drop(columns=attr_partial_pk)
                all_tables[j] = pd.DataFrame.drop_duplicates(all_tables[j])
                all_tables[j] = pd.DataFrame.to_html(
                    all_tables[j], index=False)
                all_tables[j] = all_tables[j].replace(
                    'class="dataframe"', 'class="table table-sm"')
                final_tables.append(all_tables[j])

            return render_template('3_nf.html', tables=final_tables, p_k=p_k, n_k=n_k, data=[{'name': 'SI'}, {'name': 'NO'}])


@app.route('/normalized', methods=['GET', 'POST'])
def normalized():
    if request.method == 'POST':
        parcial_dependence = request.form.get('comp_select')
        tables = request.form.get('tables')
        tables = tables.replace("[", '')
        tables = tables.replace("]:ok_hand:", '')
        tables = tables.replace('\n', '')
        tables = tables.replace('\\n', '')
        tables = tables.replace("'", '')
        tables = list(tables.split(','))

        p_k = request.form.get('primary_key')
        p_k = p_k.replace('[', '')
        p_k = p_k.replace(']', '')
        p_k = p_k.replace("'", '')
        p_k = p_k.replace(' ', '')
        p_k = list(p_k.split(','))

        n_k = request.form.get('attributes_not_key')
        n_k = n_k.replace('[', '')
        n_k = n_k.replace(']', '')
        n_k = n_k.replace("'", '')
        n_k = n_k.replace(' ', '')
        n_k = list(n_k.split(','))

        if parcial_dependence == 'NO':
            return render_template('normalized_table.html', tables=tables, p_k=p_k, n_k=n_k)
        else:
            table = request.form.get('tables')
            table = table.replace(
                'class="table table-sm"', 'class="dataframe"')
            i = 0
            all_tables = {}
            while i < len(tables):
                data = pd.read_html(table, header=0)[i]
                data = pd.DataFrame(data)
                all_tables[i] = data
                if i == 0:
                    table_1rt = data
                i = i + 1

            determinants = request.form.getlist('nk')
            dependents = request.form.getlist('dnk')
            new_table = pd.DataFrame()
            for det in determinants:
                new_table[det] = table_1rt[det]
            for dep in dependents:
                new_table[dep] = table_1rt[dep]
            all_tables[i] = new_table
            final_tables = []
            for j in all_tables:
                if j == 0:
                    all_tables[j] = all_tables[j].drop(columns=dependents)
                all_tables[j] = pd.DataFrame.drop_duplicates(all_tables[j])
                all_tables[j] = pd.DataFrame.to_html(
                    all_tables[j], index=False)
                all_tables[j] = all_tables[j].replace(
                    'class="dataframe"', 'class="table table-sm"')
                final_tables.append(all_tables[j])

            return render_template('normalized_table.html', tables=final_tables, p_k=p_k, n_k=n_k)


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run()
