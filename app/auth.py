from fastapi import Header, HTTPException
from fastapi import Request
from http import HTTPStatus
from app.models import GenericResponse
from app.enum import ErrorCode
from app.tracing import get_trace, tracer
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, SERVICE_ID
import jwt
from app.models import Trace
from fastapi import Depends


async def get_current_user(
    request: Request, 
    x_request_id: str | None = Header(default=None), 
    x_device_id: str | None = Header(default=None),
    authorization: str = Header(),
    trace: Trace = Depends(get_trace)
):
    body = await request.body()
    body_str = body.decode('utf-8')
    headers = request.headers
    attributes: dict[str, str] = {
        'body': body_str,
        'token': str(authorization), 
        'request_id': headers.get('x-request-id', ''), 
        'device_id': x_device_id or '',
    }

    with tracer.start_as_current_span("get_request_param", attributes=attributes) as span:
        credentials_exception = HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=GenericResponse.get_error_response(
                    error_code=ErrorCode.ERROR_CODE_AUTH_ERROR,
                    customer_message='Invalid Token',
                    debug_info={}
                ),
        )
        if not authorization:
            raise credentials_exception
        try:
            token = authorization.split("Bearer ")[1]
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            elif username != SERVICE_ID:
                raise credentials_exception
            
        except Exception:
            raise credentials_exception
        return trace


async def get_user_account_model(identifier: str| None = None, uuid: None = None) -> UserAccountModel | None:
    q = Q()
    if identifier:
        q &= Q(mobile_no=identifier)
    if uuid:
        q &=Q(id=uuid) 
    user_obj = await UserAccountModel.filter(q).first()
    if user_obj is None:
        return None
    return user_obj