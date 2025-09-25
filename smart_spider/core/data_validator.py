import re
import json
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
from urllib.parse import urlparse
import email.utils

from smart_spider.core.logger import logger
from smart_spider.core.exceptions import ValidationException


class DataValidator:
    """数据验证器 - 验证和清洗爬取的数据"""

    def __init__(self):
        # 预定义的正则表达式模式
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            'url': re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'),
            'ip': re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'),
            'date': re.compile(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}'),
            'time': re.compile(r'\d{1,2}:\d{2}:\d{2}'),
            'price': re.compile(r'\$?\d+(?:,\d{3})*(?:\.\d{2})?'),
            'chinese_phone': re.compile(r'1[3-9]\d{9}'),
            'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            'zipcode': re.compile(r'\b\d{5}(?:-\d{4})?\b'),
            'hex_color': re.compile(r'#?[0-9A-Fa-f]{6}'),
            'guid': re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'),
        }

        # 数据类型验证函数
        self.validators = {
            'email': self.validate_email,
            'url': self.validate_url,
            'phone': self.validate_phone,
            'date': self.validate_date,
            'number': self.validate_number,
            'integer': self.validate_integer,
            'float': self.validate_float,
            'boolean': self.validate_boolean,
            'json': self.validate_json,
            'array': self.validate_array,
            'object': self.validate_object,
            'string': self.validate_string,
            'ip_address': self.validate_ip_address,
            'credit_card': self.validate_credit_card,
            'chinese_phone': self.validate_chinese_phone,
            'price': self.validate_price,
            'zipcode': self.validate_zipcode,
            'hex_color': self.validate_hex_color,
        }

        # 清洗函数
        self.cleaners = {
            'trim': self.clean_trim,
            'remove_whitespace': self.clean_remove_whitespace,
            'remove_html': self.clean_remove_html,
            'normalize_whitespace': self.clean_normalize_whitespace,
            'to_lower': self.clean_to_lower,
            'to_upper': self.clean_to_upper,
            'remove_special_chars': self.clean_remove_special_chars,
            'normalize_unicode': self.clean_normalize_unicode,
            'extract_numbers': self.clean_extract_numbers,
            'extract_letters': self.clean_extract_letters,
            'remove_numbers': self.clean_remove_numbers,
            'capitalize': self.clean_capitalize,
            'title_case': self.clean_title_case,
        }

    def validate_email(self, value: str) -> bool:
        """验证邮箱地址"""
        if not value or not isinstance(value, str):
            return False
        return bool(self.patterns['email'].match(value.strip()))

    def validate_url(self, value: str) -> bool:
        """验证URL地址"""
        if not value or not isinstance(value, str):
            return False
        try:
            result = urlparse(value.strip())
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def validate_phone(self, value: str) -> bool:
        """验证电话号码"""
        if not value or not isinstance(value, str):
            return False
        return bool(self.patterns['phone'].match(value.strip()))

    def validate_chinese_phone(self, value: str) -> bool:
        """验证中国手机号"""
        if not value or not isinstance(value, str):
            return False
        return bool(self.patterns['chinese_phone'].match(value.strip()))

    def validate_date(self, value: str) -> bool:
        """验证日期格式"""
        if not value or not isinstance(value, str):
            return False
        return bool(self.patterns['date'].match(value.strip()))

    def validate_number(self, value: Any) -> bool:
        """验证数字"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def validate_integer(self, value: Any) -> bool:
        """验证整数"""
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False

    def validate_float(self, value: Any) -> bool:
003e bool:
        """验证浮点数"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def validate_boolean(self, value: Any) -> bool:
        """验证布尔值"""
        if isinstance(value, bool):
            return True
        if isinstance(value, str):
            return value.lower() in ['true', 'false', '1', '0', 'yes', 'no']
        if isinstance(value, (int, float)):
            return value in [0, 1]
        return False

    def validate_json(self, value: str) -> bool:
        """验证JSON格式"""
        if not value or not isinstance(value, str):
            return False
        try:
            json.loads(value)
            return True
        except json.JSONDecodeError:
            return False

    def validate_array(self, value: Any) -> bool:
        """验证数组"""
        return isinstance(value, (list, tuple))

    def validate_object(self, value: Any) -> bool:
        """验证对象"""
        return isinstance(value, dict)

    def validate_string(self, value: Any) -> bool:
        """验证字符串"""
        return isinstance(value, str)

    def validate_ip_address(self, value: str) -> bool:
        """验证IP地址"""
        if not value or not isinstance(value, str):
            return False
        return bool(self.patterns['ip'].match(value.strip()))

    def validate_credit_card(self, value: str) -> bool:
        """验证信用卡号"""
        if not value or not isinstance(value, str):
            return False
        return bool(self.patterns['credit_card'].match(value.strip()))

    def validate_price(self, value: str) -> bool:
        """验证价格格式"""
        if not value or not isinstance(value, str):
            return False
        return bool(self.patterns['price'].match(value.strip()))

    def validate_zipcode(self, value: str) -> bool:
        """验证邮政编码"""
        if not value or not isinstance(value, str):
            return False
        return bool(self.patterns['zipcode'].match(value.strip()))

    def validate_hex_color(self, value: str) -> bool:
        """验证十六进制颜色"""
        if not value or not isinstance(value, str):
            return False
        return bool(self.patterns['hex_color'].match(value.strip()))

    def clean_trim(self, value: str) -> str:
        """去除首尾空格"""
        return value.strip() if isinstance(value, str) else str(value).strip()

    def clean_remove_whitespace(self, value: str) -> str:
        """移除所有空白字符"""
        if not isinstance(value, str):
            value = str(value)
        return re.sub(r'\s+', '', value)

    def clean_remove_html(self, value: str) -> str:
        """移除HTML标签"""
        if not isinstance(value, str):
            value = str(value)
        clean = re.compile(r'<.*?>')
        return clean.sub('', value)

    def clean_normalize_whitespace(self, value: str) -> str:
        """标准化空白字符"""
        if not isinstance(value, str):
            value = str(value)
        return re.sub(r'\s+', ' ', value).strip()

    def clean_to_lower(self, value: str) -> str:
        """转换为小写"""
        return str(value).lower()

    def clean_to_upper(self, value: str) -> str:
        """转换为大写"""
        return str(value).upper()

    def clean_remove_special_chars(self, value: str) -> str:
        """移除特殊字符"""
        if not isinstance(value, str):
            value = str(value)
        return re.sub(r'[^\w\s\-_.@]', '', value)

    def clean_normalize_unicode(self, value: str) -> str:
        """标准化Unicode字符"""
        if not isinstance(value, str):
            value = str(value)
        import unicodedata
        return unicodedata.normalize('NFKC', value)

    def clean_extract_numbers(self, value: str) -> str:
        """提取数字"""
        if not isinstance(value, str):
            value = str(value)
        numbers = re.findall(r'\d+', value)
        return ''.join(numbers)

    def clean_extract_letters(self, value: str) -> str:
        """提取字母"""
        if not isinstance(value, str):
            value = str(value)
        letters = re.findall(r'[a-zA-Z]', value)
        return ''.join(letters)

    def clean_remove_numbers(self, value: str) -> str:
        """移除数字"""
        if not isinstance(value, str):
            value = str(value)
        return re.sub(r'\d+', '', value)

    def clean_capitalize(self, value: str) -> str:
        """首字母大写"""
        return str(value).capitalize()

    def clean_title_case(self, value: str) -> str:
        """标题格式"""
        return str(value).title()

    def validate_field(
        self,
        field_name: str,
        value: Any,
        field_type: str = "string",
        required: bool = True,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        pattern: Optional[str] = None,
        custom_validator: Optional[Callable] = None,
        cleaners: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """验证单个字段"""
        result = {
            'field': field_name,
            'original_value': value,
            'cleaned_value': value,
            'is_valid': True,
            'errors': [],
            'warnings': []
        }

        try:
            # 数据清洗
            if cleaners:
                cleaned_value = value
                for cleaner_name in cleaners:
                    if cleaner_name in self.cleaners:
                        try:
                            cleaned_value = self.cleaners[cleaner_name](cleaned_value)
                        except Exception as e:
                            result['warnings'].append(f"清洗器 {cleaner_name} 失败: {str(e)}")
                result['cleaned_value'] = cleaned_value
                value = cleaned_value

            # 必填检查
            if required and (value is None or value == ''):
                result['is_valid'] = False
                result['errors'].append(f"字段 {field_name} 是必填项")
                return result

            # 可选字段为空时跳过其他验证
            if not required and (value is None or value == ''):
                return result

            # 类型验证
            if field_type in self.validators:
                is_valid = self.validators[field_type](value)
                if not is_valid:
                    result['is_valid'] = False
                    result['errors'].append(f"字段 {field_name} 类型验证失败: 期望 {field_type}")
                    return result

            # 长度验证
            if isinstance(value, str):
                if min_length is not None and len(value) \u003c min_length:
                    result['is_valid'] = False
                    result['errors'].append(f"字段 {field_name} 长度不能少于 {min_length}")

                if max_length is not None and len(value) \u003e max_length:
                    result['is_valid'] = False
                    result['errors'].append(f"字段 {field_name} 长度不能超过 {max_length}")

            # 数值范围验证
            if field_type in ['number', 'integer', 'float']:
                try:
                    num_value = float(value) if field_type == 'float' else int(value)
                    if min_value is not None and num_value \u003c min_value:
                        result['is_valid'] = False
                        result['errors'].append(f"字段 {field_name} 数值不能小于 {min_value}")

                    if max_value is not None and num_value \u003e max_value:
                        result['is_valid'] = False
                        result['errors'].append(f"字段 {field_name} 数值不能大于 {max_value}")
                except (ValueError, TypeError):
                    result['is_valid'] = False
                    result['errors'].append(f"字段 {field_name} 不是有效的数值")

            # 正则表达式验证
            if pattern:
                regex = re.compile(pattern)
                if not regex.match(str(value)):
                    result['is_valid'] = False
                    result['errors'].append(f"字段 {field_name} 格式不符合要求")

            # 自定义验证器
            if custom_validator:
                try:
                    custom_result = custom_validator(value)
                    if not custom_result:
                        result['is_valid'] = False
                        result['errors'].append(f"字段 {field_name} 自定义验证失败")
                except Exception as e:
                    result['warnings'].append(f"自定义验证器异常: {str(e)}")

        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"验证过程异常: {str(e)}")
            logger.error(f"字段验证异常: {field_name} - {str(e)}")

        return result

    def validate_data(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """验证整个数据对象"""
        results = {
            'is_valid': True,
            'field_results': {},
            'errors': [],
            'warnings': [],
            'cleaned_data': {}
        }

        try:
            for field_name, field_config in schema.items():
                value = data.get(field_name)
                field_result = self.validate_field(
                    field_name=field_name,
                    value=value,
                    **field_config
                )

                results['field_results'][field_name] = field_result

                if not field_result['is_valid']:
                    results['is_valid'] = False
                    results['errors'].extend(field_result['errors'])

                if field_result['warnings']:
                    results['warnings'].extend(field_result['warnings'])

                # 收集清洗后的数据
                results['cleaned_data'][field_name] = field_result['cleaned_value']

            # 检查必填字段
            for field_name, field_config in schema.items():
                if field_config.get('required', True) and field_name not in data:
                    results['is_valid'] = False
                    results['errors'].append(f"缺少必填字段: {field_name}")

        except Exception as e:
            results['is_valid'] = False
            results['errors'].append(f"数据验证过程异常: {str(e)}")
            logger.error(f"数据验证异常: {str(e)}")

        return results

    def extract_data_by_pattern(
        self,
        text: str,
        pattern_type: str,
        return_all: bool = True
    ) -> Union[str, List[str], None]:
        """根据模式提取数据"""
        try:
            if pattern_type not in self.patterns:
                logger.warning(f"未知的模式类型: {pattern_type}")
                return None

            pattern = self.patterns[pattern_type]
            matches = pattern.findall(text)

            if not matches:
                return None

            if return_all:
                return list(set(matches))  # 去重
            else:
                return matches[0] if matches else None

        except Exception as e:
            logger.error(f"模式提取失败: {pattern_type} - {str(e)}")
            return None

    def clean_data_batch(
        self,
        data: List[Dict[str, Any]],
        cleaning_rules: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """批量清洗数据"""
        cleaned_data = []

        for item in data:
            cleaned_item = {}
            for field, cleaners in cleaning_rules.items():
                value = item.get(field, '')
                cleaned_value = value

                for cleaner_name in cleaners:
                    if cleaner_name in self.cleaners:
                        try:
                            cleaned_value = self.cleaners[cleaner_name](cleaned_value)
                        except Exception as e:
                            logger.warning(f"批量清洗失败: {field} - {cleaner_name} - {str(e)}")

                cleaned_item[field] = cleaned_value

            # 保留未清洗的字段
            for field, value in item.items():
                if field not in cleaning_rules:
                    cleaned_item[field] = value

            cleaned_data.append(cleaned_item)

        return cleaned_data

    def get_validation_stats(self) -> Dict[str, Any]:
        """获取验证统计信息"""
        return {
            'available_validators': list(self.validators.keys()),
            'available_cleaners': list(self.cleaners.keys()),
            'available_patterns': list(self.patterns.keys())
        }


# 全局验证器实例
data_validator = DataValidator()


def validate_field_value(
    field_name: str,
    value: Any,
    field_type: str = "string",
    required: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """快捷函数 - 验证单个字段"""
    return data_validator.validate_field(
        field_name=field_name,
        value=value,
        field_type=field_type,
        required=required,
        **kwargs
    )


def validate_data_object(
    data: Dict[str, Any],
    schema: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """快捷函数 - 验证数据对象"""
    return data_validator.validate_data(data, schema)


def extract_data_from_text(
    text: str,
    pattern_type: str,
    return_all: bool = True
) -> Union[str, List[str], None]:
    """快捷函数 - 从文本提取数据"""
    return data_validator.extract_data_by_pattern(text, pattern_type, return_all)


def clean_data_with_rules(
    data: List[Dict[str, Any]],
    cleaning_rules: Dict[str, List[str]]
) -> List[Dict[str, Any]]:
    """快捷函数 - 批量清洗数据"""
    return data_validator.clean_data_batch(data, cleaning_rules)


# 预定义的验证模式
PREDEFINED_SCHEMAS = {
    'basic_webpage': {
        'title': {
            'field_type': 'string',
            'required': True,
            'min_length': 1,
            'max_length': 200,
            'cleaners': ['trim', 'remove_html', 'normalize_whitespace']
        },
        'url': {
            'field_type': 'url',
            'required': True
        },
        'content': {
            'field_type': 'string',
            'required': False,
            'max_length': 10000,
            'cleaners': ['trim', 'remove_html', 'normalize_whitespace']
        },
        'publish_date': {
            'field_type': 'date',
            'required': False
        }
    },
    'ecommerce_product': {
        'name': {
            'field_type': 'string',
            'required': True,
            'min_length': 1,
            'max_length': 200,
            'cleaners': ['trim', 'normalize_whitespace']
        },
        'price': {
            'field_type': 'price',
            'required': True
        },
        'description': {
            'field_type': 'string',
            'required': False,
            'max_length': 5000,
            'cleaners': ['trim', 'remove_html', 'normalize_whitespace']
        },
        'image_url': {
            'field_type': 'url',
            'required': False
        },
        'availability': {
            'field_type': 'string',
            'required': False,
            'pattern': r'(in_stock|out_of_stock|preorder)'
        }
    },
    'contact_info': {
        'name': {
            'field_type': 'string',
            'required': True,
            'min_length': 1,
            'max_length': 100,
            'cleaners': ['trim', 'normalize_whitespace', 'title_case']
        },
        'email': {
            'field_type': 'email',
            'required': True
        },
        'phone': {
            'field_type': 'chinese_phone',
            'required': False
        },
        'company': {
            'field_type': 'string',
            'required': False,
            'max_length': 100,
            'cleaners': ['trim', 'normalize_whitespace']
        }
    }
}


def get_predefined_schema(schema_name: str) -> Dict[str, Dict[str, Any]]:
    """获取预定义的验证模式"""
    return PREDEFINED_SCHEMAS.get(schema_name, {})


def validate_with_predefined_schema(
    data: Dict[str, Any],
    schema_name: str
) -> Dict[str, Any]:
    """使用预定义模式验证数据"""
    schema = get_predefined_schema(schema_name)
    if not schema:
        logger.warning(f"未知的预定义模式: {schema_name}")
        return {'is_valid': False, 'errors': [f"未知的验证模式: {schema_name}"]}

    return validate_data_object(data, schema)\n\n\n# 导出常用函数和类
__all__ = [
    'DataValidator',
    'data_validator',
    'validate_field_value',
    'validate_data_object',
    'extract_data_from_text',
    'clean_data_with_rules',
    'get_predefined_schema',
    'validate_with_predefined_schema',
    'PREDEFINED_SCHEMAS'
]