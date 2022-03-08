
from flask import Blueprint, request, jsonify, g, current_app
from gn_modules.module import ModuleMethods
from .commands import commands
from .schema import SchemaMethods, errors
from utils_flask_sqla.generic import GenericTable
from geonature.utils.env import db
from utils_flask_sqla.generic import serializeQuery
from utils_flask_sqla.response import to_csv_resp

import datetime

blueprint = Blueprint('modules', __name__)

blueprint.cli.short_help = 'Commandes pour l''administration du module MODULES'
for cmd in commands:
    blueprint.cli.add_command(cmd)


try:
    SchemaMethods.init_schemas()
    SchemaMethods.init_routes(blueprint)

except errors.SchemaError as e:
    print("Erreur de chargement des schemas: {}".format(e))

# !!! attention restreindre les droits !!!

@blueprint.route('/modules_config', methods=['GET'])
def api_modules_config():

    return jsonify(ModuleMethods.modules_config())

@blueprint.route('/<module_code>/export/<export_code>')
def api_modules_export(module_code, export_code):
    '''
        route d'export pour les modules
        TODO le faire avec les schémas filtres etc..
    '''

    module_config = ModuleMethods.module_config(module_code)

    export = None

    for export_ in module_config.get('exports', []):
        if export_.get('export_code') == export_code:
            export = export_

    if not export:
        return (
            f"La vue pour l'export du module {module_code} de code {export_code} n'a pas été trouvée",
            500
        )

    view = export.get('export_view')

    view = GenericTable(
        tableName=view.split(".")[1],
        schemaName=view.split(".")[0],
        engine=db.engine
    )

    columns = view.tableDef.columns
    q = db.session.query(*columns)
    data = q.all()

    t = datetime.datetime.now().strftime("%Y_%m_%d_%Hh%Mm%S")
    filename = f'export_csv_{module_code}_{export_code}_{t}.csv'


    return to_csv_resp(
        filename,
        data=serializeQuery(data, q.column_descriptions),
        separator=";",
        columns=[c.key for c in columns], # Exclude the geom column from CSV
    )
