import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

token_auth_scheme = HTTPBearer()


class Auth:
    """Fast api dependency that validates an JWT token."""

    def __init__(self, domain: str, api_audience: str, algorithm: str):
        self._domain = domain
        self._api_audience = api_audience
        self._algorithm = algorithm

        self._jwks_client = jwt.PyJWKClient(f"https://{domain}/.well-known/jwks.json")

    def __call__(self, request: Request, auth_credentials: HTTPAuthorizationCredentials = Depends(token_auth_scheme)):
        token = auth_credentials.credentials

        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token).key
        except (jwt.exceptions.PyJWKClientError, jwt.exceptions.DecodeError) as e:
            raise HTTPException(status_code=401, detail=str(e))

        try:
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=self._algorithm,
                audience=self._api_audience,
                issuer=f"https://{self._domain}/",
            )
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

        request.state.auth = payload

        return payload
