"""
Protocol Buffer Codec Utilities
Peer Reviewed: GPT-5 Pro (designed), Pending pairwise validation
"""

from __future__ import annotations

from typing import Type, TypeVar
from google.protobuf.message import Message
from google.protobuf import json_format
from .errors import SerializationError, DeserializationError

T = TypeVar("T", bound=Message)

CONTENT_TYPE_PROTO = "application/x-protobuf"
HEADER_MSG_TYPE = "message-type"


def encode_protobuf(msg: Message) -> bytes:
    """
    Encode protobuf message to bytes.
    
    Args:
        msg: Protobuf message to encode
        
    Returns:
        Serialized bytes
        
    Raises:
        SerializationError: If encoding fails
    """
    try:
        return msg.SerializeToString(deterministic=True)
    except Exception as e:
        raise SerializationError(str(e)) from e


def decode_protobuf(data: bytes, cls: Type[T]) -> T:
    """
    Decode bytes to protobuf message.
    
    Args:
        data: Serialized bytes
        cls: Protobuf message class
        
    Returns:
        Deserialized protobuf message
        
    Raises:
        DeserializationError: If decoding fails
    """
    try:
        obj = cls()
        obj.ParseFromString(data)
        return obj
    except Exception as e:
        raise DeserializationError(str(e)) from e


def protobuf_to_json(msg: Message) -> str:
    """
    Convert protobuf message to JSON string.
    
    Args:
        msg: Protobuf message
        
    Returns:
        JSON string
    """
    return json_format.MessageToJson(msg, preserving_proto_field_name=True)


def json_to_protobuf(json_str: str, cls: Type[T]) -> T:
    """
    Convert JSON string to protobuf message.
    
    Args:
        json_str: JSON string
        cls: Protobuf message class
        
    Returns:
        Protobuf message
    """
    obj = cls()
    return json_format.Parse(json_str, obj)

