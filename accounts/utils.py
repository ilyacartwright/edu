def get_nested_field_value(obj, field_name):
    """
    Получает значение вложенного поля объекта
    Например, для поля 'group.specialization.name' получит объект.group.specialization.name
    """
    if obj is None:
        return None
        
    # Если поле содержит точку, значит это вложенное поле
    if '.' in field_name:
        parts = field_name.split('.')
        value = obj
        for part in parts:
            if value is None:
                return None
                
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
        return value
    
    # Проверка на get_*_display поля (для полей с choices)
    display_field = f"get_{field_name}_display"
    if hasattr(obj, display_field) and callable(getattr(obj, display_field)):
        return getattr(obj, display_field)()
    
    # Обычное поле
    if hasattr(obj, field_name):
        return getattr(obj, field_name)
    
    return None