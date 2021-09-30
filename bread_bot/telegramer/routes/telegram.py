import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request

from bread_bot.auth.methods.auth_methods import get_current_active_admin_user
from bread_bot.telegramer.models import LocalMeme, Chat, Member
from bread_bot.telegramer.schemas.api_models import LocalMemeSchema, \
    SendMessageSchema, ChatSchema, MemberDBSchema
from bread_bot.telegramer.schemas.telegram_messages import StandardBodySchema
from bread_bot.telegramer.services.message_handler import MessageHandler
from bread_bot.telegramer.services.telegram_client import TelegramClient
from bread_bot.utils.dependencies import get_async_session

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=['telegram'],
    responses={404: {'description': 'Not found'}},
)


@router.post('/')
async def handle_message(
        request: Request,
        request_body: StandardBodySchema,
        db: AsyncSession = Depends(get_async_session)
):
    import json
    data = await request.body()
    logger.debug(json.loads(data))
    try:
        await MessageHandler(request_body=request_body, db=db).handle_message()
    except Exception:
        pass
    return 'OK'


@router.post('/set_local_meme',
             dependencies=[Depends(get_current_active_admin_user)])
async def set_local_meme(
        request_body: LocalMemeSchema,
        db: AsyncSession = Depends(get_async_session)
):
    local_meme = await LocalMeme.async_first(
        session=db,
        filter_expression=(LocalMeme.type == request_body.type) &
                          (LocalMeme.chat_id == request_body.chat_id),
    )
    if not local_meme:
        await LocalMeme.async_add_by_schema(
            db=db,
            instance_schema=request_body,
        )
    else:
        local_meme.data = request_body.data
        await LocalMeme.async_add(db, local_meme)
    return 'OK'


@router.post('/send_message',
             dependencies=[Depends(get_current_active_admin_user)])
async def send_message_to_chat(
        message: SendMessageSchema,
):
    telegram_client = TelegramClient()
    try:
        await telegram_client.send_message(
            chat_id=message.chat_id,
            message=message.message,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Произошла ошибка отправки сообщения'
        )
    return 'OK'


@router.get('/chats',
            response_model=List[ChatSchema],
            dependencies=[Depends(get_current_active_admin_user)])
async def get_chats(db: AsyncSession = Depends(get_async_session)):
    return await Chat.async_all(db)


@router.get('/members',
            response_model=List[MemberDBSchema],
            dependencies=[Depends(get_current_active_admin_user)])
async def get_members(db: AsyncSession = Depends(get_async_session)):
    return await Member.async_all(db)


@router.get('/members/{username}',
            response_model=MemberDBSchema,
            dependencies=[Depends(get_current_active_admin_user)])
async def get_members(username: str,
                      db: AsyncSession = Depends(get_async_session)):
    member = await Member.async_first(db, Member.username == username)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )
    return member


@router.delete('/members/{username}',
               dependencies=[Depends(get_current_active_admin_user)])
async def get_members(username: str,
                      db: AsyncSession = Depends(get_async_session)):
    return {
        'deleted': await Member.async_delete(
            session=db,
            filter_expression=Member.username == username)
    }
