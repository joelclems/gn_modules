from sqlalchemy.orm import column_property
from sqlalchemy import func, select, case, exists, and_ , literal_column, cast, column, text
from geonature.utils.env import db
from .. import errors

class SchemaModelColumnProperties():
    '''
    '''
    pass

    def cruved_ownership(self, id_role, id_organism):
        return column_property(
            case(
                [
                    (self.Model().actors.any(id_role=id_role), 1),
                    (self.Model().actors.any(id_organism=id_organism), 2),
                ],
                else_=3
            )
        )

    def column_property_relation_x_n(self, key, column_property_def, Model):
        # a passer en argument

        cp_query = cp_select = self.cp_select(key, column_property_def, Model)

        if column_property_def.get('relation_key'):
            cp_where_conditions = self.column_property_util_relation_where_conditions(key, column_property_def , Model)
            cp_query = cp_select.where(cp_where_conditions)

        return column_property(cp_query)

    def cp_select(self, key, column_property_def, Model):

        if column_property_def.get('column_property') == 'nb':
            return select([func.count('*')])

        if column_property_def.get('column_property') == 'has':
            return exists()

        if column_property_def.get('column_property') == 'label':
            # TODO communes <area_name> (<area_code[:2]>) ??
            # relation = getattr(Model, column_property_def['relation_key'])
            # relation_entity = relation.mapper.entity
            label_key = '.'.join([column_property_def['relation_key'], column_property_def['label_key']])
            relation_label, _ = self.custom_getattr(Model, label_key)
            return select(
                [
                    func.string_agg(
                        cast(
                            relation_label,
                            db.String
                        ),
                        literal_column("', '")
                    )
                ]
            )

        if column_property_def.get('column_property') == 'st_x':
            return func.st_x(getattr(Model, column_property_def['key']))

        if column_property_def.get('column_property') == 'st_y':
            return func.st_y(getattr(Model, column_property_def['key']))


        if column_property_def.get('column_property') == 'type_complement':
            s_complement = self.cls(self.attr('meta.schema_complement'))
            query, _ = s_complement.get_list()
            complements_case = []
            for complement in query.all():
                if hasattr(Model, f'has_{complement.relation_name}'):
                    complements_case.append((getattr(Model, f'has_{complement.relation_name}'), complement.complement_name))

            return case(
                complements_case,
                else_=None
            )

            # return func.st_y(getattr(Model, column_property_def['key']))


        raise errors.SchemaModelColumnPropertyError(
            'La column_property {} {} est mal définie'
            .format(self.schema_name(), key)
        )

    def column_property_util_relation_where_conditions(self, key, column_property_def, Model):

        relation, _ = self.custom_getattr(Model, column_property_def['relation_key'])
        conditions = relation
        if column_property_def.get('filters') is not None:
            condition_filters, conditions = self.process_filter_array(
                relation.mapper.entity,
                column_property_def.get('filters'),
                query=conditions,
                condition=True
            )
            conditions = and_(
                conditions,
                condition_filters
            )

        return conditions

    def process_column_property_model(self, key, column_property_def, Model):

        # ici l'ordre import par ex type_complement après has
        return self.column_property_relation_x_n(key, column_property_def, Model)

