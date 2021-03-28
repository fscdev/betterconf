import os
import typing

from betterconf.caster import AbstractCaster
from betterconf.caster import DEFAULT_CASTER
from betterconf.exceptions import VariableNotFoundError, ImpossibleToCastError
from betterconf.providers import DEFAULT_PROVIDER

_NO_DEFAULT = object()


def is_callable(obj):
    """Checks that object is callable (needed for default values)"""
    return callable(obj)


class Field:
    def __init__(
        self,
        name: typing.Optional[str] = None,
        default: typing.Optional[typing.Any] = _NO_DEFAULT,
        provider: AbstractProvider = DEFAULT_PROVIDER,
        caster: AbstractCaster = DEFAULT_CASTER,
        ignore_caster_error: bool = False,
    ):
        self.name = name
        self._provider = provider
        self._value = None
        self._default = default
        self._caster = caster
        self._ignore_caster_error = ignore_caster_error

    @property
    def value(self):
        if self.name is None:
            raise VariableNotFoundError("no name")
        self._value = self._provider.get(self.name)
        if not self._value:
            if self._default is _NO_DEFAULT:
                raise VariableNotFoundError(self.name)
            if is_callable(self._default):
                return self._default()
            else:
                return self._default
        try:
            casted = self._caster.cast(self._value)

        except ImpossibleToCastError as e:
            if self._ignore_caster_error:
                return e.val

            else:
                raise e

        else:
            return casted


class FieldInfo(typing.NamedTuple):
    name_to_set: str
    obj: Field


class SubConfigInfo(typing.NamedTuple):
    name_to_set: str
    obj: type


def field(
    name: typing.Optional[str] = None,
    default: typing.Optional[typing.Any] = _NO_DEFAULT,
    provider: AbstractProvider = DEFAULT_PROVIDER,
    caster: AbstractCaster = DEFAULT_CASTER,
    ignore_caster_error: bool = False,
) -> Field:
    return Field(name, default, provider, caster, ignore_caster_error)


def is_dunder(name: str) -> bool:
    if name.startswith("__") and name.endswith("__"):
        return True
    else:
        return False


def as_dict(cfg: typing.Union["Config", type]) -> dict:
    """
    config serialization
    :param cfg:
    :return:
    """
    result = dict()
    for i_name in dir(cfg):
        if is_dunder(i_name):
            continue
        i_var = getattr(cfg, i_name)
        if is_callable(i_var):
            continue
        if hasattr(i_var, "__dict__"):
            result[i_name] = as_dict(i_var)
            continue
        result[i_name] = i_var
    return result


def parse_objects(
    obj_to_parse: typing.Union[typing.Type["Config"], "Config"]
) -> typing.List[typing.Union[FieldInfo, SubConfigInfo]]:
    result = []
    for var in dir(obj_to_parse):
        name_to_set = var
        if is_dunder(name_to_set):
            continue
        obj: typing.Any = getattr(obj_to_parse, var)
        if isinstance(obj, Field):
            result.append(FieldInfo(name_to_set=name_to_set, obj=obj))
        elif type(obj) is type:
            result.append(SubConfigInfo(name_to_set=name_to_set, obj=obj))
    return result


class Config:
    _prefix_: typing.Optional[str] = None

    def __init__(self, **to_override):
        self._init_fields(self._prefix_, self, **to_override)

    @classmethod
    def _init_fields(
        cls, path: str, config: typing.Union["Config", type], **to_override
    ):
        """
        Put the value in the configs
        :param path: path to config
        :param config:
        :return:
        """
        config = config() if type(config) is type else config
        path = f"{path}." if path else ""
        result = parse_objects(config)
        for obj in result:
            if obj.name_to_set in to_override:
                setattr(config, obj.name_to_set, to_override.get(obj.name_to_set))
                continue
            elif isinstance(obj, SubConfigInfo):
                _path = f"{path}{obj.name_to_set}".replace(".", "_").upper()
                sub_config = cls._init_fields(_path, obj.obj)
                setattr(config, obj.name_to_set, sub_config)
            else:
                if obj.obj.name is None:
                    obj.obj.name = f"{path}{obj.name_to_set}".replace(".", "_").upper()
                setattr(config, obj.name_to_set, obj.obj.value)
        return config


__all__ = (
    "Config",
    "field",
    "AbstractProvider",
    "EnvironmentProvider",
    "VariableNotFoundError",
)
