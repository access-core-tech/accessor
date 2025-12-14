import json
import base64


def dict_to_admin_credentials(data_dict: dict) -> str:
    """
    Конвертирует словарь в base64 строку для admin_credentials
    """
    try:
        json_str = json.dumps(data_dict, ensure_ascii=False)

        base64_bytes = base64.b64encode(json_str.encode('utf-8'))
        base64_str = base64_bytes.decode('utf-8')

        return base64_str
    except Exception as e:
        raise ValueError(f"Ошибка при конвертации: {e}")


def admin_credentials_to_dict(base64_str: str) -> dict:
    """
    Декодирует base64 строку обратно в словарь
    """
    try:
        json_bytes = base64.b64decode(base64_str)
        json_str = json_bytes.decode('utf-8')

        data_dict = json.loads(json_str)

        return data_dict
    except Exception as e:
        raise ValueError(f"Ошибка при декодировании: {e}")


a = dict_to_admin_credentials(
    {
        "user": 'postgres',
        'password': 'postgres',
        'host': 'localhost',
        'port': 5432,
    }
)
print(a)
