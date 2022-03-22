from panther.db import BaseModel
from pydantic import ValidationError
from panther.request import Request
from panther.exceptions import APIException


class API:

    @classmethod
    def validate_input(cls, data: dict, input_model):
        if input_model:
            try:
                input_model(**data)
            except ValidationError as validation_error:
                error = {}
                for e in validation_error.errors():
                    error[e['loc'][0]] = e['msg']
                raise APIException(status_code=400, detail=error)

    @classmethod
    def clean_output(cls, data, output_model):
        if output_model is None:
            return data

        if issubclass(type(data), BaseModel):
            _data = output_model(**data.dict()).dict()
        elif isinstance(data, dict):
            _data = output_model(**data).dict()
        elif isinstance(data, list) or isinstance(data, tuple):
            _data = [output_model(**d).dict() for d in data]
        elif isinstance(data, str) or isinstance(data, bool) or isinstance(data, set):
            raise TypeError('Type of Response data is not match with output_model. '
                            '\n*hint: You may want to pass None to output_model')
        else:
            raise TypeError(f"Type of Response 'data' is not valid.")
        return _data

    @classmethod
    def post(cls, input_model=None, output_model=None):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                request: Request = kwargs['request']
                cls.validate_input(data=request.data, input_model=input_model)
                response = await func(request=request)
                data = cls.clean_output(data=response._data, output_model=output_model)
                response.set_data(data)
                return response
            return wrapper
        return decorator

    @classmethod
    def put(cls, input_model=None, output_model=None):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                request: Request = kwargs['request']
                cls.validate_input(data=request.data, input_model=input_model)
                response = await func(request=request)
                data = cls.clean_output(data=response._data, output_model=output_model)
                response.set_data(data)
                return response
            return wrapper
        return decorator

    @classmethod
    def get(cls, output_model):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                response = await func(*args, **kwargs)
                data = cls.clean_output(data=response._data, output_model=output_model)
                response.set_data(data)
                return response
            return wrapper
        return decorator

    @classmethod
    def delete(cls, output_model=None):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                response = await func(*args, **kwargs)
                data = cls.clean_output(data=response._data, output_model=output_model)
                response.set_data(data)
                return response
            return wrapper
        return decorator
