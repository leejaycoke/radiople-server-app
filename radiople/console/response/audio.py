from marshmallow import Schema
from marshmallow import fields


class Audio(Schema):

    id = fields.Integer()
    filename = fields.String()
    display_length = fields.String()
    display_size = fields.String()
    upload_filename = fields.String()


class AudioResponse(Audio):

    pass


class AudioList(Schema):

    item = fields.Nested(AudioResponse, many=True)
