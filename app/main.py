import os
from fastapi import FastAPI, Depends
from fastapi.security import OAuth2AuthorizationCodeBearer
from app.security.deps import get_current_user
from app.api.v1 import metadata

app = FastAPI(
    title="SMART-PACER Registry Viewer API",
    version="v1.11.1",
    description="FastAPI implementation of the SMART-PACER Registry Viewer API",
    dependencies=[Depends(get_current_user)],
)

# OAuth2 security scheme (exposed in generated OpenAPI)
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://{os.getenv('AUTH0_DOMAIN')}/authorize",
    tokenUrl=f"https://{os.getenv('AUTH0_DOMAIN')}/oauth/token",
    scopes={
        "read:syphilis": "Read data from the syphilis registry",
        "write:syphilis": "Write data to the syphilis registry",
        "read:scd": "Read data from the scd registry",
        "write:scd": "Write data to the scd registry",
        "read:metadata": "Read metadata entries",
        "write:metadata": "Create / modify metadata entries",
    },
)

# Include API routers
app.include_router(metadata.router)
