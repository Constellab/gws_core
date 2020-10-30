import os
from base64 import b64encode

# def async_crsf_protect(function):
#     async def wrapper(*args, **kwargs):
#         request = None
#         for arg in args:
#             if isinstance(arg, Request):
#                 request = arg
#                 break
        
#         if request is None:
#             raise Exception("Invalid request")
        
#         if request["method"] == "GET":
#             if not "crsf" in request.session:
#                 random_bytes = os.urandom(64)
#                 token = b64encode(random_bytes).decode('utf-8')
#                 request.session["crsf"] = token
#         else:
#             if request.session.get("crsf", None) is None:
#                 raise Exception("Invalid CRSF token")
            
#             f = await request.form()
#             if request.session["crsf"] != f.get("crsf", None):
#                 raise Exception("Invalid CRSF token")
                            
#         return await function(*args, **kwargs)

#     return wrapper
