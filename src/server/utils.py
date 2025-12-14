from pydantic import field_validator


def validate_null_item(v):
    if not v:
        return None
    return v


def nullable_field(*field_names):
    def decorator(cls):
        for field_name in field_names:
            validator = field_validator(field_name, mode='before')(validate_null_item)
            validator_name = f"_validate_{field_name}"
            setattr(cls, validator_name, validator)
        return cls

    return decorator
