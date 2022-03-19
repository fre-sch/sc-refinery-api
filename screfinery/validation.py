class InvalidDataError(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors


def schema_validate(schema_validator, resource_name, data):
    errors = list(schema_validator.iter_errors(data))
    if errors:
        raise InvalidDataError(f"{resource_name} data not valid", errors)


def _resource_validator(resource_name, validator_spec):
    def resource_validator(config, data, case):
        validator = validator_spec.get(case)
        if validator is not None:
            schema_validate(validator, resource_name, data)
        data.pop("created", None)
        data.pop("updated", None)
        data.pop("id", None)
        return data
    return resource_validator