from types import NoneType

import orjson as json
from pydantic import BaseModel as PydanticBaseModel
from pydantic._internal._model_construction import ModelMetaclass

from panther import status
from panther.db.cursor import Cursor

ResponseDataTypes = list | tuple | set | Cursor | dict | int | float | str | bool | bytes | NoneType | ModelMetaclass
IterableDataTypes = list | tuple | set | Cursor


class Response:
    content_type = 'application/json'

    def __init__(
        self,
        data: ResponseDataTypes = None,
        headers: dict | None = None,
        status_code: int = status.HTTP_200_OK,
    ):
        """
        :param data: should be an instance of ResponseDataTypes
        :param headers: should be dict of headers
        :param status_code: should be int
        """
        self.data = self.prepare_data(data=data)
        self.headers = self.prepare_headers(headers=headers)
        self.status_code = self.check_status_code(status_code=status_code)

    @property
    def body(self) -> bytes:
        if isinstance(self.data, bytes):
            return self.data

        if self.data is None:
            return b''
        return json.dumps(self.data)

    def prepare_headers(self, headers: dict | None) -> dict:
        return {
            'Content-Type': self.content_type,
            'Content-Length': len(self.body),
            'Access-Control-Allow-Origin': '*',
        } | (headers or {})

    def prepare_data(self, data: any):
        """Make sure the response data is only ResponseDataTypes or Iterable of ResponseDataTypes"""
        if isinstance(data, (int | float | str | bool | bytes | NoneType)):
            return data

        elif isinstance(data, dict):
            return {key: self.prepare_data(value) for key, value in data.items()}

        elif issubclass(type(data), PydanticBaseModel):
            return data.model_dump()

        elif isinstance(data, IterableDataTypes):
            return [self.prepare_data(d) for d in data]

        else:
            msg = f'Invalid Response Type: {type(data)}'
            raise TypeError(msg)

    @classmethod
    def check_status_code(cls, status_code: any):
        if not isinstance(status_code, int):
            error = f'Response "status_code" Should Be "int". ("{status_code}" is {type(status_code)})'
            raise TypeError(error)
        return status_code

    @classmethod
    def apply_output_model(cls, data: any, /, output_model: ModelMetaclass):
        """This method is called in API.__call__"""
        # Dict
        if isinstance(data, dict):
            return output_model(**data).model_dump()

        # Iterable
        if isinstance(data, IterableDataTypes):
            return [cls.apply_output_model(d, output_model=output_model) for d in data]

        # Str | Bool | Bytes
        msg = 'Type of Response data is not match with `output_model`.\n*hint: You may want to remove `output_model`'
        raise TypeError(msg)

    def __str__(self):
        if len(data := str(self.data)) > 30:
            data = f'{data:.27}...'
        return f'Response(status_code={self.status_code}, data={data})'

    __repr__ = __str__


class HTMLResponse(Response):
    content_type = 'text/html; charset=utf-8'

    @property
    def body(self) -> bytes:
        if isinstance(self.data, bytes):
            return self.data
        return self.data.encode()


class PlainTextResponse(Response):
    content_type = 'text/plain; charset=utf-8'

    @property
    def body(self) -> bytes:
        if isinstance(self.data, bytes):
            return self.data
        return self.data.encode()
