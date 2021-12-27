from fastapi import FastAPI
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from starlette.requests import Request
from starlette.responses import JSONResponse
from pydantic import EmailStr, BaseModel
from typing import List
from pathlib import Path




class EmailSchema(BaseModel):
   email: List[EmailStr]

conf = ConnectionConfig(
    MAIL_USERNAME = "okechukwusamuel16@gmail.com",
    MAIL_PASSWORD = "xsmtpsib-aec1862e5aa1d60c5ee87526ef56eb58515110f5a9350c088a0d38d1f5dc45b9-Zj8zMnPKIWD0gFV2",
    MAIL_FROM = "no-reply@sendinblue.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp-relay.sendinblue.com",
    MAIL_TLS = True,
    MAIL_SSL = False,
    TEMPLATE_FOLDER = Path(__file__).parent / 'templates',
)




async def send_activation_email(email: str, body: dict):

    message = MessageSchema(
        
        subject="Activate Your Email",
        recipients=[email],  # List of recipients, as many as you can pass
        template_body=body
        )
 
    fm = FastMail(conf)
    await fm.send_message(message, template_name="activation_email.html")

    
