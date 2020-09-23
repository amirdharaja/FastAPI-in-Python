def user_serializer(data, is_multiple=None):
    if is_multiple:
        serialized_data = []
        for d in data:
            serialized_data.append({
                'id': d.id,
                'username': d.username,
                'password': d.password,
                'first_name': d.first_name,
                'last_name': d.last_name,
                'phone': d.phone,
                'gender': d.gender,
                'created_at': str(d.created_at),
                'updated_at': str(d.updated_at),
            })
        return serialized_data
    else:
        serialized_data = {
            'id': data.id,
            'username': data.username,
            'password': data.password,
            'first_name': data.first_name,
            'last_name': data.last_name,
            'phone': data.phone,
            'gender': data.gender,
            'created_at': str(data.created_at),
            'updated_at': str(data.updated_at),
        }
        return serialized_data


