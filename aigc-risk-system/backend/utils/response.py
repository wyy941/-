def success(data=None, message="success", code=200):
    return {
        "code": code,
        "message": message,
        "data": data,
    }, code


def error(message="error", code=400, data=None):
    return {
        "code": code,
        "message": message,
        "data": data,
    }, code
